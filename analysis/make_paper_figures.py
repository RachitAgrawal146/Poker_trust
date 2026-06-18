"""Generate every figure used in the Polygence paper.

Outputs go to ``paper_resources/figures/`` as PNGs (and optionally PDFs).
All data is hand-curated from the canonical scorecards under
``reports/`` and the per-seed JSON dumps at the repo root, so the script
is fully reproducible without re-running any simulation.

Usage::

    python3 analysis/make_paper_figures.py [--outdir paper_resources/figures]

Figures generated:

    01_four_tier_ladder.png       Mean trust-profit r per phase (bar)
    02_per_seed_ladder.png        Per-seed r dot plot, four phases
    03_economic_inversion.png     Rank P3 -> P3.1 slope chart
    04_behavioral_shift.png       VPIP/PFR/AF per archetype (P1 vs P3.1)
    05_trust_vs_stack.png         Trust-vs-stack scatter, four phases
    06_tma_by_archetype.png       Trust-manipulation awareness per archetype
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Canonical per-seed Pearson r between mean trust score (final hand) and
# final stack across 5 seeds (42, 137, 256, 512, 1024).
#
# PROVENANCE — these values are lifted from canonical scorecards:
#   Phase 1, Phase 2 (bounded), Phase 3, Phase 3.1:
#       reports/phase31_long_scorecard.txt (the "TRUST-PROFIT R LADDER
#       ACROSS FOUR PHASES" table)
#   Phase 2* unbounded (aggressive):
#       reports/phase2_unbounded_scorecard_aggressive.txt
#   Phase 2* unbounded (weak HC, methodology footnote):
#       reports/phase2_unbounded_scorecard.txt
#
# Last reconciled against the scorecards on 2026-05-22 at commit
# `57cca9a1`. To re-derive these numbers programmatically from the
# canonical SQLite databases, run `compute_metrics.py` on each phase's
# `runs_phase*.sqlite` and read the per-seed `r` column out of the
# scorecard output. The 95% CIs that the paper cites are computed in
# `analysis/bootstrap_ci.py`, which takes these same per-seed r values
# as input.
# ---------------------------------------------------------------------------

SEEDS = [42, 137, 256, 512, 1024]

R_BY_PHASE = {
    "Phase 1\nFrozen rules":        [-0.774, -0.608, -0.792, -0.812, -0.776],
    "Phase 2\nHill-climbing":       [-0.759, -0.424, -0.719, -0.717, -0.564],
    "Phase 3\nLLM personalities":   [-0.884, -0.525, -0.171, -0.712, -0.259],
    "Phase 3.1\nLLM + reasoning":   [-0.289, -0.338, -0.327, +0.047, +0.435],
}

# Phase 2* unbounded sub-experiment (rendered alongside the other phases
# by fig_five_tier_ladder but NOT counted as a separate phase in the
# four-tier ladder). AGGRESSIVE is the canonical "did they converge to
# Nash?" test referenced in the paper; WEAK is preserved as a
# methodology footnote (HC delta too small to give the optimizer real
# budget — see paper_resources/notes/phase2_unbounded_writeup.md).
P2_UNBOUNDED_R_AGGRESSIVE = [-0.354, -0.700, -0.344, -0.887, -0.759]
P2_UNBOUNDED_R_WEAK = [-0.791, -0.676, -0.932, -0.717, -0.779]
P2_UNBOUNDED_R = P2_UNBOUNDED_R_AGGRESSIVE  # canonical

# Ordering used for slopes / line plots
PHASE_ORDER = list(R_BY_PHASE.keys())

PHASE_COLORS = {
    "Phase 1\nFrozen rules":      "#8B0000",   # dark red — the trap
    "Phase 2\nHill-climbing":     "#C0392B",   # red
    "Phase 3\nLLM personalities": "#E67E22",   # orange
    "Phase 3.1\nLLM + reasoning": "#1B9E77",   # green — trap broken
}

ARCHETYPES = ["oracle", "sentinel", "firestorm", "wall",
              "phantom", "predator", "mirror", "judge"]

# Okabe-Ito colorblind-safe qualitative palette (Wong 2011, Nat. Methods).
# Every hue is distinguishable under deuteranopia/protanopia/tritanopia.
# The two archetypes most often discussed together -- Firestorm (the
# aggressor) and Wall (the calling-station) -- are vermillion vs blue
# (NOT red/green), so they never collide for a colourblind reader.
ARCHETYPE_COLORS = {
    "oracle":    "#999999",   # neutral grey  — baseline
    "sentinel":  "#009E73",   # bluish green  — honest/grounded
    "firestorm": "#D55E00",   # vermillion    — aggressive
    "wall":      "#0072B2",   # blue          — stoic
    "phantom":   "#CC79A7",   # reddish purple— elusive
    "predator":  "#E69F00",   # orange        — opportunistic
    "mirror":    "#56B4E9",   # sky blue      — reflective
    "judge":     "#000000",   # black         — authoritative
}

# Diverging pair for sign-coded bars (positive vs negative), colourblind-safe.
POS_COLOR = "#0072B2"   # blue
NEG_COLOR = "#D55E00"   # vermillion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_style() -> None:
    # One typeface and one size scale across every figure so the paper's
    # plots read as a single family rather than default-matplotlib output.
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "axes.titlesize": 11,
        "axes.titleweight": "normal",
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9.5,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "legend.frameon": False,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,   # embed TrueType (editable, portable) in PDF
        "ps.fonttype": 42,
    })


def _save(fig: plt.Figure, outdir: Path, name: str) -> None:
    """Write each figure twice: a vector PDF (the version the LaTeX build
    embeds) and a 300-dpi PNG (used by the pandoc/Word build, which cannot
    embed PDFs). ``name`` is given with a raster extension; the PDF sibling
    is derived from it."""
    outdir.mkdir(parents=True, exist_ok=True)
    png_path = outdir / name
    pdf_path = png_path.with_suffix(".pdf")
    fig.savefig(pdf_path, bbox_inches="tight")           # vector
    fig.savefig(png_path, dpi=300, bbox_inches="tight")  # raster fallback
    print(f"  wrote {pdf_path.name} + {png_path.name}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1: four-tier ladder bar chart
# ---------------------------------------------------------------------------

def fig_four_tier_ladder(outdir: Path) -> None:
    means = [float(np.mean(R_BY_PHASE[p])) for p in PHASE_ORDER]
    colors = [PHASE_COLORS[p] for p in PHASE_ORDER]
    # Bootstrap percentile CI on the mean (10,000 resamples, fixed seed).
    rng = np.random.default_rng(137)
    ci_lo, ci_hi = [], []
    for p in PHASE_ORDER:
        arr = np.asarray(R_BY_PHASE[p], dtype=float)
        idx = rng.integers(0, len(arr), size=(10_000, len(arr)))
        boots = arr[idx].mean(axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        ci_lo.append(float(lo))
        ci_hi.append(float(hi))
    err_lo = [m - lo for m, lo in zip(means, ci_lo)]
    err_hi = [hi - m for m, hi in zip(means, ci_hi)]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.bar(
        range(len(PHASE_ORDER)), means,
        yerr=[err_lo, err_hi],
        color=colors, edgecolor="black", linewidth=0.8,
        capsize=6, error_kw={"linewidth": 1.0, "ecolor": "#222"},
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
    ax.axhline(-1.0, color="grey", linewidth=0.4, linestyle=":")

    for i, (m, lo, hi) in enumerate(zip(means, ci_lo, ci_hi)):
        offset = -0.10 if m < 0 else 0.05
        ax.text(i, m + offset,
                f"r = {m:+.3f}\n95% CI [{lo:+.2f}, {hi:+.2f}]",
                ha="center", va="top" if m < 0 else "bottom",
                fontsize=9.5, fontweight="bold")

    ax.set_xticks(range(len(PHASE_ORDER)))
    ax.set_xticklabels(PHASE_ORDER, fontsize=10)
    ax.set_ylabel("Trust-profit Pearson r\n(mean across 5 seeds)", fontsize=11)
    ax.set_title("Trust-Profit r Across Four Agent Architectures",
                 fontsize=12)
    ax.set_ylim(-1.05, 0.40)

    fig.text(0.99, -0.02,
             "Error bars: 95% percentile bootstrap CI on the mean "
             "(10,000 resamples, n=5 seeds).\n"
             "Phase 3.1 CI contains zero AND moderate negative correlations; "
             "n=20 replication needed.",
             ha="right", va="top", fontsize=8.5, color="#555", style="italic")

    fig.tight_layout()
    _save(fig, outdir, "01_four_tier_ladder.png")


# ---------------------------------------------------------------------------
# Figure 1b: five-bar ladder including Phase 2 unbounded sub-experiment
# ---------------------------------------------------------------------------

def fig_five_tier_ladder(outdir: Path) -> None:
    labels = ["Phase 1\nFrozen rules",
              "Phase 2\nBounded HC",
              "Phase 2*\nUnbounded HC",
              "Phase 3\nLLM\npersonalities",
              "Phase 3.1\nLLM\n+ reasoning"]
    rs_lists = [
        R_BY_PHASE["Phase 1\nFrozen rules"],
        R_BY_PHASE["Phase 2\nHill-climbing"],
        P2_UNBOUNDED_R,
        R_BY_PHASE["Phase 3\nLLM personalities"],
        R_BY_PHASE["Phase 3.1\nLLM + reasoning"],
    ]
    means = [float(np.mean(rs)) for rs in rs_lists]
    # Bootstrap percentile CI on the mean (10,000 resamples, fixed seed).
    rng = np.random.default_rng(137)
    ci_lo, ci_hi = [], []
    for rs in rs_lists:
        arr = np.asarray(rs, dtype=float)
        idx = rng.integers(0, len(arr), size=(10_000, len(arr)))
        boots = arr[idx].mean(axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        ci_lo.append(float(lo))
        ci_hi.append(float(hi))
    err_lo = [m - lo for m, lo in zip(means, ci_lo)]
    err_hi = [hi - m for m, hi in zip(means, ci_hi)]
    colors = ["#8B0000", "#C0392B", "#600000",  # P2-unbounded gets darker red
              "#E67E22", "#1B9E77"]

    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    ax.bar(range(len(labels)), means,
           yerr=[err_lo, err_hi],
           color=colors,
           edgecolor="black", linewidth=0.8, capsize=6,
           error_kw={"linewidth": 1.0, "ecolor": "#222"})
    ax.axhline(0, color="black", linewidth=0.8)
    for i, (m, lo, hi) in enumerate(zip(means, ci_lo, ci_hi)):
        offset = -0.10 if m < 0 else 0.05
        ax.text(i, m + offset,
                f"r = {m:+.3f}\n95% CI [{lo:+.2f}, {hi:+.2f}]",
                ha="center", va="top" if m < 0 else "bottom",
                fontsize=9.0, fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel("Trust-profit Pearson r (mean across 5 seeds)")
    ax.set_title("Trust-Profit r Across Five Agent Architectures",
                 fontsize=12)
    ax.set_ylim(-1.05, 0.45)

    fig.text(0.99, -0.02,
             "Error bars: 95% percentile bootstrap CI on the mean (10,000 resamples, n=5 seeds).\n"
             "Phase 3.1 CI [-0.32, +0.20] contains zero AND moderate negative correlations.",
             ha="right", va="top", fontsize=8.5, color="#555", style="italic")
    fig.tight_layout()
    _save(fig, outdir, "01b_five_tier_ladder_with_unbounded.png")


# ---------------------------------------------------------------------------
# Figure 2: per-seed dot plot showing variance and trap inversion
# ---------------------------------------------------------------------------

def fig_per_seed_ladder(outdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    x_positions = np.arange(len(PHASE_ORDER))
    rng = np.random.default_rng(0)

    for i, phase in enumerate(PHASE_ORDER):
        rs = R_BY_PHASE[phase]
        # Scatter individual seeds with small horizontal jitter
        jitter = rng.uniform(-0.08, 0.08, size=len(rs))
        ax.scatter([i + j for j in jitter], rs,
                   color=PHASE_COLORS[phase], s=80, alpha=0.85,
                   edgecolor="black", linewidth=0.8, zorder=3)
        # Mean as horizontal tick
        m = float(np.mean(rs))
        ax.hlines(m, i - 0.25, i + 0.25, color="black", linewidth=2.0, zorder=4)
        ax.text(i + 0.30, m, f"mean = {m:+.3f}", va="center", ha="left",
                fontsize=9, fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(PHASE_ORDER, fontsize=10)
    ax.set_ylabel("Per-seed trust-profit r")
    ax.set_title("Per-Seed Trust-Profit r — Phase 3.1 Spreads Across Zero",
                 fontsize=12)
    ax.set_ylim(-1.05, 0.65)

    # Annotate trap inversion seeds
    for x_idx, phase in enumerate(PHASE_ORDER):
        if "3.1" not in phase:
            continue
        for seed_idx, r in enumerate(R_BY_PHASE[phase]):
            if r > 0:
                ax.annotate(f"seed {SEEDS[seed_idx]}",
                            xy=(x_idx, r), xytext=(x_idx - 0.35, r + 0.10),
                            fontsize=8.5, color="#1B9E77", fontweight="bold",
                            arrowprops=dict(arrowstyle="->", color="#1B9E77",
                                            lw=0.8))

    fig.text(0.99, -0.02,
             "Two of five Phase 3.1 seeds (512, 1024) flip the trap to POSITIVE r.",
             ha="right", va="top", fontsize=8.5, color="#555", style="italic")

    fig.tight_layout()
    _save(fig, outdir, "02_per_seed_ladder.png")


# ---------------------------------------------------------------------------
# Figure 3: economic ordering inversion (P1/P3 -> P3.1 rank slopes)
# ---------------------------------------------------------------------------

# Final-stack-derived economic ranks per archetype, lifted from
# reports/phase31_long_scorecard.txt Table 2 (rank P3 -> P3.1 column).
RANK_P3 = {
    "wall":      8,
    "firestorm": 5,
    "phantom":   1,
    "mirror":    2,
    "judge":     4,
    "sentinel":  7,
    "predator":  6,
    "oracle":    3,
}
RANK_P31 = {
    "wall":      1,
    "firestorm": 2,
    "phantom":   3,
    "mirror":    4,
    "judge":     5,
    "sentinel":  6,
    "predator":  7,
    "oracle":    8,
}


def fig_economic_inversion(outdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    archs = list(RANK_P3.keys())
    x_left, x_right = 0.0, 1.0

    for arch in archs:
        r_left = RANK_P3[arch]
        r_right = RANK_P31[arch]
        delta = r_right - r_left
        color = ARCHETYPE_COLORS[arch]
        # Highlight Wall as the headline shift
        lw = 3.0 if arch == "wall" else 1.4
        alpha = 1.0 if arch == "wall" else 0.65
        ax.plot([x_left, x_right], [r_left, r_right],
                color=color, linewidth=lw, alpha=alpha,
                marker="o", markersize=9, markeredgecolor="black",
                markeredgewidth=0.7)
        # Label both ends
        ax.text(x_left - 0.03, r_left, f"{arch} ({r_left})",
                ha="right", va="center", fontsize=9.5,
                color=color, fontweight="bold" if arch == "wall" else "normal")
        ax.text(x_right + 0.03, r_right, f"{arch} ({r_right})",
                ha="left", va="center", fontsize=9.5,
                color=color, fontweight="bold" if arch == "wall" else "normal")

    ax.invert_yaxis()  # rank 1 at top
    ax.set_xticks([x_left, x_right])
    ax.set_xticklabels(["Phase 3 economic rank", "Phase 3.1 economic rank"],
                       fontsize=10)
    ax.set_yticks(range(1, 9))
    ax.set_ylabel("Economic rank (1 = top earner)")
    ax.set_xlim(-0.45, 1.45)

    ax.grid(False)
    fig.tight_layout()
    _save(fig, outdir, "03_economic_inversion.png")


# ---------------------------------------------------------------------------
# Figure 4: behavioral fingerprint shift (VPIP/PFR/AF) P1 vs P3.1
# ---------------------------------------------------------------------------

# Per-archetype mean VPIP/PFR/AF across 5 seeds. Phase 3.1 row from
# Table 3 of reports/phase31_long_scorecard.txt; Phase 1 row from
# the personality specs (which are themselves Phase 1 v3 measurements).
BEHAVIORAL = {
    "P1": {
        "oracle":    {"vpip": 0.216, "pfr": 0.061, "af": 1.18},
        "sentinel":  {"vpip": 0.149, "pfr": 0.083, "af": 2.12},
        "firestorm": {"vpip": 0.494, "pfr": 0.120, "af": 1.12},
        "wall":      {"vpip": 0.539, "pfr": 0.015, "af": 0.13},
        "phantom":   {"vpip": 0.279, "pfr": 0.092, "af": 1.45},
        "predator":  {"vpip": 0.215, "pfr": 0.063, "af": 1.20},
        "mirror":    {"vpip": 0.214, "pfr": 0.060, "af": 1.18},
        "judge":     {"vpip": 0.149, "pfr": 0.083, "af": 2.10},
    },
    "P3.1": {
        "oracle":    {"vpip": 0.302, "pfr": 0.111, "af": 1.12},
        "sentinel":  {"vpip": 0.120, "pfr": 0.080, "af": 2.53},
        "firestorm": {"vpip": 0.722, "pfr": 0.453, "af": 2.77},
        "wall":      {"vpip": 0.626, "pfr": 0.067, "af": 0.33},
        "phantom":   {"vpip": 0.437, "pfr": 0.162, "af": 1.29},
        "predator":  {"vpip": 0.248, "pfr": 0.119, "af": 1.38},
        "mirror":    {"vpip": 0.196, "pfr": 0.087, "af": 1.11},
        "judge":     {"vpip": 0.174, "pfr": 0.098, "af": 1.87},
    },
}


def fig_behavioral_shift(outdir: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), sharey=False)
    metrics = ["vpip", "pfr", "af"]
    titles = ["VPIP (voluntary pot entry)", "PFR (preflop raise rate)",
              "Aggression Factor"]
    ylabels = ["VPIP", "PFR", "AF"]

    width = 0.38
    x = np.arange(len(ARCHETYPES))

    for ax, metric, title, ylabel in zip(axes, metrics, titles, ylabels):
        p1_vals = [BEHAVIORAL["P1"][a][metric] for a in ARCHETYPES]
        p31_vals = [BEHAVIORAL["P3.1"][a][metric] for a in ARCHETYPES]
        ax.bar(x - width/2, p1_vals, width, color="#8B0000", alpha=0.85,
               edgecolor="black", linewidth=0.6, label="Phase 1")
        ax.bar(x + width/2, p31_vals, width, color="#1B9E77", alpha=0.85,
               edgecolor="black", linewidth=0.6, label="Phase 3.1")
        ax.set_xticks(x)
        ax.set_xticklabels(ARCHETYPES, rotation=35, ha="right", fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=9)

    fig.suptitle("Behavioral Fingerprints — Phase 1 vs. Phase 3.1",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, outdir, "04_behavioral_shift.png")


# ---------------------------------------------------------------------------
# Figure 5: trust-vs-stack scatter per phase
# ---------------------------------------------------------------------------

# Phase 1 per-archetype mean trust score (final hand) and mean final
# stack, used for the left panel of the trust-vs-stack figure.
#   trust: legacy v3 deep-analysis "Trust trajectories" at h10000; trust
#          scores are horizon-independent (they converge well before
#          10k hands), so these equal the canonical Phase 1 values.
#   stack: legacy v3 deep-analysis Section 2 mean final stack per
#          archetype. Magnitudes scale with the play horizon; only the
#          trust-vs-stack *relationship* (steeply negative) is read off
#          this panel, which is what the caption describes.
P1_TRUST_STACK = {
    "oracle":    (0.753, 3091),
    "sentinel":  (0.798, 2797),
    "firestorm": (0.427, 17862),
    "wall":      (0.961, 174),
    "phantom":   (0.646, 129),
    "predator":  (0.806, 1125),
    "mirror":    (0.784, 2856),
    "judge":     (0.801, 1995),
}


def _archetype_means(stats_path: Path) -> dict:
    """Mean (trust, final_stack) per archetype across all seeds in a
    phase3/phase3.1 stats dump."""
    data = json.load(open(stats_path))
    acc: dict = {a: [[], []] for a in ARCHETYPES}
    for seed in data["seeds"]:
        for entry in seed["per_seat"]:
            a = entry["archetype"]
            if a in acc:
                acc[a][0].append(entry["trust"])
                acc[a][1].append(entry["final_stack"])
    return {a: (float(np.mean(t)), float(np.mean(s)))
            for a, (t, s) in acc.items() if t}


def fig_trust_vs_stack(outdir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), sharey=False)

    p31_path = _REPO_ROOT / "paper_resources" / "data" / "phase31_stats.json"
    if not p31_path.exists():
        print(f"  skipping fig 5: {p31_path} missing")
        plt.close(fig)
        return

    panels = [
        (axes[0], P1_TRUST_STACK, "Phase 1  (frozen rules)"),
        (axes[1], _archetype_means(p31_path), "Phase 3.1  (LLM + reasoning)"),
    ]

    for ax, means, label in panels:
        xs, ys = [], []
        for arch in ARCHETYPES:
            if arch not in means:
                continue
            t, s = means[arch]
            xs.append(t)
            ys.append(s)
            ax.scatter([t], [s], s=70, color=ARCHETYPE_COLORS[arch],
                       edgecolor="black", linewidth=0.5, zorder=3)
            ax.annotate(arch, (t, s), textcoords="offset points",
                        xytext=(5, 4), fontsize=8.0,
                        color=ARCHETYPE_COLORS[arch])

        xa, ya = np.array(xs), np.array(ys)
        # Pearson r on the log of the stack (the relationship is monotone
        # across orders of magnitude); reported in the caption, not on-figure.
        r = float(np.corrcoef(xa, np.log10(ya))[0, 1])
        slope, intercept = np.polyfit(xa, np.log10(ya), 1)
        xfit = np.linspace(xa.min(), xa.max(), 100)
        ax.plot(xfit, 10 ** (slope * xfit + intercept), color="black",
                linestyle="--", linewidth=1.0, alpha=0.6, zorder=2)
        print(f"    {label}: r(trust, log10 stack) = {r:+.3f}")

        ax.set_yscale("log")
        ax.set_xlabel("Mean trust score (final hand)")
        ax.set_ylabel("Mean final stack (chips, log scale)")
        ax.set_xlim(0.35, 1.02)
        # A small in-axis phase tag (panel identity also stated in the caption).
        ax.text(0.04, 0.94, label, transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="top")

    fig.tight_layout()
    _save(fig, outdir, "05_trust_vs_stack.png")


# ---------------------------------------------------------------------------
# Figure 6: TMA per archetype (Phase 3.1)
# ---------------------------------------------------------------------------

# From Table 4 of reports/phase31_long_scorecard.txt
TMA_P31 = {
    "wall":      +0.733,
    "sentinel":  +0.704,
    "predator":  +0.625,
    "phantom":   +0.286,
    "judge":     +0.116,
    "oracle":    +0.065,
    "mirror":    -0.277,
    "firestorm": -0.313,
}


def fig_tma_by_archetype(outdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.8))

    archs = list(TMA_P31.keys())
    vals = [TMA_P31[a] for a in archs]
    colors = [POS_COLOR if v > 0 else NEG_COLOR for v in vals]

    ax.barh(range(len(archs)), vals, color=colors, edgecolor="black",
            linewidth=0.7, alpha=0.9)
    for i, v in enumerate(vals):
        offset = -0.02 if v < 0 else 0.02
        ax.text(v + offset, i, f"{v:+.3f}",
                va="center", ha="left" if v >= 0 else "right",
                fontsize=9.5, fontweight="bold")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(len(archs)))
    ax.set_yticklabels(archs)
    ax.invert_yaxis()
    ax.set_xlabel("TMA  (positive = trust farming, negative = reactive)")
    ax.set_xlim(-0.5, 0.95)

    fig.tight_layout()
    _save(fig, outdir, "06_tma_by_archetype.png")


# ---------------------------------------------------------------------------
# Figure 7: bounded Phase 2 vs unbounded Phase 2* per-seed r
#
# Self-contained version of the paper's Fig. 3. The original two-panel
# build (analysis/phase2_unbounded_compare.py) reads the per-archetype
# economic ordering out of runs_phase2_unbounded.sqlite; that database is
# stored via git-LFS and is not always present. The paper caption only
# describes the per-seed paired bars, so this regenerates exactly that
# panel from the canonical per-seed r values already recorded above.
# ---------------------------------------------------------------------------

def fig_p2_bounded_vs_unbounded(outdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.6))

    bounded = R_BY_PHASE["Phase 2\nHill-climbing"]
    unbounded = P2_UNBOUNDED_R_AGGRESSIVE
    x = np.arange(len(SEEDS))
    width = 0.38

    ax.bar(x - width/2, bounded, width, color="#0072B2", alpha=0.9,
           edgecolor="black", linewidth=0.6,
           label=f"Phase 2 bounded (mean {np.mean(bounded):+.3f})")
    ax.bar(x + width/2, unbounded, width, color="#D55E00", alpha=0.9,
           edgecolor="black", linewidth=0.6,
           label=f"Phase 2* unbounded (mean {np.mean(unbounded):+.3f})")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"seed {s}" for s in SEEDS])
    ax.set_ylabel(r"Trust-profit Pearson $r$")
    ax.set_ylim(-1.0, 0.15)
    ax.legend(loc="lower right")

    fig.tight_layout()
    _save(fig, outdir, "07_phase2_bounded_vs_unbounded_aggressive.png")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir", default="paper_resources/figures",
        help="Where to write PNGs (default: paper_resources/figures).",
    )
    parser.add_argument(
        "--only", default=None,
        help="Comma-separated figure numbers to (re)generate. "
             "Example: --only 1,3,5",
    )
    args = parser.parse_args(argv)
    _setup_style()

    outdir = _REPO_ROOT / args.outdir
    print(f"Writing figures to: {outdir}")

    figures = [
        (1, fig_four_tier_ladder),
        (11, fig_five_tier_ladder),  # the "1b" augmented variant
        (2, fig_per_seed_ladder),
        (3, fig_economic_inversion),
        (4, fig_behavioral_shift),
        (5, fig_trust_vs_stack),
        (6, fig_tma_by_archetype),
        (7, fig_p2_bounded_vs_unbounded),
    ]

    only = None
    if args.only:
        only = {int(n.strip()) for n in args.only.split(",") if n.strip()}

    for num, fn in figures:
        if only is not None and num not in only:
            continue
        print(f"  fig {num:02d}: {fn.__name__}")
        fn(outdir)

    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
