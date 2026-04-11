"""
The Oracle — Nash Equilibrium player.

Plays a fixed per-round parameter table (from ``archetype_params.py``) and
never adapts to opponents. This is the control group for every other
archetype: near-uniform bluff rate, balanced calling, VPIP around 22-25%.

The Oracle exists to be the yardstick. Later stages compare every adaptive
type's chip trajectory against the Oracle's to isolate exploitation value.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.game import GameState

__all__ = ["Oracle"]


class Oracle(BaseAgent):
    PARAMS = ARCHETYPE_PARAMS["oracle"]

    def __init__(
        self,
        seat: int,
        name: str = "The Oracle",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="oracle", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self.PARAMS[betting_round]
