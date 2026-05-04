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
# final stack across 5 seeds (42, 137, 256, 512, 1024). Lifted from the
# scorecard table headlined "TRUST-PROFIT R LADDER ACROSS FOUR PHASES"
# (reports/phase31_long_scorecard.txt).
# ---------------------------------------------------------------------------

SEEDS = [42, 137, 256, 512, 1024]

R_BY_PHASE = {
    "Phase 1\nFrozen rules":        [-0.774, -0.608, -0.792, -0.812, -0.776],
    "Phase 2\nHill-climbing":       [-0.759, -0.424, -0.719, -0.717, -0.564],
    "Phase 3\nLLM personalities":   [-0.884, -0.525, -0.171, -0.712, -0.259],
    "Phase 3.1\nLLM + reasoning":   [-0.289, -0.338, -0.327, +0.047, +0.435],
}

# Phase 2 unbounded sub-experiment (NOT counted as a separate phase in
# the four-tier ladder; rendered alongside the other phases by
# fig_five_tier_ladder). Two variants:
#   weak: delta=0.03 (default HC). Agents barely moved; trap deepened.
#   aggressive: delta=0.15. Agents moved 11x more; trap roughly unchanged
#               from bounded but per-seed variance exploded.
# AGGRESSIVE is the canonical "did they converge to Nash" test — used in
# the five-tier ladder figure and the paper.
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

ARCHETYPE_COLORS = {
    "oracle":    "#5C5C5C",
    "sentinel":  "#1B9E77",
    "firestorm": "#D55E00",
    "wall":      "#0072B2",
    "phantom":   "#9467BD",
    "predator":  "#E41A1C",
    "mirror":    "#F0E442",
    "judge":     "#56B4E9",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "legend.frameon": False,
    })


def _save(fig: plt.Figure, outdir: Path, name: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / name
    fig.savefig(path, dpi=180, bbox_inches="tight")
    print(f"  wrote {path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1: four-tier ladder bar chart
# ---------------------------------------------------------------------------

def fig_four_tier_ladder(outdir: Path) -> None:
    means = [np.mean(R_BY_PHASE[p]) for p in PHASE_ORDER]
    stds = [np.std(R_BY_PHASE[p]) for p in PHASE_ORDER]
    colors = [PHASE_COLORS[p] for p in PHASE_ORDER]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    bars = ax.bar(
        range(len(PHASE_ORDER)), means, yerr=stds,
        color=colors, edgecolor="black", linewidth=0.8,
        capsize=6, error_kw={"linewidth": 1.0, "ecolor": "#222"},
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
    ax.axhline(-1.0, color="grey", linewidth=0.4, linestyle=":")

    for i, (m, s) in enumerate(zip(means, stds)):
        offset = -0.10 if m < 0 else 0.05
        ax.text(i, m + offset, f"r = {m:+.3f}\n(σ = {s:.3f})",
                ha="center", va="top" if m < 0 else "bottom",
                fontsize=10, fontweight="bold")

    ax.set_xticks(range(len(PHASE_ORDER)))
    ax.set_xticklabels(PHASE_ORDER, fontsize=10)
    ax.set_ylabel("Trust-profit Pearson r\n(mean across 5 seeds)", fontsize=11)
    ax.set_title("The Four-Tier Trap Ladder: Reasoning Breaks the Anti-Correlation",
                 fontsize=12)
    ax.set_ylim(-1.05, 0.30)

    fig.text(0.99, -0.02,
             "Lower (more negative) = more anti-correlation between trust and profit.\n"
             "Phase 3.1 (r = -0.094) is statistically indistinguishable from zero at n=5.",
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
    stds = [float(np.std(rs)) for rs in rs_lists]
    colors = ["#8B0000", "#C0392B", "#600000",  # P2-unbounded gets darker red
              "#E67E22", "#1B9E77"]

    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    ax.bar(range(len(labels)), means, yerr=stds, color=colors,
           edgecolor="black", linewidth=0.8, capsize=6,
           error_kw={"linewidth": 1.0, "ecolor": "#222"})
    ax.axhline(0, color="black", linewidth=0.8)
    for i, (m, s) in enumerate(zip(means, stds)):
        offset = -0.10 if m < 0 else 0.05
        ax.text(i, m + offset, f"r = {m:+.3f}\n(σ = {s:.3f})",
                ha="center", va="top" if m < 0 else "bottom",
                fontsize=9.5, fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel("Trust-profit Pearson r (mean across 5 seeds)")
    ax.set_title("Trust-Profit r With the Unbounded Sub-Experiment",
                 fontsize=12)
    ax.set_ylim(-1.05, 0.30)

    fig.text(0.99, -0.02,
             "Phase 2* (aggressive unbounded HC, [0,1] freedom) sits at r = -0.609 with "
             "high per-seed variance (σ = 0.221).\n"
             "Agents move 11x more than weak HC but DIVERGE rather than converge — "
             "the trust trap is robust to optimization strength.",
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
    ax.set_xlim(-0.45, 1.45)
    ax.set_title("Economic Ordering Inversion: Wall Goes 8 → 1, Oracle 3 → 8",
                 fontsize=12)

    fig.text(0.99, -0.02,
             "Cooperative Wall (most-trusted, calling-station) climbs from rank 8 (last) to rank 1 (first)\n"
             "in Phase 3.1, with zero rebuys. Strategic Oracle drops from 3 to 8.",
             ha="right", va="top", fontsize=8.5, color="#555", style="italic")

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

def fig_trust_vs_stack(outdir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), sharey=False)

    p3_path = _REPO_ROOT / "phase3_stats.json"
    p31_path = _REPO_ROOT / "phase31_stats.json"
    if not p3_path.exists() or not p31_path.exists():
        print(f"  skipping fig 5: {p3_path} or {p31_path} missing")
        plt.close(fig)
        return

    p3_data = json.load(open(p3_path))
    p31_data = json.load(open(p31_path))

    for ax, data, title, color in [
        (axes[0], p3_data, "Phase 3 (LLM personalities) — r = -0.510",
         "#E67E22"),
        (axes[1], p31_data, "Phase 3.1 (LLM + reasoning) — r = -0.094",
         "#1B9E77"),
    ]:
        # Pool every seat across every seed
        all_trust = []
        all_stack = []
        for seed in data["seeds"]:
            for entry in seed["per_seat"]:
                all_trust.append(entry["trust"])
                all_stack.append(entry["final_stack"])
        ax.scatter(all_trust, all_stack, c=color, s=55, alpha=0.7,
                   edgecolor="black", linewidth=0.4)

        # Best-fit line
        if len(all_trust) >= 2:
            xa = np.array(all_trust)
            ya = np.array(all_stack)
            slope, intercept = np.polyfit(xa, ya, 1)
            xs = np.linspace(xa.min(), xa.max(), 100)
            ax.plot(xs, slope * xs + intercept, color="black",
                    linestyle="--", linewidth=1.0, alpha=0.7)

        ax.set_xlabel("Mean trust score (final hand)")
        ax.set_ylabel("Final stack (chips)")
        ax.set_title(title, fontsize=11)

    fig.suptitle("Trust vs. Final Stack — Phase 3 vs. Phase 3.1",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
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
    colors = ["#1B9E77" if v > 0 else "#D55E00" for v in vals]

    ax.barh(range(len(archs)), vals, color=colors, edgecolor="black",
            linewidth=0.7, alpha=0.9)
    for i, v in enumerate(vals):
        offset = -0.02 if v < 0 else 0.02
        ax.text(v + offset, i, f"{v:+.3f}",
                va="center", ha="left" if v >= 0 else "right",
                fontsize=10, fontweight="bold")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(len(archs)))
    ax.set_yticklabels(archs, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("TMA (Trust Manipulation Awareness)")
    ax.set_title("Phase 3.1 — Trust Farming by Archetype",
                 fontsize=12)
    ax.set_xlim(-0.5, 0.95)

    fig.text(0.99, -0.02,
             "Positive TMA = the agent gains trust before exploiting it (six of eight \"farm\").\n"
             "Wall and Sentinel — the most cooperative archetypes — are the heaviest farmers.",
             ha="right", va="top", fontsize=8.5, color="#555", style="italic")

    fig.tight_layout()
    _save(fig, outdir, "06_tma_by_archetype.png")


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
