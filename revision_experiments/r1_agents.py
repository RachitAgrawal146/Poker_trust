"""Agents for the R1 rule-based conditions.

Nothing here edits an existing module. Every class is a subclass of a
published agent, and with the default configuration (``beta = 0``, no noise,
no loosening) each one takes exactly the decisions of its parent and draws
exactly the same random numbers (``revision_experiments/test_r1.py`` checks
this against ``phase1/run_sim.py``).

Three things are added.

1. A roster with all reading switched off (``no_read``): the Predator always
   plays its baseline table, the Mirror always plays its default table, and
   the Judge's grievance threshold is out of reach.

2. One uniform, explicit way of responding to a bettor's reputation, the
   *response rule*. When an agent holding a Medium or Weak hand faces a bet or
   raise, its calling probability is multiplied by

       f = 1 + beta * (T_ref - T) / (1 - T_ref)

   where ``T`` is the trust score the agent holds about the player who made
   the bet or raise (expected non-bluff rate under its posterior), ``T_ref``
   is the trust score of the uniform prior, and ``beta >= 0`` is the strength
   of the response. ``f`` is clamped at 0 and the calling probability at
   ``1 - raise probability``. The rule calls more against bettors believed to
   bluff more than a player of unknown type and folds more against bettors
   believed to bluff less. Strong hands are never touched, raising
   probabilities are never touched, and ``beta = 0`` gives ``f = 1``.

   ``source`` selects where ``T`` comes from: the agent's own posterior
   (``posterior``), the bettor's true type (``true``), or the posterior about
   a different, randomly chosen seat (``shuffled``, a placebo). ``target``
   restricts the rule to bets made by one archetype.

   ``focal`` (see ``build_roster``) gives one archetype a different bluff
   rate on every street, for the bluff-rate sweep.

3. Two controls that involve no reading: ``loosen`` multiplies the same
   calling probabilities by a fixed factor per street and hand bucket,
   whoever bet; ``noise_p`` replaces a finished decision by a uniformly
   random legal action with that probability, using a separate random
   stream.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from agents.firestorm import Firestorm
from agents.judge import Judge
from agents.mirror import Mirror
from agents.oracle import Oracle
from agents.phantom import Phantom
from agents.predator import Predator
from agents.sentinel import Sentinel
from agents.wall import Wall
from archetype_params import HONESTY_SCORES
from engine.actions import ActionType
from engine.evaluator import get_hand_strength
from trust import initial_posterior, trust_score as _trust_score

ARCHETYPES: List[str] = [
    "oracle", "sentinel", "firestorm", "wall",
    "phantom", "predator", "mirror", "judge",
]
#: Archetype -> the type whose non-bluff rate the trust score assigns to it.
TRUST_TYPE: Dict[str, str] = {
    "oracle": "oracle", "sentinel": "sentinel", "firestorm": "firestorm",
    "wall": "wall", "phantom": "phantom", "predator": "predator_baseline",
    "mirror": "mirror_default", "judge": "judge_cooperative",
}
ROUNDS = ("preflop", "flop", "turn", "river")
BUCKETS = ("Strong", "Medium", "Weak")
RESPONSES = ("fold", "call", "raise")

#: Trust score of the uniform prior: the reference point of the response rule.
T_REF: float = float(_trust_score(initial_posterior()))


# ---------------------------------------------------------------------------
# Reading switched off
# ---------------------------------------------------------------------------
class PredatorNoRead(Predator):
    """Predator that never consults its posterior: baseline table only."""

    def get_params(self, betting_round, game_state):
        return dict(self.BASELINE_PARAMS[betting_round])


class MirrorNoRead(Mirror):
    """Mirror that never copies an opponent: default table only."""

    def get_params(self, betting_round, game_state):
        return dict(self.DEFAULT_PARAMS[betting_round])


class JudgeNoRead(Judge):
    """Judge whose grievance threshold cannot be reached: cooperative table only."""

    def __init__(self, seat, name="The Judge", rng=None):
        super().__init__(seat=seat, name=name, rng=rng, tau=10 ** 12)


# ---------------------------------------------------------------------------
# Shared per-table context: configuration, bookkeeping, separate random streams
# ---------------------------------------------------------------------------
class Context:
    def __init__(self, cfg: dict, seat_archetypes: List[str], seed: int):
        self.beta: float = float(cfg.get("beta", 0.0))
        self.source: str = cfg.get("source", "posterior")
        self.target: Optional[str] = cfg.get("target")
        self.noise_p: float = float(cfg.get("noise_p", 0.0))
        self.loosen: Optional[dict] = cfg.get("loosen")
        self.seat_arch = list(seat_archetypes)
        self.true_trust = [HONESTY_SCORES[TRUST_TYPE[a]] for a in self.seat_arch]
        # Streams that never touch the table's generator.
        self.noise_rng = np.random.default_rng([seed, 7001])
        self.shuffle_rng = np.random.default_rng([seed, 7002])
        self.shuffle_map = list(range(len(self.seat_arch)))
        n = len(ARCHETYPES)
        # Responses when facing a bet or raise made by a specific opponent:
        # [responder archetype, bettor archetype, street, responder bucket, response]
        self.resp = np.zeros((n, n, 4, 3, 3), dtype=np.int64)
        # Betting when no bet is pending: [archetype, street, bucket, 0=check 1=bet]
        self.open = np.zeros((n, 4, 3, 2), dtype=np.int64)
        # Response-rule bookkeeping: decisions the rule could touch (Medium or
        # Weak hand facing a bet by an identified bettor) and the factor used.
        self.f_n = np.zeros((n, 4, 3), dtype=np.int64)       # [bettor, street, bucket]
        self.f_sum = np.zeros((n, 4, 3), dtype=np.float64)
        self.f_changed = 0
        self.noise_n = 0
        self.decisions = 0

    def new_hand(self) -> None:
        if self.source == "shuffled":
            n = len(self.seat_arch)
            while True:
                perm = self.shuffle_rng.permutation(n)
                if not np.any(perm == np.arange(n)):
                    break
            self.shuffle_map = [int(x) for x in perm]


_AI = {a: i for i, a in enumerate(ARCHETYPES)}
_RI = {r: i for i, r in enumerate(ROUNDS)}
_BI = {b: i for i, b in enumerate(BUCKETS)}


def last_aggressor(game_state, me: int) -> Optional[int]:
    """Seat whose bet or raise this agent is now facing, or None.

    None when the only money to call is the big blind (a forced bet).
    """
    for rec in reversed(game_state.actions_this_round or []):
        if rec.action_type in (ActionType.BET, ActionType.RAISE):
            return None if rec.seat == me else rec.seat
    return None


class ResponseMixin:
    """Overrides ``decide_action`` with the same logic as ``BaseAgent`` plus
    the response rule, the two controls, and bookkeeping."""

    ctx: Context = None  # set by the roster builder

    def _factor(self, bettor: int) -> float:
        c = self.ctx
        if c.beta == 0.0:
            return 1.0
        if c.target is not None and c.seat_arch[bettor] != c.target:
            return 1.0
        if c.source == "true":
            t = c.true_trust[bettor]
        elif c.source == "shuffled":
            other = c.shuffle_map[bettor]
            t = T_REF if other == self.seat else self.trust_score(other)
        else:
            t = self.trust_score(bettor)
        return max(0.0, 1.0 + c.beta * (T_REF - t) / (1.0 - T_REF))

    def decide_action(self, game_state):
        c = self.ctx
        rng = self.rng
        if rng is None:
            rng = np.random.default_rng()
        round_key = game_state.betting_round
        hs = self._hs_cache.get(round_key)
        if hs is None:
            hs = get_hand_strength(self.hole_cards, game_state.community_cards, rng=rng)
            self._hs_cache[round_key] = hs
        params = self.get_params(game_state.betting_round, game_state)
        me = _AI[self.archetype]
        ri, bi = _RI[round_key], _BI[hs]
        c.decisions += 1

        if game_state.cost_to_call == 0:
            if hs == "Strong":
                prob = params["vbr"]
            elif hs == "Medium":
                prob = params["mbr"]
            else:
                prob = params["br"]
            action = ActionType.BET if rng.random() < prob else ActionType.CHECK
            legal = (ActionType.CHECK, ActionType.BET)
            bettor = None
        else:
            if hs == "Strong":
                raise_p = params.get("strong_raise", 0.60)
                call_p = params.get("strong_call", 0.35)
            elif hs == "Medium":
                raise_p = params.get("med_raise", 0.05)
                call_p = params.get("cr", 0.33)
            else:
                raise_p = 0.0
                call_p = params.get("weak_call", 0.15)
            bettor = last_aggressor(game_state, self.seat)
            if bettor is not None and hs != "Strong":
                f = self._factor(bettor)
                if c.loosen is not None:
                    f *= float(c.loosen[round_key][hs])
                ba = _AI[c.seat_arch[bettor]]
                c.f_n[ba, ri, bi] += 1
                c.f_sum[ba, ri, bi] += f
                if f != 1.0:
                    c.f_changed += 1
                    call_p = min(max(call_p * f, 0.0), 1.0 - raise_p)
            roll = rng.random()
            if roll < raise_p:
                action = ActionType.RAISE
            elif roll < raise_p + call_p:
                action = ActionType.CALL
            else:
                action = ActionType.FOLD
            legal = (ActionType.FOLD, ActionType.CALL, ActionType.RAISE)

        if c.noise_p > 0.0 and c.noise_rng.random() < c.noise_p:
            action = legal[int(c.noise_rng.integers(len(legal)))]
            c.noise_n += 1

        if game_state.cost_to_call == 0:
            c.open[me, ri, bi, 1 if action == ActionType.BET else 0] += 1
        elif bettor is not None:
            k = 0 if action == ActionType.FOLD else (1 if action == ActionType.CALL else 2)
            c.resp[me, _AI[c.seat_arch[bettor]], ri, bi, k] += 1
        return action


def _mix(base):
    return type("R1" + base.__name__, (ResponseMixin, base), {})


_PUBLISHED = {
    "oracle": Oracle, "sentinel": Sentinel, "firestorm": Firestorm, "wall": Wall,
    "phantom": Phantom, "predator": Predator, "mirror": Mirror, "judge": Judge,
}
_NO_READ = dict(_PUBLISHED, predator=PredatorNoRead, mirror=MirrorNoRead, judge=JudgeNoRead)
_CLASSES = {
    "published": {a: _mix(k) for a, k in _PUBLISHED.items()},
    "no_read": {a: _mix(k) for a, k in _NO_READ.items()},
}


def _focal_class(base, br: float):
    """``base`` with its bluff rate (bet probability with a Weak hand when no
    bet is pending) set to ``br`` on every street. Everything else in its
    table is unchanged."""

    class Focal(base):
        FOCAL_BR = float(br)

        def get_params(self, betting_round, game_state):
            params = dict(super().get_params(betting_round, game_state))
            params["br"] = self.FOCAL_BR
            return params

    Focal.__name__ = f"{base.__name__}Br{int(round(br * 100)):02d}"
    return Focal


def build_roster(cfg: dict, seat_archetypes: List[str], seed: int):
    """Return (agents, context) for one table.

    ``cfg["focal"] = {"archetype": A, "br": x}`` replaces archetype A by a
    copy whose bluff rate is x on every street (the bluff-rate sweep).
    """
    ctx = Context(cfg, seat_archetypes, seed)
    classes = dict(_CLASSES[cfg.get("roster", "no_read")])
    focal = cfg.get("focal")
    if focal:
        classes[focal["archetype"]] = _focal_class(classes[focal["archetype"]], focal["br"])
    agents = []
    for seat, arch in enumerate(seat_archetypes):
        agent = classes[arch](seat=seat)
        agent.ctx = ctx
        agents.append(agent)
    return agents, ctx
