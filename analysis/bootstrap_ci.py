"""Bootstrap and Fisher-z confidence intervals for the trust-profit r ladder.

The headline number in every phase's scorecard is the Pearson correlation
between mean trust score (final hand) and final chip stack across the
eight archetypes. With n = 8 pairs per seed and 5 seeds per phase, two
levels of uncertainty matter:

1. **Per-seed r CI** — Fisher-z transformation on the n=8 underlying
   correlation. SE in z-space is 1/sqrt(n-3) = 1/sqrt(5) ≈ 0.447.

2. **Per-phase mean-r CI** — uncertainty about the population mean
   across seeds. Reported two ways: a Student t-interval with df=4 and
   a non-parametric percentile bootstrap (resample 5 seeds with
   replacement, 10 000 iterations).

Source values come from `reports/phase*_long_scorecard.txt` and
`phase3_stats.json` / `phase31_stats.json`. They are the canonical
5-seed-x-N-hand scorecard numbers and match the same per-seed array
defined in `analysis/make_paper_figures.py::R_BY_PHASE`. Last
reconciled against the scorecards on 2026-05-22 at commit `57cca9a1`.
If the underlying simulations are re-run, update both modules in
lockstep.

Usage::

    python3 analysis/bootstrap_ci.py
    python3 analysis/bootstrap_ci.py --csv > paper_resources/data/r_bootstrap_ci.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import sys
from typing import Dict, List, Tuple

import numpy as np


# ----------------------------------------------------------------------
# Canonical per-seed r values (5 seeds × per-phase scorecard).
#
# Phase 1 / Phase 2 / Phase 2* numbers come from the matched 5×10 000
# runs whose scorecards live under `reports/`. Phase 3 / Phase 3.1
# numbers come from the per-seed dumps at
# `paper_resources/data/phase3_stats.json` and
# `paper_resources/data/phase31_stats.json`.
# ----------------------------------------------------------------------

SEEDS = [42, 137, 256, 512, 1024]

PHASES: Dict[str, List[float]] = {
    "Phase 1 (frozen rules)":          [-0.774, -0.608, -0.792, -0.812, -0.776],
    "Phase 2 (bounded HC)":            [-0.759, -0.424, -0.719, -0.717, -0.564],
    "Phase 2* (unbounded HC, weak)":   [-0.791, -0.676, -0.932, -0.717, -0.779],
    "Phase 2* (unbounded HC, aggr.)":  [-0.354, -0.700, -0.344, -0.887, -0.759],
    "Phase 3 (LLM personalities)":     [-0.884, -0.525, -0.171, -0.712, -0.259],
    "Phase 3.1 (LLM + reasoning)":     [-0.289, -0.338, -0.327,  0.047,  0.435],
}

PAIRS_PER_SEED = 8     # archetypes per seed
N_BOOTSTRAP = 10_000
T_CRIT_DF4 = 2.776     # Student t at p=0.025, df=4
Z_CRIT = 1.959964      # normal at p=0.025


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
    """Mean and Student-t 95% CI half-width for n=5 (df=4)."""
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / math.sqrt(len(arr)))
    half = T_CRIT_DF4 * se
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


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------

def _format_per_phase_row(name: str, r_values: List[float]) -> List[str]:
    mean, t_lo, t_hi = t_interval(r_values)
    b_lo, b_hi = bootstrap_mean_ci(r_values)
    std = np.std(r_values, ddof=1)
    return [
        name,
        f"{mean:+.3f}",
        f"{std:.3f}",
        f"[{t_lo:+.3f}, {t_hi:+.3f}]",
        f"[{b_lo:+.3f}, {b_hi:+.3f}]",
    ]


def render_per_phase_table() -> str:
    headers = [
        "Phase",
        "Mean r",
        "SD (n=5)",
        "t-interval 95% CI",
        "Bootstrap 95% CI (10k)",
    ]
    rows = [_format_per_phase_row(name, vals) for name, vals in PHASES.items()]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    lines = []
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    lines.append(fmt.format(*headers))
    lines.append("  ".join("-" * w for w in widths))
    for r in rows:
        lines.append(fmt.format(*r))
    return "\n".join(lines)


def render_per_seed_table() -> str:
    headers = [
        "Phase", "Seed", "r", "Fisher-z 95% CI (n=8)",
    ]
    rows = []
    for name, vals in PHASES.items():
        for seed, r in zip(SEEDS, vals):
            lo, hi = fisher_z_ci(r, PAIRS_PER_SEED)
            rows.append([
                name,
                str(seed),
                f"{r:+.3f}",
                f"[{lo:+.3f}, {hi:+.3f}]",
            ])
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    out = [fmt.format(*headers), "  ".join("-" * w for w in widths)]
    for r in rows:
        out.append(fmt.format(*r))
    return "\n".join(out)


def render_csv() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "phase", "seed", "r",
        "fisher_z_ci_lo", "fisher_z_ci_hi",
        "phase_mean_r", "phase_sd_r",
        "phase_t_ci_lo", "phase_t_ci_hi",
        "phase_bootstrap_ci_lo", "phase_bootstrap_ci_hi",
    ])
    for name, vals in PHASES.items():
        mean, t_lo, t_hi = t_interval(vals)
        b_lo, b_hi = bootstrap_mean_ci(vals)
        std = float(np.std(vals, ddof=1))
        for seed, r in zip(SEEDS, vals):
            fz_lo, fz_hi = fisher_z_ci(r, PAIRS_PER_SEED)
            writer.writerow([
                name, seed, f"{r:.6f}",
                f"{fz_lo:.6f}", f"{fz_hi:.6f}",
                f"{mean:.6f}", f"{std:.6f}",
                f"{t_lo:.6f}", f"{t_hi:.6f}",
                f"{b_lo:.6f}", f"{b_hi:.6f}",
            ])
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", action="store_true",
        help="Emit a CSV (one row per (phase, seed)) to stdout instead of "
             "the human-readable tables.",
    )
    args = parser.parse_args()

    if args.csv:
        sys.stdout.write(render_csv())
        return 0

    print("Per-phase mean r and 95% CIs (n=5 seeds)")
    print("=" * 72)
    print(render_per_phase_table())
    print()
    print(f"Per-seed r and Fisher-z 95% CI (n={PAIRS_PER_SEED} archetype pairs)")
    print("=" * 72)
    print(render_per_seed_table())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
