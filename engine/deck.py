"""
Card and Deck primitives for the Poker Trust Simulation.

Cards are represented as integers produced by ``treys.Card.new()`` — the same
integer format used by ``treys.Evaluator``. No wrapper class is needed; a card
is just an int.

The ``Deck`` class owns a seeded ``numpy.random.Generator`` and a shuffled copy
of the 52-card deck. Reproducibility is strict: two ``Deck`` instances built
with the same ``seed`` will produce byte-identical sequences from ``deal``.
We do NOT use ``treys.Deck`` because it shuffles via the module-level
``random`` state, which defeats per-instance seeding.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from treys import Card

__all__ = ["Card", "Deck", "FULL_DECK"]


_RANKS = "23456789TJQKA"
_SUITS = "shdc"

#: The canonical 52-card deck as ``treys.Card`` ints, in a stable order.
#: Computed once at import time and shared by ``Deck`` and the evaluator.
FULL_DECK: List[int] = [Card.new(r + s) for r in _RANKS for s in _SUITS]


class Deck:
    """A seeded 52-card deck backed by ``treys.Card`` ints.

    Parameters
    ----------
    seed:
        Seed for a fresh ``numpy.random.Generator``. Ignored if ``rng`` is
        provided. ``None`` means "non-reproducible".
    rng:
        An existing ``numpy.random.Generator`` to share with the rest of the
        simulation (preferred in later stages so a single hand-level RNG
        threads through every shuffle, Monte Carlo draw, and agent decision).

    Examples
    --------
    >>> d = Deck(seed=42)
    >>> len(d.deal(5))
    5
    >>> Deck(seed=42).deal(5) == Deck(seed=42).deal(5)
    True
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self._rng: np.random.Generator = (
            rng if rng is not None else np.random.default_rng(seed)
        )
        self._cards: List[int] = list(FULL_DECK)
        self._rng.shuffle(self._cards)
        self._idx: int = 0

    def deal(self, n: int) -> List[int]:
        """Deal ``n`` cards off the top of the deck.

        Raises
        ------
        ValueError
            If fewer than ``n`` cards remain.
        """
        if n < 0:
            raise ValueError(f"Cannot deal a negative number of cards: {n}")
        if self._idx + n > len(self._cards):
            raise ValueError(
                f"Cannot deal {n} cards; only {self.remaining()} remaining"
            )
        out = self._cards[self._idx : self._idx + n]
        self._idx += n
        return out

    def remaining(self) -> int:
        """Number of cards still undealt."""
        return len(self._cards) - self._idx

    def reset(self) -> None:
        """Re-shuffle all 52 cards using the same RNG stream.

        Useful for tests that want to replay within a single Deck instance.
        Note: this advances the RNG state, so a reset Deck is NOT identical
        to a fresh Deck built with the same seed — use a new Deck for that.
        """
        self._cards = list(FULL_DECK)
        self._rng.shuffle(self._cards)
        self._idx = 0
