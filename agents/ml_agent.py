"""ML-powered poker agent for Phase 2.

Loads TWO trained sklearn models per archetype — one for the "no bet
pending" context (CHECK vs BET) and one for the "facing a bet" context
(FOLD vs CALL vs RAISE). This mirrors the rule-based agent's two-stage
decision tree exactly.

Uses ``predict_proba`` and SAMPLES from the predicted distribution
rather than argmax. Without sampling, the ML agent would be deterministic
(always picking the most likely action), which would change the behavioral
fingerprint even if the model's probabilities are correct.
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


_ROUND_MAP = {"preflop": 0.0, "flop": 0.25, "turn": 0.5, "river": 0.75}
_HS_MAP = {"Strong": 1.0, "Medium": 0.5, "Weak": 0.0}
_STARTING_STACK = 200.0


class MLAgent(BaseAgent):
    """Poker agent that uses trained split-context ML models."""

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

        # Load split-context models
        nobet_path = os.path.join(model_dir, f"{archetype}_nobet.pkl")
        facing_path = os.path.join(model_dir, f"{archetype}_facing.pkl")

        if os.path.exists(nobet_path) and os.path.exists(facing_path):
            self._model_nobet = joblib.load(nobet_path)
            self._model_facing = joblib.load(facing_path)
            self._split_mode = True
        else:
            # Fallback: single 5-way model (legacy)
            single_path = os.path.join(model_dir, f"{archetype}.pkl")
            self._model_nobet = joblib.load(single_path)
            self._model_facing = self._model_nobet
            self._split_mode = False

        # Detect feature count (7 without HS, 8 with HS)
        n = getattr(self._model_nobet, "n_features_in_", 7)
        self._has_hs_feature = n >= 8

        # Build class maps for each model
        self._nobet_class_map = self._build_map(self._model_nobet)
        self._facing_class_map = self._build_map(self._model_facing)

        self._predictions = 0
        self._fallbacks = 0

    @staticmethod
    def _build_map(model) -> dict:
        """Map model's internal class indices to canonical action indices."""
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

        cost_to_call = game_state.cost_to_call

        # Build feature vector (must match ml/extract_live.py order)
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
        if self._has_hs_feature:
            features.append(_HS_MAP.get(hs_str, 0.0))

        X = np.array([features])

        try:
            if cost_to_call == 0:
                action = self._decide_nobet(X, rng, game_state)
            else:
                action = self._decide_facing(X, rng, game_state)
            self._predictions += 1
            return action
        except Exception:
            self._fallbacks += 1
            if cost_to_call == 0:
                return ActionType.CHECK
            return ActionType.CALL

    def _decide_nobet(self, X, rng, game_state) -> ActionType:
        """No bet pending: CHECK or BET."""
        raw_probs = self._model_nobet.predict_proba(X)[0]
        class_map = self._nobet_class_map

        # Map to [check_prob, bet_prob]
        check_p = 0.0
        bet_p = 0.0
        for model_idx, canonical_idx in class_map.items():
            if model_idx < len(raw_probs):
                if canonical_idx == 1:  # CHECK
                    check_p = raw_probs[model_idx]
                elif canonical_idx == 3:  # BET
                    bet_p = raw_probs[model_idx]

        total = check_p + bet_p
        if total <= 0:
            return ActionType.CHECK

        # Sample
        if rng.random() < (bet_p / total):
            return ActionType.BET
        return ActionType.CHECK

    def _decide_facing(self, X, rng, game_state) -> ActionType:
        """Facing a bet: FOLD, CALL, or RAISE."""
        raw_probs = self._model_facing.predict_proba(X)[0]
        class_map = self._facing_class_map

        fold_p = 0.0
        call_p = 0.0
        raise_p = 0.0
        for model_idx, canonical_idx in class_map.items():
            if model_idx < len(raw_probs):
                if canonical_idx == 0:  # FOLD
                    fold_p = raw_probs[model_idx]
                elif canonical_idx == 2:  # CALL
                    call_p = raw_probs[model_idx]
                elif canonical_idx == 4:  # RAISE
                    raise_p = raw_probs[model_idx]

        # If at bet cap, convert raise to call
        if game_state.bet_count >= game_state.bet_cap:
            call_p += raise_p
            raise_p = 0.0

        total = fold_p + call_p + raise_p
        if total <= 0:
            return ActionType.CALL

        # Normalize and sample
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
