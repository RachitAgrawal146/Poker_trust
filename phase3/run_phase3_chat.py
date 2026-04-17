#!/usr/bin/env python3
"""
Phase 3 — LLM Chat Simulation Runner

Runs 8 LLM agents (each calling an LLM per decision) through the
Phase 1 poker engine. Each agent gets a personality spec as its system
prompt and reasons about every action.

Supports Claude API and Ollama (local, free):

    # Ollama (free, local — requires ollama running with a model pulled)
    python phase3/run_phase3_chat.py --provider ollama --model llama3.1:8b --hands 100

    # Claude Haiku (fast, cheap)
    python phase3/run_phase3_chat.py --provider anthropic --model claude-haiku-4-5-20251001 --hands 100

    # Claude Sonnet (higher quality, more expensive)
    python phase3/run_phase3_chat.py --provider anthropic --model claude-sonnet-4-20250514 --hands 50
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.actions import ActionType
from engine.table import Table

from phase3.llm_chat_agent import LLMChatAgent, LLMChatJudge, make_client
from phase3.dealer import Dealer


# ---------------------------------------------------------------------------
# Roster builder
# ---------------------------------------------------------------------------

ARCHETYPES = [
    (0, "LLM-Oracle", "oracle"),
    (1, "LLM-Sentinel", "sentinel"),
    (2, "LLM-Firestorm", "firestorm"),
    (3, "LLM-Wall", "wall"),
    (4, "LLM-Phantom", "phantom"),
    (5, "LLM-Predator", "predator"),
    (6, "LLM-Mirror", "mirror"),
    # seat 7 = Judge (special class)
]


def build_chat_roster(client: Any, model: str, provider: str) -> List:
    """Build the 8-seat roster where every agent calls the LLM."""
    agents = []
    for seat, name, archetype in ARCHETYPES:
        agents.append(LLMChatAgent(
            seat=seat, name=name, archetype=archetype,
            client=client, model=model, provider=provider,
        ))
    agents.append(LLMChatJudge(
        seat=7, client=client, model=model, provider=provider,
    ))
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
        f"{pct:5.1f}% | {rate:5.2f} hand/s | ETA {_fmt_eta(remaining)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Per-seed run
# ---------------------------------------------------------------------------

def run_one_seed(
    seed: int,
    num_hands: int,
    client: Any,
    model: str,
    provider: str,
    logger: SQLiteLogger,
    label: str,
) -> Dict[str, Any]:
    print("  Building roster...", flush=True)
    agents = build_chat_roster(client, model, provider)
    num_seats = len(agents)
    starting_stack = SIMULATION["starting_stack"]

    print("  Starting SQLite logger...", flush=True)
    run_id = logger.start_run(
        seed=seed, num_hands=num_hands, label=label, agents=agents,
    )
    print("  Creating table...", flush=True)
    table = Table(agents, seed=seed, logger=logger, run_id=run_id)

    dealer = Dealer(
        num_seats=num_seats, starting_stack=starting_stack,
        anomaly_check_interval=max(50, num_hands // 10),
    )

    print(f"  Playing {num_hands} hands...", flush=True)
    started = time.time()
    for i in range(1, num_hands + 1):
        hand_start = time.time()
        table.play_hand()
        hand_elapsed = time.time() - hand_start

        # Count actions and LLM calls this hand
        n_actions = len(table.last_hand.action_log) if table.last_hand else 0
        llm_calls_so_far = sum(getattr(a, "llm_calls", 0) for a in agents)

        # Print every hand so the user can see progress
        elapsed = time.time() - started
        rate = i / elapsed if elapsed > 0 else 0.0
        remaining = (num_hands - i) / rate if rate > 0 else 0.0
        print(
            f"  Hand {i:>5}/{num_hands}  "
            f"{hand_elapsed:5.1f}s  {n_actions:>2} actions  "
            f"LLM calls: {llm_calls_so_far}  "
            f"rate: {rate:4.2f} hand/s  "
            f"ETA: {_fmt_eta(remaining)}"
        )

        # Post-hand audit
        seat_stacks = [a.stack for a in agents]
        total_rebuys = sum(a.rebuys for a in agents)
        showdown_data = None
        if table.last_hand is not None:
            showdown_data = table.last_hand.showdown_data
        dealer.post_hand_audit(
            hand_id=i, seat_stacks=seat_stacks,
            total_rebuys=total_rebuys, showdown_data=showdown_data,
        )

        # Track VPIP
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

    sys.stdout.write("\n")
    sys.stdout.flush()

    logger.log_agent_stats(run_id, table)

    # Judge grievance summary
    for a in agents:
        if a.archetype == "judge" and hasattr(a, "grievance_summary"):
            summary_lines = a.grievance_summary()
            if summary_lines:
                print(f"  Judge grievances (seed={seed}):")
                for s_seat, count, triggered, _ in summary_lines:
                    arch = agents[s_seat].archetype if s_seat < len(agents) else f"seat{s_seat}"
                    t_str = "TRIGGERED" if triggered else "not triggered"
                    print(f"    vs {arch:15s} (seat {s_seat}): grievance={count:3d}  {t_str}")
            break

    # LLM call stats
    total_calls = sum(getattr(a, "llm_calls", 0) for a in agents)
    total_failures = sum(getattr(a, "llm_failures", 0) for a in agents)
    total_llm_time = sum(getattr(a, "llm_total_time", 0.0) for a in agents)

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
        "llm_calls": total_calls,
        "llm_failures": total_failures,
        "llm_time": total_llm_time,
        "dealer": dealer,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 LLM Chat Simulation — 8 LLM agents play poker"
    )
    parser.add_argument(
        "--provider", default="ollama", choices=["anthropic", "ollama"],
        help="LLM provider (default: ollama).",
    )
    parser.add_argument(
        "--model", default="llama3.1:8b",
        help="Model name (default: llama3.1:8b for ollama).",
    )
    parser.add_argument(
        "--seeds", default="42",
        help="Comma-separated seeds (default: 42).",
    )
    parser.add_argument(
        "--hands", type=int, default=100,
        help="Hands per seed (default: 100).",
    )
    parser.add_argument(
        "--db", default="runs_phase3_chat.sqlite",
        help="SQLite database path.",
    )
    parser.add_argument(
        "--label", default=None,
        help="Label for the run.",
    )
    parser.add_argument(
        "--audit", default="dealer_audit_chat.json",
        help="Dealer audit output path.",
    )
    parser.add_argument(
        "--ollama-url", default="http://localhost:11434/v1",
        help="Ollama base URL (default: http://localhost:11434/v1).",
    )
    args = parser.parse_args(argv)

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    label = args.label or f"phase3-chat-{args.provider}-{args.hands}h"

    print(f"Phase 3 LLM Chat Simulation", flush=True)
    print(f"  Provider: {args.provider}", flush=True)
    print(f"  Model: {args.model}", flush=True)
    print(f"  Seeds: {seeds}", flush=True)
    print(f"  Hands/seed: {args.hands}", flush=True)
    print(f"  Database: {args.db}", flush=True)
    print(flush=True)

    # Create client
    print("  Creating API client...", flush=True)
    client = make_client(args.provider, args.model, base_url=args.ollama_url)

    print("  Opening database...", flush=True)
    logger = SQLiteLogger(args.db)
    summaries = []

    for seed in seeds:
        summary = run_one_seed(
            seed=seed, num_hands=args.hands,
            client=client, model=args.model, provider=args.provider,
            logger=logger, label=label,
        )
        summaries.append(summary)

    logger.close()

    # Save dealer audit from last run
    if summaries:
        summaries[-1]["dealer"].save_audit(args.audit)
        summaries[-1]["dealer"].print_summary()

    # Final summary
    print()
    print("=" * 72)
    print("PHASE 3 LLM CHAT SIMULATION SUMMARY")
    print("=" * 72)
    total_calls = 0
    total_failures = 0
    total_time = 0.0
    all_conserved = True
    for s in summaries:
        conserved = s["chip_delta"] == 0
        all_conserved = all_conserved and conserved
        total_calls += s["llm_calls"]
        total_failures += s["llm_failures"]
        total_time += s["llm_time"]
        print(
            f"  seed={s['seed']:<5}  hands={s['num_hands']:<5}  "
            f"chip_delta={s['chip_delta']:<4} {'OK' if conserved else 'FAIL'}  "
            f"llm_calls={s['llm_calls']}  failures={s['llm_failures']}  "
            f"llm_time={s['llm_time']:.1f}s"
        )
    print("=" * 72)
    print(f"Chip conservation: {'all OK' if all_conserved else 'FAILED'}")
    print(f"Total LLM calls: {total_calls}")
    print(f"Total LLM failures: {total_failures} ({100*total_failures/max(total_calls,1):.1f}%)")
    print(f"Total LLM wall time: {total_time:.1f}s")
    if total_calls > 0:
        print(f"Avg latency per call: {total_time/total_calls*1000:.0f}ms")
    print(f"Audit saved to: {args.audit}")

    return 0 if all_conserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
