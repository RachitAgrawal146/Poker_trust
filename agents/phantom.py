"""
The Phantom — Deceiver / False Signal Generator.

High bluff rate (bets weak hands) AND low call rate (folds to aggression).
Deception ratio BR/VBR ~0.92 — bets carry almost no information about
hand strength. The most corrosive archetype for the table's trust
ecosystem because it floods the signal channel with noise.

Distinct from the Firestorm: the Firestorm is consistently aggressive
(bets and calls). The Phantom is selectively aggressive (bets but DOESN'T
call). Firestorm is predictably chaotic; Phantom is unpredictably
deceptive — and avoids showdown, which makes it slower to classify than
any other static type.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.game import GameState

__all__ = ["Phantom"]


class Phantom(BaseAgent):
    PARAMS = ARCHETYPE_PARAMS["phantom"]

    def __init__(
        self,
        seat: int,
        name: str = "The Phantom",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="phantom", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self.PARAMS[betting_round]
