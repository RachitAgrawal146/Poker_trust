"""
The Mirror — Tit-for-Tat / Reciprocator.

Starts from TAG-like defaults (``mirror_default``) and shifts its
per-round parameters to resemble whichever active opponent at the current
table is putting the most money in preflop (highest observed VPIP). If no
stats have accumulated yet — i.e. a fresh hand before any observations —
it falls back to the default per-round table.

Behavioral tracking (populated in ``_observe_opponent_action``):

    opponent_stats[seat] = {
        "hands_seen": int,
        "preflop_vpip_actions": int,   # call|bet|raise preflop
        "preflop_first_actions": int,  # any first preflop action (VPIP denom)
        "no_cost_bets": int,           # BET opportunities taken
        "no_cost_opps": int,           # BET + CHECK opportunities
        "facing_bet_calls": int,       # CALL facing a bet
        "facing_bet_continues": int,   # CALL + RAISE facing a bet
        "facing_bet_opps": int,        # CALL + RAISE + FOLD facing a bet
        "observed_vpip": float,        # derived
        "observed_br": float,          # derived — P(BET | no cost)
        "observed_vbr": float,         # same (no bucket visibility)
        "observed_mbr": float,         # same
        "observed_cr": float,          # derived — P(call-or-raise | facing)
    }

Distinction from spec §11.3: the spec uses a 0.6 mirror + 0.4 default
blend across all active opponents, and tracks BR/VBR/CR only. The Stage 6
Track version (per the implementation prompt) simplifies to a straight
1.0 copy of the single most-active opponent, with ``mirror_default`` as
the fallback. The blended multi-opponent version can come back later
without rewriting base infrastructure — only this class would need to
change.

Why "call-or-raise" rather than "call only" for ``observed_cr``: the Mirror
cannot see its opponents' hand-strength buckets live, so it has no way to
back out the marginal call rate per bucket. The continuation rate
``P(non-fold | facing a bet)`` is a robust single-number proxy for "how
sticky is this opponent when I bet at them?" — which is exactly the
quantity the Mirror wants to reciprocate.

Why ``weak_call`` is also mirrored from ``observed_cr``: the preflop hand
distribution is heavily skewed toward Weak (preflop_lookup classifies ~80%
of 169 holdings as Weak). If the Mirror only copied ``cr`` (which applies
to Medium hands, ~12% of starting hands), its observed VPIP would barely
move — the spec's "Mirror reflects the table's aggression" promise would
be invisible in aggregate stats. Copying ``observed_cr`` into
``weak_call`` too is the minimal additional change that lets the Mirror's
stickiness track the opponent's continuation rate across its whole
facing-a-bet policy, not just the 12 % medium slice.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS
from engine.actions import ActionRecord, ActionType
from engine.game import GameState

__all__ = ["Mirror"]


_MIRROR_KEYS = ("br", "vbr", "cr", "mbr")


def _empty_stats() -> Dict[str, float]:
    return {
        "hands_seen": 0,
        "preflop_vpip_actions": 0,
        "preflop_first_actions": 0,
        "no_cost_bets": 0,
        "no_cost_opps": 0,
        "facing_bet_calls": 0,
        "facing_bet_continues": 0,
        "facing_bet_opps": 0,
        "observed_vpip": 0.0,
        "observed_br": 0.0,
        "observed_vbr": 0.0,
        "observed_mbr": 0.0,
        "observed_cr": 0.0,
    }


class Mirror(BaseAgent):
    DEFAULT_PARAMS = ARCHETYPE_PARAMS["mirror_default"]

    def __init__(
        self,
        seat: int,
        name: str = "The Mirror",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="mirror", seat=seat, rng=rng)
        # Per-hand scratch: set of opponent seats we've already counted as
        # "seen this hand" so that ``hands_seen`` increments once per hand.
        self._seen_this_hand: set = set()
        # Same idea for VPIP: at most one "VPIP action" per opponent per hand.
        self._vpip_counted_this_hand: set = set()

    # ------------------------------------------------------------------
    def on_hand_start(self, hand_id: int) -> None:
        super().on_hand_start(hand_id)
        self._seen_this_hand = set()
        self._vpip_counted_this_hand = set()

    # ------------------------------------------------------------------
    def _observe_opponent_action(self, record: ActionRecord) -> None:
        seat = record.seat
        stats = self.opponent_stats.get(seat)
        if stats is None:
            stats = _empty_stats()
            self.opponent_stats[seat] = stats

        # Count one "hand seen" per opponent per hand — the first time we
        # observe any action from them in a hand.
        if seat not in self._seen_this_hand:
            self._seen_this_hand.add(seat)
            stats["hands_seen"] += 1

        at = record.action_type
        # Bucket the action into "no cost to call" vs "facing a bet". The
        # engine's own action semantics make this unambiguous:
        #   BET / CHECK   -> no cost_to_call for this seat
        #   CALL / RAISE / FOLD -> facing a bet
        if at == ActionType.CHECK:
            stats["no_cost_opps"] += 1
        elif at == ActionType.BET:
            stats["no_cost_opps"] += 1
            stats["no_cost_bets"] += 1
        elif at == ActionType.CALL:
            stats["facing_bet_opps"] += 1
            stats["facing_bet_calls"] += 1
            stats["facing_bet_continues"] += 1
        elif at == ActionType.RAISE:
            stats["facing_bet_opps"] += 1
            stats["facing_bet_continues"] += 1
        elif at == ActionType.FOLD:
            stats["facing_bet_opps"] += 1

        # Preflop VPIP signature (call/bet/raise counts as VPIP; check and
        # fold don't). Once per opponent per hand, to match the self-stats
        # semantics in ``BaseAgent``.
        if record.betting_round == "preflop":
            if seat not in self._vpip_counted_this_hand:
                self._vpip_counted_this_hand.add(seat)
                stats["preflop_first_actions"] += 1
                if at in (ActionType.CALL, ActionType.BET, ActionType.RAISE):
                    stats["preflop_vpip_actions"] += 1

        # Derived rolling averages — recomputed every update so
        # ``get_params`` is a straight dict read.
        hd = max(stats["hands_seen"], 1)
        nc = max(stats["no_cost_opps"], 1)
        fb = max(stats["facing_bet_opps"], 1)
        pf = max(stats["preflop_first_actions"], 1)
        stats["observed_br"] = stats["no_cost_bets"] / nc
        stats["observed_vbr"] = stats["no_cost_bets"] / nc
        stats["observed_mbr"] = stats["no_cost_bets"] / nc
        stats["observed_cr"] = stats["facing_bet_continues"] / fb
        stats["observed_vpip"] = stats["preflop_vpip_actions"] / pf

    # ------------------------------------------------------------------
    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        default = dict(self.DEFAULT_PARAMS[betting_round])

        opponents = game_state.active_opponent_seats or []
        if not opponents:
            return default

        # Only consider active opponents we actually have evidence on.
        candidates = [
            (seat, self.opponent_stats[seat])
            for seat in opponents
            if seat in self.opponent_stats
            and self.opponent_stats[seat]["preflop_first_actions"] > 0
        ]
        if not candidates:
            return default

        # Pick the single most-active opponent (highest observed VPIP).
        # Ties broken by seat order — deterministic so the same seed
        # reproduces the same decisions.
        candidates.sort(key=lambda kv: (-kv[1]["observed_vpip"], kv[0]))
        _, target_stats = candidates[0]

        # Copy the four headline metrics the prompt calls out
        # (br/vbr/cr/mbr). The strong_raise / strong_call / med_raise /
        # strong_fold keys stay at mirror_default so the Mirror still
        # has a coherent raise-when-strong policy. We additionally set
        # ``weak_call`` from observed_cr so the mirror's weak-hand
        # stickiness tracks the target's continuation rate — see the
        # module docstring for why this matters given the preflop hand
        # distribution.
        blended = default
        for key in _MIRROR_KEYS:
            blended[key] = float(target_stats[f"observed_{key}"])
        blended["weak_call"] = float(target_stats["observed_cr"])
        return blended

    # ------------------------------------------------------------------
    # Convenience accessors used by Stage 6 tests — thin wrappers over
    # the rolling averages so tests don't poke at the dict layout.
    # ------------------------------------------------------------------
    def observed_vpip(self, seat: int) -> float:
        stats = self.opponent_stats.get(seat)
        return float(stats["observed_vpip"]) if stats else 0.0

    def observed_br(self, seat: int) -> float:
        stats = self.opponent_stats.get(seat)
        return float(stats["observed_br"]) if stats else 0.0

    def observed_cr(self, seat: int) -> float:
        stats = self.opponent_stats.get(seat)
        return float(stats["observed_cr"]) if stats else 0.0
