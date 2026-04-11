"""
DummyAgent — the "always call" agent used for Stage 2 engine tests.

If there's a bet pending it CALLs; otherwise it CHECKs. Never folds, never
raises, never bluffs. Minimal agent interface — no trust model, no statistics.
Stages 3+ introduce ``BaseAgent`` with real logic and the trust plumbing.
"""

from __future__ import annotations

from typing import List, Optional

from config import SIMULATION
from engine.actions import ActionRecord, ActionType
from engine.game import GameState

__all__ = ["DummyAgent"]


class DummyAgent:
    def __init__(self, name: str, archetype: str, seat: int):
        self.name = name
        self.archetype = archetype
        self.seat = seat
        self.stack = SIMULATION["starting_stack"]
        self.rebuys = 0
        self.hole_cards: Optional[List[int]] = None

    def decide_action(self, game_state: GameState) -> ActionType:
        if game_state.cost_to_call > 0:
            return ActionType.CALL
        return ActionType.CHECK

    def receive_hole_cards(self, cards: List[int]) -> None:
        self.hole_cards = cards

    def observe_action(self, record: ActionRecord) -> None:
        # Stage 2 doesn't use trust, so this is a no-op. Later stages will
        # update posteriors here.
        pass

    def observe_showdown(self, showdown_data, community_cards=None) -> None:
        # Stage 2 doesn't use trust. Later stages update beliefs from
        # revealed hole cards here. ``community_cards`` is provided by the
        # engine so Stage 5 agents can recompute the revealed opponent's
        # hand-strength bucket at each round.
        pass


class FolderAgent(DummyAgent):
    """Always folds when facing a bet, checks when there is none. Used to
    verify "hand ends when only one player remains" and dealer rotation."""

    def decide_action(self, game_state: GameState) -> ActionType:
        if game_state.cost_to_call > 0:
            return ActionType.FOLD
        return ActionType.CHECK


class RaiserAgent(DummyAgent):
    """Always raises when possible, otherwise bets. Used to verify bet cap
    enforcement: after 4 bets/raises the engine must downgrade to CALL."""

    def decide_action(self, game_state: GameState) -> ActionType:
        if game_state.cost_to_call == 0:
            return ActionType.BET
        return ActionType.RAISE
