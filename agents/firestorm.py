"""
The Firestorm — Loose-Aggressive (LAG / Maniac).

Plays almost every hand, bets and raises almost everything. Deception
ratio BR/VBR ~0.74 — bets carry weak correlation with hand strength.
Predictably chaotic: trust drops fast, but entropy drops too. You can't
trust what the Firestorm says but you can trust that it will always lie.

Worst matchup: the Wall (calling station catches every bluff). Best
matchup: the Sentinel (TAG folds too often to Firestorm's constant
aggression).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.game import GameState

__all__ = ["Firestorm"]


class Firestorm(BaseAgent):
    PARAMS = ARCHETYPE_PARAMS["firestorm"]

    def __init__(
        self,
        seat: int,
        name: str = "The Firestorm",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="firestorm", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self.PARAMS[betting_round]
