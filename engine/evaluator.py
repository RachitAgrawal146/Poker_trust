"""
Hand-strength bucketing for the Poker Trust Simulation.

Every agent calls ``get_hand_strength`` to decide whether its current holding
is "Strong", "Medium", or "Weak". The per-round action tables in
``archetype_params.py`` are keyed on these three buckets.

Pre-flop (no community cards): lookup via ``preflop_lookup``. This is the
canonical 169-hand classification used across the simulation and tests.

Post-flop (3+ community cards): Monte Carlo equity vs. one random opponent.
We draw ``num_samples`` random (opponent hole cards, rest-of-board) rollouts,
evaluate with ``treys.Evaluator``, and bucket by win percentage using the
thresholds in ``config.HAND_STRENGTH``.

treys gotcha: ``Evaluator.evaluate(board, hand)`` returns a rank where
**lower = better** (1 = royal flush, 7462 = worst high card). Wins are
counted with ``my_rank < opp_rank`` and ties with ``==`` (half-credit).
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
from treys import Evaluator

from config import HAND_STRENGTH
from engine.deck import FULL_DECK
from preflop_lookup import get_preflop_bucket_from_treys

__all__ = ["get_hand_strength"]


_EVAL = Evaluator()


def get_hand_strength(
    hole_cards: Sequence[int],
    community_cards: Sequence[int],
    rng: Optional[np.random.Generator] = None,
    seed: Optional[int] = None,
    num_samples: Optional[int] = None,
) -> str:
    """Bucket a hand as "Strong", "Medium", or "Weak".

    Parameters
    ----------
    hole_cards:
        Two ``treys.Card`` ints for the player's hole cards.
    community_cards:
        Zero to five ``treys.Card`` ints on the board. Empty → preflop.
    rng:
        A ``numpy.random.Generator`` to draw opponent holdings and board
        completions. Shared with the rest of the simulation in later stages.
    seed:
        Convenience alternative to ``rng`` — if ``rng`` is ``None`` and
        ``seed`` is given, a fresh ``numpy.random.default_rng(seed)`` is used.
        ``test_cases.test_stage_1`` passes ``seed=42`` this way.
    num_samples:
        Monte Carlo rollouts for post-flop. Defaults to
        ``HAND_STRENGTH["monte_carlo_samples"]`` (1000).

    Returns
    -------
    str
        One of ``"Strong"``, ``"Medium"``, ``"Weak"``.
    """
    if len(hole_cards) != 2:
        raise ValueError(
            f"hole_cards must have exactly 2 cards, got {len(hole_cards)}"
        )

    # Preflop fast path — canonical lookup table, no Monte Carlo needed.
    if not community_cards:
        return get_preflop_bucket_from_treys(hole_cards[0], hole_cards[1])

    if rng is None:
        rng = np.random.default_rng(seed)
    if num_samples is None:
        num_samples = HAND_STRENGTH["monte_carlo_samples"]

    # Remove known cards from the pool of drawable cards.
    known = set(hole_cards) | set(community_cards)
    pool = np.array([c for c in FULL_DECK if c not in known], dtype=np.int64)

    board_needed = 5 - len(community_cards)
    hole_list = list(hole_cards)
    base_community = list(community_cards)

    wins = 0
    ties = 0
    for _ in range(num_samples):
        # Draw opponent's 2 hole cards + any remaining community cards in one shot.
        draw_size = 2 + board_needed
        idx = rng.choice(len(pool), size=draw_size, replace=False)
        drawn = pool[idx].tolist()
        opp_hole = drawn[:2]
        full_board = base_community + drawn[2:]

        my_rank = _EVAL.evaluate(full_board, hole_list)
        opp_rank = _EVAL.evaluate(full_board, opp_hole)

        if my_rank < opp_rank:  # treys: lower = better
            wins += 1
        elif my_rank == opp_rank:
            ties += 1

    win_pct = (wins + 0.5 * ties) / num_samples

    if win_pct > HAND_STRENGTH["strong_threshold"]:
        return "Strong"
    if win_pct > HAND_STRENGTH["medium_threshold"]:
        return "Medium"
    return "Weak"
