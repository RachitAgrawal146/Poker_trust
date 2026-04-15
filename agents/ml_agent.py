"""ML-powered poker agent for Phase 2.

Supports two model types:

1. **Tabular** (default): loads an empirical action distribution table
   keyed by (context, round, hand_strength). Samples from the distribution
   at each decision point. Exactly mirrors the rule-based agent's two-stage
   decision tree.

2. **Split RF**: loads two sklearn RandomForest models (nobet + facing)
   and samples from predict_proba. Used for comparison in the paper.

Uses SAMPLING from the predicted/empirical distribution, not argmax.
"""

from __future__ import annotations

import os
import warnings
from typing import Optional

import numpy as np
import joblib

warnings.filterwarnings("ignore")

from agents.base_agent import BaseAgent
from engine.actions import ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState

__all__ = ["MLAgent"]


_ROUND_NAMES = {
    "preflop": "preflop", "flop": "flop", "turn": "turn", "river": "river",
}
_HS_MAP = {"Strong": 1.0, "Medium": 0.5, "Weak": 0.0}
_HS_REVERSE = {1.0: "Strong", 0.5: "Medium", 0.0: "Weak"}
_STARTING_STACK = 200.0
_ROUND_MAP = {"preflop": 0.0, "flop": 0.25, "turn": 0.5, "river": 0.75}

_IDX_TO_ACTION = {
    0: ActionType.FOLD,
    1: ActionType.CHECK,
    2: ActionType.CALL,
    3: ActionType.BET,
    4: ActionType.RAISE,
}


class MLAgent(BaseAgent):
    """Poker agent using trained ML models."""

    def __init__(
        self,
        seat: int,
        archetype: str,
        model_dir: str,
        name: Optional[str] = None,
        rng: Optional[np.random.Generator] = None,
    ):
        display_name = name or f"ML-{archetype.title()}"
        super().__init__(
            name=display_name,
            archetype=archetype,
            seat=seat,
            rng=rng,
        )
        self._base_archetype = archetype
        self._predictions = 0
        self._fallbacks = 0

        # Try loading tabular model first (preferred)
        table_path = os.path.join(model_dir, f"{archetype}_table.pkl")
        if os.path.exists(table_path):
            self._table = joblib.load(table_path)
            self._mode = "tabular"
        else:
            # Fallback: split RF models
            nobet_path = os.path.join(model_dir, f"{archetype}_nobet.pkl")
            facing_path = os.path.join(model_dir, f"{archetype}_facing.pkl")
            self._model_nobet = joblib.load(nobet_path)
            self._model_facing = joblib.load(facing_path)
            self._nobet_map = self._build_map(self._model_nobet)
            self._facing_map = self._build_map(self._model_facing)
            n = getattr(self._model_nobet, "n_features_in_", 7)
            self._has_hs_feature = n >= 8
            self._mode = "split_rf"
            self._table = None

    @staticmethod
    def _build_map(model) -> dict:
        classes = getattr(model, "classes_", None)
        if classes is None:
            return {i: i for i in range(5)}
        return {i: int(c) for i, c in enumerate(classes)}

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return {}

    def decide_action(self, game_state: GameState) -> ActionType:
        rng = self.rng or np.random.default_rng()

        # Compute hand strength (cached per street)
        hs_str = self._hs_cache.get(game_state.betting_round)
        if hs_str is None:
            hs_str = get_hand_strength(
                self.hole_cards,
                game_state.community_cards,
                rng=rng,
            )
            self._hs_cache[game_state.betting_round] = hs_str

        try:
            if self._mode == "tabular":
                action = self._decide_tabular(game_state, hs_str, rng)
            else:
                action = self._decide_split_rf(game_state, hs_str, rng)
            self._predictions += 1
            return action
        except Exception:
            self._fallbacks += 1
            if game_state.cost_to_call == 0:
                return ActionType.CHECK
            return ActionType.CALL

    def _decide_tabular(self, game_state, hs_str, rng) -> ActionType:
        """Look up empirical distribution and sample."""
        round_name = game_state.betting_round
        cost_to_call = game_state.cost_to_call

        if cost_to_call == 0:
            context = "nobet"
        else:
            context = "facing"

        probs = self._table[context][round_name][hs_str]
        # probs is [P_fold, P_check, P_call, P_bet, P_raise]

        if context == "nobet":
            # Only CHECK (1) and BET (3) are legal
            check_p = probs[1]
            bet_p = probs[3]
            total = check_p + bet_p
            if total <= 0:
                return ActionType.CHECK
            if rng.random() < (bet_p / total):
                return ActionType.BET
            return ActionType.CHECK
        else:
            # FOLD (0), CALL (2), RAISE (4)
            fold_p = probs[0]
            call_p = probs[2]
            raise_p = probs[4]

            # At bet cap, convert raise to call
            if game_state.bet_count >= game_state.bet_cap:
                call_p += raise_p
                raise_p = 0.0

            total = fold_p + call_p + raise_p
            if total <= 0:
                return ActionType.CALL

            fold_p /= total
            call_p /= total
            raise_p /= total

            roll = rng.random()
            if roll < fold_p:
                return ActionType.FOLD
            if roll < fold_p + call_p:
                return ActionType.CALL
            return ActionType.RAISE

    def _decide_split_rf(self, game_state, hs_str, rng) -> ActionType:
        """Use split RF models (legacy fallback)."""
        cost_to_call = game_state.cost_to_call
        cost_norm = min(cost_to_call, 16) / _STARTING_STACK
        features = [
            _ROUND_MAP.get(game_state.betting_round, 0.0),
            game_state.pot_size / _STARTING_STACK,
            game_state.player_stack / _STARTING_STACK,
            cost_norm,
            game_state.bet_count / 4.0,
            game_state.player_position / 7.0,
            1.0 if cost_to_call > 0 else 0.0,
        ]
        if getattr(self, "_has_hs_feature", False):
            features.append(_HS_MAP.get(hs_str, 0.0))
        X = np.array([features])

        if cost_to_call == 0:
            raw = self._model_nobet.predict_proba(X)[0]
            cm = self._nobet_map
            check_p = sum(raw[i] for i, c in cm.items() if c == 1 and i < len(raw))
            bet_p = sum(raw[i] for i, c in cm.items() if c == 3 and i < len(raw))
            total = check_p + bet_p
            if total <= 0:
                return ActionType.CHECK
            if rng.random() < (bet_p / total):
                return ActionType.BET
            return ActionType.CHECK
        else:
            raw = self._model_facing.predict_proba(X)[0]
            cm = self._facing_map
            fold_p = sum(raw[i] for i, c in cm.items() if c == 0 and i < len(raw))
            call_p = sum(raw[i] for i, c in cm.items() if c == 2 and i < len(raw))
            raise_p = sum(raw[i] for i, c in cm.items() if c == 4 and i < len(raw))
            if game_state.bet_count >= game_state.bet_cap:
                call_p += raise_p
                raise_p = 0.0
            total = fold_p + call_p + raise_p
            if total <= 0:
                return ActionType.CALL
            fold_p /= total
            call_p /= total
            raise_p /= total
            roll = rng.random()
            if roll < fold_p:
                return ActionType.FOLD
            if roll < fold_p + call_p:
                return ActionType.CALL
            return ActionType.RAISE

    def prediction_stats(self) -> dict:
        total = self._predictions + self._fallbacks
        return {
            "predictions": self._predictions,
            "fallbacks": self._fallbacks,
            "fallback_rate": self._fallbacks / max(total, 1),
        }
