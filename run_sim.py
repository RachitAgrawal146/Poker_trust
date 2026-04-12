"""
Stage 8 research simulation runner.

Plays the full 10,000-hand × N-seed Limit Hold'em simulation and writes
every hand to a persistent SQLite database via ``data.sqlite_logger``.

Usage (research run, takes hours)::

    python3 run_sim.py --seeds 42,137,256,512,1024 --hands 10000 \\
        --db runs.sqlite --stage 5

Usage (smoke test, seconds)::

    python3 run_sim.py --seeds 42 --hands 500 --db /tmp/smoke.sqlite

The runner is stage-parametric: ``--stage 5`` uses the Stage 4 static
roster plus 3 Oracle fillers (what Stage 5 tests also use); higher stages
can register new rosters in ``_STAGE_ROSTERS`` as they come online. This
file deliberately does NOT import Stage 6/9 modules — those tracks are in
flight on parallel branches.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Callable, Dict, List

from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.table import Table


# ---------------------------------------------------------------------------
# Stage roster registry
# ---------------------------------------------------------------------------


def _stage5_roster() -> List:
    """8-seat static roster used for the Stage 5 research run.

    Mirrors ``_build_stage_5`` in ``run_tests.py`` so a full Stage 8 run
    logs the same configuration the Stage 5 trust-model tests exercise.
    """
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom

    return [
        Oracle(seat=0),
        Sentinel(seat=1),
        Firestorm(seat=2),
        Wall(seat=3),
        Phantom(seat=4),
        Oracle(seat=5, name="Oracle-5"),
        Oracle(seat=6, name="Oracle-6"),
        Oracle(seat=7, name="Oracle-7"),
    ]


def _stage6_roster() -> List:
    """Full 8-archetype canonical roster for Stage 6 research runs.

    Matches ``_stage6_agents`` in ``run_demo.py`` and ``_build_stage_6`` in
    ``run_tests.py``: seats 0-4 are the static archetypes (Oracle / Sentinel
    / Firestorm / Wall / Phantom) and seats 5-7 are the adaptive agents
    (Predator / Mirror / Judge). This is the canonical Phase 1 roster.
    """
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from agents.predator import Predator
    from agents.mirror import Mirror
    from agents.judge import Judge

    return [
        Oracle(seat=0),
        Sentinel(seat=1),
        Firestorm(seat=2),
        Wall(seat=3),
        Phantom(seat=4),
        Predator(seat=5),
        Mirror(seat=6),
        Judge(seat=7),
    ]


#: stage number → zero-arg agent-builder. Stage 5 is retained for
#: reproducibility with older runs; Stage 6 is the canonical research roster.
_STAGE_ROSTERS: Dict[int, Callable[[], List]] = {
    5: _stage5_roster,
    6: _stage6_roster,
}


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------


def _fmt_eta(seconds: float) -> str:
    if seconds <= 0 or seconds != seconds:  # NaN guard
        return "--:--"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _print_progress(
    seed: int, hand_i: int, total: int, started: float
) -> None:
    elapsed = time.time() - started
    rate = hand_i / elapsed if elapsed > 0 else 0.0
    remaining = (total - hand_i) / rate if rate > 0 else 0.0
    pct = 100.0 * hand_i / total if total else 100.0
    bar_width = 30
    filled = int(bar_width * hand_i / total) if total else bar_width
    bar = "#" * filled + "." * (bar_width - filled)
    msg = (
        f"\r  seed {seed:>5} [{bar}] {hand_i:>6}/{total:<6} "
        f"{pct:5.1f}% · {rate:6.1f} hand/s · ETA {_fmt_eta(remaining)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Per-seed run
# ---------------------------------------------------------------------------


def run_one_seed(
    seed: int,
    num_hands: int,
    stage: int,
    logger: SQLiteLogger,
    label: str,
) -> Dict[str, int]:
    """Build a table, play ``num_hands`` hands, log everything.

    Returns a per-seed summary dict the CLI prints at the end of each run.
    """
    builder = _STAGE_ROSTERS.get(stage)
    if builder is None:
        raise SystemExit(
            f"No roster registered for stage {stage}. "
            f"Available stages: {sorted(_STAGE_ROSTERS)}"
        )
    agents = builder()
    num_seats = len(agents)
    starting_stack = SIMULATION["starting_stack"]

    run_id = logger.start_run(
        seed=seed,
        num_hands=num_hands,
        label=label,
        agents=agents,
    )
    table = Table(agents, seed=seed, logger=logger, run_id=run_id)

    started = time.time()
    for i in range(1, num_hands + 1):
        table.play_hand()
        if i % 100 == 0 or i == num_hands:
            _print_progress(seed, i, num_hands, started)
    sys.stdout.write("\n")
    sys.stdout.flush()

    logger.log_agent_stats(run_id, table)

    # Print Judge grievance summary for this seed (if Judge is present).
    for a in agents:
        if a.archetype == "judge" and hasattr(a, "grievance_summary"):
            summary_lines = a.grievance_summary()
            if summary_lines:
                print(f"  Judge grievances (seed={seed}):")
                for s_seat, count, triggered, trigger_hand in summary_lines:
                    arch_name = agents[s_seat].archetype if s_seat < len(agents) else f"seat{s_seat}"
                    t_str = f"TRIGGERED at hand {trigger_hand}" if triggered else "not triggered"
                    print(f"    vs {arch_name:15s} (seat {s_seat}): grievance={count:3d}  {t_str}")
            break

    # Per-run summary. Everything comes back out of SQLite so we verify the
    # logger is round-trip consistent in the same process.
    cur = logger.conn.cursor()
    total_actions = cur.execute(
        "SELECT COUNT(*) FROM actions WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    total_showdowns = cur.execute(
        "SELECT COUNT(*) FROM hands WHERE run_id = ? AND had_showdown = 1",
        (run_id,),
    ).fetchone()[0]
    total_walkovers = cur.execute(
        "SELECT COUNT(*) FROM hands WHERE run_id = ? AND had_showdown = 0",
        (run_id,),
    ).fetchone()[0]
    stack_sum = cur.execute(
        "SELECT COALESCE(SUM(final_stack), 0) FROM agent_stats "
        "WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    rebuy_sum = cur.execute(
        "SELECT COALESCE(SUM(rebuys), 0) FROM agent_stats WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]

    # Chip conservation check: final chips in stacks equal
    # (initial buy-in + rebuys) × starting_stack. Rebuys top up an empty
    # seat by ``starting_stack``, so every chip in the economy is accounted
    # for by (num_seats + rebuys) × starting_stack. The Stage 8 spec wants
    # ``final_stack + rebuys * starting_stack - num_seats * starting_stack == 0``.
    expected_stack = (num_seats + rebuy_sum) * starting_stack
    chip_delta = int(stack_sum) - expected_stack

    return {
        "seed": seed,
        "run_id": run_id,
        "num_hands": num_hands,
        "total_actions": int(total_actions),
        "total_showdowns": int(total_showdowns),
        "total_walkovers": int(total_walkovers),
        "final_stack_sum": int(stack_sum),
        "rebuy_sum": int(rebuy_sum),
        "num_seats": num_seats,
        "chip_delta": int(chip_delta),
        "starting_stack": starting_stack,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        default=",".join(str(s) for s in SIMULATION["seeds"]),
        help="Comma-separated list of integer seeds.",
    )
    parser.add_argument(
        "--hands",
        type=int,
        default=SIMULATION["num_hands"],
        help="Hands to play per seed (default: 10000).",
    )
    parser.add_argument(
        "--db",
        default="runs.sqlite",
        help="SQLite database path (default: runs.sqlite).",
    )
    parser.add_argument(
        "--stage",
        type=int,
        default=max(_STAGE_ROSTERS),
        help="Stage roster to use (default: highest registered).",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Free-form label stored in the runs table.",
    )
    args = parser.parse_args(argv)

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    label = args.label or f"stage{args.stage}-{args.hands}h"

    logger = SQLiteLogger(args.db)
    print(
        f"Logging {len(seeds)} seed(s) × {args.hands} hands "
        f"to {args.db} (stage {args.stage})"
    )

    summaries: List[Dict[str, int]] = []
    for seed in seeds:
        summary = run_one_seed(
            seed=seed,
            num_hands=args.hands,
            stage=args.stage,
            logger=logger,
            label=label,
        )
        summaries.append(summary)

    logger.close()

    # --- Final per-seed summary ---
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    all_conserved = True
    for s in summaries:
        conserved = (s["chip_delta"] == 0)
        all_conserved = all_conserved and conserved
        print(
            f"seed={s['seed']:<5} run_id={s['run_id']:<4} "
            f"hands={s['num_hands']:<6} "
            f"actions={s['total_actions']:<8} "
            f"showdowns={s['total_showdowns']:<6} "
            f"walkovers={s['total_walkovers']:<6}"
        )
        print(
            f"           final_stacks={s['final_stack_sum']:<6} "
            f"rebuys={s['rebuy_sum']:<4} "
            f"chip_delta={s['chip_delta']:<4} "
            f"{'OK' if conserved else 'FAIL'}"
        )
    print("=" * 72)
    print(
        "Chip conservation: "
        + ("all seeds OK" if all_conserved else "FAILED — check logs")
    )
    return 0 if all_conserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
