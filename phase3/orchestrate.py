#!/usr/bin/env python3
"""
Phase 3 — Claude Code Orchestrator

Drives the poker simulation by reading decision requests from the
file I/O engine and dispatching them to an LLM for decisions.

This script runs alongside run_phase3_fileio.py:
  Terminal 1: python phase3/run_phase3_fileio.py --hands 20 --seed 42
  Terminal 2: python phase3/orchestrate.py --provider anthropic --model claude-haiku-4-5-20251001

Or run both from one command:
  python phase3/orchestrate.py --provider anthropic --model claude-haiku-4-5-20251001 --hands 20 --seed 42 --auto

With --auto, the orchestrator launches the engine automatically in a
background thread and handles everything.

Supports: anthropic, ollama providers (same as run_phase3_chat.py).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from phase3.llm_chat_agent import (
    make_client,
    _call_llm,
    _parse_action,
    _load_personality_spec,
)

# ---------------------------------------------------------------------------
# IPC paths (must match file_io_agent.py)
# ---------------------------------------------------------------------------
IPC_DIR = Path("/tmp/phase3_ipc")
REQUEST_FILE = IPC_DIR / "request.json"
RESPONSE_FILE = IPC_DIR / "response.json"
READY_FILE = IPC_DIR / "request_ready"
DONE_FILE = IPC_DIR / "response_done"
GAME_OVER_FILE = IPC_DIR / "game_over"
STATUS_FILE = IPC_DIR / "status.json"


# ---------------------------------------------------------------------------
# System prompts (cached per archetype)
# ---------------------------------------------------------------------------
_SYSTEM_PROMPTS: dict = {}


def _get_system_prompt(archetype: str, seat: int) -> str:
    key = (archetype, seat)
    if key not in _SYSTEM_PROMPTS:
        personality = _load_personality_spec(archetype)
        _SYSTEM_PROMPTS[key] = f"""{personality}

---

You are playing Limit Texas Hold'em at an 8-player table. You are seat {seat}.

RULES:
- Small blind = 1, Big blind = 2
- Small bet = 2 (preflop/flop), Big bet = 4 (turn/river)
- Bet cap = 4 per round (1 bet + 3 raises)
- You must respond with EXACTLY ONE of: FOLD, CHECK, CALL, BET, RAISE
- When cost_to_call = 0: you can CHECK or BET
- When cost_to_call > 0: you can FOLD, CALL, or RAISE
- RAISE is only legal if bet_count < bet_cap (4)

RESPOND WITH ONLY THE ACTION NAME. No explanation. Just one word."""
    return _SYSTEM_PROMPTS[key]


def _build_user_prompt(req: dict) -> str:
    """Build the user message from a decision request."""
    actions_str = ""
    for a in req.get("actions_this_round", []):
        actions_str += f"\n  Seat {a['seat']} ({a['archetype']}): {a['action']}"
    if not actions_str:
        actions_str = "\n  (none yet)"

    return f"""Street: {req['street']}
Your hole cards: {req['hole_cards']}
Community cards: {req['community_cards']}
Hand strength: {req['hand_strength']}

Pot: {req['pot_size']} chips
Cost to call: {req['cost_to_call']}
Bet count this round: {req['bet_count']}/{req['bet_cap']}
Bet size: {req['bet_size']}

Your stack: {req['player_stack']}
Players remaining: {req['num_active_players']}
Your position: {req['player_position']} (0=dealer)

Actions this round:{actions_str}

Your action:"""


# ---------------------------------------------------------------------------
# Orchestration loop
# ---------------------------------------------------------------------------

def orchestrate(
    client: Any,
    provider: str,
    model: str,
) -> dict:
    """Main orchestration loop. Reads requests, dispatches to LLM, writes responses.

    Returns stats dict when game_over signal is received.
    """
    stats = {
        "decisions": 0,
        "failures": 0,
        "total_time": 0.0,
    }

    print("Orchestrator waiting for decisions...", flush=True)

    while True:
        # Check for game over
        if GAME_OVER_FILE.exists():
            print("\nGame over signal received.", flush=True)
            break

        # Wait for a request
        if not READY_FILE.exists():
            time.sleep(0.05)
            continue

        # Read request
        try:
            with open(REQUEST_FILE, "r") as f:
                req = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            time.sleep(0.1)
            continue

        archetype = req["archetype"]
        seat = req["seat"]
        name = req["name"]
        hand_id = req.get("hand_id", "?")
        street = req["street"]
        hs = req["hand_strength"]

        system_prompt = _get_system_prompt(archetype, seat)
        user_prompt = _build_user_prompt(req)

        # Call LLM
        t0 = time.time()
        try:
            response = _call_llm(client, provider, model, system_prompt, user_prompt)
            action = _parse_action(response)
            if action is None:
                action_str = "fold"
                stats["failures"] += 1
            else:
                action_str = action.value
            elapsed = time.time() - t0
            stats["decisions"] += 1
            stats["total_time"] += elapsed

            print(
                f"  H{hand_id} {street:7s} {name:20s} "
                f"{req['hole_cards']:>5s} ({hs:6s}) -> {action_str:5s}  "
                f"({elapsed:.1f}s)",
                flush=True,
            )

        except Exception as e:
            elapsed = time.time() - t0
            stats["failures"] += 1
            stats["total_time"] += elapsed
            # Fallback
            action_str = "check" if req["cost_to_call"] == 0 else "fold"
            print(
                f"  H{hand_id} {street:7s} {name:20s} "
                f"ERROR -> {action_str}  ({elapsed:.1f}s): {e}",
                flush=True,
            )

        # Write response
        with open(RESPONSE_FILE, "w") as f:
            json.dump({"action": action_str}, f)
        DONE_FILE.touch()

    return stats


# ---------------------------------------------------------------------------
# Auto-launch engine in background thread
# ---------------------------------------------------------------------------

def _run_engine(hands: int, seed: int, db: str):
    """Run the file I/O engine in a subprocess."""
    cmd = [
        sys.executable,
        str(_REPO_ROOT / "phase3" / "run_phase3_fileio.py"),
        "--hands", str(hands),
        "--seed", str(seed),
        "--db", db,
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    # Stream engine output
    for line in proc.stdout:
        print(f"  [engine] {line.rstrip()}", flush=True)
    proc.wait()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 Claude Code Orchestrator"
    )
    parser.add_argument(
        "--provider", default="anthropic", choices=["anthropic", "ollama"],
    )
    parser.add_argument(
        "--model", default="claude-haiku-4-5-20251001",
    )
    parser.add_argument(
        "--ollama-url", default="http://localhost:11434/v1",
    )
    # Auto-launch options
    parser.add_argument(
        "--auto", action="store_true",
        help="Auto-launch the engine in the background.",
    )
    parser.add_argument("--hands", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", default="runs_phase3_agents.sqlite")
    args = parser.parse_args(argv)

    print(f"Phase 3 Orchestrator", flush=True)
    print(f"  Provider: {args.provider}", flush=True)
    print(f"  Model: {args.model}", flush=True)
    print(flush=True)

    # Ensure IPC directory
    IPC_DIR.mkdir(parents=True, exist_ok=True)
    for f in [REQUEST_FILE, RESPONSE_FILE, READY_FILE, DONE_FILE, GAME_OVER_FILE]:
        if f.exists():
            f.unlink()

    # Create LLM client
    client = make_client(args.provider, args.model, base_url=args.ollama_url)

    # Auto-launch engine if requested
    if args.auto:
        print(f"  Auto-launching engine: {args.hands} hands, seed {args.seed}", flush=True)
        engine_thread = threading.Thread(
            target=_run_engine,
            args=(args.hands, args.seed, args.db),
            daemon=True,
        )
        engine_thread.start()
        time.sleep(1.0)  # Let engine initialize

    # Run orchestration loop
    started = time.time()
    stats = orchestrate(client, args.provider, args.model)
    total = time.time() - started

    # Summary
    print(flush=True)
    print("=" * 60, flush=True)
    print("ORCHESTRATOR SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"  Total decisions: {stats['decisions']}", flush=True)
    print(f"  Failures: {stats['failures']}", flush=True)
    print(f"  LLM time: {stats['total_time']:.1f}s", flush=True)
    print(f"  Wall time: {total:.1f}s", flush=True)
    if stats["decisions"] > 0:
        avg = stats["total_time"] / stats["decisions"]
        print(f"  Avg per decision: {avg:.1f}s", flush=True)
        hands_per_hour = 3600 / (total / max(args.hands, 1)) if args.auto else 0
        if hands_per_hour > 0:
            print(f"  Throughput: {hands_per_hour:.1f} hands/hour", flush=True)
    print("=" * 60, flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
