"""
AdaptiveAgent and AdaptiveJudge -- Phase 2 (adaptive).

These mirror the seven non-Judge Phase 1 archetypes and the Judge,
but instead of returning a frozen ``ARCHETYPE_PARAMS[arch]`` dict from
``get_params``, they return a *mutable* per-round dict held in
``self._live_params``. The HillClimber mutates that dict in place.

Everything else inherits from BaseAgent unchanged. The decision logic
in BaseAgent.decide_action samples from these dicts the same way it
samples from frozen ones, so the only behavioral difference is that
the numbers can change between hands.

Predator and Mirror: in Phase 2 they LOSE their adaptive modifiers
(no PREDATOR_EXPLOIT blend, no per-opponent-mirror copy). They use
``predator_baseline`` / ``mirror_default`` as their starting params
and the hill-climber tunes those. Documented limitation; the question
is whether numerical optimization on aggregate reward can do what
their hand-coded modifiers were designed to do.

Judge: AdaptiveJudge keeps Phase 1's grievance/trigger machinery
verbatim and exposes TWO mutable param sets -- pre_trigger and
post_trigger -- that the climber optimizes independently.
"""

from __future__ import annotations

import sys as _sys
from copy import deepcopy
from pathlib import Path as _Path
from typing import Dict, List, Optional, Tuple

import numpy as np

_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from agents.base_agent import (  # noqa: E402
    BaseAgent,
    _community_slice_for_round,
    _fast_bucket,
)
from archetype_params import ARCHETYPE_PARAMS  # noqa: E402
from engine.actions import ActionRecord, ActionType  # noqa: E402
from engine.game import GameState  # noqa: E402

__all__ = [
    "AdaptiveAgent",
    "AdaptiveJudge",
    "ParamSnapshot",
]


#: One snapshot = (hand_number, deepcopy of the full live param dict).
ParamSnapshot = Tuple[int, Dict[str, Dict[str, float]]]


class AdaptiveAgent(BaseAgent):
    """Generic adaptive agent: mutable per-round params, no extra logic.

    Used for Oracle, Sentinel, Firestorm, Wall, Phantom, Predator
    (baseline-only), Mirror (default-only). Subclassed by AdaptiveJudge
    for the Judge's two-state mechanic.

    Parameters
    ----------
    seat
        Seat index in the table.
    name
        Display name (e.g. "AdaptiveOracle").
    archetype
        One of the BaseAgent archetype strings: oracle, sentinel,
        firestorm, wall, phantom, predator, mirror, judge. (Judge uses
        AdaptiveJudge instead of this class.)
    initial_params_key
        Key into ARCHETYPE_PARAMS used to seed self._live_params.
        Usually equal to ``archetype``, but ``predator`` -> ``predator_baseline``
        and ``mirror`` -> ``mirror_default``.
    rng
        Optional shared RNG; the Table injects this if None.
    """

    def __init__(
        self,
        seat: int,
        name: str,
        archetype: str,
        initial_params_key: str,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype=archetype, seat=seat, rng=rng)
        # deepcopy so mutation doesn't leak back into ARCHETYPE_PARAMS.
        self._live_params: Dict[str, Dict[str, float]] = deepcopy(
            ARCHETYPE_PARAMS[initial_params_key]
        )
        # Filled in on first record_snapshot() call -- ordered list of
        # (hand_number, deepcopy of _live_params).
        self._param_history: List[ParamSnapshot] = []

    # ------------------------------------------------------------------
    # BaseAgent abstract method
    # ------------------------------------------------------------------
    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return self._live_params[betting_round]

    # ------------------------------------------------------------------
    # Hooks the HillClimber calls
    # ------------------------------------------------------------------
    def get_live_params(self) -> Dict[str, Dict[str, float]]:
        """Return the agent's current full param dict (mutable view).

        The climber should treat the returned object as live -- mutation
        of any nested float updates the agent's behavior immediately on
        the next decide_action call. Use deepcopy if you need a frozen
        snapshot."""
        return self._live_params

    def update_params(self, new_params: Dict[str, Dict[str, float]]) -> None:
        """Replace the live params wholesale (deepcopy in)."""
        self._live_params = deepcopy(new_params)

    def record_snapshot(self, hand_number: int) -> None:
        """Append (hand_number, deepcopy) to the trajectory log."""
        self._param_history.append((hand_number, deepcopy(self._live_params)))

    @property
    def param_history(self) -> List[ParamSnapshot]:
        return self._param_history


class AdaptiveJudge(AdaptiveAgent):
    """Judge with two mutable param sets (cooperative / retaliatory).

    The grievance ledger, retaliation trigger (tau = 5), and per-hand
    bluff candidate buffer are identical to Phase 1's Judge. Only the
    *contents* of the two param dicts are now mutable.

    The HillClimber treats this agent specially: it inspects
    ``self._live_pre`` and ``self._live_post`` instead of
    ``self._live_params``. ``get_live_params`` returns
    ``{"pre_trigger": ..., "post_trigger": ...}`` as a flat container
    so the same snapshot machinery works.
    """

    JUDGE_TAU_DEFAULT = 5

    def __init__(
        self,
        seat: int,
        name: str = "AdaptiveJudge",
        rng: Optional[np.random.Generator] = None,
        tau: int = JUDGE_TAU_DEFAULT,
    ) -> None:
        # Seed the parent's _live_params with the cooperative dict so
        # self._live_params is non-None. We override get_live_params to
        # expose both states.
        super().__init__(
            seat=seat,
            name=name,
            archetype="judge",
            initial_params_key="judge_cooperative",
            rng=rng,
        )
        self._live_pre: Dict[str, Dict[str, float]] = deepcopy(
            ARCHETYPE_PARAMS["judge_cooperative"]
        )
        self._live_post: Dict[str, Dict[str, float]] = deepcopy(
            ARCHETYPE_PARAMS["judge_retaliatory"]
        )
        # Drop the parent's _live_params -- get_params dispatches via
        # _live_pre / _live_post directly.
        self._live_params = self._live_pre  # alias for any base-class peek

        self.tau: int = tau
        self.grievance: Dict[int, int] = {}
        self.triggered: Dict[int, bool] = {}
        self.trigger_hand: Dict[int, int] = {}
        self._bluff_candidates: Dict[int, List[str]] = {}

    # ------------------------------------------------------------------
    # Judge-specific overrides (mirror Phase 1 Judge exactly)
    # ------------------------------------------------------------------
    def on_hand_start(self, hand_id: int) -> None:
        super().on_hand_start(hand_id)
        self._bluff_candidates = {}

    def _observe_opponent_action(self, record: ActionRecord) -> None:
        if self._folded_this_hand:
            return
        if record.action_type not in (ActionType.BET, ActionType.RAISE):
            return
        self._bluff_candidates.setdefault(record.seat, []).append(
            record.betting_round
        )

    def observe_showdown(self, showdown_data, community_cards=None) -> None:
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
        # Same trigger-test as Phase 1 Judge: only retaliate if a
        # triggered opponent has actively bet/raised THIS hand.
        for seat in self._bluff_candidates:
            if self.triggered.get(seat, False):
                return self._live_post[betting_round]
        return self._live_pre[betting_round]

    # ------------------------------------------------------------------
    # HillClimber API -- expose both mutable states as one container.
    # ------------------------------------------------------------------
    def get_live_params(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        return {
            "pre_trigger": self._live_pre,
            "post_trigger": self._live_post,
        }

    def update_params(
        self, new_params: Dict[str, Dict[str, Dict[str, float]]]
    ) -> None:
        self._live_pre = deepcopy(new_params["pre_trigger"])
        self._live_post = deepcopy(new_params["post_trigger"])
        self._live_params = self._live_pre  # keep alias coherent

    def record_snapshot(self, hand_number: int) -> None:
        self._param_history.append(
            (
                hand_number,
                {
                    "pre_trigger": deepcopy(self._live_pre),
                    "post_trigger": deepcopy(self._live_post),
                },
            )
        )

    # ------------------------------------------------------------------
    # Convenience -- match Phase 1 Judge's grievance_summary signature
    # so downstream code (run_sim, run_demo) just works.
    # ------------------------------------------------------------------
    def grievance_summary(self):
        out = []
        for seat in sorted(self.grievance):
            out.append(
                (
                    seat,
                    self.grievance[seat],
                    bool(self.triggered.get(seat, False)),
                    self.trigger_hand.get(seat),
                )
            )
        return out
