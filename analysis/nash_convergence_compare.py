"""Build a single side-by-side comparison figure of cluster-spread
trajectories under weak HC (baseline) vs aggressive HC.

Outputs:
    paper_resources/figures/14_nash_convergence_compare.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.make_paper_figures import _setup_style, _save  # noqa: E402
from analysis.nash_convergence import (  # noqa: E402
    trajectory_arrays, cluster_spread,
)


def main() -> int:
    _setup_style()
    base = json.load(open(_REPO_ROOT / "phase2/adaptive/param_trajectories_unbounded.json"))
    agg = json.load(open(_REPO_ROOT / "phase2/adaptive/param_trajectories_unbounded_aggressive.json"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)

    for ax, traj, title, accent in [
        (ax1, base, "Weak HC (delta=0.03, eval=200, ~25 cycles)", "#C0392B"),
        (ax2, agg, "Aggressive HC (delta=0.15, eval=50, ~100 cycles)", "#600000"),
    ]:
        seeds = sorted(traj.keys(), key=lambda k: int(k.split("_")[1]))
        cis = []
        for seed_key in seeds:
            seed = int(seed_key.split("_")[1])
            hands, _, params = trajectory_arrays(traj[seed_key])
            spread = cluster_spread(params)
            cis.append(float(spread[-1] / spread[0]) if spread[0] > 0 else 1.0)
            ax.plot(hands, spread, marker="o", markersize=3, linewidth=1.4,
                    label=f"seed {seed}", alpha=0.85)
        mean_ci = float(np.mean(cis))
        ax.axhline(spread[0], color="grey", linewidth=0.5, linestyle=":")
        ax.set_xlabel("Hand index")
        ax.set_title(f"{title}\nMean convergence index = {mean_ci:.3f}",
                     fontsize=11, color=accent)
        ax.set_ylim(0, 10)
        ax.legend(loc="lower right" if mean_ci > 1 else "upper right",
                  fontsize=8)

    ax1.set_ylabel("Mean pairwise L1 between 8 agents (36-dim)")

    fig.suptitle("Nash Convergence Test — Stronger HC Causes DIVERGENCE",
                 fontsize=12, fontweight="bold")
    fig.text(0.5, -0.02,
             "Convergence index = final spread / initial spread. < 1 = convergence; > 1 = divergence. "
             "BOTH runs preserve archetype diversity; the aggressive run actually drives agents APART.",
             ha="center", fontsize=9, color="#444", style="italic")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    _save(fig, _REPO_ROOT / "paper_resources/figures",
          "14_nash_convergence_compare.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
