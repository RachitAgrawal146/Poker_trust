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

from treys import Card as _TreysCard, Evaluator as _TreysEvaluator

from config import SIMULATION
from engine.actions import ActionRecord, ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState
from preflop_lookup import get_preflop_bucket
import numpy as np  # noqa: F401  (already imported above; kept for clarity)

from trust import (
    initial_posterior,
    update_posterior,
    decay_posterior,
    trust_score as _trust_score,
    entropy as _entropy,
    posterior_to_dict as _posterior_to_dict,
)

__all__ = ["BaseAgent"]


def _community_slice_for_round(community_cards, round_name: str) -> list:
    """Return the portion of the community that was visible on ``round_name``.

    Preflop: no cards. Flop: first 3. Turn: first 4. River: all 5.
    """
    if round_name == "preflop":
        return []
    if round_name == "flop":
        return list(community_cards[:3])
    if round_name == "turn":
        return list(community_cards[:4])
    return list(community_cards[:5])


# Singleton evaluator shared by every BaseAgent for the fast showdown bucket.
_SHOWDOWN_EVAL = _TreysEvaluator()


def _fast_bucket(hole, community, rng=None) -> str:
    """Bucket a revealed hand into Strong / Medium / Weak WITHOUT Monte Carlo.

    Used only on the trust-refinement path in ``observe_showdown`` — we
    already know the exact hole cards, so a deterministic treys hand-class
    lookup is both faster and more appropriate than re-running equity. The
    live decision path still uses the Monte Carlo ``get_hand_strength``.

    Preflop uses the 169-bucket ``preflop_lookup`` (also O(1)).

    NOTE: ``rng`` is accepted for API compatibility but unused (deterministic).
    """
    if not community:
        c1, c2 = hole[0], hole[1]
        return get_preflop_bucket(
            _TreysCard.int_to_str(c1), _TreysCard.int_to_str(c2)
        )
    rank = _SHOWDOWN_EVAL.evaluate(list(community), list(hole))
    rank_class = _SHOWDOWN_EVAL.get_rank_class(rank)
    # treys rank classes (lower = better):
    #   1 Straight Flush, 2 Quads, 3 Full House, 4 Flush, 5 Straight,
    #   6 Trips, 7 Two Pair, 8 Pair, 9 High Card
    if rank_class <= 6:
        return "Strong"
    if rank_class <= 8:
        return "Medium"
    return "Weak"


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

        # ----- Stage 5 trust plumbing -----
        # seat -> numpy float64 array of length 8, one slot per archetype in
        # ``trust.TRUST_TYPE_LIST``. Lazy-initialized on first observation of
        # a given seat. Stored as arrays (not dicts) for vectorized updates;
        # call ``trust.posterior_to_dict`` to get a named-key view.
        self.posteriors: Dict[int, "np.ndarray"] = {}
        # seat -> {observed_br, observed_vbr, ...}. Stage 6 (Mirror) will
        # populate this with rolling behavioral averages.
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
        # True after this agent folds during the current hand — used to
        # downgrade subsequent observations to "third-party" weight.
        self._folded_this_hand: bool = False
        # Per-hand buffer of observed non-self actions, keyed by seat. At
        # showdown we replay these with the now-known bucket to sharpen the
        # posterior for revealed opponents.
        self._hand_action_log: Dict[int, List[ActionRecord]] = {}

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
        # Stage 5: per-hand trust scratch state.
        self._folded_this_hand = False
        self._hand_action_log = {}

    def on_hand_end(self, hand_id: int) -> None:
        if self._saw_flop_this_hand:
            self.stats["saw_flop"] += 1
        # Stage 5: apply one lambda-decay step per hand to every posterior
        # we've accumulated. This is the "forgetting" cycle — without it,
        # the posterior would collect evidence indefinitely; with it, the
        # model stays sensitive to behavioral shifts (Judge retaliation,
        # Mirror mimicry) at the rate the spec's worked examples assume.
        for seat, post in self.posteriors.items():
            self.posteriors[seat] = decay_posterior(post)

    def observe_action(self, record: ActionRecord) -> None:
        # Note any time *this* agent acts post-preflop — means we saw the flop.
        if (
            record.seat == self.seat
            and record.betting_round in ("flop", "turn", "river")
        ):
            self._saw_flop_this_hand = True

        if record.seat == self.seat:
            # Track self stats — and mark self-fold for "direct vs third-party"
            # bookkeeping on subsequent observations this hand.
            if record.action_type == ActionType.FOLD:
                self._folded_this_hand = True

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
            return

        # ------------------------------------------------------------------
        # Stage 5: Bayesian posterior update for the acting opponent.
        # ------------------------------------------------------------------
        # Lazy-initialize a uniform posterior on first sight of this seat.
        if record.seat not in self.posteriors:
            self.posteriors[record.seat] = initial_posterior()

        is_direct = not self._folded_this_hand
        self.posteriors[record.seat] = update_posterior(
            prior=self.posteriors[record.seat],
            action_type=record.action_type.value,
            betting_round=record.betting_round,
            bucket=None,  # unknown live — marginalize over buckets
            is_direct=is_direct,
        )

        # Buffer for showdown refinement.
        self._hand_action_log.setdefault(record.seat, []).append(record)

        # Stage 6 adaptive-agent hook. BaseAgent defaults to a no-op; Mirror
        # and Judge override ``_observe_opponent_action`` to accumulate
        # per-opponent behavioral stats / grievance candidates WITHOUT
        # replacing the audited Stage 5 trust-update flow above.
        self._observe_opponent_action(record)

    # ------------------------------------------------------------------
    # Stage 6 hook — adaptive agents override this instead of
    # ``observe_action`` itself so the Stage 5 trust plumbing stays in
    # one audited place. Called once per non-self action, after the
    # posterior update, with the same ActionRecord the engine logged.
    # ------------------------------------------------------------------
    def _observe_opponent_action(self, record: ActionRecord) -> None:
        """No-op default. Mirror tracks per-opponent rolling stats here;
        Judge buffers candidate-bluff actions here. See those subclasses."""
        return None

    def observe_showdown(self, showdown_data, community_cards=None) -> None:
        if not showdown_data:
            return
        for entry in showdown_data:
            if entry["seat"] == self.seat:
                self.stats["showdowns"] += 1
                if entry["won"]:
                    self.stats["showdowns_won"] += 1
                break

        # ------------------------------------------------------------------
        # Stage 5: refine posteriors for every revealed opponent using their
        # now-known hand-strength bucket at each round they acted.
        # ------------------------------------------------------------------
        if not community_cards:
            return
        is_direct = not self._folded_this_hand
        for entry in showdown_data:
            seat = entry["seat"]
            if seat == self.seat:
                continue
            hole = entry.get("hole_cards")
            if not hole:
                continue
            actions = self._hand_action_log.get(seat, [])
            if not actions:
                continue
            # Pre-compute the bucket at each round from the revealed hole
            # cards + the subset of community cards visible that round.
            bucket_cache: Dict[str, str] = {}
            for action in actions:
                round_name = action.betting_round
                if round_name not in bucket_cache:
                    board = _community_slice_for_round(
                        community_cards, round_name
                    )
                    bucket_cache[round_name] = _fast_bucket(
                        hole, board, rng=self.rng
                    )
                bucket = bucket_cache[round_name]
                self.posteriors[seat] = update_posterior(
                    prior=self.posteriors[seat],
                    action_type=action.action_type.value,
                    betting_round=round_name,
                    bucket=bucket,
                    is_direct=is_direct,
                )

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

    # ------------------------------------------------------------------
    # Stage 5 trust accessors
    # ------------------------------------------------------------------
    def trust_score(self, opponent_seat: int) -> float:
        """Expected honesty of ``opponent_seat`` under the current posterior.

        For seats that have never been observed, return the trust score of
        the uniform prior (the Nash baseline ≈ 0.752). This is the correct
        initial belief per the spec worked examples.
        """
        post = self.posteriors.get(opponent_seat)
        if post is None:
            return _trust_score(initial_posterior())
        return _trust_score(post)

    def entropy(self, opponent_seat: int) -> float:
        """Posterior entropy (in bits) for ``opponent_seat``.

        For unobserved seats, return ``log2(8) = 3`` — the uniform-prior
        entropy, matching the spec's "initial state" definition.
        """
        post = self.posteriors.get(opponent_seat)
        if post is None:
            return _entropy(initial_posterior())
        return _entropy(post)

    # ------------------------------------------------------------------
    # Spec-named aliases used by ``test_cases.test_stage_5``. These return
    # a plain-dict view of the posterior so tests that don't know about
    # numpy can iterate by archetype name.
    # ------------------------------------------------------------------
    def get_posterior(self, opponent_seat: int) -> Dict[str, float]:
        post = self.posteriors.get(opponent_seat)
        if post is None:
            from trust import initial_posterior as _init
            return _posterior_to_dict(_init())
        return _posterior_to_dict(post)

    def get_trust_score(self, opponent_seat: int) -> float:
        return self.trust_score(opponent_seat)

    def get_entropy(self, opponent_seat: int) -> float:
        return self.entropy(opponent_seat)
