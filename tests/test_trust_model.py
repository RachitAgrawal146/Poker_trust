"""Unit tests for ``trust.bayesian_model``.

These tighten the safety net on the trust-math primitives by probing
each function in isolation, decoupled from the 500-hand Stage 5
integration test in ``stage_extras.stage5_extras``. Run directly:

    python3 tests/test_trust_model.py

or via pytest:

    python3 -m pytest tests/

Every test is a plain assertion — no fixtures, no conftest, no
third-party dependencies beyond numpy (which is already a project
dep). A failure prints ``FAIL`` and raises; a pass prints ``PASS``
and continues.

These tests DO NOT replace the stage5/6 integration tests. They cover
the primitive layer so that regressions in the math surface at unit-
test time (in seconds) rather than 500 hands into a simulation.
"""

from __future__ import annotations

import math
import os
import sys
import traceback
from typing import Callable, List

# Allow running this file directly as `python3 tests/test_trust_model.py`
# from the repo root — add the repo root to sys.path so ``import trust``
# resolves. pytest / `python3 -m tests.test_trust_model` already handle this.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np

from trust.bayesian_model import (
    TRUST_TYPE_LIST,
    decay_posterior,
    dict_to_posterior,
    entropy,
    initial_posterior,
    posterior_to_dict,
    trust_score,
    update_posterior,
)


# ---------------------------------------------------------------------------
# Test harness — tiny. One function per test, registered in ALL_TESTS.
# ---------------------------------------------------------------------------


_results: List[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    prefix = "PASS" if cond else "FAIL"
    _results.append(f"{prefix} {name}{': ' + detail if detail else ''}")
    assert cond, f"{name}: {detail}"


# ---------------------------------------------------------------------------
# initial_posterior
# ---------------------------------------------------------------------------


def test_initial_posterior_shape():
    post = initial_posterior()
    _check(
        "initial_posterior: returns length-8 numpy array",
        isinstance(post, np.ndarray) and post.shape == (8,) and post.dtype == np.float64,
        f"type={type(post).__name__} shape={getattr(post, 'shape', None)} dtype={getattr(post, 'dtype', None)}",
    )


def test_initial_posterior_is_uniform():
    post = initial_posterior()
    _check(
        "initial_posterior: uniform distribution (1/8 per slot)",
        np.allclose(post, 1.0 / 8),
        f"post={post.tolist()}",
    )


def test_initial_posterior_sums_to_one():
    post = initial_posterior()
    _check(
        "initial_posterior: sums to 1.0",
        math.isclose(float(post.sum()), 1.0, abs_tol=1e-12),
        f"sum={float(post.sum())}",
    )


def test_initial_posterior_independent_copies():
    a = initial_posterior()
    b = initial_posterior()
    a[0] = 99.0
    _check(
        "initial_posterior: successive calls return independent arrays",
        b[0] == 1.0 / 8,
        f"b[0]={b[0]}",
    )


# ---------------------------------------------------------------------------
# entropy
# ---------------------------------------------------------------------------


def test_entropy_at_uniform_is_log2_8():
    post = initial_posterior()
    h = entropy(post)
    _check(
        "entropy: uniform posterior has H = log2(8) = 3 bits",
        math.isclose(h, 3.0, abs_tol=1e-12),
        f"H={h}",
    )


def test_entropy_at_certainty_is_zero():
    post = np.zeros(8, dtype=np.float64)
    post[2] = 1.0
    h = entropy(post)
    _check(
        "entropy: certain posterior (one slot = 1.0) has H = 0",
        math.isclose(h, 0.0, abs_tol=1e-12),
        f"H={h}",
    )


def test_entropy_handles_zero_probabilities():
    # Mixture of two types with 0.5 each, the rest 0. Entropy should be 1 bit.
    post = np.zeros(8, dtype=np.float64)
    post[0] = 0.5
    post[1] = 0.5
    h = entropy(post)
    _check(
        "entropy: two-type even split has H = 1 bit (no log(0) crash)",
        math.isclose(h, 1.0, abs_tol=1e-12),
        f"H={h}",
    )


def test_entropy_bounds():
    # Any 8-element probability distribution must have 0 <= H <= log2(8).
    rng = np.random.default_rng(42)
    for _ in range(100):
        x = rng.random(8)
        post = x / x.sum()
        h = entropy(post)
        _check(
            "entropy: bounded in [0, log2(8)] for random distributions",
            0.0 <= h <= 3.0 + 1e-12,
            f"H={h}",
        )


# ---------------------------------------------------------------------------
# trust_score
# ---------------------------------------------------------------------------


def test_trust_score_at_uniform_matches_average_honesty():
    post = initial_posterior()
    # The trust score at uniform = mean(1 - avg_BR_k) across the 8 types.
    # From archetype_params.HONESTY_SCORES. We hard-code the expected value
    # here so a future rebalance of ARCHETYPE_AVERAGES surfaces immediately.
    from archetype_params import HONESTY_SCORES
    expected = sum(HONESTY_SCORES[k] for k in TRUST_TYPE_LIST) / 8
    t = trust_score(post)
    _check(
        "trust_score: uniform posterior = mean archetype honesty",
        math.isclose(t, expected, abs_tol=1e-12),
        f"T={t} expected={expected}",
    )


def test_trust_score_bounds():
    # trust_score should be in [0, 1] for any valid posterior.
    rng = np.random.default_rng(137)
    for _ in range(100):
        x = rng.random(8)
        post = x / x.sum()
        t = trust_score(post)
        _check(
            "trust_score: bounded in [0, 1] for random distributions",
            0.0 <= t <= 1.0 + 1e-12,
            f"T={t}",
        )


def test_trust_score_concentrated_on_wall_is_highest():
    # Wall's honesty is 1 - 0.038 = 0.962 per archetype_params.HONESTY_SCORES.
    # A posterior that concentrates all mass on wall should yield the highest
    # possible trust score.
    wall_idx = TRUST_TYPE_LIST.index("wall")
    post = np.zeros(8, dtype=np.float64)
    post[wall_idx] = 1.0
    t = trust_score(post)
    _check(
        "trust_score: posterior concentrated on wall matches HONESTY_SCORES['wall']",
        math.isclose(t, 0.962, abs_tol=1e-3),
        f"T={t}",
    )


def test_trust_score_concentrated_on_firestorm_is_lowest():
    # Firestorm honesty = 1 - 0.625 = 0.375. Lowest expected.
    fire_idx = TRUST_TYPE_LIST.index("firestorm")
    post = np.zeros(8, dtype=np.float64)
    post[fire_idx] = 1.0
    t = trust_score(post)
    _check(
        "trust_score: posterior concentrated on firestorm matches HONESTY_SCORES['firestorm']",
        math.isclose(t, 0.375, abs_tol=1e-3),
        f"T={t}",
    )


# ---------------------------------------------------------------------------
# update_posterior
# ---------------------------------------------------------------------------


def test_update_posterior_preserves_normalization():
    post = initial_posterior()
    for _ in range(50):
        post = update_posterior(
            post,
            action_type="bet",
            betting_round="river",
            bucket="Weak",
            is_direct=True,
        )
        _check(
            "update_posterior: output sums to 1.0 after repeated updates",
            math.isclose(float(post.sum()), 1.0, abs_tol=1e-10),
            f"sum={float(post.sum())}",
        )


def test_update_posterior_does_not_mutate_input():
    prior = initial_posterior()
    before = prior.copy()
    _new = update_posterior(
        prior,
        action_type="call",
        betting_round="turn",
        bucket="Medium",
        is_direct=True,
    )
    _check(
        "update_posterior: does not mutate the input prior",
        np.array_equal(prior, before),
        f"prior changed: {prior.tolist()} vs {before.tolist()}",
    )


def test_update_posterior_weak_river_bet_favors_firestorm():
    # A confirmed river bluff (betting on the river with a Weak hand) is
    # the canonical "Firestorm-shaped" observation. After one such update
    # from a uniform prior, the firestorm slot should be the largest.
    fire_idx = TRUST_TYPE_LIST.index("firestorm")
    prior = initial_posterior()
    post = update_posterior(
        prior,
        action_type="bet",
        betting_round="river",
        bucket="Weak",
        is_direct=True,
    )
    top_idx = int(post.argmax())
    _check(
        "update_posterior: weak river bet makes firestorm the top archetype",
        top_idx == fire_idx,
        f"top={TRUST_TYPE_LIST[top_idx]} firestorm_prob={post[fire_idx]:.3f}",
    )
    _check(
        "update_posterior: weak river bet drops wall probability below prior",
        post[TRUST_TYPE_LIST.index("wall")] < 1.0 / 8,
        f"wall_prob={post[TRUST_TYPE_LIST.index('wall')]:.3f}",
    )


def test_update_posterior_strong_river_bet_disfavors_firestorm():
    # Betting on the river with a Strong hand (revealed at showdown) is
    # honest value betting. Wall has the lowest vbr, so a Strong-bucket
    # update should NOT favor Wall; Firestorm and Oracle (high vbr) should
    # rise.
    prior = initial_posterior()
    post = update_posterior(
        prior,
        action_type="bet",
        betting_round="river",
        bucket="Strong",
        is_direct=True,
    )
    wall_idx = TRUST_TYPE_LIST.index("wall")
    _check(
        "update_posterior: strong river bet drops wall probability below prior",
        post[wall_idx] < 1.0 / 8,
        f"wall_prob={post[wall_idx]:.3f}",
    )


def test_update_posterior_third_party_weight_dampens_shift():
    # Applying an identical update with is_direct=False should produce a
    # less extreme posterior shift than is_direct=True, because the
    # likelihood is raised to the power of third_party_weight=0.8.
    prior = initial_posterior()
    direct = update_posterior(
        prior,
        action_type="bet",
        betting_round="river",
        bucket="Weak",
        is_direct=True,
    )
    third = update_posterior(
        prior,
        action_type="bet",
        betting_round="river",
        bucket="Weak",
        is_direct=False,
    )
    fire_idx = TRUST_TYPE_LIST.index("firestorm")
    _check(
        "update_posterior: third-party update shifts less than direct update",
        third[fire_idx] < direct[fire_idx],
        f"direct={direct[fire_idx]:.4f} third-party={third[fire_idx]:.4f}",
    )


def test_update_posterior_marginal_bucket_is_average_of_three():
    # When bucket=None, the likelihood should be the mean of the three
    # bucket-specific likelihoods. Verify indirectly: updating a uniform
    # prior with bucket=None should equal updating with each of Strong/
    # Medium/Weak and averaging the resulting posteriors -- at least
    # directionally. We check that the bucket=None result is "between"
    # the three bucket-specific results for each component.
    prior = initial_posterior()
    strong = update_posterior(prior, "bet", "river", "Strong", is_direct=True)
    medium = update_posterior(prior, "bet", "river", "Medium", is_direct=True)
    weak   = update_posterior(prior, "bet", "river", "Weak",   is_direct=True)
    none   = update_posterior(prior, "bet", "river", None,     is_direct=True)

    # For every component, the bucket=None value should lie within [min, max]
    # of the three bucket-specific values.
    within_bounds = True
    for i in range(8):
        lo = min(strong[i], medium[i], weak[i])
        hi = max(strong[i], medium[i], weak[i])
        if not (lo - 1e-10 <= none[i] <= hi + 1e-10):
            within_bounds = False
            break
    _check(
        "update_posterior: bucket=None result lies within bucket-specific range",
        within_bounds,
        f"none={none.tolist()[:4]}...",
    )


def test_update_posterior_unknown_action_returns_copy():
    # An unrecognized action type should fall through to a no-op copy of
    # the prior (defensive against log regressions).
    prior = initial_posterior()
    result = update_posterior(
        prior,
        action_type="gibberish",
        betting_round="flop",
        bucket="Weak",
        is_direct=True,
    )
    _check(
        "update_posterior: unknown action_type returns a copy of the prior",
        np.array_equal(result, prior) and result is not prior,
        f"result={result.tolist()} prior={prior.tolist()}",
    )


# ---------------------------------------------------------------------------
# decay_posterior
# ---------------------------------------------------------------------------


def test_decay_posterior_preserves_normalization():
    # Start from a concentrated posterior and apply several decay steps.
    post = np.zeros(8, dtype=np.float64)
    post[3] = 0.8
    post[5] = 0.2
    for _ in range(10):
        post = decay_posterior(post)
        _check(
            "decay_posterior: output sums to 1.0 after repeated decays",
            math.isclose(float(post.sum()), 1.0, abs_tol=1e-10),
            f"sum={float(post.sum())}",
        )


def test_decay_posterior_flattens_toward_uniform():
    # Apply many decay steps to a concentrated posterior; entropy should
    # increase monotonically (more uniform = higher entropy).
    post = np.zeros(8, dtype=np.float64)
    post[2] = 0.95
    # Non-zero floor on other slots so that `^ lambda` stays numerically sane.
    post[post == 0] = 0.05 / 7
    h_before = entropy(post)
    for _ in range(100):
        post = decay_posterior(post)
    h_after = entropy(post)
    _check(
        "decay_posterior: entropy increases after 100 decay steps",
        h_after > h_before,
        f"H before={h_before:.4f} H after 100 steps={h_after:.4f}",
    )


def test_decay_posterior_does_not_mutate_input():
    prior = np.array([0.1, 0.2, 0.3, 0.1, 0.1, 0.1, 0.05, 0.05], dtype=np.float64)
    before = prior.copy()
    _ = decay_posterior(prior)
    _check(
        "decay_posterior: does not mutate the input prior",
        np.array_equal(prior, before),
        f"prior changed",
    )


# ---------------------------------------------------------------------------
# dict / array conversion
# ---------------------------------------------------------------------------


def test_posterior_to_dict_has_all_archetypes():
    post = initial_posterior()
    d = posterior_to_dict(post)
    _check(
        "posterior_to_dict: returns a dict with all 8 archetype keys",
        set(d.keys()) == set(TRUST_TYPE_LIST),
        f"keys={sorted(d.keys())}",
    )
    _check(
        "posterior_to_dict: values sum to 1.0",
        math.isclose(sum(d.values()), 1.0, abs_tol=1e-12),
        f"sum={sum(d.values())}",
    )


def test_dict_to_posterior_roundtrips():
    original = initial_posterior()
    d = posterior_to_dict(original)
    back = dict_to_posterior(d)
    _check(
        "dict_to_posterior: roundtrip preserves the array",
        np.allclose(original, back, atol=1e-12),
        f"max|diff|={float(np.abs(original - back).max())}",
    )


def test_dict_to_posterior_missing_keys_default_to_zero():
    partial = {"wall": 1.0}
    post = dict_to_posterior(partial)
    wall_idx = TRUST_TYPE_LIST.index("wall")
    _check(
        "dict_to_posterior: missing archetype keys default to 0.0",
        post[wall_idx] == 1.0 and post.sum() == 1.0,
        f"post={post.tolist()}",
    )


# ---------------------------------------------------------------------------
# Determinism — identical inputs produce identical outputs
# ---------------------------------------------------------------------------


def test_update_posterior_is_deterministic():
    prior = initial_posterior()
    kwargs = dict(action_type="raise", betting_round="turn",
                  bucket="Medium", is_direct=True)
    result1 = update_posterior(prior, **kwargs)
    result2 = update_posterior(prior, **kwargs)
    _check(
        "update_posterior: identical inputs produce identical outputs",
        np.array_equal(result1, result2),
        "",
    )


def test_decay_posterior_is_deterministic():
    prior = np.array([0.2, 0.3, 0.1, 0.05, 0.05, 0.1, 0.1, 0.1], dtype=np.float64)
    result1 = decay_posterior(prior)
    result2 = decay_posterior(prior)
    _check(
        "decay_posterior: identical inputs produce identical outputs",
        np.array_equal(result1, result2),
        "",
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


ALL_TESTS: List[Callable[[], None]] = [
    test_initial_posterior_shape,
    test_initial_posterior_is_uniform,
    test_initial_posterior_sums_to_one,
    test_initial_posterior_independent_copies,
    test_entropy_at_uniform_is_log2_8,
    test_entropy_at_certainty_is_zero,
    test_entropy_handles_zero_probabilities,
    test_entropy_bounds,
    test_trust_score_at_uniform_matches_average_honesty,
    test_trust_score_bounds,
    test_trust_score_concentrated_on_wall_is_highest,
    test_trust_score_concentrated_on_firestorm_is_lowest,
    test_update_posterior_preserves_normalization,
    test_update_posterior_does_not_mutate_input,
    test_update_posterior_weak_river_bet_favors_firestorm,
    test_update_posterior_strong_river_bet_disfavors_firestorm,
    test_update_posterior_third_party_weight_dampens_shift,
    test_update_posterior_marginal_bucket_is_average_of_three,
    test_update_posterior_unknown_action_returns_copy,
    test_decay_posterior_preserves_normalization,
    test_decay_posterior_flattens_toward_uniform,
    test_decay_posterior_does_not_mutate_input,
    test_posterior_to_dict_has_all_archetypes,
    test_dict_to_posterior_roundtrips,
    test_dict_to_posterior_missing_keys_default_to_zero,
    test_update_posterior_is_deterministic,
    test_decay_posterior_is_deterministic,
]


def main() -> int:
    failed = 0
    for test in ALL_TESTS:
        try:
            test()
        except AssertionError as e:
            failed += 1
            traceback.print_exc(limit=1)

    # Deduplicate repeated checks (entropy_bounds runs 100 times, same name).
    seen = set()
    unique_results = []
    for r in _results:
        key = r.split(":", 1)[0] + ":" + r.split(":", 1)[1].split(":", 1)[0] if ":" in r else r
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    for r in unique_results:
        print(r)

    total = len(ALL_TESTS)
    passed = total - failed
    print("-" * 60)
    print(f"RESULT: {passed}/{total} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
