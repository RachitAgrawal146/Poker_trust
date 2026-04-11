"""
Action types and action records for the game engine.

``ActionType`` is the enum every agent returns from ``decide_action``. The
engine derives the amount (how many chips actually move) from the enum plus
the current bet state, so agents never deal with raw amounts — they just say
"fold / check / call / bet / raise".

``ActionRecord`` is the logged version of what actually happened: who did
what, how much moved, and the surrounding game state. Stage 7 will extend
this dataclass with more fields (hand strength, position, opponents
remaining, etc.) for SQLite logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


@dataclass
class ActionRecord:
    """One row per action taken. Fields outside the Stage 2 core are optional
    so that later stages can enrich logging without breaking the engine."""

    hand_id: int
    seat: int
    archetype: str
    betting_round: str
    action_type: ActionType
    amount: int
    pot_before: int
    pot_after: int
    stack_before: int
    stack_after: int
    sequence_num: int
    num_opponents_remaining: int
    position_relative_to_dealer: int
    bet_count: int = 0            # bets + raises so far this round (after this action)
    current_bet: int = 0          # max per-player contribution this round (after this action)
    hand_strength_bucket: Optional[str] = None
