"""Generate per-hand trajectory figures from a Phase-2-style SQLite.

Outputs go to ``paper_resources/figures/``. Two figures emerge:

    08_stack_trajectories.png   Per-archetype stack over hand index, one
                                panel per seed plus a "mean" panel
    09_trust_evolution.png      Per-archetype mean trust score over hand
                                index (averaged across observers)

Usage::

    python3 analysis/make_trajectory_figures.py --db runs_phase2_unbounded.sqlite

The script auto-detects which seeds are present in the database and
generates one panel per seed plus a population-mean panel.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.make_paper_figures import (  # noqa: E402
    ARCHETYPES, ARCHETYPE_COLORS, _setup_style, _save,
)

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_per_hand_stacks(conn: sqlite3.Connection, run_id: int,
                         num_hands: int) -> dict:
    """Return {archetype: np.ndarray of len num_hands+1} of stack values
    sampled at the END of each hand.

    Stack at end of hand H = stack_after of the last action by that
    seat in hand H, or the previous value if the seat folded earlier.
    Easiest robust derivation: pick the maximum hand_id_for_seat in
    hand H and grab its stack_after.
    """
    out = {}
    seat_arch = {}
    for r in conn.execute("""
        SELECT seat, archetype FROM agent_stats WHERE run_id=?
    """, (run_id,)):
        seat_arch[r[0]] = r[1]

    starting = 200  # SIMULATION["starting_stack"]

    for seat, arch in seat_arch.items():
        # Per-hand: stack_after of the last action this seat took, OR
        # the rolling carry if no action.
        stacks = np.full(num_hands + 1, float(starting))
        rows = conn.execute("""
            SELECT hand_id, MAX(sequence_num), stack_after
            FROM actions
            WHERE run_id=? AND seat=?
            GROUP BY hand_id
            ORDER BY hand_id
        """, (run_id, seat)).fetchall()
        cur = float(starting)
        last_h = 0
        for hand_id, _, stack_after in rows:
            for i in range(last_h + 1, hand_id + 1):
                stacks[i] = cur
            stacks[hand_id] = float(stack_after)
            cur = float(stack_after)
            last_h = hand_id
        for i in range(last_h + 1, num_hands + 1):
            stacks[i] = cur
        out[arch] = stacks
    return out


def load_per_hand_trust(conn: sqlite3.Connection, run_id: int) -> dict:
    """Return {archetype: (hand_ids array, mean_trust array)}.

    Mean trust = average of trust posterior over all OBSERVERS who
    rated this archetype on a given hand_id.
    """
    out = {}
    seat_arch = {}
    for r in conn.execute("""
        SELECT seat, archetype FROM agent_stats WHERE run_id=?
    """, (run_id,)):
        seat_arch[r[0]] = r[1]

    for seat, arch in seat_arch.items():
        rows = conn.execute("""
            SELECT hand_id, AVG(trust)
            FROM trust_snapshots
            WHERE run_id=? AND target_seat=?
            GROUP BY hand_id
            ORDER BY hand_id
        """, (run_id, seat)).fetchall()
        if not rows:
            continue
        hids = np.array([r[0] for r in rows])
        ts = np.array([r[1] for r in rows], dtype=float)
        out[arch] = (hids, ts)
    return out


# ---------------------------------------------------------------------------
# Figure 8: Stack trajectories
# ---------------------------------------------------------------------------

def fig_stack_trajectories(conn: sqlite3.Connection, outdir: Path,
                           tag: str) -> None:
    runs = conn.execute(
        "SELECT run_id, seed, num_hands FROM runs ORDER BY seed"
    ).fetchall()
    n = len(runs)
    if n == 0:
        print("  no runs found in DB")
        return

    cols = min(3, n)
    rows = int(np.ceil((n + 1) / cols))  # +1 for the mean panel

    fig, axes = plt.subplots(rows, cols, figsize=(5.0 * cols, 3.4 * rows),
                             sharey=True)
    axes = np.atleast_1d(axes).flatten()

    all_seed_stacks = {a: [] for a in ARCHETYPES}

    for ax, (run_id, seed, num_hands) in zip(axes, runs):
        per_arch = load_per_hand_stacks(conn, run_id, num_hands)
        x = np.arange(num_hands + 1)
        for arch in ARCHETYPES:
            if arch not in per_arch:
                continue
            ax.plot(x, per_arch[arch], color=ARCHETYPE_COLORS[arch],
                    linewidth=1.2, label=arch, alpha=0.9)
            # Pad to common length by repeating last value
            pad = np.full(max(0, max((r[2] for r in runs)) - num_hands),
                          per_arch[arch][-1])
            all_seed_stacks[arch].append(np.concatenate([per_arch[arch], pad]))
        ax.set_title(f"seed {seed}", fontsize=11)
        ax.set_xlabel("hand")
        ax.axhline(0, color="black", linewidth=0.5, linestyle=":")
        ax.set_ylim(-50, max(800, ax.get_ylim()[1]))

    # Mean panel — only meaningful when we have >= 2 seeds
    if len(axes) > n and n >= 2 and any(all_seed_stacks.values()):
        ax = axes[n]
        for arch in ARCHETYPES:
            if not all_seed_stacks[arch]:
                continue
            min_len = min(len(s) for s in all_seed_stacks[arch])
            arr = np.array([s[:min_len] for s in all_seed_stacks[arch]])
            mean = arr.mean(axis=0)
            ax.plot(np.arange(min_len), mean, color=ARCHETYPE_COLORS[arch],
                    linewidth=1.6, label=arch, alpha=0.9)
        ax.set_title("mean across seeds", fontsize=11, fontweight="bold")
        ax.set_xlabel("hand")
        ax.axhline(0, color="black", linewidth=0.5, linestyle=":")
        ax.legend(loc="upper left", fontsize=8, ncol=2)
    elif len(axes) > n:
        # Hide the unused mean panel when there's only one seed
        axes[n].set_visible(False)

    # Hide any extra axes
    for j in range(n + 1, len(axes)):
        axes[j].set_visible(False)

    axes[0].set_ylabel("stack (chips)")
    fig.suptitle(f"Stack Trajectories — {tag}", fontsize=13,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, outdir, f"08_stack_trajectories_{tag}.png")


# ---------------------------------------------------------------------------
# Figure 9: Trust evolution
# ---------------------------------------------------------------------------

def fig_trust_evolution(conn: sqlite3.Connection, outdir: Path,
                        tag: str) -> None:
    runs = conn.execute(
        "SELECT run_id, seed, num_hands FROM runs ORDER BY seed"
    ).fetchall()
    n = len(runs)
    if n == 0:
        return

    cols = min(3, n)
    rows = int(np.ceil(n / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(5.0 * cols, 3.4 * rows),
                             sharey=True)
    axes = np.atleast_1d(axes).flatten()

    for ax, (run_id, seed, num_hands) in zip(axes, runs):
        per_arch = load_per_hand_trust(conn, run_id)
        for arch in ARCHETYPES:
            if arch not in per_arch:
                continue
            hids, ts = per_arch[arch]
            ax.plot(hids, ts, color=ARCHETYPE_COLORS[arch],
                    linewidth=1.0, label=arch, alpha=0.85)
        ax.set_title(f"seed {seed}", fontsize=11)
        ax.set_xlabel("hand")
        ax.axhline(0.5, color="grey", linewidth=0.4, linestyle=":")
        ax.set_ylim(-0.05, 1.05)

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    axes[0].set_ylabel("mean trust score (across observers)")
    if n > 0:
        axes[min(n - 1, len(axes) - 1)].legend(
            loc="lower right", fontsize=8, ncol=2)
    fig.suptitle(f"Trust Score Evolution — {tag}", fontsize=13,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, outdir, f"09_trust_evolution_{tag}.png")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", required=True,
        help="Path to SQLite database with the standard Phase 1/2 schema.",
    )
    parser.add_argument(
        "--tag", default=None,
        help="Filename suffix to distinguish runs "
             "(default: derived from --db).",
    )
    parser.add_argument(
        "--outdir", default="paper_resources/figures",
        help="Where to write PNGs.",
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

    tag = args.tag or db_path.stem.replace("runs_", "").replace(".sqlite", "")
    outdir = _REPO_ROOT / args.outdir

    conn = sqlite3.connect(str(db_path))
    fig_stack_trajectories(conn, outdir, tag)
    fig_trust_evolution(conn, outdir, tag)
    conn.close()
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
