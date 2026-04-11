"""Stage 10 — multi-seed orchestration CLI.

Runs the canonical Stage-5 agent roster (Oracle / Sentinel / Firestorm /
Wall / Phantom + three Oracle fillers) across several RNG seeds and writes
ML-ready CSVs plus cross-seed aggregate tables. This is the research entry
point downstream notebooks consume — it deliberately stays tiny and
stateless so it can also be driven in-process from a test.

Usage
-----

::

    python3 run_multiseed.py --seeds 42,137,256,512,1024 --hands 1000 \\
        --outdir runs/

Output layout::

    runs/
    ├── seed_42/
    │   ├── actions.csv
    │   ├── hands.csv
    │   └── agent_stats.csv
    ├── seed_137/
    │   └── ...
    ├── seed_aggregate.csv        # one row per (archetype, seed)
    └── seed_aggregate_mean.csv   # one row per archetype (mean ± std)

``seed_aggregate.csv`` is the long-format table; ``seed_aggregate_mean.csv``
collapses it to one row per archetype with mean and sample standard
deviation across the seeds. Both are stdlib-csv only — no pandas.

Reproducibility note
--------------------
Every seed gets a FRESH roster (new ``Oracle(seat=0)`` etc.) so seed N's
run is independent of seed M. Because the engine is fully seed-driven,
re-running with the same ``--seeds`` should produce byte-identical CSVs —
the Stage 10 extras assert this directly.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from typing import Dict, List, Tuple

from data.csv_exporter import (
    write_actions_csv,
    write_hands_csv,
    write_agent_stats_csv,
)


# =============================================================================
# Agent roster — Stage 5 canonical (matches run_demo._stage5_agents).
# =============================================================================
def build_agents():
    """Return a fresh 8-seat Stage 5 roster. Must be called once per seed."""
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom

    return [
        Oracle(seat=0),
        Sentinel(seat=1),
        Firestorm(seat=2),
        Wall(seat=3),
        Phantom(seat=4),
        Oracle(seat=5, name="Oracle-5"),
        Oracle(seat=6, name="Oracle-6"),
        Oracle(seat=7, name="Oracle-7"),
    ]


# =============================================================================
# Core: run one seed and collect CSVs + in-memory agents/hands.
# =============================================================================
def run_one_seed(seed: int, num_hands: int, outdir: str) -> Tuple[list, list]:
    """Play ``num_hands`` hands with a fresh roster at ``seed`` and write
    the three per-seed CSVs under ``outdir/seed_{seed}/``. Returns
    ``(agents, hands)`` so callers can aggregate further."""
    from engine.table import Table

    agents = build_agents()
    table = Table(agents, seed=seed)
    hands: list = []
    for _ in range(num_hands):
        table.play_hand()
        assert table.last_hand is not None
        hands.append(table.last_hand)

    run_id = f"seed_{seed}"
    seed_dir = os.path.join(outdir, run_id)
    os.makedirs(seed_dir, exist_ok=True)
    write_actions_csv(hands, agents, os.path.join(seed_dir, "actions.csv"), run_id)
    write_hands_csv(hands, agents, os.path.join(seed_dir, "hands.csv"), run_id)
    write_agent_stats_csv(agents, run_id, os.path.join(seed_dir, "agent_stats.csv"))
    return agents, hands


# =============================================================================
# Cross-seed aggregation.
# =============================================================================
_AGG_HEADER = ["archetype", "seat", "seed", "vpip_pct", "pfr_pct", "af",
               "hands_dealt", "final_stack", "rebuys"]

_AGG_MEAN_HEADER = [
    "archetype",
    "num_seeds",
    "vpip_pct_mean", "vpip_pct_std",
    "pfr_pct_mean",  "pfr_pct_std",
    "af_mean",       "af_std",
    "final_stack_mean", "final_stack_std",
]


def _stddev(vals: List[float]) -> float:
    """Sample standard deviation. Returns 0 for singletons."""
    n = len(vals)
    if n < 2:
        return 0.0
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    return math.sqrt(var)


def write_seed_aggregates(
    per_seed_agents: Dict[int, list],
    outdir: str,
) -> Tuple[str, str]:
    """Write ``seed_aggregate.csv`` (long) + ``seed_aggregate_mean.csv``
    (archetype means). Returns the two paths."""
    long_path = os.path.join(outdir, "seed_aggregate.csv")
    mean_path = os.path.join(outdir, "seed_aggregate_mean.csv")

    os.makedirs(outdir, exist_ok=True)

    # --- long-format: one row per (seed, seat/archetype) ---
    # We iterate seeds in the caller's insertion order so tests can rely on
    # deterministic row order.
    arch_rows: Dict[str, List[Dict[str, float]]] = {}
    with open(long_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_AGG_HEADER)
        for seed, agents in per_seed_agents.items():
            for a in sorted(agents, key=lambda x: x.seat):
                v = a.vpip() * 100.0
                p = a.pfr() * 100.0
                af = a.af()
                writer.writerow([
                    a.archetype, a.seat, seed,
                    f"{v:.4f}", f"{p:.4f}", f"{af:.4f}",
                    a.stats.get("hands_dealt", 0),
                    a.stack,
                    getattr(a, "rebuys", 0),
                ])
                arch_rows.setdefault(a.archetype, []).append({
                    "vpip": v, "pfr": p, "af": af,
                    "stack": float(a.stack),
                })

    # --- mean-format: one row per archetype ---
    with open(mean_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_AGG_MEAN_HEADER)
        for arch in sorted(arch_rows):
            rows = arch_rows[arch]
            vpips = [r["vpip"] for r in rows]
            pfrs = [r["pfr"] for r in rows]
            afs = [r["af"] for r in rows]
            stacks = [r["stack"] for r in rows]
            writer.writerow([
                arch,
                len(rows),
                f"{sum(vpips)/len(vpips):.4f}", f"{_stddev(vpips):.4f}",
                f"{sum(pfrs)/len(pfrs):.4f}",   f"{_stddev(pfrs):.4f}",
                f"{sum(afs)/len(afs):.4f}",     f"{_stddev(afs):.4f}",
                f"{sum(stacks)/len(stacks):.4f}", f"{_stddev(stacks):.4f}",
            ])

    return long_path, mean_path


# =============================================================================
# High-level orchestration + CLI
# =============================================================================
def run(seeds: List[int], num_hands: int, outdir: str) -> Dict[int, list]:
    """Run every seed, write per-seed CSVs + aggregates. Returns the per-seed
    agent dict so in-process callers (tests) can inspect final state."""
    os.makedirs(outdir, exist_ok=True)
    per_seed_agents: Dict[int, list] = {}
    per_seed_summary: List[str] = []

    for seed in seeds:
        agents, _hands = run_one_seed(seed, num_hands, outdir)
        per_seed_agents[seed] = agents
        # Canonical 5 archetypes (seats 0-4) drive the summary line.
        arch5 = agents[:5]
        vp = sum(a.vpip() for a in arch5) / 5 * 100
        pf = sum(a.pfr() for a in arch5) / 5 * 100
        per_seed_summary.append(
            f"  seed={seed:<6d} arch5-mean VPIP={vp:5.1f}%  PFR={pf:5.1f}%  "
            f"total_chips={sum(a.stack for a in agents):5d}"
        )

    write_seed_aggregates(per_seed_agents, outdir)

    # Aggregate-over-seeds summary for console.
    arch_vpips: Dict[str, List[float]] = {}
    arch_pfrs: Dict[str, List[float]] = {}
    for agents in per_seed_agents.values():
        for a in agents:
            arch_vpips.setdefault(a.archetype, []).append(a.vpip() * 100)
            arch_pfrs.setdefault(a.archetype, []).append(a.pfr() * 100)

    print(f"Multi-seed run complete: {len(seeds)} seeds × {num_hands} hands → {outdir}")
    print("Per-seed (seats 0-4 mean):")
    for line in per_seed_summary:
        print(line)
    print("Cross-seed archetype aggregates:")
    for arch in sorted(arch_vpips):
        v = arch_vpips[arch]
        p = arch_pfrs[arch]
        vmean = sum(v) / len(v)
        pmean = sum(p) / len(p)
        print(
            f"  {arch:<20} VPIP={vmean:5.1f}% ±{_stddev(v):4.1f}  "
            f"PFR={pmean:5.1f}% ±{_stddev(p):4.1f}"
        )

    return per_seed_agents


def _parse_seeds(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 10 multi-seed orchestration — writes CSVs for every seed."
    )
    parser.add_argument(
        "--seeds", default="42,137,256,512,1024",
        help="Comma-separated RNG seeds (default: 42,137,256,512,1024)",
    )
    parser.add_argument(
        "--hands", type=int, default=1000,
        help="Number of hands per seed (default: 1000)",
    )
    parser.add_argument(
        "--outdir", default="runs/",
        help="Output root directory (default: runs/)",
    )
    args = parser.parse_args(argv)

    seeds = _parse_seeds(args.seeds)
    if not seeds:
        parser.error("--seeds must contain at least one integer")

    run(seeds, args.hands, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
