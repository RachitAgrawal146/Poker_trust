"""
Stage demo runner.

Plays a small simulation with the agents available at the current build
stage and writes a visualizer data file. Re-run this after each stage to
refresh ``visualizer/data.js``:

    python3 run_demo.py                 # current highest stage, 20 hands
    python3 run_demo.py --stage 2       # force a specific stage
    python3 run_demo.py --hands 50      # more hands
    python3 run_demo.py --seed 137      # different seed
    python3 run_demo.py --output visualizer/data.js

Open ``visualizer/poker_table.html`` in any modern browser to view the
result.
"""

from __future__ import annotations

import argparse
from typing import Callable, List, Tuple

from data.visualizer_export import run_and_export


def _stage2_agents():
    # Stage 2: engine sanity with scripted agents. No real strategy yet —
    # this mix is chosen to produce varied action: some seats always call
    # (Dummy), some always fold to bets (Folder), some always raise
    # (Raiser), so every hand exercises the betting-round state machine.
    from agents.dummy_agent import DummyAgent, FolderAgent, RaiserAgent

    return [
        DummyAgent("D0", "dummy", 0),
        DummyAgent("D1", "dummy", 1),
        RaiserAgent("R2", "raiser", 2),
        DummyAgent("D3", "dummy", 3),
        FolderAgent("F4", "folder", 4),
        DummyAgent("D5", "dummy", 5),
        RaiserAgent("R6", "raiser", 6),
        FolderAgent("F7", "folder", 7),
    ]


# stage -> (agents builder, label)
STAGE_DEMOS: dict = {
    2: (_stage2_agents, "Stage 2 demo · scripted engine test"),
}

HIGHEST_STAGE = max(STAGE_DEMOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, default=HIGHEST_STAGE,
                        help=f"Stage to demo (default: {HIGHEST_STAGE})")
    parser.add_argument("--hands", type=int, default=20,
                        help="Number of hands to play (default: 20)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed for reproducibility (default: 42)")
    parser.add_argument("--output", default="visualizer/data.js",
                        help="Output path (default: visualizer/data.js)")
    args = parser.parse_args()

    if args.stage not in STAGE_DEMOS:
        raise SystemExit(
            f"No demo registered for stage {args.stage}. "
            f"Available: {sorted(STAGE_DEMOS)}"
        )

    builder, label = STAGE_DEMOS[args.stage]
    agents = builder()

    run_and_export(
        agents=agents,
        num_hands=args.hands,
        seed=args.seed,
        output_path=args.output,
        stage=args.stage,
        label=label,
    )
    print(f"Wrote {args.hands} hands → {args.output}")
    print("Open visualizer/poker_table.html in your browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
