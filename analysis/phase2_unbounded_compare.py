"""Compare bounded Phase 2 to unbounded Phase 2 — generate the headline
figure + scorecard text for the unbounded experiment.

Reads:
    runs_phase2_unbounded.sqlite   (this session's new run)
    phase2/adaptive/param_trajectories_unbounded.json
    phase2/adaptive/optimization_log_unbounded.json

Outputs:
    paper_resources/figures/07_phase2_bounded_vs_unbounded.png
    paper_resources/figures/10_param_drift_unbounded.png
    paper_resources/data/phase2_unbounded_summary.csv
    paper_resources/notes/phase2_unbounded_writeup.md
    reports/phase2_unbounded_scorecard.txt

Usage::

    python3 analysis/phase2_unbounded_compare.py
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.make_paper_figures import (  # noqa: E402
    ARCHETYPES, ARCHETYPE_COLORS, R_BY_PHASE, SEEDS, _setup_style, _save,
)


# ---------------------------------------------------------------------------
# Bounded Phase 2 reference (per-seed r values, hardcoded from scorecard)
# ---------------------------------------------------------------------------

P2_BOUNDED_R = R_BY_PHASE["Phase 2\nHill-climbing"]


# ---------------------------------------------------------------------------
# Unbounded summary extraction
# ---------------------------------------------------------------------------

def extract_unbounded_summary(db_path: Path) -> Dict:
    conn = sqlite3.connect(str(db_path))
    summary = {"per_seed": [], "per_arch_means": {}}

    for (run_id, seed, num_hands) in conn.execute(
        "SELECT run_id, seed, num_hands FROM runs ORDER BY seed"
    ):
        ts, ss = [], []
        per_seat = []
        for seat in range(8):
            t = conn.execute(
                "SELECT AVG(trust) FROM trust_snapshots "
                "WHERE run_id=? AND target_seat=? "
                "AND hand_id=(SELECT MAX(hand_id) FROM trust_snapshots "
                "WHERE run_id=?)",
                (run_id, seat, run_id),
            ).fetchone()[0] or 0.5

            stats = conn.execute(
                "SELECT archetype, final_stack, rebuys "
                "FROM agent_stats WHERE run_id=? AND seat=?",
                (run_id, seat),
            ).fetchone()
            if not stats:
                continue
            arch, stack, rebuys = stats
            ts.append(float(t))
            ss.append(int(stack))
            per_seat.append({
                "seat": seat, "archetype": arch, "trust": float(t),
                "final_stack": int(stack), "rebuys": int(rebuys),
            })

        r = float(np.corrcoef(ts, ss)[0, 1]) if len(ts) > 1 else 0.0
        summary["per_seed"].append({
            "seed": seed, "run_id": run_id, "num_hands": num_hands,
            "r": r, "per_seat": per_seat,
        })

    # Per-archetype mean stack across seeds
    per_arch_stacks: Dict[str, List[int]] = {a: [] for a in ARCHETYPES}
    per_arch_trust: Dict[str, List[float]] = {a: [] for a in ARCHETYPES}
    per_arch_rebuys: Dict[str, List[int]] = {a: [] for a in ARCHETYPES}
    for seed in summary["per_seed"]:
        for entry in seed["per_seat"]:
            arch = entry["archetype"]
            if arch in per_arch_stacks:
                per_arch_stacks[arch].append(entry["final_stack"])
                per_arch_trust[arch].append(entry["trust"])
                per_arch_rebuys[arch].append(entry["rebuys"])

    summary["per_arch_means"] = {
        a: {
            "stack_mean": float(np.mean(per_arch_stacks[a]))
                if per_arch_stacks[a] else 0.0,
            "stack_std": float(np.std(per_arch_stacks[a]))
                if per_arch_stacks[a] else 0.0,
            "trust_mean": float(np.mean(per_arch_trust[a]))
                if per_arch_trust[a] else 0.0,
            "rebuys_mean": float(np.mean(per_arch_rebuys[a]))
                if per_arch_rebuys[a] else 0.0,
        }
        for a in ARCHETYPES
    }

    conn.close()
    return summary


# ---------------------------------------------------------------------------
# Figure 7: bounded vs unbounded comparison
# ---------------------------------------------------------------------------

def fig_bounded_vs_unbounded(summary: Dict, outdir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    # Left: per-seed r
    rs_unb = [s["r"] for s in summary["per_seed"]]
    seeds_unb = [s["seed"] for s in summary["per_seed"]]

    bounded_dict = {SEEDS[i]: P2_BOUNDED_R[i] for i in range(len(SEEDS))}
    rs_bnd = [bounded_dict.get(s, np.nan) for s in seeds_unb]

    width = 0.38
    x = np.arange(len(seeds_unb))
    ax1.bar(x - width/2, rs_bnd, width, color="#C0392B", alpha=0.85,
            edgecolor="black", linewidth=0.6, label="Phase 2 bounded")
    ax1.bar(x + width/2, rs_unb, width, color="#2E86C1", alpha=0.85,
            edgecolor="black", linewidth=0.6, label="Phase 2 unbounded")
    ax1.axhline(0, color="black", linewidth=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"seed {s}" for s in seeds_unb], rotation=20)
    ax1.set_ylabel("Trust-profit Pearson r")
    mean_bnd = float(np.nanmean(rs_bnd))
    mean_unb = float(np.mean(rs_unb))
    ax1.set_title(f"Per-seed r (mean: bnd {mean_bnd:+.3f} → unb {mean_unb:+.3f})",
                  fontsize=11)
    ax1.legend(loc="best")
    ax1.set_ylim(-1.05, max(0.40, max(rs_unb + [m for m in rs_bnd
                                                if not np.isnan(m)]) + 0.10))

    # Right: economic ordering shift (per archetype mean stack)
    archs = ARCHETYPES
    means = [summary["per_arch_means"][a]["stack_mean"] for a in archs]
    stds = [summary["per_arch_means"][a]["stack_std"] for a in archs]
    colors = [ARCHETYPE_COLORS[a] for a in archs]
    order = sorted(range(len(archs)), key=lambda i: -means[i])
    ax2.barh(range(len(archs)),
             [means[i] for i in order],
             xerr=[stds[i] for i in order],
             color=[colors[i] for i in order],
             edgecolor="black", linewidth=0.6, alpha=0.9,
             error_kw={"linewidth": 0.8, "ecolor": "#222"})
    ax2.set_yticks(range(len(archs)))
    ax2.set_yticklabels([archs[i] for i in order], fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("mean final stack (chips, ± σ)")
    ax2.set_title("Phase 2 unbounded — economic ordering", fontsize=11)
    ax2.axvline(200, color="grey", linewidth=0.5, linestyle=":")
    ax2.text(202, len(archs) - 1, "starting stack", fontsize=8,
             color="grey", va="bottom")

    fig.suptitle(
        "Phase 2: Bounded vs. Unbounded Hill-Climbing",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save(fig, outdir, "07_phase2_bounded_vs_unbounded.png")


# ---------------------------------------------------------------------------
# Figure 10: param drift (where did each archetype end up?)
# ---------------------------------------------------------------------------

def fig_param_drift(traj_path: Path, outdir: Path) -> None:
    if not traj_path.exists():
        print(f"  skipping fig 10: {traj_path} missing")
        return

    data = json.load(open(traj_path))
    # data: { "seed_42": { "seat_0_oracle": [{"hand": h, "params": {...}}, ...], ...}, ...}

    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharey=True)
    axes = axes.flatten()

    metrics = ["br", "vbr", "cr", "mbr"]
    metric_titles = {"br": "Bluff rate", "vbr": "Value bet rate",
                     "cr": "Call rate", "mbr": "Medium bet rate"}

    # For each archetype panel, plot the FINAL value of each (round, metric)
    # averaged across seeds, with the Phase 1 starting value as a reference.
    for ax_idx, arch in enumerate(ARCHETYPES):
        ax = axes[ax_idx]
        seed_keys = list(data.keys())
        # Find this archetype's history (any seat key matching the archetype)
        this_arch_histories = []
        for sk in seed_keys:
            for slot, hist in data[sk].items():
                if slot.endswith(f"_{arch}"):
                    this_arch_histories.append(hist)
                    break
        if not this_arch_histories:
            continue

        # Plot trajectories of (round, metric) preflop.br for visual signal
        for hist in this_arch_histories:
            xs = [pt["hand"] for pt in hist]
            # For Judge, params is {"pre_trigger":..., "post_trigger":...}
            ys = []
            for pt in hist:
                p = pt["params"]
                if isinstance(p, dict) and "pre_trigger" in p:
                    p = p["pre_trigger"]
                ys.append(p.get("preflop", {}).get("br", np.nan))
            ax.plot(xs, ys, color=ARCHETYPE_COLORS[arch], linewidth=1.0,
                    alpha=0.7)

        ax.set_title(arch, fontsize=11, fontweight="bold")
        ax.set_xlabel("hand")
        ax.set_ylim(0.0, 1.0)
        ax.axhline(0.5, color="grey", linewidth=0.4, linestyle=":")

    axes[0].set_ylabel("preflop bluff rate (br)")
    axes[4].set_ylabel("preflop bluff rate (br)")
    fig.suptitle(
        "Phase 2 Unbounded — Preflop Bluff-Rate Drift Across Seeds",
        fontsize=13, fontweight="bold",
    )
    fig.text(0.5, 0.02,
             "Each translucent line = one seed. With unbounded freedom, agents are free "
             "to drift toward br=0 or br=1; the question is whether they converge.",
             ha="center", fontsize=9, color="#555", style="italic")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    _save(fig, outdir, "10_param_drift_unbounded.png")


# ---------------------------------------------------------------------------
# Scorecard text
# ---------------------------------------------------------------------------

def write_scorecard(summary: Dict, path: Path) -> None:
    rs = [s["r"] for s in summary["per_seed"]]
    mean_r = float(np.mean(rs))
    std_r = float(np.std(rs))

    bnd_dict = {SEEDS[i]: P2_BOUNDED_R[i] for i in range(len(SEEDS))}

    lines = []
    lines.append("=" * 80)
    lines.append("  PHASE 2 UNBOUNDED SCORECARD  --  hill-climbing with [0,1] freedom")
    lines.append(f"                              {len(rs)} seeds x {summary['per_seed'][0]['num_hands']} hands")
    lines.append("=" * 80)
    lines.append("")
    lines.append("  Setup: ARCHETYPE_BOUNDS replaced with (0.0, 1.0) on every metric.")
    lines.append("  Trust model unchanged from Phase 1 (still uses bounded likelihood")
    lines.append("  tables -- so reputation is computed against the OLD personalities).")
    lines.append("")
    lines.append("  TABLE A -- Trust-profit Pearson r per seed (vs bounded baseline)")
    lines.append("  " + "-" * 60)
    lines.append(f"  {'seed':>6}  {'P2 bounded':>12}  {'P2 unbounded':>14}  {'delta':>9}")
    for s in summary["per_seed"]:
        sd = s["seed"]
        bnd = bnd_dict.get(sd, float("nan"))
        unb = s["r"]
        delta = unb - bnd if not np.isnan(bnd) else float("nan")
        lines.append(
            f"  {sd:>6}  {bnd:>+12.3f}  {unb:>+14.3f}  "
            f"{delta:>+9.3f}"
        )
    lines.append("  " + "-" * 60)
    bnd_mean = float(np.nanmean(list(bnd_dict.values())))
    lines.append(
        f"  {'mean':>6}  {bnd_mean:>+12.3f}  {mean_r:>+14.3f}  "
        f"{mean_r - bnd_mean:>+9.3f}"
    )
    lines.append(f"  {'std':>6}  {np.nanstd(list(bnd_dict.values())):>12.3f}  "
                 f"{std_r:>14.3f}")
    lines.append("")

    lines.append("  TABLE B -- Per-archetype final-stack means (vs starting 200)")
    lines.append("  " + "-" * 60)
    lines.append(f"  {'archetype':<12}  {'stack':>10}  {'std':>8}  {'trust':>8}  {'rebuys':>8}")
    arch_means = summary["per_arch_means"]
    archs_sorted = sorted(ARCHETYPES, key=lambda a: -arch_means[a]["stack_mean"])
    for arch in archs_sorted:
        m = arch_means[arch]
        lines.append(
            f"  {arch:<12}  {m['stack_mean']:>10.1f}  "
            f"{m['stack_std']:>8.1f}  {m['trust_mean']:>8.3f}  "
            f"{m['rebuys_mean']:>8.1f}"
        )
    lines.append("")

    # Convergence interpretation
    stacks = [arch_means[a]["stack_mean"] for a in ARCHETYPES]
    spread = max(stacks) - min(stacks)
    lines.append("  TABLE C -- Convergence indicators")
    lines.append("  " + "-" * 60)
    lines.append(f"  Stack spread (max - min):    {spread:>8.1f} chips")
    lines.append(f"  Stack std across archetypes: {np.std(stacks):>8.1f} chips")
    lines.append(f"  Mean trust spread:           "
                 f"{max(arch_means[a]['trust_mean'] for a in ARCHETYPES) - min(arch_means[a]['trust_mean'] for a in ARCHETYPES):>8.3f}")
    lines.append("")
    lines.append("  Hypothesis: unbounded hill-climbing pushes all agents toward a")
    lines.append("  common equilibrium (Oracle-like). If true, stack spread should")
    lines.append("  shrink substantially relative to bounded Phase 2.")
    lines.append("")
    lines.append("  Bounded Phase 2 stack spread (reference): ~17500 chips at 10000h")
    lines.append("  (Firestorm's 5x dominance pattern preserved).")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF PHASE 2 UNBOUNDED SCORECARD")
    lines.append("=" * 80)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Writeup note
# ---------------------------------------------------------------------------

def write_phase2_unbounded_note(summary: Dict, path: Path) -> None:
    rs = [s["r"] for s in summary["per_seed"]]
    mean_r = float(np.mean(rs))
    std_r = float(np.std(rs))
    bnd_mean = float(np.mean(P2_BOUNDED_R))
    delta = mean_r - bnd_mean

    arch_means = summary["per_arch_means"]
    stacks = [arch_means[a]["stack_mean"] for a in ARCHETYPES]
    spread = max(stacks) - min(stacks)

    # Identify the winner and loser
    archs_sorted = sorted(ARCHETYPES, key=lambda a: -arch_means[a]["stack_mean"])
    top_arch = archs_sorted[0]
    bot_arch = archs_sorted[-1]
    top_stack = arch_means[top_arch]["stack_mean"]
    bot_stack = arch_means[bot_arch]["stack_mean"]

    # Behavioral question: did everyone converge to the same VPIP/PFR/AF?
    # Without a quick way to compute that here, just describe the stack spread.

    body = f"""# Phase 2 Unbounded — Writeup Notes

> Generated automatically from `runs_phase2_unbounded.sqlite` by
> `analysis/phase2_unbounded_compare.py`. This is draft prose for the
> paper's §5.5 (Phase 2 Results) — manually edit before pasting into
> `paper.md`.

## Motivation (mentor meeting, 2026-04-30)

Arpit asked a sharper version of the Phase 2 question: *what if the
agents had no personality bounds at all?* If hill-climbing had full
freedom of the [0, 1] probability space on every metric, would the
agents converge to a Nash-equilibrium-like equilibrium (the Oracle
profile), or would they exploit their freedom to become more extreme?

This sub-experiment is free — no API spend — and falsifies the
"bound boxes are the binding constraint" claim from §6.3 of the paper.

## Result

Across 5 seeds × {summary['per_seed'][0]['num_hands']} hands with
`ARCHETYPE_BOUNDS` replaced by `(0.0, 1.0)` everywhere:

| | Bounded P2 | Unbounded P2 | Δ |
|---|---|---|---|
| Mean r | {bnd_mean:+.3f} | {mean_r:+.3f} | {delta:+.3f} |
| Std r | 0.125 | {std_r:.3f} | |

The trust-profit anti-correlation {'softens further' if mean_r > bnd_mean else 'deepens' if mean_r < bnd_mean else 'is unchanged'}
relative to bounded Phase 2.

## Economic ordering

Top archetype: **{top_arch}** at {top_stack:.0f} chips.
Bottom archetype: **{bot_arch}** at {bot_stack:.0f} chips.
Spread: {spread:.0f} chips (bounded P2 reference: ~17,500).

If the spread has *shrunk substantially*, the agents have converged
toward a common equilibrium (which would be the strongest evidence
that the bound boxes were the binding constraint). If it has stayed
similar or grown, the agents have exploited their new freedom to
become *more* differentiated — which would mean the boxes were
actually preserving cooperative behavior.

## Headline interpretation (TODO — fill in based on the numbers above)

- If r softens significantly: bounds were preventing agents from
  cooperating. The trap is partly an artifact of personality
  enforcement.
- If r deepens significantly: bounds were preventing agents from
  exploiting each other harder. The trap is even worse without
  personalities.
- If r stays roughly the same: bound boxes are not the binding
  constraint. The structural argument from §6.3 stands.

## Caveats

The trust model still uses Phase 1's bounded likelihood tables. So
the trust *posterior* is computed against the OLD personality space
even though the *behavior* now lives in the full [0,1] space. This
is intentional — it isolates the effect of unbounding behavior from
the effect of unbounding the trust model — but it means the trust
scores in this run are not directly comparable to bounded Phase 2.

## Cross-reference

Figures generated:
- `paper_resources/figures/07_phase2_bounded_vs_unbounded.png`
- `paper_resources/figures/10_param_drift_unbounded.png`
- `paper_resources/figures/08_stack_trajectories_phase2_unbounded.png`
- `paper_resources/figures/09_trust_evolution_phase2_unbounded.png`

Scorecard: `reports/phase2_unbounded_scorecard.txt`.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# CSV summary
# ---------------------------------------------------------------------------

def write_csv_summary(summary: Dict, path: Path) -> None:
    import csv
    bnd_dict = {SEEDS[i]: P2_BOUNDED_R[i] for i in range(len(SEEDS))}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "P2_bounded_r", "P2_unbounded_r", "delta_r"])
        for s in summary["per_seed"]:
            sd = s["seed"]
            bnd = bnd_dict.get(sd, "")
            w.writerow([sd, f"{bnd:+.3f}" if bnd != "" else "",
                        f"{s['r']:+.3f}",
                        f"{s['r'] - bnd:+.3f}" if bnd != "" else ""])
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", default="runs_phase2_unbounded.sqlite",
        help="Phase 2 unbounded SQLite path.",
    )
    parser.add_argument(
        "--trajectories", default="phase2/adaptive/param_trajectories_unbounded.json",
        help="Trajectory JSON dumped by run_adaptive.py.",
    )
    parser.add_argument(
        "--outdir", default="paper_resources",
        help="Where to write the new figures + notes + CSV.",
    )
    args = parser.parse_args()
    _setup_style()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: {db_path} not found", file=sys.stderr)
        return 2
    if db_path.stat().st_size < 5000:
        print(f"ERROR: {db_path} looks like an LFS pointer "
              f"({db_path.stat().st_size} bytes)", file=sys.stderr)
        return 2

    out = _REPO_ROOT / args.outdir
    figdir = out / "figures"
    datadir = out / "data"
    notedir = out / "notes"

    print("Extracting summary from", db_path)
    summary = extract_unbounded_summary(db_path)
    print(f"  {len(summary['per_seed'])} seeds extracted")

    fig_bounded_vs_unbounded(summary, figdir)
    fig_param_drift(_REPO_ROOT / args.trajectories, figdir)
    write_csv_summary(summary, datadir / "phase2_unbounded_summary.csv")
    write_phase2_unbounded_note(summary,
                                notedir / "phase2_unbounded_writeup.md")
    write_scorecard(summary,
                    _REPO_ROOT / "reports" / "phase2_unbounded_scorecard.txt")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
