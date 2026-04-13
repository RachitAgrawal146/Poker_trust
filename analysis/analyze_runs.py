#!/usr/bin/env python3
"""Research analysis report for Poker Trust Simulation runs.

Reads a ``runs.sqlite`` database produced by ``run_sim.py`` and prints a
structured research report covering the key Phase 1 questions:

  1. Cross-seed archetype performance (stack, rebuys, showdown win rate)
  2. Behavioral profile (VPIP / PFR / AF) per archetype
  3. Trust convergence: who trusts whom at the final hand
  4. Archetype identification accuracy (Predator's posterior)
  5. Judge retaliation detection: when and against whom
  6. Pot size analysis: which archetypes drive action
  7. Sanity checks: chip conservation + orphan actions

Usage:

    python3 analyze_runs.py --db runs.sqlite
    python3 analyze_runs.py --db runs.sqlite --section trust
    python3 analyze_runs.py --db runs.sqlite --csv results/

Run ``python3 analyze_runs.py --help`` for all options.
"""

from __future__ import annotations

import argparse
import csv as csv_mod
import math
import os
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found.", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def _fetchall(db, sql, params=()):
    return db.execute(sql, params).fetchall()


def _fetchone(db, sql, params=()):
    return db.execute(sql, params).fetchone()


def _stddev(vals):
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))


# ---------------------------------------------------------------------------
# Section 1: Overview
# ---------------------------------------------------------------------------

def section_overview(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 1: DATABASE OVERVIEW")
    lines.append("=" * 72)

    runs = _fetchall(db, "SELECT * FROM runs ORDER BY run_id")
    lines.append(f"  Runs:           {len(runs)}")
    total_hands = _fetchone(db, "SELECT COUNT(*) AS c FROM hands")["c"]
    total_actions = _fetchone(db, "SELECT COUNT(*) AS c FROM actions")["c"]
    total_showdowns = _fetchone(db, "SELECT COUNT(*) AS c FROM showdowns")["c"]
    total_trust = _fetchone(db, "SELECT COUNT(*) AS c FROM trust_snapshots")["c"]
    lines.append(f"  Hands:          {total_hands:,}")
    lines.append(f"  Actions:        {total_actions:,}")
    lines.append(f"  Showdown rows:  {total_showdowns:,}")
    lines.append(f"  Trust snapshots:{total_trust:,}")
    lines.append(f"  Seeds:          {', '.join(str(r['seed']) for r in runs)}")
    if runs:
        lines.append(f"  Hands/seed:     {runs[0]['num_hands']}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 2: Archetype performance
# ---------------------------------------------------------------------------

def section_performance(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 2: ARCHETYPE PERFORMANCE (cross-seed)")
    lines.append("=" * 72)

    rows = _fetchall(db, """
        SELECT
            archetype,
            AVG(final_stack) AS mean_stack,
            AVG(rebuys) AS mean_rebuys,
            AVG(showdowns_won * 1.0 / CASE WHEN showdowns > 0 THEN showdowns ELSE 1 END) AS mean_sd_winrate,
            COUNT(*) AS n_seeds
        FROM agent_stats
        GROUP BY archetype
        ORDER BY mean_stack DESC
    """)

    lines.append(f"  {'Archetype':<20} {'Stack':>8} {'Rebuys':>8} {'SD Win%':>8} {'Seeds':>6}")
    lines.append(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")
    for r in rows:
        lines.append(
            f"  {r['archetype']:<20} {r['mean_stack']:>8.0f} "
            f"{r['mean_rebuys']:>8.1f} {r['mean_sd_winrate']*100:>7.1f}% "
            f"{r['n_seeds']:>6}"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 3: Behavioral profile
# ---------------------------------------------------------------------------

def section_behavior(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 3: BEHAVIORAL PROFILE (VPIP / PFR / AF)")
    lines.append("=" * 72)

    rows = _fetchall(db, """
        SELECT
            archetype,
            AVG(vpip_count * 100.0 / hands_dealt) AS vpip,
            AVG(pfr_count * 100.0 / hands_dealt) AS pfr,
            AVG((bets + raises) * 1.0 / CASE WHEN calls > 0 THEN calls ELSE 1 END) AS af,
            AVG(showdowns * 100.0 / hands_dealt) AS sd_pct
        FROM agent_stats
        GROUP BY archetype
        ORDER BY vpip DESC
    """)

    lines.append(f"  {'Archetype':<20} {'VPIP%':>7} {'PFR%':>7} {'AF':>6} {'SD%':>6}")
    lines.append(f"  {'-'*20} {'-'*7} {'-'*7} {'-'*6} {'-'*6}")
    for r in rows:
        lines.append(
            f"  {r['archetype']:<20} {r['vpip']:>6.1f}% {r['pfr']:>6.1f}% "
            f"{r['af']:>6.2f} {r['sd_pct']:>5.1f}%"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 4: Trust at final hand
# ---------------------------------------------------------------------------

def section_trust(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 4: MEAN TRUST TOWARD EACH ARCHETYPE (final hand)")
    lines.append("=" * 72)

    rows = _fetchall(db, """
        WITH final_hand AS (
            SELECT run_id, MAX(hand_id) AS last_hand
            FROM trust_snapshots GROUP BY run_id
        )
        SELECT
            ag.archetype AS target,
            ROUND(AVG(t.trust), 4) AS mean_trust,
            ROUND(AVG(t.entropy), 4) AS mean_entropy,
            COUNT(*) AS n
        FROM trust_snapshots t
        JOIN final_hand fh ON t.run_id = fh.run_id AND t.hand_id = fh.last_hand
        JOIN agent_stats ag ON t.run_id = ag.run_id AND t.target_seat = ag.seat
        GROUP BY ag.archetype
        ORDER BY mean_trust DESC
    """)

    lines.append(f"  {'Target':<20} {'Trust':>8} {'Entropy':>9} {'Samples':>9}")
    lines.append(f"  {'-'*20} {'-'*8} {'-'*9} {'-'*9}")
    for r in rows:
        lines.append(
            f"  {r['target']:<20} {r['mean_trust']:>8.4f} "
            f"{r['mean_entropy']:>9.4f} {r['n']:>9}"
        )
    lines.append("")

    # Hypothesis check
    if len(rows) >= 2:
        trust_map = {r['target']: r['mean_trust'] for r in rows}
        wall_t = trust_map.get('wall', 0)
        fire_t = trust_map.get('firestorm', 0)
        if wall_t > fire_t:
            lines.append(f"  CONFIRMED: Wall ({wall_t:.3f}) > Firestorm ({fire_t:.3f})")
        else:
            lines.append(f"  UNEXPECTED: Wall ({wall_t:.3f}) <= Firestorm ({fire_t:.3f})")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 5: Predator classification accuracy
# ---------------------------------------------------------------------------

def section_predator(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 5: PREDATOR CLASSIFICATION (posterior at milestones)")
    lines.append("=" * 72)

    # Get all run_ids
    run_ids = [r['run_id'] for r in _fetchall(db, "SELECT run_id FROM runs ORDER BY run_id")]
    milestones = [100, 500, 1000, 2500, 5000, 10000]

    # Check max hand_id to filter valid milestones
    max_hand = _fetchone(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots")["m"] or 0
    milestones = [m for m in milestones if m <= max_hand]

    if not milestones or not run_ids:
        lines.append("  (not enough data for milestone analysis)")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"  Predator (seat 5) posterior about each target, averaged across {len(run_ids)} seeds:")
    lines.append(f"  Milestones: {milestones}")
    lines.append("")

    # Get archetype names for each seat from agent_stats (first run)
    seat_arch = {}
    for r in _fetchall(db, "SELECT seat, archetype FROM agent_stats WHERE run_id = ?", (run_ids[0],)):
        seat_arch[r['seat']] = r['archetype']

    for target_seat in range(8):
        if target_seat == 5:
            continue
        arch = seat_arch.get(target_seat, '?')
        line_parts = [f"  S{target_seat} ({arch:<12})"]
        for m in milestones:
            row = _fetchone(db, """
                SELECT
                    AVG(top_prob) AS avg_prob,
                    GROUP_CONCAT(DISTINCT top_archetype) AS archs
                FROM trust_snapshots
                WHERE observer_seat = 5 AND target_seat = ? AND hand_id = ?
            """, (target_seat, m))
            if row and row['avg_prob'] is not None:
                line_parts.append(f"h{m}: {row['avg_prob']:.2f}")
            else:
                line_parts.append(f"h{m}: ---")
        lines.append("  ".join(line_parts))

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 6: Judge retaliation
# ---------------------------------------------------------------------------

def section_judge(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 6: JUDGE BEHAVIOR SHIFT (rolling preflop bet rate)")
    lines.append("=" * 72)

    # Judge is seat 7. Look for a regime change in preflop bet/raise rate.
    run_ids = [r['run_id'] for r in _fetchall(db, "SELECT run_id FROM runs ORDER BY run_id")]

    for rid in run_ids[:5]:  # Limit to first 5 seeds for brevity
        rows = _fetchall(db, """
            SELECT
                hand_id,
                SUM(CASE WHEN action_type IN ('bet','raise') THEN 1 ELSE 0 END) AS br,
                COUNT(*) AS total
            FROM actions
            WHERE run_id = ? AND seat = 7 AND betting_round = 'preflop'
            GROUP BY hand_id
            ORDER BY hand_id
        """, (rid,))

        if not rows:
            continue

        # Compute rolling 100-hand bet rate
        window = []
        shift_hand = None
        for r in rows:
            window.append((r['br'], r['total']))
            if len(window) > 100:
                window.pop(0)
            if len(window) >= 50:
                br_sum = sum(x[0] for x in window)
                total_sum = sum(x[1] for x in window)
                rate = br_sum / total_sum if total_sum > 0 else 0
                # Detect shift: cooperative br ~0.10, retaliatory br ~0.70
                if rate > 0.30 and shift_hand is None:
                    shift_hand = r['hand_id']

        seed = _fetchone(db, "SELECT seed FROM runs WHERE run_id = ?", (rid,))['seed']
        if shift_hand:
            lines.append(f"  seed={seed}: Judge bet rate jumps above 0.30 at hand ~{shift_hand} (retaliation likely)")
        else:
            lines.append(f"  seed={seed}: Judge bet rate stays below 0.30 (no retaliation detected in preflop)")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 7: Pot size by archetype involvement
# ---------------------------------------------------------------------------

def section_pots(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 7: POT SIZE BY ARCHETYPE INVOLVEMENT")
    lines.append("=" * 72)

    rows = _fetchall(db, """
        SELECT
            ag.archetype,
            COUNT(DISTINCT a.run_id || '-' || a.hand_id) AS hands_in,
            AVG(h.final_pot) AS mean_pot,
            MAX(h.final_pot) AS max_pot
        FROM actions a
        JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
        JOIN agent_stats ag ON a.run_id = ag.run_id AND a.seat = ag.seat
        WHERE a.action_type IN ('bet', 'raise', 'call')
        GROUP BY ag.archetype
        ORDER BY mean_pot DESC
    """)

    lines.append(f"  {'Archetype':<20} {'Hands':>8} {'Mean Pot':>10} {'Max Pot':>10}")
    lines.append(f"  {'-'*20} {'-'*8} {'-'*10} {'-'*10}")
    for r in rows:
        lines.append(
            f"  {r['archetype']:<20} {r['hands_in']:>8} "
            f"{r['mean_pot']:>10.1f} {r['max_pot']:>10}"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 8: Sanity checks
# ---------------------------------------------------------------------------

def section_sanity(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 8: SANITY CHECKS")
    lines.append("=" * 72)

    # Chip conservation
    rows = _fetchall(db, """
        SELECT
            run_id,
            SUM(final_stack) AS total_stack,
            SUM(rebuys) AS total_rebuys,
            SUM(final_stack) - (SUM(rebuys) + 8) * 200 AS chip_delta
        FROM agent_stats
        GROUP BY run_id
    """)
    all_ok = all(r['chip_delta'] == 0 for r in rows)
    lines.append(f"  Chip conservation: {'ALL OK' if all_ok else 'FAILURES DETECTED'}")
    if not all_ok:
        for r in rows:
            if r['chip_delta'] != 0:
                lines.append(f"    run_id={r['run_id']}: delta={r['chip_delta']}")

    # Orphan actions
    orphans = _fetchone(db, """
        SELECT COUNT(*) AS c FROM actions a
        LEFT JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
        WHERE h.hand_id IS NULL
    """)["c"]
    lines.append(f"  Orphan actions:   {orphans} {'(OK)' if orphans == 0 else '(PROBLEM)'}")

    # Trust snapshot completeness
    expected_per_hand = 8 * 7  # 56
    sample = _fetchone(db, """
        SELECT COUNT(*) AS c FROM trust_snapshots WHERE run_id = 1 AND hand_id = 1
    """)
    actual = sample["c"] if sample else 0
    lines.append(f"  Trust rows/hand:  {actual} (expected {expected_per_hand})")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 9: Trust convergence (trajectory sample)
# ---------------------------------------------------------------------------

def section_convergence(db) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("SECTION 9: TRUST CONVERGENCE (mean trust toward seat, run 1)")
    lines.append("=" * 72)

    max_hand = _fetchone(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots WHERE run_id = 1")
    if not max_hand or not max_hand["m"]:
        lines.append("  (no data for run 1)")
        return "\n".join(lines)

    mh = max_hand["m"]
    milestones = [h for h in [1, 50, 100, 250, 500, 1000, 2500, 5000, 10000] if h <= mh]
    milestones.append(mh)

    seat_arch = {}
    for r in _fetchall(db, "SELECT seat, archetype FROM agent_stats WHERE run_id = 1"):
        seat_arch[r['seat']] = r['archetype']

    lines.append(f"  Hand    " + "  ".join(f"S{s}({seat_arch.get(s,'?')[:4]})" for s in range(8)))
    lines.append(f"  ------  " + "  ".join("-" * 12 for _ in range(8)))

    for h in milestones:
        row_data = {}
        for r in _fetchall(db, """
            SELECT target_seat, AVG(trust) AS t
            FROM trust_snapshots
            WHERE run_id = 1 AND hand_id = ?
            GROUP BY target_seat
        """, (h,)):
            row_data[r['target_seat']] = r['t']
        cells = []
        for s in range(8):
            t = row_data.get(s)
            cells.append(f"{t:>12.3f}" if t is not None else f"{'---':>12}")
        lines.append(f"  {h:<6}  " + "  ".join(cells))

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

ALL_SECTIONS = {
    "overview": section_overview,
    "performance": section_performance,
    "behavior": section_behavior,
    "trust": section_trust,
    "predator": section_predator,
    "judge": section_judge,
    "pots": section_pots,
    "sanity": section_sanity,
    "convergence": section_convergence,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", required=True, help="Path to runs.sqlite")
    parser.add_argument("--section", default=None,
                        choices=list(ALL_SECTIONS) + ["all"],
                        help="Run only one section (default: all)")
    parser.add_argument("--csv", default=None,
                        help="Write per-section CSVs to this directory (optional)")
    args = parser.parse_args(argv)

    db = _connect(args.db)

    sections = list(ALL_SECTIONS) if args.section in (None, "all") else [args.section]

    print()
    print("  POKER TRUST SIMULATION — RESEARCH ANALYSIS REPORT")
    print(f"  Database: {args.db}")
    print()

    for name in sections:
        output = ALL_SECTIONS[name](db)
        print(output)

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
