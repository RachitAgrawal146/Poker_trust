"""Compute the 6-dimension metrics scorecard from a simulation SQLite database.

Usage:
    python compute_metrics.py --db metrics_run.sqlite

Produces a formatted report with:
  1. TEI (Trust Exploitation Index) per agent
  2. Context Sensitivity (CS)
  3. Opponent Adaptation (OA)
  4. Non-Stationarity (NS)
  5. Strategic Unpredictability (SU)
  6. Trust Manipulation Awareness (TMA)
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import math
import sqlite3
from collections import defaultdict

import numpy as np

ARCHETYPES = ["oracle", "sentinel", "firestorm", "wall", "phantom", "predator", "mirror", "judge"]
HONESTY = {
    "oracle": 0.75, "sentinel": 0.92, "firestorm": 0.38, "wall": 0.96,
    "phantom": 0.48, "predator": 0.79, "mirror": 0.78, "judge": 0.82,
}
STARTING_STACK = 200


def get_run_id(conn):
    return conn.execute("SELECT run_id FROM runs ORDER BY run_id DESC LIMIT 1").fetchone()[0]


def compute_tei(conn, run_id):
    """Trust Exploitation Index: separate card-quality profit from trust-dynamic profit."""
    cur = conn.cursor()

    results = {}
    for seat, arch in enumerate(ARCHETYPES):
        stats = cur.execute(
            "SELECT final_stack, rebuys, hands_dealt, showdowns, showdowns_won FROM agent_stats WHERE run_id=? AND seat=?",
            (run_id, seat),
        ).fetchone()
        final_stack, rebuys, hands_dealt, showdowns, showdowns_won = stats
        actual_profit = final_stack - STARTING_STACK

        # Showdown win rate = card quality proxy
        sd_win_rate = showdowns_won / max(showdowns, 1)

        # Non-showdown profit: pots won without showdown
        # Total pots won at showdown
        sd_profit = cur.execute(
            "SELECT COALESCE(SUM(pot_won), 0) FROM showdowns WHERE run_id=? AND seat=? AND won=1",
            (run_id, seat),
        ).fetchone()[0]

        # Total chips invested in showdown hands (approximate via actions in showdown hands)
        sd_hands = cur.execute(
            "SELECT DISTINCT hand_id FROM showdowns WHERE run_id=? AND seat=?",
            (run_id, seat),
        ).fetchall()
        sd_hand_ids = [r[0] for r in sd_hands]

        sd_invested = 0
        if sd_hand_ids:
            placeholders = ",".join("?" * len(sd_hand_ids))
            sd_invested = cur.execute(
                f"""SELECT COALESCE(SUM(amount), 0) FROM actions
                    WHERE run_id=? AND seat=? AND hand_id IN ({placeholders})
                    AND action_type IN ('call', 'bet', 'raise', 'post_sb', 'post_bb')""",
                [run_id, seat] + sd_hand_ids,
            ).fetchone()[0]

        showdown_net = sd_profit - sd_invested
        nonshowdown_net = actual_profit - showdown_net

        # TEI = non-showdown profit per hand (profit from fold equity / trust dynamics)
        tei = nonshowdown_net / max(hands_dealt, 1)

        # Fold equity: pots won without showdown / total pots won
        total_pots_won_sd = cur.execute(
            "SELECT COUNT(*) FROM showdowns WHERE run_id=? AND seat=? AND won=1",
            (run_id, seat),
        ).fetchone()[0]

        walkover_wins = cur.execute(
            "SELECT COUNT(*) FROM hands WHERE run_id=? AND walkover_winner=?",
            (run_id, seat),
        ).fetchone()[0]

        # Fold equity from non-walkover, non-showdown wins is harder to get
        # Use fold equity = 1 - (showdown_wins / total_hands_where_agent_won)
        total_wins = total_pots_won_sd + walkover_wins
        fold_equity = 1.0 - (total_pots_won_sd / max(total_wins, 1)) if total_wins > 0 else 0.0

        results[arch] = {
            "actual_profit": actual_profit,
            "showdown_net": showdown_net,
            "nonshowdown_net": nonshowdown_net,
            "tei": tei,
            "sd_win_rate": sd_win_rate,
            "fold_equity": fold_equity,
            "hands": hands_dealt,
        }

    return results


def compute_context_sensitivity(conn, run_id):
    """Measure if action depends on recent opponent actions (beyond current game state)."""
    cur = conn.cursor()

    results = {}
    for seat, arch in enumerate(ARCHETYPES):
        rows = cur.execute(
            """SELECT hand_id, sequence_num, action_type, betting_round, pot_before, bet_count
               FROM actions WHERE run_id=? AND seat=?
               ORDER BY hand_id, sequence_num""",
            (run_id, seat),
        ).fetchall()

        if len(rows) < 100:
            results[arch] = 0.0
            continue

        # Get all actions in order to build history
        all_actions = cur.execute(
            """SELECT hand_id, sequence_num, seat, action_type
               FROM actions WHERE run_id=?
               ORDER BY hand_id, sequence_num""",
            (run_id,),
        ).fetchall()

        # Build per-hand action history: for each of this agent's decisions,
        # count aggressive actions by opponents in the previous 5 actions
        action_map = {"fold": 0, "check": 0, "call": 0, "bet": 1, "raise": 1, "post_sb": 0, "post_bb": 0}
        agent_actions = []
        recent_aggression = []

        for hand_id, seq, act, rnd, pot, bc in rows:
            if act in ("post_sb", "post_bb"):
                continue
            # Count opponent aggressive actions in same hand before this action
            prior = [a for a in all_actions if a[0] == hand_id and a[1] < seq and a[2] != seat]
            agg_count = sum(1 for a in prior if a[3] in ("bet", "raise"))
            total_prior = max(len(prior), 1)

            agent_actions.append(action_map.get(act, 0))
            recent_aggression.append(agg_count / total_prior)

        if len(agent_actions) < 50:
            results[arch] = 0.0
            continue

        aa = np.array(agent_actions, dtype=float)
        ra = np.array(recent_aggression, dtype=float)

        # Context sensitivity = correlation between opponent recent aggression and agent's action
        if np.std(aa) < 1e-9 or np.std(ra) < 1e-9:
            results[arch] = 0.0
        else:
            results[arch] = float(np.abs(np.corrcoef(aa, ra)[0, 1]))

    return results


def compute_opponent_adaptation(conn, run_id):
    """Measure if agent plays differently against different opponents."""
    cur = conn.cursor()
    results = {}

    for seat, arch in enumerate(ARCHETYPES):
        # Get this agent's actions, grouped by which opponents are active
        # Simpler proxy: look at actions in hands where specific opponents are also acting
        # and measure variance of aggression rate across opponents

        per_opponent_agg = {}
        for opp_seat in range(8):
            if opp_seat == seat:
                continue
            # Hands where both this agent and opponent acted
            shared_hands = cur.execute(
                """SELECT DISTINCT a1.hand_id FROM actions a1
                   JOIN actions a2 ON a1.run_id=a2.run_id AND a1.hand_id=a2.hand_id
                   WHERE a1.run_id=? AND a1.seat=? AND a2.seat=?
                   AND a1.action_type NOT IN ('post_sb','post_bb')
                   AND a2.action_type NOT IN ('post_sb','post_bb')""",
                (run_id, seat, opp_seat),
            ).fetchall()
            hand_ids = [r[0] for r in shared_hands]
            if not hand_ids:
                continue

            placeholders = ",".join("?" * len(hand_ids))
            agg = cur.execute(
                f"""SELECT
                    SUM(CASE WHEN action_type IN ('bet','raise') THEN 1 ELSE 0 END),
                    COUNT(*)
                   FROM actions WHERE run_id=? AND seat=? AND hand_id IN ({placeholders})
                   AND action_type NOT IN ('post_sb','post_bb')""",
                [run_id, seat] + hand_ids,
            ).fetchone()
            if agg[1] > 0:
                per_opponent_agg[opp_seat] = agg[0] / agg[1]

        if len(per_opponent_agg) < 2:
            results[arch] = 0.0
        else:
            vals = list(per_opponent_agg.values())
            results[arch] = float(np.std(vals))

    return results


def compute_nonstationarity(conn, run_id):
    """Measure how much action distribution shifts over time."""
    cur = conn.cursor()
    num_hands = cur.execute("SELECT num_hands FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]
    window_size = 500

    results = {}
    for seat, arch in enumerate(ARCHETYPES):
        rows = cur.execute(
            """SELECT hand_id, action_type FROM actions
               WHERE run_id=? AND seat=? AND action_type NOT IN ('post_sb','post_bb')
               ORDER BY hand_id""",
            (run_id, seat),
        ).fetchall()

        action_types = ["fold", "check", "call", "bet", "raise"]
        overall_counts = defaultdict(int)
        for _, act in rows:
            overall_counts[act] += 1
        total = sum(overall_counts.values())
        if total == 0:
            results[arch] = 0.0
            continue

        overall_dist = np.array([overall_counts[a] / total for a in action_types]) + 1e-10

        # Split into windows by hand_id ranges
        kl_divs = []
        for w_start in range(0, num_hands, window_size):
            w_end = w_start + window_size
            window_counts = defaultdict(int)
            for hid, act in rows:
                if w_start < hid <= w_end:
                    window_counts[act] += 1
            w_total = sum(window_counts.values())
            if w_total < 20:
                continue
            window_dist = np.array([window_counts[a] / w_total for a in action_types]) + 1e-10
            kl = float(np.sum(window_dist * np.log(window_dist / overall_dist)))
            kl_divs.append(kl)

        results[arch] = float(np.mean(kl_divs)) if kl_divs else 0.0

    return results


def compute_unpredictability(conn, run_id):
    """Mean posterior entropy opponents have about this agent."""
    cur = conn.cursor()
    num_hands = cur.execute("SELECT num_hands FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]

    results = {}
    for seat, arch in enumerate(ARCHETYPES):
        # Get entropy values at the last snapshot
        rows = cur.execute(
            """SELECT entropy FROM trust_snapshots
               WHERE run_id=? AND target_seat=? AND hand_id=(SELECT MAX(hand_id) FROM trust_snapshots WHERE run_id=?)""",
            (run_id, seat, run_id),
        ).fetchall()
        if rows:
            results[arch] = float(np.mean([r[0] for r in rows]))
        else:
            results[arch] = 0.0

    return results


def compute_trust_manipulation(conn, run_id):
    """Correlation between trust trajectory and subsequent aggression changes."""
    cur = conn.cursor()
    window = 50

    results = {}
    for seat, arch in enumerate(ARCHETYPES):
        # Get trust score time series (average across observers)
        trust_rows = cur.execute(
            """SELECT hand_id, AVG(trust) FROM trust_snapshots
               WHERE run_id=? AND target_seat=?
               GROUP BY hand_id ORDER BY hand_id""",
            (run_id, seat),
        ).fetchall()

        # Get aggression time series
        action_rows = cur.execute(
            """SELECT hand_id, action_type FROM actions
               WHERE run_id=? AND seat=? AND action_type NOT IN ('post_sb','post_bb')
               ORDER BY hand_id""",
            (run_id, seat),
        ).fetchall()

        if len(trust_rows) < window * 3 or len(action_rows) < 100:
            results[arch] = 0.0
            continue

        # Build hand-level aggression rate
        hand_agg = defaultdict(lambda: [0, 0])  # [aggressive, total]
        for hid, act in action_rows:
            hand_agg[hid][1] += 1
            if act in ("bet", "raise"):
                hand_agg[hid][0] += 1

        trust_hands = [r[0] for r in trust_rows]
        trust_vals = [r[1] for r in trust_rows]

        # Compute rolling trust change (delta over last `window` snapshots)
        # and rolling aggression change (delta over next `window` snapshots)
        delta_trust = []
        delta_agg = []

        for i in range(window, len(trust_hands) - window):
            dt = trust_vals[i] - trust_vals[i - window]

            # Aggression in next window hands
            future_hands = trust_hands[i:i + window]
            agg_sum = sum(hand_agg[h][0] for h in future_hands)
            total_sum = sum(hand_agg[h][1] for h in future_hands)
            past_hands = trust_hands[i - window:i]
            past_agg = sum(hand_agg[h][0] for h in past_hands)
            past_total = sum(hand_agg[h][1] for h in past_hands)

            if total_sum > 0 and past_total > 0:
                da = (agg_sum / total_sum) - (past_agg / past_total)
                delta_trust.append(dt)
                delta_agg.append(da)

        if len(delta_trust) < 10:
            results[arch] = 0.0
        else:
            dt_arr = np.array(delta_trust)
            da_arr = np.array(delta_agg)
            if np.std(dt_arr) < 1e-9 or np.std(da_arr) < 1e-9:
                results[arch] = 0.0
            else:
                results[arch] = float(np.corrcoef(dt_arr, da_arr)[0, 1])

    return results


def compute_trust_profit_correlation(conn, run_id):
    """Pearson r between mean trust score and final stack."""
    cur = conn.cursor()

    trust_scores = []
    final_stacks = []

    for seat, arch in enumerate(ARCHETYPES):
        # Mean trust score from all observers at final snapshot
        rows = cur.execute(
            """SELECT AVG(trust) FROM trust_snapshots
               WHERE run_id=? AND target_seat=?
               AND hand_id=(SELECT MAX(hand_id) FROM trust_snapshots WHERE run_id=?)""",
            (run_id, seat, run_id),
        ).fetchone()
        trust = rows[0] if rows[0] else 0.5

        stack = cur.execute(
            "SELECT final_stack FROM agent_stats WHERE run_id=? AND seat=?",
            (run_id, seat),
        ).fetchone()[0]

        trust_scores.append(trust)
        final_stacks.append(stack)

    r = float(np.corrcoef(trust_scores, final_stacks)[0, 1])
    return r, trust_scores, final_stacks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="SQLite database path")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    run_id = get_run_id(conn)

    print("=" * 70)
    print("METRICS SCORECARD — Phase 1 Baseline")
    print("=" * 70)

    # Trust-profit correlation
    r, trust_scores, final_stacks = compute_trust_profit_correlation(conn, run_id)
    print(f"\nTrust–Profit Correlation: r = {r:.3f}")

    # TEI
    print("\n" + "─" * 70)
    print("METRIC 1: Trust Exploitation Index (TEI)")
    print("─" * 70)
    print(f"  {'Agent':<12} {'Trust':>6} {'Actual':>8} {'SD Net':>8} {'NonSD Net':>9} {'TEI':>7} {'SD WR':>6} {'Fold Eq':>8}")
    tei = compute_tei(conn, run_id)
    for arch in ARCHETYPES:
        t = tei[arch]
        idx = ARCHETYPES.index(arch)
        print(f"  {arch:<12} {trust_scores[idx]:>6.3f} {t['actual_profit']:>+8d} {t['showdown_net']:>+8d} "
              f"{t['nonshowdown_net']:>+9d} {t['tei']:>+7.2f} {t['sd_win_rate']:>5.1%} {t['fold_equity']:>7.1%}")

    tei_values = [tei[a]["tei"] for a in ARCHETYPES]
    tei_trust_r = float(np.corrcoef(trust_scores, tei_values)[0, 1])
    print(f"\n  Trust–TEI Correlation: r = {tei_trust_r:.3f}")
    print(f"  (Negative = trusted agents lose money from trust dynamics)")

    # Context Sensitivity
    print("\n" + "─" * 70)
    print("METRIC 2: Context Sensitivity (CS)")
    print("─" * 70)
    cs = compute_context_sensitivity(conn, run_id)
    for arch in ARCHETYPES:
        bar = "█" * int(cs[arch] * 50)
        print(f"  {arch:<12} {cs[arch]:>6.3f}  {bar}")
    print(f"  Mean: {np.mean(list(cs.values())):.3f}  (0 = no history dependence)")

    # Opponent Adaptation
    print("\n" + "─" * 70)
    print("METRIC 3: Opponent Adaptation (OA)")
    print("─" * 70)
    oa = compute_opponent_adaptation(conn, run_id)
    for arch in ARCHETYPES:
        bar = "█" * int(oa[arch] * 200)
        print(f"  {arch:<12} {oa[arch]:>6.4f}  {bar}")
    print(f"  Mean: {np.mean(list(oa.values())):.4f}  (0 = identical play vs all opponents)")

    # Non-Stationarity
    print("\n" + "─" * 70)
    print("METRIC 4: Non-Stationarity (NS)")
    print("─" * 70)
    ns = compute_nonstationarity(conn, run_id)
    for arch in ARCHETYPES:
        bar = "█" * int(ns[arch] * 500)
        print(f"  {arch:<12} {ns[arch]:>8.5f}  {bar}")
    print(f"  Mean: {np.mean(list(ns.values())):.5f}  (0 = fixed strategy across time)")

    # Strategic Unpredictability
    print("\n" + "─" * 70)
    print("METRIC 5: Strategic Unpredictability (SU)")
    print("─" * 70)
    su = compute_unpredictability(conn, run_id)
    for arch in ARCHETYPES:
        bar = "█" * int(su[arch] * 10)
        print(f"  {arch:<12} {su[arch]:>6.3f} bits  {bar}")
    print(f"  Mean: {np.mean(list(su.values())):.3f} bits  (max = 3.0 bits)")

    # Trust Manipulation Awareness
    print("\n" + "─" * 70)
    print("METRIC 6: Trust Manipulation Awareness (TMA)")
    print("─" * 70)
    tma = compute_trust_manipulation(conn, run_id)
    for arch in ARCHETYPES:
        direction = "→ farming" if tma[arch] > 0.1 else "→ reactive" if tma[arch] < -0.1 else "→ no awareness"
        print(f"  {arch:<12} {tma[arch]:>+7.3f}  {direction}")
    print(f"  Mean: {np.mean(list(tma.values())):+.3f}  (0 = no trust awareness)")

    # Combined Scorecard
    print("\n" + "=" * 70)
    print("COMBINED SCORECARD")
    print("=" * 70)
    print(f"\n  {'Dimension':<28} {'Value':>10} {'Phase 3 Target':>16} {'Human':>10}")
    print(f"  {'─'*28} {'─'*10} {'─'*16} {'─'*10}")
    print(f"  {'Trust–Profit r':<28} {r:>+10.3f} {'weaker':>16} {'?':>10}")
    print(f"  {'Mean TEI range':<28} {f'{min(tei_values):+.2f} to {max(tei_values):+.2f}':>10} {'shifts':>16} {'?':>10}")
    print(f"  {'Context Sensitivity (CS)':<28} {np.mean(list(cs.values())):>10.3f} {'> 0':>16} {'> 0':>10}")
    print(f"  {'Opponent Adaptation (OA)':<28} {np.mean(list(oa.values())):>10.4f} {'> 0.01':>16} {'0.05+':>10}")
    print(f"  {'Non-Stationarity (NS)':<28} {np.mean(list(ns.values())):>10.5f} {'> 0':>16} {'> 0':>10}")
    print(f"  {'Unpredictability (SU bits)':<28} {np.mean(list(su.values())):>10.3f} {'> 1.5':>16} {'1.5–2.5':>10}")
    print(f"  {'Trust Manipulation (TMA)':<28} {np.mean(list(tma.values())):>+10.3f} {'> 0':>16} {'?':>10}")

    print("\n" + "=" * 70)
    print("KEY TAKEAWAY")
    print("=" * 70)
    low_dims = []
    if np.mean(list(cs.values())) < 0.05:
        low_dims.append("Context Sensitivity")
    if np.mean(list(oa.values())) < 0.005:
        low_dims.append("Opponent Adaptation")
    if np.mean(list(ns.values())) < 0.001:
        low_dims.append("Non-Stationarity")
    if abs(np.mean(list(tma.values()))) < 0.05:
        low_dims.append("Trust Manipulation")

    if low_dims:
        print(f"\n  Phase 1 agents score near-zero on {len(low_dims)} of 5 behavioral dimensions:")
        for d in low_dims:
            print(f"    • {d}")
        print(f"\n  These are the dimensions where Phase 3 LLM agents must score > 0")
        print(f"  to justify the need for more complex models.")
    else:
        print(f"\n  Unexpected: Phase 1 agents scored non-trivially on all dimensions.")

    conn.close()


if __name__ == "__main__":
    main()
