"""
Phase 3 — LLM Agent Class

Thin wrapper around BaseAgent that loads LLM-generated parameters (from
phase3/generated_params/) and uses the exact same decide_action logic
as Phase 1 with probability sampling (NOT argmax).

Provides:
- LLMAgent: for the 5 static archetypes (oracle, sentinel, firestorm,
  wall, phantom) and the default-state adaptive agents (mirror)
- LLMPredator: adaptive agent that reads posteriors and blends baseline
  toward exploit table, using LLM-generated params instead of Phase 1 params
- LLMJudge: adaptive agent with pre/post trigger params and tau=5 threshold

All agents inherit from BaseAgent so they plug directly into the Phase 1
game engine (Table, Hand) without modification. The only difference from
Phase 1 agents is the source of their parameter tables.

Usage::

    from phase3.llm_agent import LLMAgent, LLMPredator, LLMJudge
    from phase3.generated_params import GENERATED_PARAMS

    oracle = LLMAgent(seat=0, name="LLM-Oracle", archetype="oracle",
                      params=GENERATED_PARAMS)
    predator = LLMPredator(seat=5, params=GENERATED_PARAMS)
    judge = LLMJudge(seat=7, params=GENERATED_PARAMS)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from agents.base_agent import BaseAgent, _community_slice_for_round, _fast_bucket
from engine.actions import ActionRecord, ActionType
from engine.game import GameState

try:
    from trust import TRUST_TYPE_LIST
except ImportError:
    # Fallback for environments where trust module isn't available
    TRUST_TYPE_LIST = [
        "oracle", "sentinel", "firestorm", "wall",
        "phantom", "predator_baseline", "mirror_default", "judge_cooperative",
    ]

__all__ = [
    "LLMAgent",
    "LLMPredator",
    "LLMJudge",
]


# ---------------------------------------------------------------------------
# Archetype → param key mapping
# ---------------------------------------------------------------------------

# Maps the user-facing archetype name to the key in the params dict
_ARCHETYPE_TO_PARAM_KEY = {
    "oracle": "oracle",
    "sentinel": "sentinel",
    "firestorm": "firestorm",
    "wall": "wall",
    "phantom": "phantom",
    "predator": "predator_baseline",
    "mirror": "mirror_default",
    "judge": "judge_cooperative",
}


# ---------------------------------------------------------------------------
# LLMAgent — Static archetypes + Mirror default
# ---------------------------------------------------------------------------

class LLMAgent(BaseAgent):
    """LLM-parameterized agent for static archetypes.

    Loads per-round parameters from the GENERATED_PARAMS dict and uses
    the exact same decide_action logic as Phase 1 BaseAgent (probability
    sampling, NOT argmax).
    """

    def __init__(
        self,
        seat: int,
        name: str,
        archetype: str,
        params: Dict[str, Any],
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype=archetype, seat=seat, rng=rng)

        # Resolve param key
        param_key = _ARCHETYPE_TO_PARAM_KEY.get(archetype, archetype)
        if param_key not in params:
            raise KeyError(
                f"Archetype '{archetype}' (param key '{param_key}') "
                f"not found in generated params. "
                f"Available: {list(params.keys())}"
            )
        self._params: Dict[str, Dict[str, float]] = params[param_key]

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self._params[betting_round]


# ---------------------------------------------------------------------------
# LLMPredator — Adaptive exploiter with LLM-generated params
# ---------------------------------------------------------------------------

# Classification constants (same as Phase 1)
CLASSIFICATION_THRESHOLD = 0.60
ALPHA_DENOMINATOR = 0.30


class LLMPredator(BaseAgent):
    """LLM-parameterized Predator that reads posteriors and blends toward
    exploit parameters when opponent is classified with >60% confidence.

    Uses the exact same blend logic as Phase 1 Predator:
        alpha = min(1.0, (max_post - 0.60) / 0.30)
        params = alpha * exploit + (1 - alpha) * baseline
    """

    def __init__(
        self,
        seat: int,
        params: Dict[str, Any],
        name: str = "LLM-Predator",
        rng: Optional[np.random.Generator] = None,
        exploit_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, archetype="predator", seat=seat, rng=rng)

        if "predator_baseline" not in params:
            raise KeyError(
                "predator_baseline not found in generated params. "
                f"Available: {list(params.keys())}"
            )
        self._baseline: Dict[str, Dict[str, float]] = params["predator_baseline"]

        # Exploit table (optional — Predator still works without it,
        # just plays baseline permanently)
        self._exploit: Dict[str, Dict[str, Dict[str, float]]] = exploit_params or {}

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        baseline = self._baseline[betting_round]
        opponents = game_state.active_opponent_seats or []

        best_alpha = 0.0
        best_target: Optional[str] = None

        for opp_seat in opponents:
            post = self.posteriors.get(opp_seat)
            if post is None:
                continue
            max_idx = int(np.argmax(post))
            max_prob = float(post[max_idx])
            if max_prob <= CLASSIFICATION_THRESHOLD:
                continue
            alpha = min(1.0, (max_prob - CLASSIFICATION_THRESHOLD) / ALPHA_DENOMINATOR)
            if alpha > best_alpha:
                best_alpha = alpha
                best_target = TRUST_TYPE_LIST[max_idx]

        if best_target is None or best_alpha <= 0.0:
            return dict(baseline)

        exploit_round = self._exploit.get(best_target, {}).get(betting_round, {})
        if not exploit_round:
            return dict(baseline)

        # Blend: only override keys that appear in the exploit table
        blended = dict(baseline)
        for key, exploit_val in exploit_round.items():
            base_val = baseline.get(key, exploit_val)
            blended[key] = best_alpha * exploit_val + (1.0 - best_alpha) * base_val
        return blended


# ---------------------------------------------------------------------------
# LLMJudge — Conditional cooperator with tau=5 retaliation threshold
# ---------------------------------------------------------------------------

JUDGE_TAU_DEFAULT = 5


class LLMJudge(BaseAgent):
    """LLM-parameterized Judge with cooperative/retaliatory dual-state.

    Maintains a per-opponent grievance ledger. When an opponent accumulates
    tau=5 confirmed bluffs (bet/raise with Weak hand at showdown), the
    Judge permanently switches to retaliatory params against that opponent.

    Uses the exact same grievance mechanism as Phase 1 Judge.
    """

    def __init__(
        self,
        seat: int,
        params: Dict[str, Any],
        name: str = "LLM-Judge",
        rng: Optional[np.random.Generator] = None,
        tau: int = JUDGE_TAU_DEFAULT,
    ) -> None:
        super().__init__(name=name, archetype="judge", seat=seat, rng=rng)
        self.tau: int = tau

        if "judge_cooperative" not in params:
            raise KeyError(
                "judge_cooperative not found in generated params. "
                f"Available: {list(params.keys())}"
            )
        if "judge_retaliatory" not in params:
            raise KeyError(
                "judge_retaliatory not found in generated params. "
                f"Available: {list(params.keys())}"
            )
        self._cooperative: Dict[str, Dict[str, float]] = params["judge_cooperative"]
        self._retaliatory: Dict[str, Dict[str, float]] = params["judge_retaliatory"]

        # Persistent grievance state (never decays)
        self.grievance: Dict[int, int] = {}
        self.triggered: Dict[int, bool] = {}
        self.trigger_hand: Dict[int, int] = {}

        # Per-hand scratch: seats that bet/raised while Judge was in hand
        self._bluff_candidates: Dict[int, List[str]] = {}

    def on_hand_start(self, hand_id: int) -> None:
        super().on_hand_start(hand_id)
        self._bluff_candidates = {}

    def _observe_opponent_action(self, record: ActionRecord) -> None:
        """Track candidate bluffs: BET/RAISE while Judge is still in hand."""
        if self._folded_this_hand:
            return
        if record.action_type not in (ActionType.BET, ActionType.RAISE):
            return
        self._bluff_candidates.setdefault(record.seat, []).append(
            record.betting_round
        )

    def observe_showdown(self, showdown_data, community_cards=None) -> None:
        """Refine posteriors (Stage 5) then check for grievances."""
        super().observe_showdown(showdown_data, community_cards=community_cards)

        if not showdown_data or not community_cards:
            return

        for entry in showdown_data:
            seat = entry["seat"]
            if seat == self.seat:
                continue
            hole = entry.get("hole_cards")
            if not hole:
                continue
            rounds = self._bluff_candidates.get(seat)
            if not rounds:
                continue

            # One confirmed weak-bluff = one grievance tick (not one per round)
            weak_found = False
            for round_name in rounds:
                board = _community_slice_for_round(community_cards, round_name)
                bucket = _fast_bucket(hole, board, rng=self.rng)
                if bucket == "Weak":
                    weak_found = True
                    break
            if not weak_found:
                continue

            new_count = self.grievance.get(seat, 0) + 1
            self.grievance[seat] = new_count
            if new_count >= self.tau and not self.triggered.get(seat, False):
                self.triggered[seat] = True
                self.trigger_hand[seat] = self._current_hand_id or 0

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        """Return retaliatory params if a triggered opponent is actively
        aggressing this hand; cooperative params otherwise."""
        for seat in self._bluff_candidates:
            if self.triggered.get(seat, False):
                return self._retaliatory[betting_round]
        return self._cooperative[betting_round]

    def grievance_summary(self) -> List[Tuple[int, int, bool, Optional[int]]]:
        """Return [(seat, count, triggered, trigger_hand), ...] sorted by seat."""
        out: List[Tuple[int, int, bool, Optional[int]]] = []
        for seat in sorted(self.grievance):
            out.append((
                seat,
                self.grievance[seat],
                bool(self.triggered.get(seat, False)),
                self.trigger_hand.get(seat),
            ))
        return out
