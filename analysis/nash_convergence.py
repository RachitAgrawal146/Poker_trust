"""Nash convergence analysis for the aggressive unbounded run.

Question: with strong economically-motivated hill-climbing, do the
eight different starting archetypes converge to a common Nash-like
parameter profile?

Methodology:
    Each agent's parameter state at hand H is a 36-vector (4 rounds
    × 9 metrics). Across 8 agents we have a "cloud" of 8 points in
    R^36 at every hand. Convergence is measured by:

      * cluster_spread(H) = mean pairwise L1 distance between the 8
                            agents at hand H. Approaches 0 if they
                            converge to a common point.

      * drift_from_self(H, agent) = L1 distance between the agent's
                            params at hand H and its starting params.
                            Grows as the agent migrates away from its
                            archetype.

      * convergence_index = final_spread / initial_spread.
                            < 1.0 means agents got closer to each other.
                            < 0.5 is meaningful convergence.
                            ~ 1.0 means no movement.

Outputs:
    paper_resources/figures/11_nash_convergence_spread.png
    paper_resources/figures/12_nash_convergence_drift.png
    paper_resources/data/nash_convergence_summary.csv
    paper_resources/notes/nash_convergence_writeup.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.make_paper_figures import ARCHETYPE_COLORS, _setup_style, _save  # noqa: E402

_ROUNDS = ("preflop", "flop", "turn", "river")
_METRICS = ("br", "vbr", "cr", "mbr",
            "strong_raise", "strong_call", "strong_fold",
            "med_raise", "weak_call")


def flatten_params(params: dict) -> np.ndarray:
    """Flatten {round: {metric: val}} -> 36-vector. Handles Judge's
    {pre_trigger:..., post_trigger:...} by taking pre_trigger."""
    if isinstance(params, dict) and "pre_trigger" in params:
        params = params["pre_trigger"]
    vals = []
    for r in _ROUNDS:
        for m in _METRICS:
            vals.append(float(params.get(r, {}).get(m, 0.0)))
    return np.array(vals)


def trajectory_arrays(seed_data: dict) -> tuple:
    """Return (hands array, archetype list, [N, T, 36] params array).

    hands[i] = hand number at checkpoint i
    archetypes[a] = string archetype name for slot a
    params[a, i, :] = 36-vector of agent a at checkpoint i
    """
    slots = sorted(seed_data.keys(), key=lambda k: int(k.split("_")[1]))
    archetypes = [s.split("_", 2)[2] for s in slots]
    # Use the first slot's hand checkpoints as the canonical timeline
    hands = [pt["hand"] for pt in seed_data[slots[0]]]
    n_agents = len(slots)
    n_checkpoints = len(hands)
    params = np.zeros((n_agents, n_checkpoints, 36))
    for a, slot in enumerate(slots):
        for i, pt in enumerate(seed_data[slot]):
            params[a, i, :] = flatten_params(pt["params"])
    return np.array(hands), archetypes, params


def cluster_spread(params: np.ndarray) -> np.ndarray:
    """Given [N_agents, T_checkpoints, 36] params array, return the
    mean pairwise L1 distance between agents at each timestep, shape [T].
    """
    n_agents, n_t, _ = params.shape
    out = np.zeros(n_t)
    for t in range(n_t):
        # Mean pairwise L1
        s = 0.0
        n_pairs = 0
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                s += float(np.abs(params[i, t] - params[j, t]).sum())
                n_pairs += 1
        out[t] = s / max(n_pairs, 1)
    return out


def drift_from_self(params: np.ndarray) -> np.ndarray:
    """For each agent, L1 distance of its params at time t from its
    params at time 0. Returns shape [N_agents, T_checkpoints].
    """
    return np.abs(params - params[:, :1, :]).sum(axis=2)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig_cluster_spread(traj: dict, outdir: Path, tag: str) -> dict:
    """Plot mean pairwise L1 between agents over hands, one line per
    seed. Returns a dict of per-seed convergence indices."""
    seeds = sorted(traj.keys(), key=lambda k: int(k.split("_")[1]))
    fig, ax = plt.subplots(figsize=(9, 5))
    convergence_index = {}
    for seed_key in seeds:
        seed = int(seed_key.split("_")[1])
        hands, _, params = trajectory_arrays(traj[seed_key])
        spread = cluster_spread(params)
        ax.plot(hands, spread, marker="o", markersize=3, linewidth=1.4,
                label=f"seed {seed}", alpha=0.85)
        convergence_index[seed] = float(spread[-1] / spread[0]) if spread[0] > 0 else 1.0

    ax.set_xlabel("Hand index")
    ax.set_ylabel("Mean pairwise L1 distance between 8 agents (36-dim params)")
    ax.set_title(f"Nash Convergence Test — Cluster Spread Over Time ({tag})",
                 fontsize=12)
    ax.legend(loc="best", fontsize=9)
    ax.set_ylim(bottom=0)

    # Annotate final convergence indices
    text_parts = ["Convergence index (final / initial):"]
    for seed, ci in sorted(convergence_index.items()):
        marker = "← converging" if ci < 0.5 else (
            "← partial" if ci < 0.85 else "← no convergence")
        text_parts.append(f"  seed {seed}: {ci:.3f}  {marker}")
    fig.text(0.99, -0.02, "\n".join(text_parts),
             ha="right", va="top", fontsize=8.5, color="#333",
             family="monospace")
    fig.tight_layout()
    _save(fig, outdir, f"11_nash_convergence_spread_{tag}.png")
    return convergence_index


def fig_drift_from_self(traj: dict, outdir: Path, tag: str) -> None:
    """Plot per-agent drift from initial params, one panel per seed.
    Each agent line colored by archetype."""
    seeds = sorted(traj.keys(), key=lambda k: int(k.split("_")[1]))
    n = len(seeds)
    cols = min(3, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5.5 * cols, 3.5 * rows),
                             sharey=True)
    axes = np.atleast_1d(axes).flatten()

    for ax, seed_key in zip(axes, seeds):
        seed = int(seed_key.split("_")[1])
        hands, archetypes, params = trajectory_arrays(traj[seed_key])
        drift = drift_from_self(params)
        for a, arch in enumerate(archetypes):
            color = ARCHETYPE_COLORS.get(arch, "#666")
            ax.plot(hands, drift[a], color=color, linewidth=1.4,
                    label=arch, alpha=0.9)
        ax.set_title(f"seed {seed}", fontsize=11)
        ax.set_xlabel("hand")
        ax.set_ylabel("L1 distance from starting params")
        ax.set_ylim(bottom=0)

    # Single legend in last available axis position
    if n < len(axes):
        axes[n].set_visible(False)
    axes[0].legend(loc="upper left", fontsize=8, ncol=2)

    fig.suptitle(f"How Far Each Agent Drifts From Its Starting Archetype ({tag})",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, outdir, f"12_nash_convergence_drift_{tag}.png")


def fig_pca_trajectories(traj: dict, outdir: Path, tag: str) -> None:
    """2D PCA of all agent params across all seeds × all checkpoints.
    Plot each agent's trajectory in this shared 2D space, with start
    marked X and end marked O. If they converge, the O markers cluster.
    """
    seeds = sorted(traj.keys(), key=lambda k: int(k.split("_")[1]))

    # Stack all parameter snapshots into one matrix [N_total, 36]
    all_points = []
    seed_archetype_traj = {}  # (seed, archetype) -> [T, 36]
    for seed_key in seeds:
        seed = int(seed_key.split("_")[1])
        hands, archetypes, params = trajectory_arrays(traj[seed_key])
        for a, arch in enumerate(archetypes):
            seed_archetype_traj[(seed, arch)] = params[a]
            all_points.append(params[a])
    big = np.vstack(all_points)  # [n_seeds * n_agents * T, 36]

    # PCA via SVD on centered data
    centered = big - big.mean(axis=0)
    u, s, vh = np.linalg.svd(centered, full_matrices=False)
    components = vh[:2]  # [2, 36]
    var_explained = (s[:2] ** 2 / (s ** 2).sum()) * 100

    def project(arr):
        return (arr - big.mean(axis=0)) @ components.T

    fig, axes = plt.subplots(1, len(seeds), figsize=(4.5 * len(seeds), 4.5),
                             sharex=True, sharey=True)
    if len(seeds) == 1:
        axes = [axes]

    for ax, seed_key in zip(axes, seeds):
        seed = int(seed_key.split("_")[1])
        _, archetypes, _ = trajectory_arrays(traj[seed_key])
        for arch in archetypes:
            traj_pts = seed_archetype_traj[(seed, arch)]
            proj = project(traj_pts)
            color = ARCHETYPE_COLORS.get(arch, "#666")
            ax.plot(proj[:, 0], proj[:, 1], color=color, linewidth=1.0,
                    alpha=0.6)
            # Start marker (X), end marker (O)
            ax.plot(proj[0, 0], proj[0, 1], marker="x", color=color,
                    markersize=11, markeredgewidth=2.0)
            ax.plot(proj[-1, 0], proj[-1, 1], marker="o", color=color,
                    markersize=10, markeredgecolor="black",
                    markeredgewidth=0.8, label=arch)
        ax.set_title(f"seed {seed}", fontsize=11)
        ax.set_xlabel(f"PC1 ({var_explained[0]:.1f}%)")
        ax.set_ylabel(f"PC2 ({var_explained[1]:.1f}%)")
        ax.axhline(0, color="grey", linewidth=0.4, linestyle=":")
        ax.axvline(0, color="grey", linewidth=0.4, linestyle=":")

    if seeds:
        axes[-1].legend(bbox_to_anchor=(1.02, 1), loc="upper left",
                        fontsize=8)
    fig.suptitle(
        f"2D PCA — Agent Trajectories in Parameter Space ({tag})",
        fontsize=12, fontweight="bold",
    )
    fig.text(0.5, -0.02,
             "× = starting position    ● = final position    "
             "Tight cluster of ●'s = Nash convergence.",
             ha="center", fontsize=9, color="#555", style="italic")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    _save(fig, outdir, f"13_nash_convergence_pca_{tag}.png")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trajectories", required=True,
        help="JSON path written by run_adaptive.py.",
    )
    parser.add_argument(
        "--tag", default="aggressive",
        help="Suffix for output filenames (default: aggressive).",
    )
    parser.add_argument(
        "--outdir", default="paper_resources",
        help="Where to write figures, data, notes.",
    )
    args = parser.parse_args()
    _setup_style()

    traj_path = Path(args.trajectories)
    if not traj_path.exists():
        print(f"ERROR: {traj_path} not found", file=sys.stderr)
        return 2

    traj = json.load(open(traj_path))
    out = _REPO_ROOT / args.outdir
    figdir = out / "figures"
    datadir = out / "data"
    notedir = out / "notes"

    print(f"Analyzing: {traj_path}")
    convergence_index = fig_cluster_spread(traj, figdir, args.tag)
    fig_drift_from_self(traj, figdir, args.tag)
    fig_pca_trajectories(traj, figdir, args.tag)

    # Compute per-seed initial / final spread
    summary = []
    for seed_key in sorted(traj.keys(), key=lambda k: int(k.split("_")[1])):
        seed = int(seed_key.split("_")[1])
        hands, _, params = trajectory_arrays(traj[seed_key])
        spread = cluster_spread(params)
        drift = drift_from_self(params)
        summary.append({
            "seed": seed,
            "initial_spread": float(spread[0]),
            "final_spread": float(spread[-1]),
            "convergence_index": float(spread[-1] / spread[0]) if spread[0] > 0 else 1.0,
            "max_drift": float(drift[:, -1].max()),
            "mean_drift": float(drift[:, -1].mean()),
        })

    # CSV
    csv_path = datadir / f"nash_convergence_{args.tag}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "initial_spread", "final_spread",
                    "convergence_index", "max_drift", "mean_drift"])
        for s in summary:
            w.writerow([s["seed"], f"{s['initial_spread']:.3f}",
                        f"{s['final_spread']:.3f}",
                        f"{s['convergence_index']:.3f}",
                        f"{s['max_drift']:.3f}",
                        f"{s['mean_drift']:.3f}"])
    print(f"  wrote {csv_path}")

    # Markdown writeup
    mean_ci = float(np.mean([s["convergence_index"] for s in summary]))
    if mean_ci < 0.5:
        verdict = "**STRONG CONVERGENCE** — agents collapsed toward a common region."
    elif mean_ci < 0.85:
        verdict = "**PARTIAL CONVERGENCE** — agents got closer but did not fully merge."
    else:
        verdict = "**NO CONVERGENCE** — agents preserved their archetype diversity."

    md_lines = [
        f"# Nash Convergence Test ({args.tag})",
        "",
        f"> Aggressive unbounded hill-climbing: 5 seeds × 10,000 hands.",
        f"> Each agent independently maximizes its own profit.",
        f"> Cluster spread = mean pairwise L1 between 8 agents in 36-dim params.",
        "",
        "## Headline",
        "",
        f"Mean convergence index across 5 seeds: **{mean_ci:.3f}**.",
        f"{verdict}",
        "",
        "## Per-seed results",
        "",
        "| seed | initial spread | final spread | convergence index | mean drift | max drift |",
        "|---|---|---|---|---|---|",
    ]
    for s in summary:
        md_lines.append(
            f"| {s['seed']} | {s['initial_spread']:.3f} | "
            f"{s['final_spread']:.3f} | {s['convergence_index']:.3f} | "
            f"{s['mean_drift']:.3f} | {s['max_drift']:.3f} |"
        )
    md_lines += [
        "",
        "## Interpretation guide",
        "",
        "- **Convergence index ≈ 1.0** — agents barely moved relative to each other.",
        "- **Convergence index < 0.5** — agents merged into a tight cluster (Nash basin).",
        "- **Convergence index < 0.1** — virtually identical strategies.",
        "",
        "- **Drift > 5.0** — agent meaningfully migrated from its starting archetype.",
        "- **Drift < 1.0** — agent stayed near its starting profile.",
        "",
        "## Figures",
        "",
        f"- `paper_resources/figures/11_nash_convergence_spread_{args.tag}.png`",
        f"- `paper_resources/figures/12_nash_convergence_drift_{args.tag}.png`",
        "",
    ]
    md_path = notedir / f"nash_convergence_{args.tag}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"  wrote {md_path}")
    print()
    print(f"Mean convergence index: {mean_ci:.3f}")
    print(verdict.replace("*", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
