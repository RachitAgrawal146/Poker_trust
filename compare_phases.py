"""Phase 1 vs Phase 2 side-by-side comparison.

Reads the agent_stats and trust_snapshots from both databases and produces
a structured comparison across behavioral fingerprints, economic performance,
trust dynamics, and classification accuracy.

Usage::

    python compare_phases.py \\
        --phase1-db runs_v3.sqlite \\
        --phase2-db ml_runs_rf.sqlite \\
        --out comparison_report.txt
"""

from __future__ import annotations

import argparse
import math
import os
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple


def _connect(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


def _q(db, sql, params=()):
    return db.execute(sql, params).fetchall()


def _q1(db, sql, params=()):
    return db.execute(sql, params).fetchone()


def _stddev(vals):
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _pct(num, den):
    return 100.0 * num / den if den else 0.0


def _behavioral_profile(db) -> Dict[str, Dict[str, float]]:
    """Extract per-archetype behavioral stats."""
    rows = _q(db, """
        SELECT archetype,
               AVG(vpip_count*100.0/hands_dealt) AS vpip,
               AVG(pfr_count*100.0/hands_dealt) AS pfr,
               AVG((bets+raises)*1.0/CASE WHEN calls>0 THEN calls ELSE 1 END) AS af,
               AVG(showdowns*100.0/hands_dealt) AS sd_pct,
               AVG(final_stack) AS mean_stack,
               AVG(rebuys) AS mean_rebuys
        FROM agent_stats GROUP BY archetype
    """)
    return {r["archetype"]: dict(r) for r in rows}


def _trust_profile(db) -> Dict[str, Dict[str, float]]:
    """Extract per-archetype trust at final hand."""
    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT ag.archetype,
               AVG(t.trust) AS mean_trust,
               AVG(t.entropy) AS mean_entropy
        FROM trust_snapshots t
        JOIN fh ON t.run_id=fh.run_id AND t.hand_id=fh.lh
        JOIN agent_stats ag ON t.run_id=ag.run_id AND t.target_seat=ag.seat
        GROUP BY ag.archetype
    """)
    return {r["archetype"]: dict(r) for r in rows}


def _classification_accuracy(db) -> Dict[str, Tuple[int, int, float]]:
    """For each seat, compute how often top_archetype matches true archetype."""
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r["seat"]] = r["archetype"]

    # Map short archetype names to trust-type names used in posteriors
    _MAP = {
        "predator": "predator_baseline",
        "mirror": "mirror_default",
        "judge": "judge_cooperative",
    }

    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT t.target_seat, t.top_archetype, COUNT(*) AS n
        FROM trust_snapshots t
        JOIN fh ON t.run_id=fh.run_id AND t.hand_id=fh.lh
        GROUP BY t.target_seat, t.top_archetype
    """)

    by_seat = {}
    for r in rows:
        by_seat.setdefault(r["target_seat"], []).append(r)

    result = {}
    for seat, entries in by_seat.items():
        true_arch = seat_arch.get(seat, "?")
        trust_name = _MAP.get(true_arch, true_arch)
        n_total = sum(e["n"] for e in entries)
        n_correct = sum(e["n"] for e in entries if e["top_archetype"] == trust_name)
        acc = _pct(n_correct, n_total)
        result[true_arch] = (n_correct, n_total, acc)
    return result


def compare(phase1_db_path: str, phase2_db_path: str, out_path: Optional[str] = None) -> str:
    db1 = _connect(phase1_db_path)
    db2 = _connect(phase2_db_path)

    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("  PHASE 1 vs PHASE 2 COMPARISON REPORT")
    lines.append("=" * 78)
    lines.append(f"  Phase 1: {phase1_db_path}")
    lines.append(f"  Phase 2: {phase2_db_path}")
    lines.append("")

    # Table 1: Behavioral fingerprints
    bp1 = _behavioral_profile(db1)
    bp2 = _behavioral_profile(db2)
    archetypes = sorted(set(bp1.keys()) | set(bp2.keys()))

    lines.append("TABLE 1: BEHAVIORAL FINGERPRINT COMPARISON")
    lines.append("-" * 78)
    lines.append(f"  {'':20s}  {'--- Phase 1 ---':^30s}  {'--- Phase 2 ---':^30s}")
    lines.append(f"  {'Archetype':20s}  {'VPIP':>7} {'PFR':>7} {'AF':>6} {'SD%':>6}  {'VPIP':>7} {'PFR':>7} {'AF':>6} {'SD%':>6}")
    lines.append("  " + "-" * 76)
    for arch in archetypes:
        p1 = bp1.get(arch, {})
        p2 = bp2.get(arch, {})
        lines.append(
            f"  {arch:20s}"
            f"  {p1.get('vpip', 0):6.1f}% {p1.get('pfr', 0):6.1f}% {p1.get('af', 0):6.2f} {p1.get('sd_pct', 0):5.1f}%"
            f"  {p2.get('vpip', 0):6.1f}% {p2.get('pfr', 0):6.1f}% {p2.get('af', 0):6.2f} {p2.get('sd_pct', 0):5.1f}%"
        )
    lines.append("")

    # Table 2: Economic performance
    lines.append("TABLE 2: ECONOMIC PERFORMANCE COMPARISON")
    lines.append("-" * 70)
    lines.append(f"  {'Archetype':20s}  {'P1 Stack':>10} {'P1 RB':>7}  {'P2 Stack':>10} {'P2 RB':>7}  {'Delta%':>8}")
    lines.append("  " + "-" * 68)
    for arch in archetypes:
        p1 = bp1.get(arch, {})
        p2 = bp2.get(arch, {})
        s1 = p1.get("mean_stack", 0)
        s2 = p2.get("mean_stack", 0)
        delta_pct = ((s2 - s1) / s1 * 100) if s1 != 0 else 0
        lines.append(
            f"  {arch:20s}"
            f"  {s1:10.0f} {p1.get('mean_rebuys', 0):6.1f}"
            f"  {s2:10.0f} {p2.get('mean_rebuys', 0):6.1f}"
            f"  {delta_pct:+7.1f}%"
        )
    lines.append("")

    # Table 3: Trust dynamics
    tp1 = _trust_profile(db1)
    tp2 = _trust_profile(db2)
    lines.append("TABLE 3: TRUST DYNAMICS COMPARISON")
    lines.append("-" * 60)
    lines.append(f"  {'Archetype':20s}  {'P1 Trust':>10} {'P1 H':>7}  {'P2 Trust':>10} {'P2 H':>7}")
    lines.append("  " + "-" * 58)
    for arch in archetypes:
        t1 = tp1.get(arch, {})
        t2 = tp2.get(arch, {})
        lines.append(
            f"  {arch:20s}"
            f"  {t1.get('mean_trust', 0):10.4f} {t1.get('mean_entropy', 0):7.3f}"
            f"  {t2.get('mean_trust', 0):10.4f} {t2.get('mean_entropy', 0):7.3f}"
        )

    # Trust-profit correlation for each phase
    def _trust_profit_r(bp, tp):
        archs = [a for a in bp if a in tp]
        if len(archs) < 3:
            return 0.0
        stacks = [bp[a].get("mean_stack", 0) for a in archs]
        trusts = [tp[a].get("mean_trust", 0) for a in archs]
        n = len(archs)
        mean_s = sum(stacks) / n
        mean_t = sum(trusts) / n
        cov = sum((s - mean_s) * (t - mean_t) for s, t in zip(stacks, trusts))
        var_s = sum((s - mean_s) ** 2 for s in stacks)
        var_t = sum((t - mean_t) ** 2 for t in trusts)
        denom = math.sqrt(var_s * var_t)
        return cov / denom if denom > 0 else 0.0

    r1 = _trust_profit_r(bp1, tp1)
    r2 = _trust_profit_r(bp2, tp2)
    lines.append(f"\n  Trust-profit correlation:  Phase 1 r={r1:.3f}  Phase 2 r={r2:.3f}")
    lines.append("")

    # Table 4: Classification accuracy
    ca1 = _classification_accuracy(db1)
    ca2 = _classification_accuracy(db2)
    lines.append("TABLE 4: CLASSIFICATION ACCURACY (top_archetype at final hand)")
    lines.append("-" * 60)
    lines.append(f"  {'Archetype':20s}  {'P1 Acc':>10}  {'P2 Acc':>10}")
    lines.append("  " + "-" * 44)
    for arch in archetypes:
        a1 = ca1.get(arch, (0, 0, 0))
        a2 = ca2.get(arch, (0, 0, 0))
        lines.append(f"  {arch:20s}  {a1[2]:9.1f}%  {a2[2]:9.1f}%")
    n_classified_1 = sum(1 for v in ca1.values() if v[2] > 50)
    n_classified_2 = sum(1 for v in ca2.values() if v[2] > 50)
    lines.append(f"\n  Classification ceiling:  Phase 1 = {n_classified_1}/8  Phase 2 = {n_classified_2}/8")
    lines.append("")

    # Key questions
    lines.append("=" * 78)
    lines.append("  KEY FINDINGS")
    lines.append("=" * 78)

    # Q1: Does Firestorm still dominate?
    top1 = max(bp1, key=lambda a: bp1[a].get("mean_stack", 0)) if bp1 else "?"
    top2 = max(bp2, key=lambda a: bp2[a].get("mean_stack", 0)) if bp2 else "?"
    lines.append(f"\n  Q1: Top economic performer")
    lines.append(f"      Phase 1: {top1} ({bp1.get(top1, {}).get('mean_stack', 0):.0f})")
    lines.append(f"      Phase 2: {top2} ({bp2.get(top2, {}).get('mean_stack', 0):.0f})")
    if top1 == top2:
        lines.append(f"      SAME — dominance is a property of the strategy, not implementation")
    else:
        lines.append(f"      DIFFERENT — strategy advantage is implementation-sensitive")

    # Q2: Trust-profit anticorrelation
    lines.append(f"\n  Q2: Trust-profit anticorrelation")
    lines.append(f"      Phase 1: r={r1:.3f}  Phase 2: r={r2:.3f}")
    if r2 < -0.5:
        lines.append(f"      ROBUST — anticorrelation holds across implementation methods")
    else:
        lines.append(f"      WEAKENED — anticorrelation may be parameter-specific")

    # Q3: Classification
    lines.append(f"\n  Q3: Bayesian classification of ML agents")
    lines.append(f"      Phase 1 ceiling: {n_classified_1}/8  Phase 2 ceiling: {n_classified_2}/8")
    if n_classified_2 > n_classified_1:
        lines.append(f"      EASIER — ML agents are more stereotyped")
    elif n_classified_2 < n_classified_1:
        lines.append(f"      HARDER — ML agents are more nuanced")
    else:
        lines.append(f"      SIMILAR — behavioral signatures faithfully reproduced")

    lines.append("")
    lines.append("=" * 78)
    lines.append("  END OF COMPARISON")
    lines.append("=" * 78)

    report = "\n".join(lines)
    if out_path:
        with open(out_path, "w") as f:
            f.write(report + "\n")
        print(f"Report saved to {out_path}")
    print(report)

    db1.close()
    db2.close()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase1-db", required=True, help="Phase 1 database path")
    parser.add_argument("--phase2-db", required=True, help="Phase 2 database path")
    parser.add_argument("--out", default="comparison_report.txt", help="Output report path")
    args = parser.parse_args(argv)
    compare(args.phase1_db, args.phase2_db, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
