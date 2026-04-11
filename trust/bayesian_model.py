"""Bayesian trust model primitives.

Each agent tracks ``posteriors[opponent_seat]``, a distribution over the 8
archetype types. Every observed action drives one Bayesian update step:

    adjusted_likelihood = (1 - epsilon) * raw_likelihood + epsilon * (1/num_actions)
    decayed_prior       = prior ** lambda_decay
    unnormalized        = decayed_prior * (adjusted_likelihood ** weight)
    posterior           = unnormalized / sum(unnormalized)

The ``weight`` exponent distinguishes *direct* evidence (weight = 1.0 — the
observer was in the hand at the time of the action) from *third-party*
evidence (weight = 0.8 — the observer had already folded before the action).

The ``raw_likelihood`` is the probability that a player of ``archetype`` would
choose ``action_type`` at ``betting_round`` given their hand-strength bucket.
If the bucket is unknown (no showdown yet), we marginalize with a uniform
prior over ``{Strong, Medium, Weak}``.

Internally posteriors are numpy float arrays of length 8 (one slot per
archetype in ``TRUST_TYPE_LIST``). ``BaseAgent`` stores the arrays directly
and exposes dict-shaped views via ``posterior_to_dict`` / ``dict_to_posterior``
for any code that prefers named keys.

Hot-path performance matters: a 500-hand Stage 4 demo runs ~192 posterior
updates per action × ~50 actions × 500 hands ≈ 4.8M updates. Everything in
``update_posterior`` is vectorized over the 8-element posterior to keep the
per-update cost under ~10 microseconds.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from archetype_params import (
    ARCHETYPE_PARAMS,
    HONESTY_SCORES,
    TRUST_TYPE_LIST,
)
from config import TRUST


__all__ = [
    "initial_posterior",
    "update_posterior",
    "decay_posterior",
    "trust_score",
    "entropy",
    "posterior_to_dict",
    "dict_to_posterior",
    "TRUST_TYPE_LIST",
]


# ---------------------------------------------------------------------------
# Precomputed lookup tables (built once at module import).
# ---------------------------------------------------------------------------
# Indexed by (archetype, round, action, bucket). Stored as dense float arrays
# so the hot path is a single slice. All likelihoods are clamped to a small
# floor so log-space math downstream can't hit log(0).
# ---------------------------------------------------------------------------

_LIKELIHOOD_FLOOR = 1e-6

_ROUNDS = ("preflop", "flop", "turn", "river")
# Action indices: fold=0, check=1, call=2, bet=3, raise=4
_ACTIONS = ("fold", "check", "call", "bet", "raise")
_BUCKETS = ("Strong", "Medium", "Weak")

_NUM_ARCH = len(TRUST_TYPE_LIST)
_NUM_ROUND = len(_ROUNDS)
_NUM_BUCKET = len(_BUCKETS)
_NUM_ACTION = len(_ACTIONS)

# Number of legal actions available when the agent chose this action. Used
# for the trembling-hand uniform blend: eps * (1/num_actions).
#   bet/check → no bet pending, 2 legal choices
#   call/raise/fold → facing a bet, 3 legal choices
_NUM_AVAILABLE = np.array([3.0, 2.0, 3.0, 2.0, 3.0], dtype=np.float64)


def _compute_bucket_action_likelihood(arch: str, round_name: str, bucket: str, action: str) -> float:
    """P(action | archetype, round, bucket) for a single cell."""
    params = ARCHETYPE_PARAMS[arch][round_name]
    if action in ("bet", "check"):
        if bucket == "Strong":
            p_bet = params["vbr"]
        elif bucket == "Medium":
            p_bet = params["mbr"]
        else:
            p_bet = params["br"]
        val = p_bet if action == "bet" else (1.0 - p_bet)
    else:
        if bucket == "Strong":
            raise_p = params.get("strong_raise", 0.60)
            call_p = params.get("strong_call", 0.35)
        elif bucket == "Medium":
            raise_p = params.get("med_raise", 0.05)
            call_p = params.get("cr", 0.33)
        else:
            raise_p = 0.0
            call_p = params.get("weak_call", 0.15)
        fold_p = 1.0 - raise_p - call_p
        if action == "raise":
            val = raise_p
        elif action == "call":
            val = call_p
        else:
            val = fold_p
    return max(val, _LIKELIHOOD_FLOOR)


def _build_tables():
    """Build the two lookup tables.

    Returns
    -------
    known_L : np.ndarray, shape (num_round, num_bucket, num_action, num_arch)
        ``known_L[r, b, a, :]`` is the 8-element likelihood vector over
        archetypes when the opponent's bucket is known.
    marginal_L : np.ndarray, shape (num_round, num_action, num_arch)
        ``marginal_L[r, a, :]`` is the uniform-bucket marginal of ``known_L``
        averaged over buckets.
    """
    known = np.empty(
        (_NUM_ROUND, _NUM_BUCKET, _NUM_ACTION, _NUM_ARCH),
        dtype=np.float64,
    )
    for ri, round_name in enumerate(_ROUNDS):
        for bi, bucket in enumerate(_BUCKETS):
            for ai, action in enumerate(_ACTIONS):
                for ki, arch in enumerate(TRUST_TYPE_LIST):
                    known[ri, bi, ai, ki] = _compute_bucket_action_likelihood(
                        arch, round_name, bucket, action
                    )
    marginal = known.mean(axis=1)  # average over bucket axis
    return known, marginal


_KNOWN_L, _MARGINAL_L = _build_tables()

# Index maps for fast string→int lookup on the hot path.
_ROUND_IDX = {r: i for i, r in enumerate(_ROUNDS)}
_ACTION_IDX = {a: i for i, a in enumerate(_ACTIONS)}
_BUCKET_IDX = {b: i for i, b in enumerate(_BUCKETS)}

# Vectorized honesty scores aligned with TRUST_TYPE_LIST order.
_HONESTY = np.array(
    [HONESTY_SCORES[arch] for arch in TRUST_TYPE_LIST],
    dtype=np.float64,
)

# Cached constants from config.
_LAMBDA = float(TRUST["lambda_decay"])
_EPS = float(TRUST["epsilon_noise"])
_TPW = float(TRUST["third_party_weight"])
_INITIAL = float(TRUST["initial_prior"])


# ---------------------------------------------------------------------------
# Public API — posterior as a numpy float64 array of length 8.
# ---------------------------------------------------------------------------


def initial_posterior() -> np.ndarray:
    """Uniform prior over the 8 archetype types."""
    return np.full(_NUM_ARCH, _INITIAL, dtype=np.float64)


def update_posterior(
    prior: np.ndarray,
    action_type: str,
    betting_round: str,
    bucket: Optional[str],
    is_direct: bool,
) -> np.ndarray:
    """Return the new posterior after observing one action.

    Does NOT mutate ``prior``. Uses module-level config constants for epsilon
    and third-party weight. **Lambda decay is NOT applied here** — it is
    applied once per hand via ``decay_posterior`` so evidence from the
    sequence of actions within a hand accumulates without being flattened
    between each one. The worked examples apply the lambda decay "per
    observation cycle", and one hand is one observation cycle for an agent
    (the set of actions they witness before the next hand-start).
    """
    r_idx = _ROUND_IDX.get(betting_round)
    a_idx = _ACTION_IDX.get(action_type)
    if r_idx is None or a_idx is None:
        return prior.copy()

    if bucket is None:
        lk = _MARGINAL_L[r_idx, a_idx]
    else:
        b_idx = _BUCKET_IDX.get(bucket)
        if b_idx is None:
            lk = _MARGINAL_L[r_idx, a_idx]
        else:
            lk = _KNOWN_L[r_idx, b_idx, a_idx]

    uniform = 1.0 / _NUM_AVAILABLE[a_idx]
    adj_lk = (1.0 - _EPS) * lk + _EPS * uniform
    weight = 1.0 if is_direct else _TPW
    # Power is only needed when weight != 1.
    if weight != 1.0:
        adj_lk = adj_lk ** weight
    raw = prior * adj_lk
    total = raw.sum()
    if total <= 0 or not np.isfinite(total):
        return prior.copy()
    return raw / total


def decay_posterior(prior: np.ndarray) -> np.ndarray:
    """Apply one lambda-decay step to a posterior.

    Raises every component to ``lambda_decay`` and renormalizes. This is
    called once per hand (in ``BaseAgent.on_hand_end``) so old beliefs fade
    at the rate the spec assumes — one forgetting cycle per hand, not one
    per action.
    """
    if _LAMBDA == 1.0:
        return prior.copy()
    raw = prior ** _LAMBDA
    total = raw.sum()
    if total <= 0 or not np.isfinite(total):
        return prior.copy()
    return raw / total


def trust_score(posterior: np.ndarray) -> float:
    """T = Σ P_k × honesty_k. Returns a value in ``[0, 1]``."""
    return float(np.dot(posterior, _HONESTY))


def entropy(posterior: np.ndarray) -> float:
    """H = -Σ P_k × log2(P_k), in bits. Max ≈ 3 for 8 types."""
    mask = posterior > 0
    if not np.any(mask):
        return 0.0
    safe = posterior[mask]
    return float(-np.sum(safe * np.log2(safe)))


# ---------------------------------------------------------------------------
# Dict views for code that wants named keys (tests, visualizer exporter).
# ---------------------------------------------------------------------------


def posterior_to_dict(posterior: np.ndarray) -> Dict[str, float]:
    return {arch: float(posterior[i]) for i, arch in enumerate(TRUST_TYPE_LIST)}


def dict_to_posterior(d: Dict[str, float]) -> np.ndarray:
    out = np.zeros(_NUM_ARCH, dtype=np.float64)
    for i, arch in enumerate(TRUST_TYPE_LIST):
        out[i] = d.get(arch, 0.0)
    return out
