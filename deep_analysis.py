#!/usr/bin/env python3
"""Exhaustive research analysis of Poker Trust Simulation runs.

Reads ``runs.sqlite`` and produces a detailed log covering every
analysis dimension the schema supports. Writes both to stdout and
to a log file (``--out``, default ``deep_analysis_report.txt``).

Usage:
    python3 deep_analysis.py --db runs.sqlite
    python3 deep_analysis.py --db runs.sqlite --out my_report.txt

25+ analysis sections covering:
  Economics, behavior, trust dynamics, identification accuracy,
  adaptive agent verification, positional effects, temporal dynamics,
  head-to-head matchups, pot distributions, and sanity checks.
"""

from __future__ import annotations

import argparse
import math
import os
import sqlite3
import sys
from collections import defaultdict
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found.", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(db_path)
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

class Report:
    """Collects lines and writes to both stdout and a file."""
    def __init__(self, out_path: Optional[str] = None):
        self.lines: List[str] = []
        self.out_path = out_path

    def w(self, line: str = ""):
        self.lines.append(line)
        print(line)

    def header(self, num: int, title: str):
        self.w("")
        self.w("=" * 78)
        self.w(f"  SECTION {num}: {title}")
        self.w("=" * 78)

    def subheader(self, title: str):
        self.w(f"\n  --- {title} ---")

    def table(self, headers, rows, widths=None):
        if not widths:
            widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=4)) + 2
                      for i, h in enumerate(headers)]
        fmt = "  " + "".join(f"{{:<{w}}}" if i == 0 else f"{{:>{w}}}" for i, w in enumerate(widths))
        self.w(fmt.format(*headers))
        self.w("  " + "".join("-" * w for w in widths))
        for row in rows:
            self.w(fmt.format(*row))

    def save(self):
        if self.out_path:
            with open(self.out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))
                f.write("\n")
            print(f"\n  Report saved to {self.out_path}")


# ---------------------------------------------------------------------------
# Section 1: Database overview
# ---------------------------------------------------------------------------

def s01_overview(db, R):
    R.header(1, "DATABASE OVERVIEW")
    runs = _q(db, "SELECT * FROM runs ORDER BY run_id")
    R.w(f"  Runs:              {len(runs)}")
    R.w(f"  Hands:             {_q1(db, 'SELECT COUNT(*) AS c FROM hands')['c']:,}")
    R.w(f"  Actions:           {_q1(db, 'SELECT COUNT(*) AS c FROM actions')['c']:,}")
    R.w(f"  Showdown entries:  {_q1(db, 'SELECT COUNT(*) AS c FROM showdowns')['c']:,}")
    R.w(f"  Trust snapshots:   {_q1(db, 'SELECT COUNT(*) AS c FROM trust_snapshots')['c']:,}")
    R.w(f"  Agent stat rows:   {_q1(db, 'SELECT COUNT(*) AS c FROM agent_stats')['c']:,}")
    R.w(f"  Seeds:             {', '.join(str(r['seed']) for r in runs)}")
    if runs:
        R.w(f"  Hands per seed:    {runs[0]['num_hands']}")
        R.w(f"  Seats per run:     {runs[0]['num_seats']}")
    # Showdown vs walkover split
    sd = _q1(db, "SELECT SUM(had_showdown) AS sd, COUNT(*) - SUM(had_showdown) AS wo FROM hands")
    R.w(f"  Showdown hands:    {sd['sd']:,} ({_pct(sd['sd'], sd['sd']+sd['wo']):.1f}%)")
    R.w(f"  Walkover hands:    {sd['wo']:,} ({_pct(sd['wo'], sd['sd']+sd['wo']):.1f}%)")


# ---------------------------------------------------------------------------
# Section 2: Archetype economic performance
# ---------------------------------------------------------------------------

def s02_economics(db, R):
    R.header(2, "ARCHETYPE ECONOMIC PERFORMANCE")
    rows = _q(db, """
        SELECT archetype,
               AVG(final_stack) AS mean_stack,
               MIN(final_stack) AS min_stack, MAX(final_stack) AS max_stack,
               AVG(rebuys) AS mean_rebuys,
               SUM(rebuys) AS total_rebuys,
               COUNT(*) AS n
        FROM agent_stats GROUP BY archetype ORDER BY mean_stack DESC
    """)
    data = []
    for r in rows:
        data.append([r['archetype'], f"{r['mean_stack']:.0f}", f"{r['min_stack']}", f"{r['max_stack']}",
                      f"{r['mean_rebuys']:.1f}", f"{r['total_rebuys']}", f"{r['n']}"])
    R.table(["Archetype", "MeanStk", "MinStk", "MaxStk", "MeanRB", "TotRB", "Seeds"],
            data, [20, 10, 10, 10, 10, 10, 8])

    R.subheader("Cross-seed standard deviation of final_stack")
    for arch in [r['archetype'] for r in rows]:
        vals = [r['final_stack'] for r in _q(db, "SELECT final_stack FROM agent_stats WHERE archetype=?", (arch,))]
        R.w(f"    {arch:<20} mean={sum(vals)/len(vals):8.0f}  std={_stddev(vals):8.0f}")


# ---------------------------------------------------------------------------
# Section 3: Behavioral profile
# ---------------------------------------------------------------------------

def s03_behavior(db, R):
    R.header(3, "BEHAVIORAL PROFILE (VPIP / PFR / AF / Showdown %)")
    rows = _q(db, """
        SELECT archetype,
               AVG(vpip_count*100.0/hands_dealt) AS vpip,
               AVG(pfr_count*100.0/hands_dealt) AS pfr,
               AVG((bets+raises)*1.0/CASE WHEN calls>0 THEN calls ELSE 1 END) AS af,
               AVG(showdowns*100.0/hands_dealt) AS sd_pct,
               AVG(showdowns_won*100.0/CASE WHEN showdowns>0 THEN showdowns ELSE 1 END) AS sd_win
        FROM agent_stats GROUP BY archetype ORDER BY vpip DESC
    """)
    data = []
    for r in rows:
        data.append([r['archetype'], f"{r['vpip']:.1f}%", f"{r['pfr']:.1f}%",
                      f"{r['af']:.2f}", f"{r['sd_pct']:.1f}%", f"{r['sd_win']:.1f}%"])
    R.table(["Archetype", "VPIP", "PFR", "AF", "SD%", "SDWin%"],
            data, [20, 9, 9, 8, 8, 9])


# ---------------------------------------------------------------------------
# Section 4: Action frequency per archetype
# ---------------------------------------------------------------------------

def s04_action_freq(db, R):
    R.header(4, "ACTION FREQUENCY BY ARCHETYPE")
    rows = _q(db, """
        SELECT archetype, action_type, COUNT(*) AS cnt
        FROM actions GROUP BY archetype, action_type
    """)
    # Pivot: archetype -> {action: count}
    totals = defaultdict(lambda: defaultdict(int))
    for r in rows:
        totals[r['archetype']][r['action_type']] = r['cnt']
    acts = ['fold', 'check', 'call', 'bet', 'raise']
    data = []
    for arch in sorted(totals):
        total = sum(totals[arch].values())
        data.append([arch] + [f"{_pct(totals[arch].get(a,0), total):.1f}%" for a in acts] + [f"{total:,}"])
    R.table(["Archetype", "Fold%", "Check%", "Call%", "Bet%", "Raise%", "Total"],
            data, [20, 9, 9, 9, 9, 9, 12])


# ---------------------------------------------------------------------------
# Section 5: Per-street aggression
# ---------------------------------------------------------------------------

def s05_street_aggression(db, R):
    R.header(5, "PER-STREET AGGRESSION (bet+raise % of actions)")
    rows = _q(db, """
        SELECT archetype, betting_round,
               SUM(CASE WHEN action_type IN ('bet','raise') THEN 1 ELSE 0 END)*100.0/COUNT(*) AS agg_pct,
               COUNT(*) AS n
        FROM actions GROUP BY archetype, betting_round
    """)
    by_arch = defaultdict(dict)
    for r in rows:
        by_arch[r['archetype']][r['betting_round']] = (r['agg_pct'], r['n'])
    streets = ['preflop', 'flop', 'turn', 'river']
    data = []
    for arch in sorted(by_arch):
        row = [arch]
        for st in streets:
            if st in by_arch[arch]:
                pct, n = by_arch[arch][st]
                row.append(f"{pct:.1f}%")
            else:
                row.append("---")
        data.append(row)
    R.table(["Archetype", "Preflop", "Flop", "Turn", "River"],
            data, [20, 10, 10, 10, 10])


# ---------------------------------------------------------------------------
# Section 6: Positional analysis (profit by position)
# ---------------------------------------------------------------------------

def s06_position(db, R):
    R.header(6, "POSITIONAL ANALYSIS (mean pot won by dealer-relative position)")
    R.w("  Position 0 = dealer, 1 = SB, 2 = BB, 3-7 = early to late")
    rows = _q(db, """
        SELECT
            (s.seat - h.dealer + 8) % 8 AS position,
            ag.archetype,
            AVG(s.pot_won) AS mean_won
        FROM showdowns s
        JOIN hands h ON s.run_id = h.run_id AND s.hand_id = h.hand_id
        JOIN agent_stats ag ON s.run_id = ag.run_id AND s.seat = ag.seat
        WHERE s.won = 1
        GROUP BY position, ag.archetype
        ORDER BY ag.archetype, position
    """)
    by_arch = defaultdict(dict)
    for r in rows:
        by_arch[r['archetype']][r['position']] = r['mean_won']
    data = []
    for arch in sorted(by_arch):
        row = [arch]
        for p in range(8):
            v = by_arch[arch].get(p)
            row.append(f"{v:.1f}" if v else "---")
        data.append(row)
    R.table(["Archetype"] + [f"Pos{p}" for p in range(8)],
            data, [20] + [8]*8)


# ---------------------------------------------------------------------------
# Section 7: Showdown analysis
# ---------------------------------------------------------------------------

def s07_showdown(db, R):
    R.header(7, "SHOWDOWN ANALYSIS")

    R.subheader("Win rate at showdown per archetype")
    rows = _q(db, """
        SELECT ag.archetype,
               SUM(s.won) AS wins, COUNT(*) AS total,
               ROUND(100.0*SUM(s.won)/COUNT(*),1) AS win_pct,
               AVG(s.hand_rank) AS avg_rank,
               AVG(CASE WHEN s.won=1 THEN s.pot_won ELSE 0 END) AS avg_pot_won
        FROM showdowns s
        JOIN agent_stats ag ON s.run_id = ag.run_id AND s.seat = ag.seat
        GROUP BY ag.archetype ORDER BY win_pct DESC
    """)
    data = [[r['archetype'], f"{r['wins']:,}", f"{r['total']:,}", f"{r['win_pct']}%",
             f"{r['avg_rank']:.0f}", f"{r['avg_pot_won']:.1f}"] for r in rows]
    R.table(["Archetype", "Wins", "Total", "Win%", "AvgRank", "AvgPotWon"],
            data, [20, 10, 10, 8, 10, 12])

    R.subheader("Hand rank distribution at showdown (lower rank = better)")
    rows = _q(db, """
        SELECT ag.archetype,
               MIN(s.hand_rank) AS best, MAX(s.hand_rank) AS worst,
               AVG(s.hand_rank) AS mean_rank
        FROM showdowns s
        JOIN agent_stats ag ON s.run_id = ag.run_id AND s.seat = ag.seat
        GROUP BY ag.archetype ORDER BY mean_rank
    """)
    data = [[r['archetype'], f"{r['best']}", f"{r['worst']}", f"{r['mean_rank']:.0f}"] for r in rows]
    R.table(["Archetype", "BestRank", "WorstRank", "MeanRank"], data, [20, 12, 12, 12])


# ---------------------------------------------------------------------------
# Section 8: Walkover analysis
# ---------------------------------------------------------------------------

def s08_walkover(db, R):
    R.header(8, "WALKOVER ANALYSIS (wins without showdown)")
    rows = _q(db, """
        SELECT ag.archetype,
               COUNT(*) AS walkovers,
               AVG(h.final_pot) AS avg_pot
        FROM hands h
        JOIN agent_stats ag ON h.run_id = ag.run_id AND h.walkover_winner = ag.seat
        WHERE h.walkover_winner IS NOT NULL
        GROUP BY ag.archetype ORDER BY walkovers DESC
    """)
    total_wo = sum(r['walkovers'] for r in rows)
    data = [[r['archetype'], f"{r['walkovers']:,}", f"{_pct(r['walkovers'], total_wo):.1f}%",
             f"{r['avg_pot']:.1f}"] for r in rows]
    R.table(["Archetype", "Walkovers", "Share%", "AvgPot"], data, [20, 12, 10, 10])


# ---------------------------------------------------------------------------
# Section 9: Pot size distribution
# ---------------------------------------------------------------------------

def s09_pots(db, R):
    R.header(9, "POT SIZE DISTRIBUTION")

    R.subheader("Overall pot statistics")
    stats = _q1(db, """
        SELECT AVG(final_pot) AS mean_pot, MIN(final_pot) AS min_pot,
               MAX(final_pot) AS max_pot, COUNT(*) AS n
        FROM hands
    """)
    R.w(f"  Mean pot: {stats['mean_pot']:.1f}  Min: {stats['min_pot']}  Max: {stats['max_pot']}  Hands: {stats['n']:,}")

    R.subheader("Mean pot by whether hand reached showdown")
    rows = _q(db, """
        SELECT had_showdown, AVG(final_pot) AS mean_pot, COUNT(*) AS n
        FROM hands GROUP BY had_showdown
    """)
    for r in rows:
        label = "Showdown" if r['had_showdown'] else "Walkover"
        R.w(f"  {label:<12} mean_pot={r['mean_pot']:.1f}  hands={r['n']:,}")

    R.subheader("Pot size by archetype involvement (any non-fold action)")
    rows = _q(db, """
        SELECT ag.archetype,
               COUNT(DISTINCT a.run_id || '-' || a.hand_id) AS hands_in,
               AVG(h.final_pot) AS mean_pot, MAX(h.final_pot) AS max_pot
        FROM actions a
        JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
        JOIN agent_stats ag ON a.run_id = ag.run_id AND a.seat = ag.seat
        WHERE a.action_type != 'fold'
        GROUP BY ag.archetype ORDER BY mean_pot DESC
    """)
    data = [[r['archetype'], f"{r['hands_in']:,}", f"{r['mean_pot']:.1f}", f"{r['max_pot']}"] for r in rows]
    R.table(["Archetype", "HandsIn", "MeanPot", "MaxPot"], data, [20, 12, 10, 10])


# ---------------------------------------------------------------------------
# Section 10: Trust matrix at final hand
# ---------------------------------------------------------------------------

def s10_trust_matrix(db, R):
    R.header(10, "TRUST MATRIX AT FINAL HAND (all-pairs, averaged across seeds)")
    # Get seat->archetype mapping
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype'][:4]

    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT t.observer_seat AS obs, t.target_seat AS tgt,
               AVG(t.trust) AS t_avg, AVG(t.entropy) AS e_avg
        FROM trust_snapshots t
        JOIN fh ON t.run_id = fh.run_id AND t.hand_id = fh.lh
        GROUP BY obs, tgt ORDER BY obs, tgt
    """)
    matrix = defaultdict(dict)
    for r in rows:
        matrix[r['obs']][r['tgt']] = r['t_avg']

    R.w(f"  {'':>6}" + "".join(f"  S{s}({seat_arch.get(s,'?'):>4})" for s in range(8)))
    for obs in range(8):
        cells = []
        for tgt in range(8):
            if obs == tgt:
                cells.append("   ---  ")
            else:
                v = matrix.get(obs, {}).get(tgt)
                cells.append(f"  {v:.3f} " if v else "   ???  ")
        R.w(f"  S{obs}({seat_arch.get(obs,'?'):>4})" + "".join(cells))


# ---------------------------------------------------------------------------
# Section 11: Entropy matrix at final hand
# ---------------------------------------------------------------------------

def s11_entropy_matrix(db, R):
    R.header(11, "ENTROPY MATRIX AT FINAL HAND (posterior uncertainty, bits)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype'][:4]

    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT t.observer_seat AS obs, t.target_seat AS tgt,
               AVG(t.entropy) AS e_avg
        FROM trust_snapshots t
        JOIN fh ON t.run_id = fh.run_id AND t.hand_id = fh.lh
        GROUP BY obs, tgt ORDER BY obs, tgt
    """)
    matrix = defaultdict(dict)
    for r in rows:
        matrix[r['obs']][r['tgt']] = r['e_avg']

    R.w(f"  {'':>6}" + "".join(f"  S{s}({seat_arch.get(s,'?'):>4})" for s in range(8)))
    for obs in range(8):
        cells = []
        for tgt in range(8):
            if obs == tgt:
                cells.append("   ---  ")
            else:
                v = matrix.get(obs, {}).get(tgt)
                cells.append(f"  {v:.3f} " if v else "   ???  ")
        R.w(f"  S{obs}({seat_arch.get(obs,'?'):>4})" + "".join(cells))


# ---------------------------------------------------------------------------
# Section 12: Archetype identification accuracy
# ---------------------------------------------------------------------------

def s12_identification(db, R):
    R.header(12, "ARCHETYPE IDENTIFICATION ACCURACY (top_archetype at final hand)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype']

    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT t.target_seat, t.top_archetype, AVG(t.top_prob) AS avg_prob,
               COUNT(*) AS n
        FROM trust_snapshots t
        JOIN fh ON t.run_id = fh.run_id AND t.hand_id = fh.lh
        GROUP BY t.target_seat, t.top_archetype
        ORDER BY t.target_seat, avg_prob DESC
    """)
    by_seat = defaultdict(list)
    for r in rows:
        by_seat[r['target_seat']].append(r)

    for seat in range(8):
        true_arch = seat_arch.get(seat, "?")
        R.w(f"\n  Seat {seat} (true: {true_arch}):")
        entries = by_seat.get(seat, [])
        for e in entries[:4]:
            match = " <-- CORRECT" if true_arch in e['top_archetype'] else ""
            R.w(f"    {e['top_archetype']:<25} avg_prob={e['avg_prob']:.3f}  n={e['n']}{match}")


# ---------------------------------------------------------------------------
# Section 13: Trust convergence over time
# ---------------------------------------------------------------------------

def s13_trust_convergence(db, R):
    R.header(13, "TRUST CONVERGENCE OVER TIME (mean trust toward each seat, run 1)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype'][:5]

    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots WHERE run_id=1")['m'] or 0
    milestones = [h for h in [1, 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000] if h <= max_h]
    if max_h not in milestones:
        milestones.append(max_h)

    R.w(f"  {'Hand':<8}" + "".join(f" S{s}({seat_arch.get(s,'?'):<5})" for s in range(8)))
    R.w(f"  {'----':<8}" + "".join(f" {'----------':>11}" for _ in range(8)))

    for h in milestones:
        row_data = {}
        for r in _q(db, """
            SELECT target_seat, AVG(trust) AS t
            FROM trust_snapshots WHERE run_id=1 AND hand_id=? GROUP BY target_seat
        """, (h,)):
            row_data[r['target_seat']] = r['t']
        cells = [f" {row_data.get(s, 0):.4f}     " if s in row_data else " ---        " for s in range(8)]
        R.w(f"  {h:<8}" + "".join(cells))


# ---------------------------------------------------------------------------
# Section 14: Entropy convergence over time
# ---------------------------------------------------------------------------

def s14_entropy_convergence(db, R):
    R.header(14, "ENTROPY CONVERGENCE OVER TIME (bits, run 1)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype'][:5]

    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots WHERE run_id=1")['m'] or 0
    milestones = [h for h in [1, 50, 100, 500, 1000, 5000, 10000] if h <= max_h]
    if max_h not in milestones:
        milestones.append(max_h)

    R.w(f"  {'Hand':<8}" + "".join(f" S{s}({seat_arch.get(s,'?'):<5})" for s in range(8)))
    for h in milestones:
        row_data = {}
        for r in _q(db, """
            SELECT target_seat, AVG(entropy) AS e
            FROM trust_snapshots WHERE run_id=1 AND hand_id=? GROUP BY target_seat
        """, (h,)):
            row_data[r['target_seat']] = r['e']
        cells = [f" {row_data.get(s, 3.0):.3f}      " if s in row_data else " ---        " for s in range(8)]
        R.w(f"  {h:<8}" + "".join(cells))


# ---------------------------------------------------------------------------
# Section 15: Predator exploitation analysis
# ---------------------------------------------------------------------------

def s15_predator(db, R):
    R.header(15, "PREDATOR EXPLOITATION ANALYSIS")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype']

    R.subheader("Predator (seat 5) posterior evolution per target, averaged across seeds")
    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots")['m'] or 0
    milestones = [h for h in [100, 500, 1000, 2500, 5000, 10000] if h <= max_h]

    for tgt in range(8):
        if tgt == 5:
            continue
        arch = seat_arch.get(tgt, '?')
        R.w(f"\n  Target S{tgt} ({arch}):")
        for h in milestones:
            row = _q1(db, """
                SELECT AVG(trust) AS t, AVG(entropy) AS e, AVG(top_prob) AS p,
                       GROUP_CONCAT(DISTINCT top_archetype) AS archs
                FROM trust_snapshots
                WHERE observer_seat=5 AND target_seat=? AND hand_id=?
            """, (tgt, h))
            if row and row['t'] is not None:
                R.w(f"    h{h:>5}: trust={row['t']:.3f}  H={row['e']:.3f}  "
                    f"top_prob={row['p']:.3f}  top_archs={row['archs']}")


# ---------------------------------------------------------------------------
# Section 16: Judge retaliation deep dive
# ---------------------------------------------------------------------------

def s16_judge(db, R):
    R.header(16, "JUDGE RETALIATION DEEP DIVE")

    R.subheader("Judge (seat 7) overall aggression over time — ALL streets, run 1")
    R.w("  (Rolling 200-hand window of bet+raise rate across all streets)")
    rows = _q(db, """
        SELECT hand_id,
               SUM(CASE WHEN action_type IN ('bet','raise') THEN 1 ELSE 0 END) AS br,
               COUNT(*) AS total
        FROM actions WHERE run_id=1 AND seat=7
        GROUP BY hand_id ORDER BY hand_id
    """)
    window = []
    sampled = []
    for r in rows:
        window.append((r['br'], r['total']))
        if len(window) > 200:
            window.pop(0)
        if len(window) >= 50 and r['hand_id'] % 100 == 0:
            br_sum = sum(x[0] for x in window)
            total_sum = sum(x[1] for x in window)
            rate = br_sum / total_sum if total_sum > 0 else 0
            sampled.append((r['hand_id'], rate))

    for hand_id, rate in sampled[:20]:
        bar = "#" * int(rate * 50)
        R.w(f"    h{hand_id:>5}: {rate:.3f} |{bar}")

    R.subheader("Judge bet rate CONDITIONAL on each opponent being in the hand")
    R.w("  (Key insight: retaliation only fires when a triggered opponent is")
    R.w("   active. The aggregate rate dilutes the signal. Per-opponent rates")
    R.w("   reveal the behavioral shift.)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype']
    run_ids = [r['run_id'] for r in _q(db, "SELECT run_id FROM runs ORDER BY run_id LIMIT 5")]
    for opp_seat in range(8):
        if opp_seat == 7:
            continue
        arch = seat_arch.get(opp_seat, '?')
        # For each seed, compute Judge's bet+raise rate in hands where
        # this opponent also acted (both were in the hand).
        rates = []
        for rid in run_ids:
            row = _q1(db, """
                SELECT
                    SUM(CASE WHEN a.action_type IN ('bet','raise') THEN 1 ELSE 0 END) AS br,
                    COUNT(*) AS total
                FROM actions a
                WHERE a.run_id = ? AND a.seat = 7
                  AND a.hand_id IN (
                      SELECT DISTINCT hand_id FROM actions
                      WHERE run_id = ? AND seat = ?
                  )
            """, (rid, rid, opp_seat))
            if row and row['total'] and row['total'] > 0:
                rates.append(row['br'] / row['total'])
        if rates:
            mean_rate = sum(rates) / len(rates)
            R.w(f"    vs S{opp_seat} ({arch:<12}): bet_rate={mean_rate:.3f} "
                f"(across {len(rates)} seeds)")

    R.subheader("Judge trust RECEIVED from others over time (run 1)")
    R.w("  (If retaliation is detected, trust toward Judge should drop)")
    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots WHERE run_id=1")['m'] or 0
    milestones = [h for h in [100, 500, 1000, 2000, 5000, 10000] if h <= max_h]
    for h in milestones:
        row = _q1(db, """
            SELECT AVG(trust) AS t, AVG(entropy) AS e
            FROM trust_snapshots WHERE run_id=1 AND target_seat=7 AND hand_id=?
        """, (h,))
        if row and row['t'] is not None:
            R.w(f"    h{h:>5}: trust_received={row['t']:.3f}  entropy_about_judge={row['e']:.3f}")


# ---------------------------------------------------------------------------
# Section 17: Mirror mimicry analysis
# ---------------------------------------------------------------------------

def s17_mirror(db, R):
    R.header(17, "MIRROR MIMICRY ANALYSIS")

    R.subheader("Mirror (seat 6) behavioral profile over time — run 1")
    R.w("  (Rolling 200-hand aggression rate. NOTE: rolling VPIP proxy may")
    R.w("   overcount due to action-table sampling. Authoritative cumulative")
    R.w("   VPIP from agent_stats is in Section 3.)")
    # Print the authoritative cumulative VPIP for reference.
    cum = _q1(db, """
        SELECT vpip_count*100.0/hands_dealt AS vpip, (bets+raises)*1.0/CASE WHEN calls>0 THEN calls ELSE 1 END AS af
        FROM agent_stats WHERE run_id=1 AND seat=6
    """)
    if cum:
        R.w(f"  Authoritative cumulative: VPIP={cum['vpip']:.1f}%  AF={cum['af']:.2f}")
    rows = _q(db, """
        SELECT hand_id, betting_round, action_type
        FROM actions WHERE run_id=1 AND seat=6 ORDER BY hand_id, sequence_num
    """)
    # Compute per-hand: did Mirror VPIP? did Mirror bet/raise?
    hand_actions = defaultdict(lambda: {"vpip": False, "br": 0, "calls": 0})
    for r in rows:
        hid = r['hand_id']
        if r['betting_round'] == 'preflop' and r['action_type'] in ('call', 'bet', 'raise'):
            hand_actions[hid]["vpip"] = True
        if r['action_type'] in ('bet', 'raise'):
            hand_actions[hid]["br"] += 1
        if r['action_type'] == 'call':
            hand_actions[hid]["calls"] += 1

    window = []
    for hid in sorted(hand_actions):
        ha = hand_actions[hid]
        window.append(ha)
        if len(window) > 200:
            window.pop(0)
        if len(window) >= 50 and hid % 200 == 0:
            vpip_rate = sum(1 for w in window if w["vpip"]) / len(window)
            br_sum = sum(w["br"] for w in window)
            call_sum = max(sum(w["calls"] for w in window), 1)
            af = br_sum / call_sum
            R.w(f"    h{hid:>5}: VPIP={vpip_rate*100:5.1f}%  AF={af:.2f}")

    R.subheader("Mirror trust identification over time (run 1)")
    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM trust_snapshots WHERE run_id=1")['m'] or 0
    milestones = [h for h in [50, 100, 500, 1000, 5000, 10000] if h <= max_h]
    for h in milestones:
        row = _q1(db, """
            SELECT AVG(trust) AS t, AVG(entropy) AS e, AVG(top_prob) AS p
            FROM trust_snapshots WHERE run_id=1 AND target_seat=6 AND hand_id=?
        """, (h,))
        if row and row['t'] is not None:
            R.w(f"    h{h:>5}: trust={row['t']:.3f}  H={row['e']:.3f}  top_prob={row['p']:.3f}")


# ---------------------------------------------------------------------------
# Section 18: Temporal dynamics (early vs late game)
# ---------------------------------------------------------------------------

def s18_temporal(db, R):
    R.header(18, "TEMPORAL DYNAMICS (early vs late 1000 hands, run 1)")
    max_h = _q1(db, "SELECT MAX(hand_id) AS m FROM hands WHERE run_id=1")['m'] or 0
    cutoff = min(1000, max_h // 2)

    for label, lo, hi in [("Early (1-{})".format(cutoff), 1, cutoff),
                           ("Late ({}-{})".format(max_h-cutoff+1, max_h), max_h-cutoff+1, max_h)]:
        R.w(f"\n  {label}:")
        rows = _q(db, """
            SELECT ag.archetype,
                   SUM(CASE WHEN a.action_type IN ('bet','raise') THEN 1 ELSE 0 END)*100.0/COUNT(*) AS agg,
                   COUNT(*) AS n
            FROM actions a
            JOIN agent_stats ag ON a.run_id = ag.run_id AND a.seat = ag.seat
            WHERE a.run_id = 1 AND a.hand_id BETWEEN ? AND ?
            GROUP BY ag.archetype ORDER BY agg DESC
        """, (lo, hi))
        for r in rows:
            R.w(f"    {r['archetype']:<20} aggression={r['agg']:.1f}%  actions={r['n']}")


# ---------------------------------------------------------------------------
# Section 19: Head-to-head showdown matchups
# ---------------------------------------------------------------------------

def s19_h2h(db, R):
    R.header(19, "HEAD-TO-HEAD SHOWDOWN MATCHUPS")
    R.w("  (Net chip flow: positive = row archetype profits from column archetype)")
    seat_arch = {}
    for r in _q(db, "SELECT seat, archetype FROM agent_stats WHERE run_id=1"):
        seat_arch[r['seat']] = r['archetype'][:4]

    # For each pair of archetypes that met at showdown, compute net pot won
    rows = _q(db, """
        SELECT
            w.seat AS winner_seat, l.seat AS loser_seat,
            SUM(w.pot_won) AS total_won, COUNT(*) AS times
        FROM showdowns w
        JOIN showdowns l ON w.run_id = l.run_id AND w.hand_id = l.hand_id
            AND w.seat != l.seat AND w.won = 1 AND l.won = 0
        GROUP BY winner_seat, loser_seat
    """)
    net = defaultdict(lambda: defaultdict(int))
    for r in rows:
        ws = r['winner_seat']
        ls = r['loser_seat']
        net[ws][ls] += r['total_won']
        net[ls][ws] -= r['total_won']

    R.w(f"  {'':>6}" + "".join(f"  S{s}({seat_arch.get(s,'?'):>4})" for s in range(8)))
    for s1 in range(8):
        cells = []
        for s2 in range(8):
            if s1 == s2:
                cells.append("    --- ")
            else:
                v = net.get(s1, {}).get(s2, 0)
                sign = "+" if v > 0 else ""
                cells.append(f" {sign}{v:>6} ")
        R.w(f"  S{s1}({seat_arch.get(s1,'?'):>4})" + "".join(cells))


# ---------------------------------------------------------------------------
# Section 20: Trust-profit correlation
# ---------------------------------------------------------------------------

def s20_trust_profit(db, R):
    R.header(20, "TRUST-PROFIT CORRELATION")
    R.w("  Does being trusted (high trust received) correlate with stack performance?")

    rows = _q(db, """
        WITH fh AS (SELECT run_id, MAX(hand_id) AS lh FROM trust_snapshots GROUP BY run_id)
        SELECT
            ag.archetype,
            ag.final_stack,
            AVG(t.trust) AS trust_received,
            AVG(t.entropy) AS entropy_about
        FROM agent_stats ag
        JOIN trust_snapshots t ON ag.run_id = t.run_id AND ag.seat = t.target_seat
        JOIN fh ON t.run_id = fh.run_id AND t.hand_id = fh.lh
        GROUP BY ag.run_id, ag.seat
    """)
    by_arch = defaultdict(lambda: {"stacks": [], "trusts": []})
    for r in rows:
        by_arch[r['archetype']]["stacks"].append(r['final_stack'])
        by_arch[r['archetype']]["trusts"].append(r['trust_received'])

    data = []
    for arch in sorted(by_arch):
        d = by_arch[arch]
        ms = sum(d["stacks"]) / len(d["stacks"])
        mt = sum(d["trusts"]) / len(d["trusts"])
        data.append([arch, f"{ms:.0f}", f"{mt:.3f}"])
    R.table(["Archetype", "MeanStack", "MeanTrustRcvd"], data, [20, 12, 15])

    # Simple correlation
    all_stacks = []
    all_trusts = []
    for d in by_arch.values():
        all_stacks.extend(d["stacks"])
        all_trusts.extend(d["trusts"])
    if len(all_stacks) > 2:
        n = len(all_stacks)
        mx = sum(all_stacks) / n
        my = sum(all_trusts) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(all_stacks, all_trusts)) / (n - 1)
        sx = _stddev(all_stacks)
        sy = _stddev(all_trusts)
        corr = cov / (sx * sy) if sx > 0 and sy > 0 else 0
        R.w(f"\n  Pearson correlation (stack vs trust_received): r = {corr:.3f}")
        if corr < -0.3:
            R.w("  FINDING: Negative correlation — being trusted does NOT help economically")
        elif corr > 0.3:
            R.w("  FINDING: Positive correlation — trust and profit are aligned")
        else:
            R.w("  FINDING: Weak/no linear correlation between trust and profit")


# ---------------------------------------------------------------------------
# Section 21: Cross-seed consistency
# ---------------------------------------------------------------------------

def s21_consistency(db, R):
    R.header(21, "CROSS-SEED CONSISTENCY")
    R.w("  Standard deviation of key metrics across seeds:")

    rows = _q(db, """
        SELECT archetype,
               vpip_count*100.0/hands_dealt AS vpip,
               pfr_count*100.0/hands_dealt AS pfr,
               final_stack
        FROM agent_stats
    """)
    by_arch = defaultdict(lambda: {"vpip": [], "pfr": [], "stack": []})
    for r in rows:
        by_arch[r['archetype']]["vpip"].append(r['vpip'])
        by_arch[r['archetype']]["pfr"].append(r['pfr'])
        by_arch[r['archetype']]["stack"].append(r['final_stack'])

    data = []
    for arch in sorted(by_arch):
        d = by_arch[arch]
        data.append([arch,
                      f"{sum(d['vpip'])/len(d['vpip']):.1f} +/- {_stddev(d['vpip']):.1f}",
                      f"{sum(d['pfr'])/len(d['pfr']):.1f} +/- {_stddev(d['pfr']):.1f}",
                      f"{sum(d['stack'])/len(d['stack']):.0f} +/- {_stddev(d['stack']):.0f}"])
    R.table(["Archetype", "VPIP%", "PFR%", "Stack"], data, [20, 18, 18, 18])


# ---------------------------------------------------------------------------
# Section 22: Bet sizing analysis
# ---------------------------------------------------------------------------

def s22_bet_sizing(db, R):
    R.header(22, "BET SIZING ANALYSIS")
    rows = _q(db, """
        SELECT ag.archetype, a.betting_round, a.action_type,
               AVG(a.amount) AS mean_amt, COUNT(*) AS n
        FROM actions a
        JOIN agent_stats ag ON a.run_id = ag.run_id AND a.seat = ag.seat
        WHERE a.action_type IN ('bet', 'raise', 'call') AND a.amount > 0
        GROUP BY ag.archetype, a.betting_round, a.action_type
        ORDER BY ag.archetype, a.betting_round
    """)
    by_arch = defaultdict(list)
    for r in rows:
        by_arch[r['archetype']].append(r)

    for arch in sorted(by_arch):
        R.w(f"\n  {arch}:")
        for r in by_arch[arch]:
            R.w(f"    {r['betting_round']:<10} {r['action_type']:<8} mean_amt={r['mean_amt']:.2f}  n={r['n']:,}")


# ---------------------------------------------------------------------------
# Section 23: Bluff success rate
# ---------------------------------------------------------------------------

def s23_bluff_success(db, R):
    R.header(23, "BLUFF SUCCESS RATE (bets/raises that won without showdown)")
    R.w("  Approximation: for each archetype, fraction of hands where they")
    R.w("  bet or raised AND won the pot via walkover (opponent(s) folded).")

    rows = _q(db, """
        SELECT ag.archetype,
               COUNT(DISTINCT a.run_id || '-' || a.hand_id) AS hands_with_aggression,
               SUM(CASE WHEN h.walkover_winner = a.seat THEN 1 ELSE 0 END) AS walkover_wins
        FROM actions a
        JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
        JOIN agent_stats ag ON a.run_id = ag.run_id AND a.seat = ag.seat
        WHERE a.action_type IN ('bet', 'raise')
        GROUP BY ag.archetype ORDER BY ag.archetype
    """)
    data = []
    for r in rows:
        rate = _pct(r['walkover_wins'], r['hands_with_aggression'])
        data.append([r['archetype'], f"{r['hands_with_aggression']:,}",
                      f"{r['walkover_wins']:,}", f"{rate:.1f}%"])
    R.table(["Archetype", "HandsAggr", "WalkoverWins", "FoldEquity%"],
            data, [20, 14, 14, 14])


# ---------------------------------------------------------------------------
# Section 24: Rebuy analysis
# ---------------------------------------------------------------------------

def s24_rebuys(db, R):
    R.header(24, "REBUY ANALYSIS")
    rows = _q(db, """
        SELECT archetype,
               SUM(rebuys) AS total_rb, AVG(rebuys) AS mean_rb,
               MIN(rebuys) AS min_rb, MAX(rebuys) AS max_rb,
               COUNT(*) AS seeds
        FROM agent_stats GROUP BY archetype ORDER BY total_rb DESC
    """)
    data = []
    for r in rows:
        data.append([r['archetype'], f"{r['total_rb']}", f"{r['mean_rb']:.1f}",
                      f"{r['min_rb']}", f"{r['max_rb']}"])
    R.table(["Archetype", "TotalRB", "MeanRB", "MinRB", "MaxRB"],
            data, [20, 10, 10, 8, 8])


# ---------------------------------------------------------------------------
# Section 25: Sanity checks
# ---------------------------------------------------------------------------

def s25_sanity(db, R):
    R.header(25, "SANITY CHECKS")

    # Chip conservation
    rows = _q(db, """
        SELECT run_id, SUM(final_stack) AS ts, SUM(rebuys) AS tr,
               SUM(final_stack) - (SUM(rebuys)+8)*200 AS delta
        FROM agent_stats GROUP BY run_id
    """)
    bad = [r for r in rows if r['delta'] != 0]
    R.w(f"  Chip conservation:   {'ALL OK' if not bad else f'{len(bad)} FAILURES'}")

    # Orphans
    orphans = _q1(db, """
        SELECT COUNT(*) AS c FROM actions a
        LEFT JOIN hands h ON a.run_id=h.run_id AND a.hand_id=h.hand_id
        WHERE h.hand_id IS NULL
    """)['c']
    R.w(f"  Orphan actions:      {orphans} {'(OK)' if orphans == 0 else '(PROBLEM)'}")

    # Trust completeness
    sample = _q1(db, "SELECT COUNT(*) AS c FROM trust_snapshots WHERE run_id=1 AND hand_id=1")
    R.w(f"  Trust rows/hand:     {sample['c']} (expected 56)")

    # Action count per hand
    aph = _q1(db, "SELECT AVG(cnt) AS avg_aph FROM (SELECT COUNT(*) AS cnt FROM actions GROUP BY run_id, hand_id)")
    R.w(f"  Mean actions/hand:   {aph['avg_aph']:.1f}")

    # Showdown participants
    spp = _q1(db, "SELECT AVG(cnt) AS avg FROM (SELECT COUNT(*) AS cnt FROM showdowns GROUP BY run_id, hand_id)")
    R.w(f"  Mean SD participants:{spp['avg']:.1f}")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

ALL_SECTIONS = [
    ("overview",           s01_overview),
    ("economics",          s02_economics),
    ("behavior",           s03_behavior),
    ("action_freq",        s04_action_freq),
    ("street_aggression",  s05_street_aggression),
    ("position",           s06_position),
    ("showdown",           s07_showdown),
    ("walkover",           s08_walkover),
    ("pots",               s09_pots),
    ("trust_matrix",       s10_trust_matrix),
    ("entropy_matrix",     s11_entropy_matrix),
    ("identification",     s12_identification),
    ("trust_convergence",  s13_trust_convergence),
    ("entropy_convergence",s14_entropy_convergence),
    ("predator",           s15_predator),
    ("judge",              s16_judge),
    ("mirror",             s17_mirror),
    ("temporal",           s18_temporal),
    ("h2h",                s19_h2h),
    ("trust_profit",       s20_trust_profit),
    ("consistency",        s21_consistency),
    ("bet_sizing",         s22_bet_sizing),
    ("bluff_success",      s23_bluff_success),
    ("rebuys",             s24_rebuys),
    ("sanity",             s25_sanity),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", required=True, help="Path to runs.sqlite")
    parser.add_argument("--out", default="deep_analysis_report.txt",
                        help="Output log file (default: deep_analysis_report.txt)")
    parser.add_argument("--section", default=None,
                        choices=[name for name, _ in ALL_SECTIONS] + ["all"],
                        help="Run only one section (default: all)")
    args = parser.parse_args(argv)

    db = _connect(args.db)
    R = Report(out_path=args.out)

    R.w("=" * 78)
    R.w("  POKER TRUST SIMULATION — DEEP ANALYSIS REPORT")
    R.w(f"  Database: {args.db}")
    R.w("=" * 78)

    sections = ALL_SECTIONS if args.section in (None, "all") else [(args.section, dict(ALL_SECTIONS)[args.section])]

    for name, fn in sections:
        try:
            fn(db, R)
        except Exception as e:
            R.w(f"\n  ERROR in section {name}: {e}")

    R.w("\n" + "=" * 78)
    R.w("  END OF REPORT")
    R.w("=" * 78)

    R.save()
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
