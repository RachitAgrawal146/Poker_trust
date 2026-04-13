#!/usr/bin/env python3
"""
Phase 3 — Simulation Runner

Loads LLM-generated parameters from phase3/generated_params/all_params.json,
creates LLMAgent/LLMPredator/LLMJudge instances in the canonical 8-seat
roster, runs through the same Phase 1 game engine with the Dealer active,
and logs everything to a SQLite database.

Configuration: 25,000 hands x 20 seeds (same seeds as Phase 1 v3).

Usage::

    # After running generate_params.py:
    python3 phase3/run_phase3.py

    # Custom seeds/hands:
    python3 phase3/run_phase3.py --seeds 42,137,256 --hands 5000

    # Specify database:
    python3 phase3/run_phase3.py --db runs_phase3.sqlite

NOTE: This script will FAIL if generate_params.py has not been run first.
That is expected — there is no offline fallback for parameters.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure repo root is on sys.path so we can import Phase 1 modules
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.actions import ActionType
from engine.table import Table

from phase3.llm_agent import (
    LLMAgent,
    LLMJudge,
    LLMPredator,
)
from phase3.generated_params import GENERATED_PARAMS
from phase3.dealer import Dealer


# ---------------------------------------------------------------------------
# Seeds — same 20 seeds as Phase 1 v3 research run
# ---------------------------------------------------------------------------

PHASE3_SEEDS = [
    42, 137, 256, 512, 1024,
    2048, 4096, 8192, 16384, 32768,
    65536, 131072, 262144, 524288, 1048576,
    2097152, 4194304, 8388608, 16777216, 33554432,
]

PHASE3_HANDS = 25_000


# ---------------------------------------------------------------------------
# Roster builder
# ---------------------------------------------------------------------------

def build_phase3_roster(params: Dict[str, Any]) -> List:
    """Build the canonical 8-seat Phase 3 roster with LLM-generated params.

    Seats match Phase 1 canonical layout:
        0: Oracle, 1: Sentinel, 2: Firestorm, 3: Wall,
        4: Phantom, 5: Predator, 6: Mirror, 7: Judge
    """
    return [
        LLMAgent(seat=0, name="LLM-Oracle", archetype="oracle", params=params),
        LLMAgent(seat=1, name="LLM-Sentinel", archetype="sentinel", params=params),
        LLMAgent(seat=2, name="LLM-Firestorm", archetype="firestorm", params=params),
        LLMAgent(seat=3, name="LLM-Wall", archetype="wall", params=params),
        LLMAgent(seat=4, name="LLM-Phantom", archetype="phantom", params=params),
        LLMPredator(seat=5, params=params, name="LLM-Predator"),
        LLMAgent(seat=6, name="LLM-Mirror", archetype="mirror", params=params),
        LLMJudge(seat=7, params=params, name="LLM-Judge"),
    ]


# ---------------------------------------------------------------------------
# Progress bar (same pattern as Phase 1 run_sim.py)
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
        f"\r  seed {seed:>8} [{bar}] {hand_i:>6}/{total:<6} "
        f"{pct:5.1f}% | {rate:6.1f} hand/s | ETA {_fmt_eta(remaining)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Per-seed run
# ---------------------------------------------------------------------------

def run_one_seed(
    seed: int,
    num_hands: int,
    params: Dict[str, Any],
    logger: SQLiteLogger,
    label: str,
) -> Dict[str, Any]:
    """Build a table with LLM agents, play num_hands, log everything.

    Returns a per-seed summary dict.
    """
    agents = build_phase3_roster(params)
    num_seats = len(agents)
    starting_stack = SIMULATION["starting_stack"]

    run_id = logger.start_run(
        seed=seed,
        num_hands=num_hands,
        label=label,
        agents=agents,
    )
    table = Table(agents, seed=seed, logger=logger, run_id=run_id)

    # Create the Dealer integrity layer
    dealer = Dealer(
        num_seats=num_seats,
        starting_stack=starting_stack,
        anomaly_check_interval=500,
    )

    started = time.time()
    for i in range(1, num_hands + 1):
        # Record VPIP status for each agent from previous hand
        # (simplified: dealer tracks from action observations)
        table.play_hand()

        # Post-hand audit
        seat_stacks = [a.stack for a in agents]
        total_rebuys = sum(a.rebuys for a in agents)
        showdown_data = None
        if table.last_hand is not None:
            showdown_data = table.last_hand.showdown_data
        dealer.post_hand_audit(
            hand_id=i,
            seat_stacks=seat_stacks,
            total_rebuys=total_rebuys,
            showdown_data=showdown_data,
        )

        # Track VPIP for each agent using per-hand action log
        vpip_this_hand = set()
        if table.last_hand is not None:
            for record in table.last_hand.action_log:
                dealer._seat_archetypes[record.seat] = record.archetype
                if (record.betting_round == "preflop"
                        and record.action_type in (
                            ActionType.CALL, ActionType.BET, ActionType.RAISE)):
                    vpip_this_hand.add(record.seat)
        for a in agents:
            dealer.record_hand_vpip(a.seat, a.seat in vpip_this_hand)

        if i % 100 == 0 or i == num_hands:
            _print_progress(seed, i, num_hands, started)
    sys.stdout.write("\n")
    sys.stdout.flush()

    logger.log_agent_stats(run_id, table)

    # Print Judge grievance summary
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

    # Chip conservation check
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
        "dealer_substitutions": dealer.total_substitutions,
        "dealer_anomalies": len(dealer.anomalies),
        "dealer": dealer,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 simulation runner — LLM-generated archetype agents"
    )
    parser.add_argument(
        "--seeds",
        default=",".join(str(s) for s in PHASE3_SEEDS),
        help=(
            "Comma-separated list of integer seeds. "
            f"Default: 20 Phase 1 v3 seeds."
        ),
    )
    parser.add_argument(
        "--hands",
        type=int,
        default=PHASE3_HANDS,
        help=f"Hands to play per seed (default: {PHASE3_HANDS}).",
    )
    parser.add_argument(
        "--db",
        default="runs_phase3.sqlite",
        help="SQLite database path (default: runs_phase3.sqlite).",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Free-form label stored in the runs table.",
    )
    parser.add_argument(
        "--audit",
        default="dealer_audit.json",
        help="Path for dealer audit JSON (default: dealer_audit.json).",
    )
    args = parser.parse_args(argv)

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    label = args.label or f"phase3-{args.hands}h"

    # Load LLM-generated parameters (imported from Python module)
    params = GENERATED_PARAMS
    print("Loading LLM-generated parameters...")
    print(f"  Loaded {len(params)} archetype param sets")
    print()

    logger = SQLiteLogger(args.db)
    print(
        f"Running Phase 3 simulation: {len(seeds)} seed(s) x {args.hands} hands"
    )
    print(f"  Database: {args.db}")
    print(f"  Audit log: {args.audit}")
    print()

    summaries: List[Dict[str, Any]] = []
    combined_dealer = None

    for seed in seeds:
        summary = run_one_seed(
            seed=seed,
            num_hands=args.hands,
            params=params,
            logger=logger,
            label=label,
        )
        summaries.append(summary)
        combined_dealer = summary["dealer"]

    logger.close()

    # Save dealer audit from last seed (contains cumulative stats from that seed)
    if combined_dealer is not None:
        combined_dealer.save_audit(args.audit)
        combined_dealer.print_summary()

    # Final summary
    print()
    print("=" * 72)
    print("PHASE 3 SIMULATION SUMMARY")
    print("=" * 72)
    all_conserved = True
    total_substitutions = 0
    total_anomalies = 0
    for s in summaries:
        conserved = (s["chip_delta"] == 0)
        all_conserved = all_conserved and conserved
        total_substitutions += s["dealer_substitutions"]
        total_anomalies += s["dealer_anomalies"]
        print(
            f"seed={s['seed']:<10} run_id={s['run_id']:<4} "
            f"hands={s['num_hands']:<6} "
            f"actions={s['total_actions']:<8} "
            f"showdowns={s['total_showdowns']:<6} "
            f"walkovers={s['total_walkovers']:<6}"
        )
        print(
            f"             final_stacks={s['final_stack_sum']:<6} "
            f"rebuys={s['rebuy_sum']:<4} "
            f"chip_delta={s['chip_delta']:<4} "
            f"{'OK' if conserved else 'FAIL'}  "
            f"subs={s['dealer_substitutions']}  anomalies={s['dealer_anomalies']}"
        )
    print("=" * 72)
    print(
        f"Chip conservation: "
        + ("all seeds OK" if all_conserved else "FAILED - check logs")
    )
    print(f"Total dealer substitutions: {total_substitutions}")
    print(f"Total anomaly flags: {total_anomalies}")
    print(f"Audit saved to: {args.audit}")

    return 0 if all_conserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
