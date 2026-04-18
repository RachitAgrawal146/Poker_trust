"""
Stage-aware test runner.

``test_cases.py`` defines ``test_stage_N(modules)`` functions that consume a
dict of implementation hooks (Card, Deck, evaluators, Table, create_agents,
...). This runner assembles the right dict for each stage and dispatches.

Usage::

    python run_tests.py --stage 1
    python run_tests.py --stage all    # run every stage that has a builder
"""

from __future__ import annotations

# Ensure repo root is on sys.path (this file lives in phase1/ or phase2/)
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))


import argparse
import sys

import stage_extras
import test_cases


def _build_stage_1() -> dict:
    from treys import Card
    from engine.deck import Deck
    from engine.evaluator import get_hand_strength
    from preflop_lookup import get_preflop_bucket

    return {
        "Card": Card,
        "Deck": Deck,
        "get_preflop_bucket": get_preflop_bucket,
        "get_hand_strength": get_hand_strength,
    }


def _build_stage_2() -> dict:
    from agents.dummy_agent import DummyAgent, FolderAgent, RaiserAgent
    from engine.actions import ActionType
    from engine.table import Table

    return {
        "Table": Table,
        "DummyAgent": DummyAgent,
        "FolderAgent": FolderAgent,
        "RaiserAgent": RaiserAgent,
        "ActionType": ActionType,
    }


def _build_stage_3() -> dict:
    from agents.dummy_agent import DummyAgent
    from agents.oracle import Oracle
    from engine.table import Table

    return {
        "Oracle": Oracle,
        "DummyAgent": DummyAgent,
        "Table": Table,
    }


def _build_stage_4() -> dict:
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from engine.table import Table

    return {
        "Oracle": Oracle,
        "Sentinel": Sentinel,
        "Firestorm": Firestorm,
        "Wall": Wall,
        "Phantom": Phantom,
        "Table": Table,
    }


def _build_stage_5() -> dict:
    # Stage 5 shares the Stage 4 agent roster — trust is a property every
    # BaseAgent subclass inherits, so no new agent classes are introduced.
    # The canonical ``test_cases.test_stage_5`` expects a ``create_agents``
    # callable that returns the 8-seat static roster.
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom

    def create_agents():
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

    modules = _build_stage_4()
    modules["create_agents"] = create_agents
    return modules


def _build_stage_7() -> dict:
    # Stage 7 adds the persistent SQLite logger. The roster is the same
    # Stage 5 static table (Oracle / Sentinel / Firestorm / Wall / Phantom
    # + 3 Oracle fillers) because the trust-snapshot assertions in
    # ``stage7_extras`` need agents that expose the Stage 5 trust API.
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from data.sqlite_logger import SQLiteLogger
    from engine.table import Table

    def create_agents():
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

    return {
        "Table": Table,
        "SQLiteLogger": SQLiteLogger,
        "Oracle": Oracle,
        "Sentinel": Sentinel,
        "Firestorm": Firestorm,
        "Wall": Wall,
        "Phantom": Phantom,
        "create_agents": create_agents,
    }


def _build_stage_6() -> dict:
    # Stage 6 wires up the three adaptive archetypes (Predator, Mirror,
    # Judge) in their canonical seats 5-7. The extras test rebuilds the
    # full 8-archetype table from this module dict.
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from agents.predator import Predator
    from agents.mirror import Mirror
    from agents.judge import Judge
    from engine.game import GameState
    from engine.table import Table

    def create_agents():
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

    return {
        "Oracle": Oracle,
        "Sentinel": Sentinel,
        "Firestorm": Firestorm,
        "Wall": Wall,
        "Phantom": Phantom,
        "Predator": Predator,
        "Mirror": Mirror,
        "Judge": Judge,
        "Table": Table,
        "GameState": GameState,
        "create_agents": create_agents,
    }


#: Maps a stage number to a zero-arg builder that returns the modules dict.
#: Later stages register themselves here as they come online.
STAGE_BUILDERS = {
    1: _build_stage_1,
    2: _build_stage_2,
    3: _build_stage_3,
    4: _build_stage_4,
    5: _build_stage_5,
    6: _build_stage_6,
    7: _build_stage_7,
    10: _build_stage_5,
    11: _build_stage_5,
}

#: Maps a stage number to an extra-assertions function from ``stage_extras``.
#: These augment the canonical (placeholder-heavy) ``test_cases`` stages.
STAGE_EXTRAS = {
    2: stage_extras.stage2_extras,
    3: stage_extras.stage3_extras,
    4: stage_extras.stage4_extras,
    5: stage_extras.stage5_extras,
    6: stage_extras.stage6_extras,
    7: stage_extras.stage7_extras,
    10: stage_extras.stage10_extras,
    11: stage_extras.stage11_extras,
}


def run_stage(stage: int) -> int:
    """Run one stage's tests. Returns the number of failures."""
    builder = STAGE_BUILDERS.get(stage)
    if builder is None:
        print(f"Stage {stage} has no builder registered yet.")
        return 0

    print("=" * 60)
    print(f"STAGE {stage}")
    print("=" * 60)

    fails = 0
    modules = builder()

    # Canonical test_cases results (may be placeholder "TEST ..." strings).
    fn = getattr(test_cases, f"test_stage_{stage}", None)
    if fn is not None:
        canonical = fn(modules)
        for r in canonical:
            print(f"  {r}")
            if r.startswith("FAIL"):
                fails += 1

    # Extra assertions layered on top.
    extra_fn = STAGE_EXTRAS.get(stage)
    if extra_fn is not None:
        print("  --- extras ---")
        for r in extra_fn(modules):
            print(f"  {r}")
            if r.startswith("FAIL"):
                fails += 1

    return fails


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="1", help="Stage number or 'all'")
    args = parser.parse_args()

    if args.stage == "all":
        stages = sorted(STAGE_BUILDERS)
    else:
        stages = [int(args.stage)]

    total_fails = 0
    for s in stages:
        total_fails += run_stage(s)

    print("=" * 60)
    if total_fails:
        print(f"RESULT: {total_fails} failure(s)")
        return 1
    print("RESULT: all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
