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


def _stage3_agents():
    # Stage 3: Oracle (real archetype) + mixed scripted stand-ins. The mix
    # forces Oracle to deal with aggression (Raiser), passivity (Dummy),
    # and tight opponents (Folder), so every hand stress-tests the decision
    # branches and hand-strength caching.
    from agents.dummy_agent import DummyAgent, FolderAgent, RaiserAgent
    from agents.oracle import Oracle

    return [
        Oracle(seat=0),
        DummyAgent("D1", "dummy", 1),
        RaiserAgent("R2", "raiser", 2),
        FolderAgent("F3", "folder", 3),
        DummyAgent("D4", "dummy", 4),
        RaiserAgent("R5", "raiser", 5),
        FolderAgent("F6", "folder", 6),
        DummyAgent("D7", "dummy", 7),
    ]


def _stage4_agents():
    # Stage 4: all 5 static archetypes in their canonical seats from
    # SEATING (oracle, sentinel, firestorm, wall, phantom). Seats 5-7 will
    # become Predator/Mirror/Judge in Stage 6; until then they're Oracle
    # stand-ins so every hand exercises the full 8-seat engine.
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
        Oracle(seat=5, name="Oracle-2"),
        Oracle(seat=6, name="Oracle-3"),
        Oracle(seat=7, name="Oracle-4"),
    ]


def _stage5_agents():
    # Stage 5: same 5-archetype table as Stage 4 — trust is not a new agent
    # class but rather state that every BaseAgent subclass accumulates. The
    # exporter picks up each agent's ``posteriors`` / ``trust_score`` /
    # ``entropy`` accessors and writes the per-hand snapshot into data.js.
    return _stage4_agents()


def _stage6_agents():
    # Stage 6: the full 8-archetype canonical roster. Seats 5-7 are now
    # the three adaptive agents — Predator (exploiter), Mirror
    # (tit-for-tat), Judge (grudger). Adaptive state lives on the
    # agents themselves, so nothing else in the demo wiring changes.
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


# stage -> (agents builder, label, default_hands)
STAGE_DEMOS: dict = {
    2: (_stage2_agents, "Stage 2 demo · scripted engine test", 20),
    3: (_stage3_agents, "Stage 3 demo · Oracle vs scripted mix", 20),
    4: (_stage4_agents, "Stage 4 demo · 5 static archetypes + Oracle fillers", 20),
    5: (_stage5_agents, "Stage 5 demo · Bayesian trust model in action", 20),
    6: (_stage6_agents, "Stage 6 demo · full 8-archetype adaptive table", 50),
}

HIGHEST_STAGE = max(STAGE_DEMOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, default=HIGHEST_STAGE,
                        help=f"Stage to demo (default: {HIGHEST_STAGE})")
    parser.add_argument("--hands", type=int, default=None,
                        help="Number of hands to play (default: stage-specific)")
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

    builder, label, default_hands = STAGE_DEMOS[args.stage]
    num_hands = args.hands if args.hands is not None else default_hands
    agents = builder()

    run_and_export(
        agents=agents,
        num_hands=num_hands,
        seed=args.seed,
        output_path=args.output,
        stage=args.stage,
        label=label,
    )
    print(f"Wrote {num_hands} hands → {args.output}")
    print("Open visualizer/poker_table.html in your browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
