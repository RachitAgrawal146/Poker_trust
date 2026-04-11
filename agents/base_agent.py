"""
Abstract base class for all rule-based archetype agents.

Concrete agents (Oracle, Sentinel, Firestorm, ...) subclass this and only
override ``get_params(round, state)`` — everything else (decide_action, stat
tracking, observation hooks) lives here so the behavior of every archetype
flows through a single audited code path.

Decision logic (from the spec):

- With no cost to call: bet with probability VBR/MBR/BR (Strong/Medium/Weak).
  Otherwise check.
- Facing a bet: roll once, fall through raise→call→fold with per-strength
  raise_p and call_p sourced from the per-round params table.

Notes:

- The RNG is shared with the Table. ``Table.__init__`` injects
  ``agent.rng = table._rng`` so every stochastic decision consumes random
  numbers from the same seeded stream, making the whole game reproducible.
- Hand strength is cached per (agent, betting round) for the duration of a
  single hand — Monte Carlo equity only needs to be computed once per
  street, not once per decision. ``on_hand_start`` clears the cache.
- Stats track the player's own behavior (VPIP, PFR, per-action counts,
  showdowns) plus "opponent_stats" / "posteriors" dicts that Stage 5 will
  populate with the Bayesian trust model. For Stage 3 those stay empty.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set

import numpy as np

from config import SIMULATION
from engine.actions import ActionRecord, ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState

__all__ = ["BaseAgent"]


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        archetype: str,
        seat: int,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.name = name
        self.archetype = archetype
        self.seat = seat
        self.stack: int = SIMULATION["starting_stack"]
        self.hole_cards: Optional[List[int]] = None
        self.rebuys: int = 0

        # Shared RNG (Table injects this if None). Must be set before
        # decide_action is called.
        self.rng: Optional[np.random.Generator] = rng

        # ----- Stage 5 trust plumbing (stubs for now) -----
        # seat -> {archetype_name: probability}
        self.posteriors: Dict[int, Dict[str, float]] = {}
        # seat -> {observed_br, observed_vbr, ...}
        self.opponent_stats: Dict[int, Dict[str, float]] = {}

        # ----- Cumulative self-stats -----
        self.stats = {
            "hands_dealt": 0,
            "vpip_count": 0,
            "pfr_count": 0,
            "bets": 0,
            "raises": 0,
            "calls": 0,
            "folds": 0,
            "checks": 0,
            "showdowns": 0,
            "showdowns_won": 0,
            "saw_flop": 0,
        }
        # Track which hand_ids we've already counted for VPIP/PFR so we don't
        # double-count when an agent makes multiple preflop actions.
        self._vpip_hands: Set[int] = set()
        self._pfr_hands: Set[int] = set()

        # Per-hand scratch state (reset in on_hand_start).
        self._current_hand_id: Optional[int] = None
        self._saw_flop_this_hand: bool = False
        self._hs_cache: Dict[str, str] = {}  # round -> "Strong"/"Medium"/"Weak"

    # ------------------------------------------------------------------
    # Abstract surface
    # ------------------------------------------------------------------
    @abstractmethod
    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        """Return the ``{br, vbr, cr, mbr, strong_raise, ...}`` dict for the
        current context. Static agents just return a fixed per-round dict;
        adaptive agents (Predator/Mirror/Judge) will override with dynamic
        logic in Stage 6."""

    # ------------------------------------------------------------------
    # Decision path
    # ------------------------------------------------------------------
    def decide_action(self, game_state: GameState) -> ActionType:
        rng = self.rng
        if rng is None:
            # Fallback for unit tests that call decide_action directly.
            rng = np.random.default_rng()

        # Cache hand strength for the whole street — Monte Carlo on the same
        # hole/board combo always yields the same bucket in expectation, and
        # re-running 1000 samples on every decision would dominate runtime.
        round_key = game_state.betting_round
        hs = self._hs_cache.get(round_key)
        if hs is None:
            hs = get_hand_strength(
                self.hole_cards,
                game_state.community_cards,
                rng=rng,
            )
            self._hs_cache[round_key] = hs

        params = self.get_params(game_state.betting_round, game_state)

        # Branch on cost_to_call, not current_bet. On preflop the BB faces
        # cost_to_call == 0 (the "BB option") even though current_bet == 2.
        if game_state.cost_to_call == 0:
            if hs == "Strong":
                prob = params["vbr"]
            elif hs == "Medium":
                prob = params["mbr"]
            else:
                prob = params["br"]
            return ActionType.BET if rng.random() < prob else ActionType.CHECK

        # Facing a bet: raise → call → fold in priority order.
        if hs == "Strong":
            raise_p = params.get("strong_raise", 0.60)
            call_p = params.get("strong_call", 0.35)
        elif hs == "Medium":
            raise_p = params.get("med_raise", 0.05)
            call_p = params.get("cr", 0.33)
        else:
            raise_p = 0.0
            call_p = params.get("weak_call", 0.15)

        roll = rng.random()
        if roll < raise_p:
            return ActionType.RAISE
        if roll < raise_p + call_p:
            return ActionType.CALL
        return ActionType.FOLD

    # ------------------------------------------------------------------
    # Table hooks
    # ------------------------------------------------------------------
    def receive_hole_cards(self, cards: List[int]) -> None:
        self.hole_cards = cards

    def on_hand_start(self, hand_id: int) -> None:
        self._current_hand_id = hand_id
        self._saw_flop_this_hand = False
        self._hs_cache = {}
        self.hole_cards = None
        self.stats["hands_dealt"] += 1

    def on_hand_end(self, hand_id: int) -> None:
        if self._saw_flop_this_hand:
            self.stats["saw_flop"] += 1

    def observe_action(self, record: ActionRecord) -> None:
        # Note any time *this* agent acts post-preflop — means we saw the flop.
        if (
            record.seat == self.seat
            and record.betting_round in ("flop", "turn", "river")
        ):
            self._saw_flop_this_hand = True

        if record.seat != self.seat:
            return

        # Count the action type.
        t = record.action_type
        if t == ActionType.BET:
            self.stats["bets"] += 1
        elif t == ActionType.RAISE:
            self.stats["raises"] += 1
        elif t == ActionType.CALL:
            self.stats["calls"] += 1
        elif t == ActionType.FOLD:
            self.stats["folds"] += 1
        elif t == ActionType.CHECK:
            self.stats["checks"] += 1

        # VPIP and PFR — both are per-hand flags, incremented at most once.
        if record.betting_round == "preflop":
            if t in (ActionType.CALL, ActionType.BET, ActionType.RAISE):
                if record.hand_id not in self._vpip_hands:
                    self.stats["vpip_count"] += 1
                    self._vpip_hands.add(record.hand_id)
            if t in (ActionType.BET, ActionType.RAISE):
                if record.hand_id not in self._pfr_hands:
                    self.stats["pfr_count"] += 1
                    self._pfr_hands.add(record.hand_id)

    def observe_showdown(self, showdown_data) -> None:
        if not showdown_data:
            return
        for entry in showdown_data:
            if entry["seat"] == self.seat:
                self.stats["showdowns"] += 1
                if entry["won"]:
                    self.stats["showdowns_won"] += 1
                break

    # ------------------------------------------------------------------
    # Convenience derived stats (used by tests and the visualizer)
    # ------------------------------------------------------------------
    def vpip(self) -> float:
        hd = self.stats["hands_dealt"]
        return self.stats["vpip_count"] / hd if hd else 0.0

    def pfr(self) -> float:
        hd = self.stats["hands_dealt"]
        return self.stats["pfr_count"] / hd if hd else 0.0

    def af(self) -> float:
        """Aggression factor = (bets + raises) / calls."""
        calls = max(self.stats["calls"], 1)
        return (self.stats["bets"] + self.stats["raises"]) / calls
