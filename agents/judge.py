"""
The Judge — Grudger / Punisher.

Starts in the COOPERATIVE state (identical params to the Sentinel) and
maintains a permanent per-opponent integer grievance ledger. Every time
an opponent is caught at showdown having bet or raised against the Judge
earlier in the hand with what was, in truth, a Weak bucket, the Judge's
grievance counter for that seat ticks up by one.

When the grievance counter reaches τ = 5 (configurable via
``JUDGE_TAU_DEFAULT``), the Judge permanently switches to the RETALIATORY
state against that specific opponent. Once triggered, always triggered —
the ledger has no decay. Contrast with the Bayesian trust model, which
decays one lambda step per hand: the Judge's emotional memory is
asymmetric with its rational model, which is the whole point of the
archetype.

Key details from the spec (§12.4) and ``worked_examples.md`` Example 3:

- Grievance is counted at most once per opponent per hand. Multiple
  weak-bluff bets on the same street from the same opponent collapse to
  a single +1. (Worked example 3 is explicit: "grievance[seat_2] = 4 +
  1 = 5".)
- "Against the Judge" means the Judge was still in the hand — i.e. had
  not yet folded — at the moment the opponent acted. Bets made after
  the Judge folded are not grievances; they couldn't have been
  intended as deception against the Judge.
- Only BET or RAISE actions count. CALL is not a deception signal.
- The Judge activates retaliatory params only when a triggered opponent
  has actively bet or raised against the Judge in the current hand.
  If a triggered opponent is at the table but hasn't aggressed this
  hand (e.g., checked or hasn't acted yet), the Judge plays cooperative.
  This produces the spec's intended behavioral split: observers see
  cooperative play in calm hands and retaliatory play only when a
  known deceiver is actively pressuring.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from agents.base_agent import BaseAgent, _community_slice_for_round, _fast_bucket
from archetype_params import ARCHETYPE_PARAMS
from engine.actions import ActionRecord, ActionType
from engine.game import GameState

__all__ = ["Judge", "JUDGE_TAU_DEFAULT"]


#: Grievance threshold. Match spec default τ = 5. Sensitivity sweeps in
#: later stages can override this via a constructor argument.
JUDGE_TAU_DEFAULT = 5


class Judge(BaseAgent):
    COOPERATIVE_PARAMS = ARCHETYPE_PARAMS["judge_cooperative"]
    RETALIATORY_PARAMS = ARCHETYPE_PARAMS["judge_retaliatory"]

    def __init__(
        self,
        seat: int,
        name: str = "The Judge",
        rng: Optional[np.random.Generator] = None,
        tau: int = JUDGE_TAU_DEFAULT,
    ) -> None:
        super().__init__(name=name, archetype="judge", seat=seat, rng=rng)
        self.tau: int = tau

        # Persistent state (survives across hands, never decays).
        self.grievance: Dict[int, int] = {}
        self.triggered: Dict[int, bool] = {}
        self.trigger_hand: Dict[int, int] = {}

        # Per-hand scratch state: for each opponent seat, the list of
        # (betting_round, action_type) tuples that count as candidate
        # grievances — i.e. BETs and RAISEs made while the Judge was
        # still in the hand. We don't need the full ActionRecord, only
        # the round name (for bucket recomputation at showdown).
        self._bluff_candidates: Dict[int, List[str]] = {}

    # ------------------------------------------------------------------
    def on_hand_start(self, hand_id: int) -> None:
        super().on_hand_start(hand_id)
        self._bluff_candidates = {}

    # ------------------------------------------------------------------
    def _observe_opponent_action(self, record: ActionRecord) -> None:
        # Only BET / RAISE while the Judge is still holding cards.
        # ``_folded_this_hand`` flips to True inside
        # ``BaseAgent.observe_action`` as soon as the Judge records its
        # own fold, so any opponent actions that appear after that have
        # ``_folded_this_hand == True`` and are correctly excluded here.
        if self._folded_this_hand:
            return
        if record.action_type not in (ActionType.BET, ActionType.RAISE):
            return
        self._bluff_candidates.setdefault(record.seat, []).append(
            record.betting_round
        )

    # ------------------------------------------------------------------
    def observe_showdown(self, showdown_data, community_cards=None) -> None:
        # Preserve Stage 5 trust-refinement updates — don't rewrite that
        # whole path, just add the grievance pass on top of it.
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

            # Compute the bucket at each candidate round using the revealed
            # hole cards + that round's board slice. If ANY candidate round
            # was a Weak-bucket bet, that's ONE grievance increment for
            # this hand (not one per round). The worked example is
            # explicit: one confirmed bluff = one ledger tick.
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

    # ------------------------------------------------------------------
    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        # Only retaliate if a TRIGGERED opponent has actively bet or raised
        # against the Judge in THIS hand — not just if they're at the table.
        # _bluff_candidates tracks exactly this: seats that have bet/raised
        # while the Judge was still holding cards, accumulated across all
        # streets this hand, reset in on_hand_start.
        for seat in self._bluff_candidates:
            if self.triggered.get(seat, False):
                return self.RETALIATORY_PARAMS[betting_round]
        return self.COOPERATIVE_PARAMS[betting_round]

    # ------------------------------------------------------------------
    # Convenience — used by Stage 6 extras to print a concise status line.
    # ------------------------------------------------------------------
    def grievance_summary(self) -> List[Tuple[int, int, bool, Optional[int]]]:
        """Return [(seat, grievance_count, triggered, trigger_hand), ...]
        for every opponent with non-zero grievance, sorted by seat."""
        out: List[Tuple[int, int, bool, Optional[int]]] = []
        for seat in sorted(self.grievance):
            out.append((
                seat,
                self.grievance[seat],
                bool(self.triggered.get(seat, False)),
                self.trigger_hand.get(seat),
            ))
        return out
