"""
The Wall — Passive Calling Station.

Near-zero bluff rate, near-zero raise rate, calls almost everything. The
immovable object: absorbs aggression rather than fighting it. Trust in
the Wall is uniformly high (rare bets are almost perfectly reliable) but
its exploitability is also maximal — Predator value-bets it relentlessly
since the Wall never folds.

Most profitable against the Firestorm (catches constant bluffs). Least
profitable against the Predator (loses to pure value betting).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.game import GameState

__all__ = ["Wall"]


class Wall(BaseAgent):
    PARAMS = ARCHETYPE_PARAMS["wall"]

    def __init__(
        self,
        seat: int,
        name: str = "The Wall",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="wall", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self.PARAMS[betting_round]
