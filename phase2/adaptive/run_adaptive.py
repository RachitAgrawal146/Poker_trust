"""
Phase 2 (adaptive) simulation runner.

Builds an 8-seat table of AdaptiveAgents (one per archetype, plus the
AdaptiveJudge), wires one HillClimber per agent, and plays the
canonical 3-seed x 5000-hand research run. The trust model is left
unchanged from Phase 1 -- it imports the static archetype likelihood
tables, so as agents adapt their reputation grows increasingly
miscalibrated. Schema is identical to Phase 1's so analyze_runs.py /
deep_analysis.py work without modification.

Outputs:
  --db <path>                 -- SQLite (default: runs_phase2_adaptive.sqlite)
  --trajectories <path>       -- per-agent param history JSON
                                 (default: phase2/adaptive/param_trajectories.json)
  --optlog <path>             -- per-cycle hill-climber log JSON
                                 (default: phase2/adaptive/optimization_log.json)

Usage::

    python3 phase2/adaptive/run_adaptive.py --hands 5000 --seeds 42,137,256

Smoke test (~minute)::

    python3 phase2/adaptive/run_adaptive.py --hands 50 --seeds 42 --eval-window 10
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

import argparse
import json
import sys
import time
from typing import Any, Dict, List

import numpy as np

from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.table import Table

from phase2.adaptive.adaptive_agent import AdaptiveAgent, AdaptiveJudge
from phase2.adaptive.bounds import (
    ARCHETYPE_BOUNDS,
    make_unbounded_bounds,
    verify_bounds_cover_initial_values,
)
from phase2.adaptive.hill_climber import HillClimber

__all__ = ["build_adaptive_roster", "run_one_seed", "main"]


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

ARCHETYPES = [
    (0, "Adaptive-Oracle",    "oracle",    "oracle"),
    (1, "Adaptive-Sentinel",  "sentinel",  "sentinel"),
    (2, "Adaptive-Firestorm", "firestorm", "firestorm"),
    (3, "Adaptive-Wall",      "wall",      "wall"),
    (4, "Adaptive-Phantom",   "phantom",   "phantom"),
    (5, "Adaptive-Predator",  "predator",  "predator_baseline"),
    (6, "Adaptive-Mirror",    "mirror",    "mirror_default"),
    # seat 7 is AdaptiveJudge (special class)
]


def build_adaptive_roster() -> List[AdaptiveAgent]:
    agents: List[AdaptiveAgent] = []
    for seat, name, archetype, params_key in ARCHETYPES:
        agents.append(
            AdaptiveAgent(
                seat=seat, name=name, archetype=archetype,
                initial_params_key=params_key,
            )
        )
    agents.append(AdaptiveJudge(seat=7))
    return agents


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def _fmt_eta(seconds: float) -> str:
    if seconds <= 0 or seconds != seconds:
        return "--:--"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _print_progress(seed: int, hand_i: int, total: int, started: float) -> None:
    elapsed = time.time() - started
    rate = hand_i / elapsed if elapsed > 0 else 0.0
    remaining = (total - hand_i) / rate if rate > 0 else 0.0
    pct = 100.0 * hand_i / total if total else 100.0
    bar_w = 30
    filled = int(bar_w * hand_i / total) if total else bar_w
    bar = "#" * filled + "." * (bar_w - filled)
    msg = (
        f"\r  seed {seed:>5} [{bar}] {hand_i:>5}/{total:<5} "
        f"{pct:5.1f}% | {rate:5.1f} hand/s | ETA {_fmt_eta(remaining)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Per-seed run
# ---------------------------------------------------------------------------

def run_one_seed(
    seed: int,
    num_hands: int,
    eval_window: int,
    delta: float,
    min_delta: float,
    decay_rate: float,
    logger: SQLiteLogger,
    label: str,
    unbounded: bool = False,
) -> Dict[str, Any]:
    agents = build_adaptive_roster()
    num_seats = len(agents)
    starting_stack = SIMULATION["starting_stack"]

    run_id = logger.start_run(
        seed=seed, num_hands=num_hands, label=label, agents=agents,
    )
    table = Table(agents, seed=seed, logger=logger, run_id=run_id)

    bounds = make_unbounded_bounds() if unbounded else ARCHETYPE_BOUNDS

    # One HillClimber per agent; seed each climber's RNG deterministically
    # off the global seed + the agent's seat so different seeds produce
    # different perturbation orders, but the same seed reproduces.
    climbers: List[HillClimber] = []
    for a in agents:
        hc_rng = np.random.default_rng(seed * 100003 + a.seat * 17)
        climbers.append(
            HillClimber(
                agent=a,
                eval_window=eval_window,
                delta=delta,
                min_delta=min_delta,
                decay_rate=decay_rate,
                rng=hc_rng,
                bounds=bounds,
            )
        )

    # Per-agent rolling stack/rebuy reference for true P/L computation.
    last_stack = [a.stack for a in agents]
    last_rebuys = [a.rebuys for a in agents]

    started = time.time()
    for i in range(1, num_hands + 1):
        table.play_hand()

        for agent_index, agent in enumerate(agents):
            stack_now = agent.stack
            rebuys_now = agent.rebuys
            rebuy_delta = rebuys_now - last_rebuys[agent_index]
            # True P/L = stack delta minus chips infused via rebuys.
            hand_profit = (
                stack_now - last_stack[agent_index]
                - rebuy_delta * starting_stack
            )
            climbers[agent_index].on_hand_end(i, float(hand_profit))
            last_stack[agent_index] = stack_now
            last_rebuys[agent_index] = rebuys_now

        if i % 50 == 0 or i == num_hands:
            _print_progress(seed, i, num_hands, started)

    sys.stdout.write("\n")
    sys.stdout.flush()

    logger.log_agent_stats(run_id, table)

    # Judge summary, mirrors Phase 1 runner
    for a in agents:
        if a.archetype == "judge" and hasattr(a, "grievance_summary"):
            summary_lines = a.grievance_summary()
            if summary_lines:
                print(f"  Judge grievances (seed={seed}):")
                for s_seat, count, triggered, _ in summary_lines:
                    arch = (
                        agents[s_seat].archetype
                        if s_seat < len(agents)
                        else f"seat{s_seat}"
                    )
                    t_str = "TRIGGERED" if triggered else "not triggered"
                    print(
                        f"    vs {arch:15s} (seat {s_seat}): "
                        f"grievance={count:3d}  {t_str}"
                    )
            break

    # Climber summaries
    print(f"  HillClimber summaries (seed={seed}):")
    for c in climbers:
        s = c.summary()
        print(
            f"    seat={s['seat']} {s['archetype']:10s} "
            f"cycles={s['cycles']:3d}  accepted={s['accepted']:3d}  "
            f"rejected={s['rejected']:3d}  delta={s['current_delta']:.4f}"
        )

    # Chip conservation
    cur = logger.conn.cursor()
    stack_sum = cur.execute(
        "SELECT COALESCE(SUM(final_stack), 0) FROM agent_stats WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    rebuy_sum = cur.execute(
        "SELECT COALESCE(SUM(rebuys), 0) FROM agent_stats WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    expected = (num_seats + rebuy_sum) * starting_stack
    chip_delta = int(stack_sum) - expected

    return {
        "seed": seed,
        "run_id": run_id,
        "num_hands": num_hands,
        "chip_delta": chip_delta,
        "agents": agents,
        "climbers": climbers,
    }


# ---------------------------------------------------------------------------
# Trajectory + log serialization
# ---------------------------------------------------------------------------

def _serialize_trajectories(seed_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for summary in seed_summaries:
        seed = summary["seed"]
        per_seed: Dict[str, Any] = {}
        for agent in summary["agents"]:
            per_seed[f"seat_{agent.seat}_{agent.archetype}"] = [
                {"hand": h, "params": p}
                for (h, p) in agent.param_history
            ]
        out[f"seed_{seed}"] = per_seed
    return out


def _serialize_optlog(seed_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for summary in seed_summaries:
        seed = summary["seed"]
        out[f"seed_{seed}"] = [
            {**entry}
            for c in summary["climbers"]
            for entry in c.log
        ]
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", default="42,137,256",
        help="Comma-separated seeds. Default: first 3 Phase 1 seeds.",
    )
    parser.add_argument(
        "--hands", type=int, default=5000,
        help="Hands per seed. Default: 5000.",
    )
    parser.add_argument(
        "--db", default="runs_phase2_adaptive.sqlite",
        help="SQLite database path.",
    )
    parser.add_argument(
        "--trajectories",
        default="phase2/adaptive/param_trajectories.json",
        help="Per-agent parameter history output path.",
    )
    parser.add_argument(
        "--optlog",
        default="phase2/adaptive/optimization_log.json",
        help="Per-cycle hill-climber log output path.",
    )
    parser.add_argument(
        "--eval-window", type=int, default=200,
        help="Hill-climber phase length in hands. Default: 200.",
    )
    parser.add_argument(
        "--delta", type=float, default=0.03,
        help="Initial perturbation magnitude. Default: 0.03.",
    )
    parser.add_argument(
        "--min-delta", type=float, default=0.005,
        help="Floor for delta after decay. Default: 0.005.",
    )
    parser.add_argument(
        "--decay-rate", type=float, default=0.995,
        help="Per-cycle delta multiplier. Default: 0.995.",
    )
    parser.add_argument(
        "--label", default=None,
        help="Free-form run label.",
    )
    parser.add_argument(
        "--unbounded", action="store_true", default=False,
        help="Replace ARCHETYPE_BOUNDS with full [0, 1] freedom on every "
             "(round, metric). Tests whether agents converge to a common "
             "equilibrium when the personality cage is removed.",
    )
    args = parser.parse_args(argv)

    # Validate bounds before doing anything expensive (skip when unbounded —
    # the [0,1] box trivially covers every Phase 1 starting value).
    if not args.unbounded:
        verify_bounds_cover_initial_values()

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    suffix = "-unbounded" if args.unbounded else ""
    label = (
        args.label
        or f"phase2-adaptive{suffix}-{args.hands}h-eval{args.eval_window}-d{args.delta}"
    )

    mode = "UNBOUNDED [0, 1]" if args.unbounded else "bounded (per-archetype)"
    print(f"Phase 2 (adaptive) -- online hill-climbing  mode={mode}", flush=True)
    print(f"  Seeds:      {seeds}", flush=True)
    print(f"  Hands/seed: {args.hands}", flush=True)
    print(f"  Eval window: {args.eval_window}  delta={args.delta}  "
          f"min={args.min_delta}  decay={args.decay_rate}", flush=True)
    print(f"  DB:         {args.db}", flush=True)
    print(flush=True)

    logger = SQLiteLogger(args.db)
    summaries: List[Dict[str, Any]] = []

    for seed in seeds:
        summary = run_one_seed(
            seed=seed,
            num_hands=args.hands,
            eval_window=args.eval_window,
            delta=args.delta,
            min_delta=args.min_delta,
            decay_rate=args.decay_rate,
            logger=logger,
            label=label,
            unbounded=args.unbounded,
        )
        summaries.append(summary)

    logger.close()

    # Serialize trajectories + opt log.
    traj_path = _Path(args.trajectories)
    traj_path.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_path, "w", encoding="utf-8") as f:
        json.dump(_serialize_trajectories(summaries), f, indent=1)
    log_path = _Path(args.optlog)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(_serialize_optlog(summaries), f, indent=1)

    # Final summary
    print()
    print("=" * 72)
    print("PHASE 2 ADAPTIVE SIMULATION SUMMARY")
    print("=" * 72)
    all_conserved = True
    for s in summaries:
        conserved = s["chip_delta"] == 0
        all_conserved = all_conserved and conserved
        print(
            f"  seed={s['seed']:<5} hands={s['num_hands']:<5} "
            f"chip_delta={s['chip_delta']:<4} {'OK' if conserved else 'FAIL'}"
        )
    print("=" * 72)
    print(f"Chip conservation: {'all OK' if all_conserved else 'FAILED'}")
    print(f"Trajectories saved to: {traj_path}")
    print(f"Optimization log saved to: {log_path}")
    return 0 if all_conserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
