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

import argparse
import sys

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


#: Maps a stage number to a zero-arg builder that returns the modules dict.
#: Later stages register themselves here as they come online.
STAGE_BUILDERS = {
    1: _build_stage_1,
}


def run_stage(stage: int) -> int:
    """Run one stage's tests. Returns the number of failures."""
    builder = STAGE_BUILDERS.get(stage)
    if builder is None:
        print(f"Stage {stage} has no builder registered yet.")
        return 0

    fn = getattr(test_cases, f"test_stage_{stage}", None)
    if fn is None:
        print(f"test_cases.test_stage_{stage} does not exist.")
        return 0

    print("=" * 60)
    print(f"STAGE {stage}")
    print("=" * 60)

    modules = builder()
    results = fn(modules)
    fails = 0
    for r in results:
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
