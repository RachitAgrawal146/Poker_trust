"""ML-powered poker agent for Phase 2.

Loads a trained sklearn model and uses it to make decisions. Inherits from
BaseAgent so it plugs into the same trust model, stat tracking, and observer
pattern as the rule-based agents.

CRITICAL: Uses ``predict_proba`` and SAMPLES from the predicted distribution
rather than argmax. The rule-based agents roll dice against probability
tables — the ML agent rolls dice against predicted probabilities. Without
sampling, the ML agent would be deterministic (always picking the most
likely action), which would change the behavioral fingerprint even if the
model's probabilities are correct.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import joblib

from agents.base_agent import BaseAgent
from engine.actions import ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState

__all__ = ["MLAgent"]


_ROUND_MAP = {"preflop": 0.0, "flop": 0.25, "turn": 0.5, "river": 0.75}
_HS_MAP = {"Strong": 1.0, "Medium": 0.5, "Weak": 0.0}
_STARTING_STACK = 200.0

# Action index → ActionType (matches ml.feature_engineering.ACTION_LABELS)
_IDX_TO_ACTION = {
    0: ActionType.FOLD,
    1: ActionType.CHECK,
    2: ActionType.CALL,
    3: ActionType.BET,
    4: ActionType.RAISE,
}


class MLAgent(BaseAgent):
    """Poker agent that uses a trained ML model for decisions."""

    def __init__(
        self,
        seat: int,
        archetype: str,
        model_path: str,
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
        self._model = joblib.load(model_path)
        self._has_hs_feature = self._detect_feature_count()

        # Track prediction statistics
        self._predictions = 0
        self._fallbacks = 0

    def _detect_feature_count(self) -> bool:
        """Detect whether the model expects 7 features (no HS) or 8 (with HS).

        We probe the model's expected input shape. sklearn models store this
        as n_features_in_ after fitting.
        """
        n = getattr(self._model, "n_features_in_", None)
        if n is not None:
            return n >= 8
        # Fallback: try to infer from model internals
        return False

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        """Not used — MLAgent overrides decide_action entirely."""
        return {}

    def decide_action(self, game_state: GameState) -> ActionType:
        """Use the trained model to predict an action."""
        rng = self.rng or np.random.default_rng()

        # Compute hand strength (cached per street, same as BaseAgent)
        hs_str = self._hs_cache.get(game_state.betting_round)
        if hs_str is None:
            hs_str = get_hand_strength(
                self.hole_cards,
                game_state.community_cards,
                rng=rng,
            )
            self._hs_cache[game_state.betting_round] = hs_str

        # Build feature vector (must match extraction order)
        cost_to_call = game_state.cost_to_call
        features = [
            _ROUND_MAP.get(game_state.betting_round, 0.0),
            game_state.pot_size / _STARTING_STACK,
            game_state.player_stack / _STARTING_STACK,
            cost_to_call / _STARTING_STACK,
            game_state.bet_count / 4.0,
            game_state.player_position / 7.0,
            1.0 if cost_to_call > 0 else 0.0,
        ]

        if self._has_hs_feature:
            features.append(_HS_MAP.get(hs_str, 0.0))

        X = np.array([features])

        try:
            probs = self._model.predict_proba(X)[0]
            self._predictions += 1

            # Zero out illegal actions before sampling
            if cost_to_call == 0:
                # No bet pending: CHECK (1) or BET (3)
                legal_mask = np.array([0, 1, 0, 1, 0], dtype=np.float64)
            elif game_state.bet_count >= game_state.bet_cap:
                # Cap reached: FOLD (0) or CALL (2)
                legal_mask = np.array([1, 0, 1, 0, 0], dtype=np.float64)
            else:
                # Facing bet: FOLD (0), CALL (2), or RAISE (4)
                legal_mask = np.array([1, 0, 1, 0, 1], dtype=np.float64)

            masked_probs = probs * legal_mask
            total = masked_probs.sum()
            if total <= 0:
                return self._fallback(game_state)

            masked_probs /= total  # Renormalize

            # SAMPLE from distribution (not argmax!)
            action_idx = int(rng.choice(5, p=masked_probs))
            action = _IDX_TO_ACTION[action_idx]
            return self._validate(action, game_state)

        except Exception:
            self._fallbacks += 1
            return self._fallback(game_state)

    def _validate(self, action: ActionType, game_state: GameState) -> ActionType:
        """Ensure the action is legal in the current game state."""
        if game_state.cost_to_call == 0:
            if action in (ActionType.CHECK, ActionType.BET):
                return action
            if action == ActionType.RAISE:
                return ActionType.BET
            return ActionType.CHECK
        else:
            if action in (ActionType.FOLD, ActionType.CALL):
                return action
            if action == ActionType.RAISE:
                if game_state.bet_count >= game_state.bet_cap:
                    return ActionType.CALL
                return ActionType.RAISE
            if action == ActionType.BET:
                return ActionType.RAISE
            return ActionType.CALL

    def _fallback(self, game_state: GameState) -> ActionType:
        """Safe default when model prediction fails."""
        self._fallbacks += 1
        if game_state.cost_to_call == 0:
            return ActionType.CHECK
        return ActionType.CALL

    def prediction_stats(self) -> dict:
        total = self._predictions + self._fallbacks
        return {
            "predictions": self._predictions,
            "fallbacks": self._fallbacks,
            "fallback_rate": self._fallbacks / max(total, 1),
        }
