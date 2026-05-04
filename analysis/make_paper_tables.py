"""Generate every CSV + LaTeX table used in the Polygence paper.

Outputs go to ``paper_resources/data/`` (CSVs) and
``paper_resources/tables/`` (LaTeX `tabular` snippets).

Usage::

    python3 analysis/make_paper_tables.py

Tables generated:

    headline_ladder              4-tier r ladder, mean +/- std + per-seed
    per_archetype_p31            Phase 3.1 final stats per archetype
    behavioral_shift_p1_p31      VPIP/PFR/AF deltas P1 -> P3.1
    tma_by_archetype             Trust Manipulation Awareness rankings
    economic_inversion           Rank in P3 vs rank in P3.1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Reuse the same canonical numbers the figures script uses
from analysis.make_paper_figures import (  # type: ignore  # noqa: E402
    R_BY_PHASE, SEEDS, ARCHETYPES, BEHAVIORAL,
    RANK_P3, RANK_P31, TMA_P31,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    print(f"  wrote {path}")


def _write_latex_table(path: Path, caption: str, label: str,
                       column_spec: str, header: list, rows: list,
                       footnote: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\small",
        rf"\begin{{tabular}}{{{column_spec}}}",
        r"\hline",
        " & ".join(header) + r" \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(" & ".join(str(c) for c in row) + r" \\")
    lines += [r"\hline", r"\end{tabular}"]
    if footnote:
        lines.append(rf"\\[2pt]\footnotesize\emph{{{footnote}}}")
    lines += [
        rf"\caption{{{caption}}}",
        rf"\label{{tab:{label}}}",
        r"\end{table}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Table 1: Headline 4-tier ladder
# ---------------------------------------------------------------------------

def table_headline_ladder(data_dir: Path, tex_dir: Path) -> None:
    phases_short = ["Phase 1", "Phase 2", "Phase 3", "Phase 3.1"]
    phase_keys = list(R_BY_PHASE.keys())

    # CSV: per-seed and summary
    header = ["seed"] + phases_short
    rows = []
    for i, seed in enumerate(SEEDS):
        rows.append([seed] + [f"{R_BY_PHASE[p][i]:+.3f}" for p in phase_keys])
    rows.append(["mean"] + [f"{np.mean(R_BY_PHASE[p]):+.3f}" for p in phase_keys])
    rows.append(["std"]  + [f"{np.std(R_BY_PHASE[p]):.3f}" for p in phase_keys])
    _write_csv(data_dir / "headline_ladder.csv", header, rows)

    # LaTeX
    _write_latex_table(
        tex_dir / "headline_ladder.tex",
        caption="Per-seed Pearson r between mean trust score (final hand) and "
                "final stack across the four agent architectures. Phase 3.1 "
                "(LLM agents with chain-of-thought, opponent memory, and "
                "adaptive strategy notes) breaks the trap: the mean r is "
                "statistically indistinguishable from zero at $n=5$.",
        label="ladder",
        column_spec="lrrrr",
        header=["Seed", "P1", "P2", "P3", "P3.1"],
        rows=rows,
        footnote=(r"P1 $\to$ P3.1: $\Delta r = +0.658$, larger than all "
                  r"intermediate steps combined."),
    )


# ---------------------------------------------------------------------------
# Table 2: Per-archetype Phase 3.1 results
# ---------------------------------------------------------------------------

P31_PER_ARCHETYPE = {
    "wall":      {"trust": 0.849, "stack": 280, "stack_std": 88,
                  "rebuys": 0.0, "rank_p3": 8, "rank_p31": 1},
    "firestorm": {"trust": 0.481, "stack": 231, "stack_std": 104,
                  "rebuys": 0.2, "rank_p3": 5, "rank_p31": 2},
    "phantom":   {"trust": 0.748, "stack": 230, "stack_std": 61,
                  "rebuys": 0.2, "rank_p3": 1, "rank_p31": 3},
    "mirror":    {"trust": 0.728, "stack": 208, "stack_std": 83,
                  "rebuys": 0.0, "rank_p3": 2, "rank_p31": 4},
    "judge":     {"trust": 0.781, "stack": 191, "stack_std": 45,
                  "rebuys": 0.0, "rank_p3": 4, "rank_p31": 5},
    "sentinel":  {"trust": 0.786, "stack": 183, "stack_std": 58,
                  "rebuys": 0.0, "rank_p3": 7, "rank_p31": 6},
    "predator":  {"trust": 0.797, "stack": 179, "stack_std": 98,
                  "rebuys": 0.0, "rank_p3": 6, "rank_p31": 7},
    "oracle":    {"trust": 0.625, "stack": 175, "stack_std": 64,
                  "rebuys": 0.0, "rank_p3": 3, "rank_p31": 8},
}


def table_per_archetype_p31(data_dir: Path, tex_dir: Path) -> None:
    archetypes = list(P31_PER_ARCHETYPE.keys())
    header = ["archetype", "trust", "stack_mean", "stack_std",
              "rebuys", "rank_P3", "rank_P31", "rank_change"]
    rows = []
    for arch in archetypes:
        row = P31_PER_ARCHETYPE[arch]
        change = row["rank_p3"] - row["rank_p31"]
        rows.append([
            arch, f"{row['trust']:.3f}", row["stack"], row["stack_std"],
            f"{row['rebuys']:.1f}", row["rank_p3"], row["rank_p31"],
            f"{change:+d}",
        ])
    _write_csv(data_dir / "per_archetype_p31.csv", header, rows)

    _write_latex_table(
        tex_dir / "per_archetype_p31.tex",
        caption="Phase 3.1 economic outcomes by archetype (mean across 5 seeds, "
                "150 hands each). Ranks are derived from final-stack ordering. "
                "Wall, the most-trusted archetype, climbs from rank 8 (Phase 3) "
                "to rank 1 (Phase 3.1), with zero rebuys.",
        label="archetype-p31",
        column_spec="lrrrrrrr",
        header=["Archetype", "Trust", "Stack", "$\\sigma$",
                "Rebuys", "Rank P3", "Rank P3.1", "$\\Delta$"],
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Table 3: Behavioral shift P1 -> P3.1
# ---------------------------------------------------------------------------

def table_behavioral_shift(data_dir: Path, tex_dir: Path) -> None:
    header = ["archetype", "VPIP_P1", "VPIP_P31", "PFR_P1", "PFR_P31",
              "AF_P1", "AF_P31"]
    rows = []
    for arch in ARCHETYPES:
        p1 = BEHAVIORAL["P1"][arch]
        p31 = BEHAVIORAL["P3.1"][arch]
        rows.append([
            arch,
            f"{p1['vpip']:.3f}", f"{p31['vpip']:.3f}",
            f"{p1['pfr']:.3f}",  f"{p31['pfr']:.3f}",
            f"{p1['af']:.2f}",   f"{p31['af']:.2f}",
        ])
    _write_csv(data_dir / "behavioral_shift_p1_p31.csv", header, rows)

    _write_latex_table(
        tex_dir / "behavioral_shift_p1_p31.tex",
        caption="Phase 1 (frozen rules) vs. Phase 3.1 (LLM + reasoning) "
                "behavioral fingerprints. VPIP = voluntarily put in pot; "
                "PFR = preflop raise rate; AF = aggression factor "
                "((bets+raises)/calls).",
        label="behavioral-shift",
        column_spec="lrrrrrr",
        header=["Archetype", "VPIP P1", "VPIP P3.1", "PFR P1", "PFR P3.1",
                "AF P1", "AF P3.1"],
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Table 4: TMA by archetype (P3.1)
# ---------------------------------------------------------------------------

def table_tma(data_dir: Path, tex_dir: Path) -> None:
    items = sorted(TMA_P31.items(), key=lambda kv: -kv[1])
    header = ["archetype", "TMA", "direction"]
    rows = []
    for arch, val in items:
        if val > 0.5:
            direction = "farming (heavy)"
        elif val > 0.0:
            direction = "farming"
        elif val > -0.2:
            direction = "no awareness"
        else:
            direction = "reactive"
        rows.append([arch, f"{val:+.3f}", direction])
    _write_csv(data_dir / "tma_by_archetype.csv", header, rows)

    _write_latex_table(
        tex_dir / "tma_by_archetype.tex",
        caption="Trust Manipulation Awareness (TMA) per archetype in Phase 3.1. "
                "Positive TMA = the agent gains trust before exploiting it. "
                "Six of eight archetypes farm, with Wall and Sentinel showing "
                "the strongest signals.",
        label="tma",
        column_spec="lrl",
        header=["Archetype", "TMA", "Direction"],
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Table 5: Economic inversion (rank slopes)
# ---------------------------------------------------------------------------

def table_economic_inversion(data_dir: Path, tex_dir: Path) -> None:
    archs = list(RANK_P3.keys())
    header = ["archetype", "rank_P3", "rank_P31", "delta"]
    rows = []
    # sort by P31 rank so it reads naturally (best -> worst in P3.1)
    archs_sorted = sorted(archs, key=lambda a: RANK_P31[a])
    for a in archs_sorted:
        delta = RANK_P3[a] - RANK_P31[a]  # positive = climbed
        rows.append([a, RANK_P3[a], RANK_P31[a], f"{delta:+d}"])
    _write_csv(data_dir / "economic_inversion.csv", header, rows)

    _write_latex_table(
        tex_dir / "economic_inversion.tex",
        caption="Economic ranking before and after reasoning scaffolding. "
                "Positive $\\Delta$ = climbed up the leaderboard. Wall climbs "
                "by seven ranks; Oracle drops by five.",
        label="econ-inversion",
        column_spec="lrrr",
        header=["Archetype", "Rank P3", "Rank P3.1", "$\\Delta$"],
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Table 6: Per-seed final stacks per archetype (from JSON dumps)
# ---------------------------------------------------------------------------

def table_per_seed_stacks(data_dir: Path, tex_dir: Path) -> None:
    """Emit a CSV of per-seed final stacks per archetype for both P3 and P3.1."""
    for phase, json_name in [("P3", "phase3_stats.json"),
                             ("P3.1", "phase31_stats.json")]:
        path = _REPO_ROOT / json_name
        if not path.exists():
            print(f"  skipping {phase} per-seed stacks: {path} missing")
            continue
        data = json.load(open(path))
        # Build per-archetype dict of per-seed stacks
        per_arch: dict = {a: {} for a in ARCHETYPES}
        for seed in data["seeds"]:
            sd = seed["seed"]
            for entry in seed["per_seat"]:
                arch = entry["archetype"]
                per_arch.setdefault(arch, {})[sd] = entry["final_stack"]
        seeds_sorted = sorted({s for arch in per_arch.values() for s in arch.keys()})
        header = ["archetype"] + [f"seed_{s}" for s in seeds_sorted] + ["mean"]
        rows = []
        for arch in ARCHETYPES:
            stacks = [per_arch.get(arch, {}).get(s, "") for s in seeds_sorted]
            numeric = [v for v in stacks if isinstance(v, (int, float))]
            mean = round(float(np.mean(numeric)), 1) if numeric else ""
            rows.append([arch] + stacks + [mean])
        out_name = f"per_seed_stacks_{phase.lower().replace('.', '')}.csv"
        _write_csv(data_dir / out_name, header, rows)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", default="paper_resources/data",
        help="Where to write CSVs.",
    )
    parser.add_argument(
        "--tex-dir", default="paper_resources/tables",
        help="Where to write LaTeX tables.",
    )
    args = parser.parse_args()

    data_dir = _REPO_ROOT / args.data_dir
    tex_dir = _REPO_ROOT / args.tex_dir

    print(f"Writing CSVs to:    {data_dir}")
    print(f"Writing LaTeX to:   {tex_dir}")

    table_headline_ladder(data_dir, tex_dir)
    table_per_archetype_p31(data_dir, tex_dir)
    table_behavioral_shift(data_dir, tex_dir)
    table_tma(data_dir, tex_dir)
    table_economic_inversion(data_dir, tex_dir)
    table_per_seed_stacks(data_dir, tex_dir)

    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
