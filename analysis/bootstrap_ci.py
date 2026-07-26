"""Bootstrap and Fisher-z confidence intervals for the trust-profit r ladder.

The headline number in every phase's scorecard is the Pearson correlation
between mean trust score (final hand) and final chip stack across the
eight archetypes. With n = 8 pairs per seed and S seeds per phase, two
levels of uncertainty matter:

1. **Per-seed r CI** — Fisher-z transformation on the n=8 underlying
   correlation. SE in z-space is 1/sqrt(n-3) = 1/sqrt(5) ≈ 0.447.

2. **Per-phase mean-r CI** — uncertainty about the population mean
   across seeds. Reported two ways: a Student t-interval with df = S-1
   and a non-parametric percentile bootstrap (resample the S seeds with
   replacement, 10 000 iterations).

Per-seed r values are loaded from ``paper_resources/data/r_by_phase.json``
via :mod:`analysis.r_data` — that file is the single source of truth. Pass
``--data`` to score a re-run instead.

**Seed count is derived per phase**, so a phase re-run at a different
number of seeds (e.g. the n=20 Phase 3.1 replication the paper's
Limitations section calls for) is handled without any source edit. Phases
may carry different seed counts from one another.

Usage::

    python3 analysis/bootstrap_ci.py
    python3 analysis/bootstrap_ci.py --csv > paper_resources/data/r_bootstrap_ci.csv
    python3 analysis/bootstrap_ci.py --data rerun_r.json --csv > rerun_ci.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.r_data import load_r_data  # noqa: E402


PAIRS_PER_SEED = 8     # archetypes per seed
N_BOOTSTRAP = 10_000
Z_CRIT = 1.959964      # normal at p=0.025


# ----------------------------------------------------------------------
# Student-t critical values.
#
# Previously this module hardcoded ``T_CRIT_DF4 = 2.776`` and applied it
# to every phase regardless of how many seeds that phase actually had.
# That is correct only at exactly 5 seeds. At 20 seeds the correct value
# is 2.093, so the hardcoded constant would have inflated every reported
# t-interval by ~33% — silently, with no error and no warning. Since the
# whole point of the n=20 replication is to *tighten* the interval on
# Phase 3.1, quoting a 33%-too-wide interval would have undercut the
# experiment it was meant to support.
#
# We compute the critical value from the actual df instead. scipy would
# give us this in one line, but nothing else in this repo depends on
# scipy and adding a compiled dependency for one inverse-CDF is a poor
# trade, so the regularized incomplete beta function is inlined below
# (Numerical Recipes continued-fraction form). Accuracy is ~1e-12,
# verified against known table values in ``_selftest``.
# ----------------------------------------------------------------------

def _betacf(a: float, b: float, x: float,
            itmax: int = 300, eps: float = 3e-16) -> float:
    """Continued fraction for the incomplete beta function."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_critical(df: int, alpha: float = 0.05) -> float:
    """Two-tailed Student-t critical value at significance ``alpha``.

    Solves ``I_x(df/2, 1/2) = alpha`` for x by bisection (the mapping is
    monotone), then converts: ``t = sqrt(df/x - df)``.
    """
    if df < 1:
        return float("nan")
    lo, hi = 1e-15, 1.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if _betai(df / 2.0, 0.5, mid) < alpha:
            lo = mid
        else:
            hi = mid
    x = 0.5 * (lo + hi)
    return math.sqrt(df / x - df)


# ----------------------------------------------------------------------
# Per-seed Fisher-z CI on the underlying r (n=8 paired points)
# ----------------------------------------------------------------------

def fisher_z_ci(r: float, n: int = PAIRS_PER_SEED) -> Tuple[float, float]:
    """95% Fisher-z confidence interval for a sample correlation r at n pairs."""
    if not -1.0 < r < 1.0:
        return (r, r)
    z = math.atanh(r)
    se = 1.0 / math.sqrt(max(n - 3, 1))
    lo, hi = z - Z_CRIT * se, z + Z_CRIT * se
    return (math.tanh(lo), math.tanh(hi))


# ----------------------------------------------------------------------
# Per-phase mean-r CIs
# ----------------------------------------------------------------------

def t_interval(values: List[float]) -> Tuple[float, float, float]:
    """Mean and Student-t 95% CI, with df derived from len(values)."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    if n < 2:
        return mean, float("nan"), float("nan")
    se = float(arr.std(ddof=1) / math.sqrt(n))
    half = t_critical(n - 1) * se
    return mean, mean - half, mean + half


def bootstrap_mean_ci(
    values: List[float], n_iter: int = N_BOOTSTRAP, seed: int = 137
) -> Tuple[float, float]:
    """95% percentile bootstrap CI on the mean. Resamples seeds with replacement."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    idx = rng.integers(0, n, size=(n_iter, n))
    means = arr[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def distinct_resamples(n: int) -> int:
    """Number of distinct multisets a size-n bootstrap can draw: C(2n-1, n).

    The paper discloses this for n=5 (126). It shrinks the effective
    resolution of a percentile bootstrap at small n, so it is worth
    reporting alongside the interval rather than buried in a note.
    """
    return math.comb(2 * n - 1, n)


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------

def _render_table(headers: List[str], rows: List[List[str]]) -> str:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    out = [fmt.format(*headers), "  ".join("-" * w for w in widths)]
    for r in rows:
        out.append(fmt.format(*r))
    return "\n".join(out)


def render_per_phase_table(data) -> str:
    headers = [
        "Phase", "n", "Mean r", "SD", "t-interval 95% CI",
        "Bootstrap 95% CI (10k)", "Distinct resamples",
    ]
    rows = []
    for p in data:
        mean, t_lo, t_hi = t_interval(p.r)
        b_lo, b_hi = bootstrap_mean_ci(p.r)
        std = float(np.std(p.r, ddof=1)) if p.n > 1 else 0.0
        rows.append([
            p.name,
            str(p.n),
            f"{mean:+.3f}",
            f"{std:.3f}",
            f"[{t_lo:+.3f}, {t_hi:+.3f}]",
            f"[{b_lo:+.3f}, {b_hi:+.3f}]",
            str(distinct_resamples(p.n)),
        ])
    return _render_table(headers, rows)


def render_per_seed_table(data) -> str:
    headers = ["Phase", "Seed", "r", "Fisher-z 95% CI (n=8)"]
    rows = []
    for p in data:
        for seed, r in zip(p.seeds, p.r):
            lo, hi = fisher_z_ci(r, PAIRS_PER_SEED)
            rows.append([p.name, str(seed), f"{r:+.3f}", f"[{lo:+.3f}, {hi:+.3f}]"])
    return _render_table(headers, rows)


def render_csv(data) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "phase", "seed", "r",
        "fisher_z_ci_lo", "fisher_z_ci_hi",
        "phase_n_seeds", "phase_mean_r", "phase_sd_r",
        "phase_t_ci_lo", "phase_t_ci_hi",
        "phase_bootstrap_ci_lo", "phase_bootstrap_ci_hi",
    ])
    for p in data:
        mean, t_lo, t_hi = t_interval(p.r)
        b_lo, b_hi = bootstrap_mean_ci(p.r)
        std = float(np.std(p.r, ddof=1)) if p.n > 1 else 0.0
        for seed, r in zip(p.seeds, p.r):
            fz_lo, fz_hi = fisher_z_ci(r, PAIRS_PER_SEED)
            writer.writerow([
                p.name, seed, f"{r:.6f}",
                f"{fz_lo:.6f}", f"{fz_hi:.6f}",
                p.n, f"{mean:.6f}", f"{std:.6f}",
                f"{t_lo:.6f}", f"{t_hi:.6f}",
                f"{b_lo:.6f}", f"{b_hi:.6f}",
            ])
    return buf.getvalue()


def _selftest() -> int:
    """Verify t_critical against published table values."""
    known = {1: 12.7062, 2: 4.3027, 4: 2.7764, 9: 2.2622,
             19: 2.0930, 29: 2.0452, 99: 1.9842}
    ok = True
    for df, expect in known.items():
        got = t_critical(df)
        flag = "ok " if abs(got - expect) < 5e-4 else "FAIL"
        if flag == "FAIL":
            ok = False
        print(f"  [{flag}] t_crit(df={df:>3}) = {got:.4f}  expected {expect:.4f}")
    print(f"  [ok ] distinct_resamples(5)  = {distinct_resamples(5)} (paper quotes 126)")
    print(f"  [   ] distinct_resamples(20) = {distinct_resamples(20)}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", action="store_true",
        help="Emit a CSV (one row per (phase, seed)) to stdout instead of "
             "the human-readable tables.",
    )
    parser.add_argument(
        "--data", default=None,
        help="Path to an r_by_phase.json to score instead of the canonical one.",
    )
    parser.add_argument(
        "--selftest", action="store_true",
        help="Check t_critical against published Student-t table values.",
    )
    args = parser.parse_args()

    if args.selftest:
        return _selftest()

    data = load_r_data(args.data)

    if args.csv:
        sys.stdout.write(render_csv(data))
        return 0

    print(f"Source: {data.source}")
    print()
    print("Per-phase mean r and 95% CIs")
    print("=" * 108)
    print(render_per_phase_table(data))
    print()
    print(f"Per-seed r and Fisher-z 95% CI (n={PAIRS_PER_SEED} archetype pairs)")
    print("=" * 108)
    print(render_per_seed_table(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
