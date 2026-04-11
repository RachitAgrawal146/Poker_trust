"""
The Sentinel — Tight-Aggressive (TAG).

Plays few hands, bets strong ones hard, almost never bluffs. The most
"honest" archetype: rare bets are high-signal, so the Sentinel is quickly
classified by observers and earns the highest trust. Legible, disciplined,
but exploitable by Predator (identified as TAG, attacked with targeted
bluffs that the Sentinel folds to).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.game import GameState

__all__ = ["Sentinel"]


class Sentinel(BaseAgent):
    PARAMS = ARCHETYPE_PARAMS["sentinel"]

    def __init__(
        self,
        seat: int,
        name: str = "The Sentinel",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="sentinel", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self.PARAMS[betting_round]
