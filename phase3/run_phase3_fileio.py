#!/usr/bin/env python3
"""
Phase 3 — File I/O Engine Runner

Runs the poker engine with FileIOAgents that pause at each decision point,
waiting for Claude Code to write the response via files.

Usage (run in background from Claude Code):
    python phase3/run_phase3_fileio.py --hands 20 --seed 42

The engine writes decision requests to /tmp/phase3_ipc/request.json
and polls for responses at /tmp/phase3_ipc/response.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.actions import ActionType
from engine.table import Table

from phase3.file_io_agent import (
    FileIOAgent,
    FileIOJudge,
    IPC_DIR,
    GAME_OVER_FILE,
    _ensure_ipc_dir,
)


def build_roster() -> List:
    return [
        FileIOAgent(seat=0, name="LLM-Oracle", archetype="oracle"),
        FileIOAgent(seat=1, name="LLM-Sentinel", archetype="sentinel"),
        FileIOAgent(seat=2, name="LLM-Firestorm", archetype="firestorm"),
        FileIOAgent(seat=3, name="LLM-Wall", archetype="wall"),
        FileIOAgent(seat=4, name="LLM-Phantom", archetype="phantom"),
        FileIOAgent(seat=5, name="LLM-Predator", archetype="predator"),
        FileIOAgent(seat=6, name="LLM-Mirror", archetype="mirror"),
        FileIOJudge(seat=7, name="LLM-Judge"),
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 File I/O engine")
    parser.add_argument("--hands", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", default="runs_phase3_agents.sqlite")
    args = parser.parse_args(argv)

    _ensure_ipc_dir()

    agents = build_roster()
    logger = SQLiteLogger(args.db)
    run_id = logger.start_run(
        seed=args.seed, num_hands=args.hands,
        label=f"phase3-agents-{args.hands}h", agents=agents,
    )
    table = Table(agents, seed=args.seed, logger=logger, run_id=run_id)

    # Write initial status
    status_file = IPC_DIR / "status.json"
    started = time.time()

    for i in range(1, args.hands + 1):
        hand_start = time.time()
        table.play_hand()
        hand_time = time.time() - hand_start

        n_actions = len(table.last_hand.action_log) if table.last_hand else 0
        elapsed = time.time() - started
        rate = i / elapsed if elapsed > 0 else 0

        status = {
            "hand": i,
            "total_hands": args.hands,
            "hand_time": round(hand_time, 1),
            "actions": n_actions,
            "rate": round(rate, 3),
            "elapsed": round(elapsed, 1),
        }
        with open(status_file, "w") as f:
            json.dump(status, f)

        # Print to stdout for monitoring
        print(
            f"Hand {i}/{args.hands}  {hand_time:.1f}s  "
            f"{n_actions} actions  {rate:.3f} hand/s",
            flush=True,
        )

    logger.log_agent_stats(run_id, table)
    logger.close()

    # Print final summary
    print(f"\nCompleted {args.hands} hands in {time.time()-started:.1f}s", flush=True)
    for a in agents:
        print(f"  {a.name:20s}  stack={a.stack:>5}  rebuys={a.rebuys}", flush=True)

    # Signal game over
    GAME_OVER_FILE.touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
