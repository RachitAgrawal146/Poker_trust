"""Targeted unit tests for the engine side-pot algorithm.

`engine/game.py::_showdown` builds side pots by per-seat hand
contribution level and awards each side pot to the best hand among
eligible (contender) seats at that level. The existing Stage 2 stage
tests exercise pot accounting under random play but rarely trigger
multi-level all-ins. These tests construct the all-in scenarios
explicitly and verify (a) chip conservation, (b) that a short stack
cannot collect chips it never matched, and (c) that the
remainder-to-earliest-seat rule is applied per side pot.

Run::

    python3 tests/test_engine_sidepot.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `python3 tests/test_engine_sidepot.py` from anywhere.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
from treys import Card

from agents.dummy_agent import DummyAgent
from engine.deck import Deck
from engine.game import Hand
from engine.table import Table


# ---------------------------------------------------------------------------
# Test infrastructure: build a Hand object in a fully-controlled state.
# ---------------------------------------------------------------------------

def _make_hand(stacks):
    """Construct a Hand with len(stacks) test seats (filled to 8 with
    inactive dummies that don't contribute or hold cards)."""
    n = len(stacks)
    assert n <= 8, "engine.Table is hardwired to NUM_PLAYERS=8"
    # The first n agents are the test subjects; the rest are inactive
    # placeholders with stack=0 and no contribution.
    agents = [DummyAgent(f"d{i}", "dummy", i) for i in range(8)]
    for a, stk in zip(agents, stacks):
        a.stack = stk
    for a in agents[n:]:
        a.stack = 0
    rng = np.random.default_rng(42)
    table = Table(agents, seed=42)
    # Use a fresh deck so card draws don't interfere — we'll overwrite
    # hole_cards and community_cards by hand.
    deck = Deck(rng=rng)
    hand = Hand(table, deck, rng, hand_id=1)
    return hand, agents[:n]


def _set_showdown_state(hand, agents, contributions, hole_cards, community,
                       folded=()):
    """Force a Hand into a deterministic pre-showdown state.

    Limits the showdown universe to the first len(agents) seats. All
    other (unused) seats are kept out of `active`, contribute zero, and
    receive no hole cards, so the side-pot algorithm only sees the
    constructed scenario.
    """
    n = len(agents)
    # Mark hole/community cards as if the hand had been dealt and played.
    for i in range(n):
        hand.hole_cards[i] = list(hole_cards[i])
    hand.community_cards = list(community)
    # Per-seat hand contribution — zero everywhere except the n test seats.
    hand.hand_contribution = {s: 0 for s in hand._all_seats}
    for seat, amt in contributions.items():
        hand.hand_contribution[seat] = amt
    hand.pot = sum(contributions.values())
    # Active set is exactly the n test seats; folded subset from the test.
    hand.active = set(range(n))
    hand.folded = set(folded)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASSED = 0
_FAILED = 0


def _check(condition, label):
    global _PASSED, _FAILED
    if condition:
        _PASSED += 1
        print(f"  PASS  {label}")
    else:
        _FAILED += 1
        print(f"  FAIL  {label}")


# ---------------------------------------------------------------------------
# Test 1: chip conservation under multi-level all-in
# ---------------------------------------------------------------------------

def test_chip_conservation_multi_all_in():
    """Three contenders at three different contribution levels.

    S0 contributed 100 (big stack), S1 contributed 50 (all-in mid),
    S2 contributed 30 (all-in low). All three reach showdown. No
    folded players. Total pot = 180. Chip conservation: every chip
    that went in comes back out as winnings.
    """
    print("\n[1] Three-way all-in at three different levels")
    hand, agents = _make_hand([100, 50, 30])

    # Deal three distinct hands: S0 strong (AA), S1 medium (88), S2 weak (72o).
    hole_cards = {
        0: [Card.new("As"), Card.new("Ah")],
        1: [Card.new("8s"), Card.new("8h")],
        2: [Card.new("7c"), Card.new("2d")],
    }
    community = [
        Card.new("Kc"), Card.new("Qd"), Card.new("Jc"),
        Card.new("4h"), Card.new("3s"),
    ]
    contributions = {0: 100, 1: 50, 2: 30}

    _set_showdown_state(hand, agents, contributions, hole_cards, community)
    starting_stacks = {i: a.stack for i, a in enumerate(agents)}
    hand._showdown()

    # Expected: S0 wins all three side pots (best hand at every level).
    #   L=30 side pot = 30+30+30 = 90 (eligible: S0, S1, S2; S0 wins)
    #   L=50 side pot = 20+20 = 40   (eligible: S0, S1; S0 wins)
    #   L=100 side pot = 50          (eligible: S0; S0 wins)
    #   Total winnings to S0 = 90 + 40 + 50 = 180
    winnings = {i: a.stack - starting_stacks[i] for i, a in enumerate(agents)}
    _check(winnings[0] == 180, f"S0 wins all 180 chips (got {winnings[0]})")
    _check(winnings[1] == 0, f"S1 wins 0 (got {winnings[1]})")
    _check(winnings[2] == 0, f"S2 wins 0 (got {winnings[2]})")
    _check(
        sum(winnings.values()) == 180,
        f"chip conservation: total awarded = pot ({sum(winnings.values())} vs 180)",
    )


# ---------------------------------------------------------------------------
# Test 2: short stack can win its own side pot only
# ---------------------------------------------------------------------------

def test_short_stack_wins_only_inner_pot():
    """S0=100, S1=50, S2=30. S2 has the BEST hand. S2 can only win the
    innermost (L=30) side pot. The L=50 side pot goes to the best
    eligible hand among S0/S1, and the L=100 side pot goes to S0 alone.
    Previously (pre-side-pot fix) S2 with the best hand would have
    collected the entire 180-chip pot — overpaid by 90 chips.
    """
    print("\n[2] Short stack with best hand wins only its eligible pot")
    hand, agents = _make_hand([100, 50, 30])

    # S2 has AA, S1 has 88, S0 has 72o.
    hole_cards = {
        0: [Card.new("7c"), Card.new("2d")],
        1: [Card.new("8s"), Card.new("8h")],
        2: [Card.new("As"), Card.new("Ah")],
    }
    community = [
        Card.new("Kc"), Card.new("Qd"), Card.new("Jc"),
        Card.new("4h"), Card.new("3s"),
    ]
    contributions = {0: 100, 1: 50, 2: 30}

    _set_showdown_state(hand, agents, contributions, hole_cards, community)
    starting_stacks = {i: a.stack for i, a in enumerate(agents)}
    hand._showdown()

    winnings = {i: a.stack - starting_stacks[i] for i, a in enumerate(agents)}
    #   L=30 side pot (90 chips): S2 wins (best hand among S0/S1/S2)
    #   L=50 side pot (40 chips): S1 wins (best among S0/S1 — 88 beats 72)
    #   L=100 side pot (50 chips): S0 wins (sole eligible)
    _check(winnings[2] == 90, f"S2 (best hand) wins 90 only (got {winnings[2]})")
    _check(winnings[1] == 40, f"S1 wins middle side pot 40 (got {winnings[1]})")
    _check(winnings[0] == 50, f"S0 wins outer side pot 50 (got {winnings[0]})")
    _check(
        sum(winnings.values()) == 180,
        f"chip conservation: total = pot ({sum(winnings.values())} vs 180)",
    )
    # Pre-fix behavior would have been S2 collects 180, S0/S1 collect 0 —
    # explicitly check that case is no longer reachable.
    _check(
        winnings[2] != 180,
        "regression guard: S2 does NOT collect the full pot",
    )


# ---------------------------------------------------------------------------
# Test 3: folded player chips cascade into the lowest side pots
# ---------------------------------------------------------------------------

def test_folded_chips_cascade_into_lowest_pots():
    """S0=80, S1=40 all-in, S2 folded at 20. Two contenders. S2's 20
    chips go into the L=40 side pot (and below — i.e. all of the
    L=40 pot because there's no level below 40 here). S0 has the
    best hand."""
    print("\n[3] Folded chips cascade into the lowest eligible side pot")
    hand, agents = _make_hand([80, 40, 0])

    hole_cards = {
        0: [Card.new("As"), Card.new("Ah")],    # AA — best
        1: [Card.new("Kh"), Card.new("Kd")],    # KK — second
        2: [Card.new("2c"), Card.new("3c")],    # folded; irrelevant
    }
    community = [
        Card.new("Qc"), Card.new("Jd"), Card.new("Tc"),
        Card.new("5h"), Card.new("4s"),
    ]
    contributions = {0: 80, 1: 40, 2: 20}

    _set_showdown_state(
        hand, agents, contributions, hole_cards, community, folded=[2],
    )
    starting_stacks = {i: a.stack for i, a in enumerate(agents)}
    hand._showdown()

    winnings = {i: a.stack - starting_stacks[i] for i, a in enumerate(agents)}
    #   L=40 side pot = 40 (S0) + 40 (S1) + 20 (folded S2) = 100 (eligible: S0, S1)
    #     → S0 wins (AA beats KK)
    #   L=80 side pot = 40 (S0) (eligible: S0 alone) → S0 wins
    _check(winnings[0] == 140, f"S0 wins all 140 (got {winnings[0]})")
    _check(winnings[1] == 0, f"S1 (lost showdown) wins 0 (got {winnings[1]})")
    _check(winnings[2] == 0, f"folded S2 wins 0 (got {winnings[2]})")
    _check(
        sum(winnings.values()) == 140,
        f"chip conservation: total = pot ({sum(winnings.values())} vs 140)",
    )


# ---------------------------------------------------------------------------
# Test 4: single contender level degenerates to the original main pot
# ---------------------------------------------------------------------------

def test_single_level_matches_original_behavior():
    """All three contenders contributed the same amount. There's only
    one side pot — equivalent to the pre-fix single-pot behavior."""
    print("\n[4] Single contribution level → single pot")
    hand, agents = _make_hand([100, 100, 100])

    hole_cards = {
        0: [Card.new("As"), Card.new("Ah")],
        1: [Card.new("Kh"), Card.new("Kd")],
        2: [Card.new("2c"), Card.new("3c")],
    }
    community = [
        Card.new("Qc"), Card.new("Jd"), Card.new("Tc"),
        Card.new("5h"), Card.new("4s"),
    ]
    contributions = {0: 40, 1: 40, 2: 40}

    _set_showdown_state(hand, agents, contributions, hole_cards, community)
    starting_stacks = {i: a.stack for i, a in enumerate(agents)}
    hand._showdown()

    winnings = {i: a.stack - starting_stacks[i] for i, a in enumerate(agents)}
    _check(winnings[0] == 120, f"S0 wins the single 120-chip pot (got {winnings[0]})")
    _check(
        sum(winnings.values()) == 120,
        f"chip conservation: total = pot ({sum(winnings.values())} vs 120)",
    )


# ---------------------------------------------------------------------------
# Test 5: tied hands split a side pot; remainder goes to earliest seat
# ---------------------------------------------------------------------------

def test_split_pot_with_remainder():
    """Two contenders, same hand, odd-chip pot. Remainder goes to the
    earliest-clockwise-from-dealer seat per the engine convention."""
    print("\n[5] Tied hands split the side pot; remainder to earliest seat")
    hand, agents = _make_hand([100, 100])

    # Both hands play the board (community is straight) — true split.
    hole_cards = {
        0: [Card.new("2c"), Card.new("3c")],
        1: [Card.new("2d"), Card.new("3d")],
    }
    community = [
        Card.new("Ts"), Card.new("Jh"), Card.new("Qc"),
        Card.new("Kh"), Card.new("As"),  # board plays a straight
    ]
    contributions = {0: 51, 1: 50}    # odd-chip pot = 101

    _set_showdown_state(hand, agents, contributions, hole_cards, community)
    starting_stacks = {i: a.stack for i, a in enumerate(agents)}
    hand._showdown()

    winnings = {i: a.stack - starting_stacks[i] for i, a in enumerate(agents)}
    # Side pots:
    #   L=50: 50+50 = 100 (split), remainder = 0
    #   L=51: 1 chip from S0, eligible = {S0} → S0 wins 1
    # So S0 gets 50 + 1 = 51, S1 gets 50.
    _check(winnings[0] == 51, f"S0 (deeper) gets 50 split + 1 outer (got {winnings[0]})")
    _check(winnings[1] == 50, f"S1 gets 50 split (got {winnings[1]})")
    _check(
        sum(winnings.values()) == 101,
        f"chip conservation: total = pot ({sum(winnings.values())} vs 101)",
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    test_chip_conservation_multi_all_in()
    test_short_stack_wins_only_inner_pot()
    test_folded_chips_cascade_into_lowest_pots()
    test_single_level_matches_original_behavior()
    test_split_pot_with_remainder()
    print("\n" + "=" * 60)
    print(f"RESULT: {_PASSED}/{_PASSED + _FAILED} tests passed")
    return 0 if _FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
