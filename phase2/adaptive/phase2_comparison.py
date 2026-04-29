"""
Phase 1 vs Phase 2 (adaptive) scorecard.

Reads two SQLite databases (one per phase), reuses compute_metrics.py for the
six behavioral dimensions, and emits seven tables (mean +/- std across seeds):

  Table 0 -- Headline scorecard (P1 vs P2, 6 metrics + r)
  Table 1 -- Behavioral fingerprints (VPIP, PFR, AF per archetype, P1 vs P2)
  Table 2 -- Economic ordering (final stacks, rebuys, rank shifts)
  Table 3 -- Trust-profit r per seed and aggregate
  Table 4 -- Parameter trajectories (cycles, accept rate, most-moved metric)
  Table 5 -- Adaptation success (last-1000-hands profit + per-opponent deltas)
  Table 6 -- Aberration Index (L2 drift in normalized VPIP/PFR/AF space)

Usage:
    python3 phase2/adaptive/phase2_comparison.py \\
        --phase1-db runs_phase1_ref.sqlite \\
        --phase2-db runs_phase2_adaptive.sqlite \\
        --trajectories phase2/adaptive/param_trajectories.json \\
        --optlog phase2/adaptive/optimization_log.json \\
        --output reports/phase2_scorecard.txt
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from compute_metrics import (
    compute_context_sensitivity,
    compute_nonstationarity,
    compute_opponent_adaptation,
    compute_tei,
    compute_trust_manipulation,
    compute_trust_profit_correlation,
    compute_unpredictability,
)

ARCHETYPES = [
    "oracle", "sentinel", "firestorm", "wall",
    "phantom", "predator", "mirror", "judge",
]
STARTING_STACK = 200
LAST_WINDOW_HANDS = 1000


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def list_run_ids(conn: sqlite3.Connection) -> List[int]:
    return [r[0] for r in conn.execute(
        "SELECT run_id FROM runs ORDER BY run_id"
    ).fetchall()]


def get_seed(conn: sqlite3.Connection, run_id: int) -> int:
    return conn.execute(
        "SELECT seed FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()[0]


def get_num_hands(conn: sqlite3.Connection, run_id: int) -> int:
    return conn.execute(
        "SELECT num_hands FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()[0]


def fmt_meanstd(vals: List[float], digits: int = 3) -> str:
    if not vals:
        return "n/a"
    if len(vals) == 1:
        return f"{vals[0]:+.{digits}f}"
    return f"{np.mean(vals):+.{digits}f} +/- {np.std(vals):.{digits}f}"


def fmt_meanstd_int(vals: List[float]) -> str:
    if not vals:
        return "n/a"
    if len(vals) == 1:
        return f"{int(round(vals[0]))}"
    return f"{int(round(np.mean(vals)))} +/- {int(round(np.std(vals)))}"


# ---------------------------------------------------------------------------
# Per-archetype behavioral stats (VPIP / PFR / AF) per seed
# ---------------------------------------------------------------------------

def compute_behavioral_fingerprints(
    conn: sqlite3.Connection, run_id: int
) -> Dict[str, Dict[str, float]]:
    """Return per-archetype {VPIP, PFR, AF} for a single run."""
    cur = conn.cursor()
    out: Dict[str, Dict[str, float]] = {}
    for seat, arch in enumerate(ARCHETYPES):
        row = cur.execute(
            """SELECT hands_dealt, vpip_count, pfr_count, bets, raises,
                      calls, folds, checks
               FROM agent_stats WHERE run_id = ? AND seat = ?""",
            (run_id, seat),
        ).fetchone()
        if not row:
            out[arch] = {"vpip": 0.0, "pfr": 0.0, "af": 0.0}
            continue
        hd, vp, pf, bets, raises, calls, folds, checks = row
        hd = max(hd, 1)
        vpip = vp / hd
        pfr = pf / hd
        af = (bets + raises) / max(calls, 1)
        out[arch] = {"vpip": vpip, "pfr": pfr, "af": af}
    return out


def compute_final_stacks(
    conn: sqlite3.Connection, run_id: int
) -> Dict[str, Dict[str, float]]:
    """Per-archetype {final_stack, rebuys, profit} for a single run."""
    cur = conn.cursor()
    out: Dict[str, Dict[str, float]] = {}
    for seat, arch in enumerate(ARCHETYPES):
        row = cur.execute(
            "SELECT final_stack, rebuys FROM agent_stats "
            "WHERE run_id = ? AND seat = ?",
            (run_id, seat),
        ).fetchone()
        if not row:
            out[arch] = {"final_stack": 0.0, "rebuys": 0.0, "profit": 0.0}
            continue
        fs, rb = row
        # rebuy-adjusted profit
        profit = fs - STARTING_STACK - rb * STARTING_STACK
        out[arch] = {"final_stack": float(fs), "rebuys": float(rb),
                     "profit": float(profit)}
    return out


def compute_last_window_profit(
    conn: sqlite3.Connection, run_id: int, window: int = LAST_WINDOW_HANDS
) -> Dict[str, float]:
    """Per-archetype net chip flow during the final ``window`` hands.

    Approximated from the actions table: profit = chips won (pots collected)
    minus chips invested in those hands. We get pots-won via showdowns +
    walkovers, and invested via the actions table.
    """
    cur = conn.cursor()
    num_hands = get_num_hands(conn, run_id)
    cutoff = max(num_hands - window, 0)

    out: Dict[str, float] = {}
    for seat, arch in enumerate(ARCHETYPES):
        invested = cur.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM actions
               WHERE run_id = ? AND seat = ? AND hand_id > ?
               AND action_type IN ('call','bet','raise','post_sb','post_bb')""",
            (run_id, seat, cutoff),
        ).fetchone()[0]
        sd_won = cur.execute(
            """SELECT COALESCE(SUM(pot_won), 0) FROM showdowns
               WHERE run_id = ? AND seat = ? AND won = 1 AND hand_id > ?""",
            (run_id, seat, cutoff),
        ).fetchone()[0]
        walk_won = cur.execute(
            """SELECT COALESCE(SUM(final_pot), 0) FROM hands
               WHERE run_id = ? AND walkover_winner = ? AND hand_id > ?""",
            (run_id, seat, cutoff),
        ).fetchone()[0]
        out[arch] = float(sd_won + walk_won - invested)
    return out


def compute_opponent_profit_matrix(
    conn: sqlite3.Connection, run_id: int
) -> Dict[str, Dict[str, float]]:
    """For each (A, B) pair: chips A invested in hands B won at showdown.

    This approximates "chips A leaks to B". Returns a per-archetype map
    {arch_A: {arch_B: chips_invested_in_B_wins}}.
    """
    cur = conn.cursor()
    matrix: Dict[str, Dict[str, float]] = {a: {b: 0.0 for b in ARCHETYPES}
                                           for a in ARCHETYPES}
    rows = cur.execute(
        """SELECT s.hand_id, s.seat AS winner_seat,
                  a.seat AS investor_seat, a.amount
           FROM showdowns s
           JOIN actions a ON a.run_id = s.run_id AND a.hand_id = s.hand_id
           WHERE s.run_id = ? AND s.won = 1
             AND a.action_type IN ('call','bet','raise','post_sb','post_bb')""",
        (run_id,),
    ).fetchall()
    for _hand_id, winner_seat, investor_seat, amount in rows:
        if investor_seat == winner_seat:
            continue
        if 0 <= investor_seat < 8 and 0 <= winner_seat < 8:
            matrix[ARCHETYPES[investor_seat]][ARCHETYPES[winner_seat]] += amount
    return matrix


# ---------------------------------------------------------------------------
# Trajectory + opt-log analysis
# ---------------------------------------------------------------------------

def summarize_optlog(optlog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Aggregate the per-cycle log into per-archetype stats across seeds.

    Returns: {archetype: {cycles, accepted, rejected, accept_rate,
                          most_moved: (round, metric, cumulative_signed_delta)}}
    """
    cycles_by: Dict[str, int] = defaultdict(int)
    accepted_by: Dict[str, int] = defaultdict(int)
    delta_sum: Dict[str, Dict[Tuple[str, str], float]] = defaultdict(
        lambda: defaultdict(float)
    )

    for seed_key, entries in optlog.items():
        for e in entries:
            arch = e.get("archetype") or "unknown"
            cycles_by[arch] += 1
            if e.get("accepted"):
                accepted_by[arch] += 1
                rnd = e.get("round")
                metric = e.get("metric")
                old_v = e.get("old_value", 0.0)
                new_v = e.get("new_value", 0.0)
                if rnd and metric:
                    delta_sum[arch][(rnd, metric)] += float(new_v - old_v)

    out: Dict[str, Dict[str, Any]] = {}
    archetypes = set(cycles_by.keys()) | set(accepted_by.keys())
    for arch in sorted(archetypes):
        cycles = cycles_by[arch]
        accepted = accepted_by[arch]
        rejected = cycles - accepted
        rate = accepted / cycles if cycles else 0.0
        most: Tuple[str, str, float] = ("-", "-", 0.0)
        if delta_sum[arch]:
            (rnd, metric), val = max(
                delta_sum[arch].items(), key=lambda kv: abs(kv[1])
            )
            most = (rnd, metric, val)
        out[arch] = {
            "cycles": cycles,
            "accepted": accepted,
            "rejected": rejected,
            "accept_rate": rate,
            "most_moved": most,
        }
    return out


def total_param_movement(trajectories: Dict[str, Any]) -> Dict[str, float]:
    """Per-archetype total L1 distance traveled (initial -> final params).

    Averaged across seeds. Useful for "how far did each archetype move?"
    """
    by_arch: Dict[str, List[float]] = defaultdict(list)
    for seed_key, agents in trajectories.items():
        for agent_key, history in agents.items():
            if not history:
                continue
            arch = agent_key.split("_", 2)[-1]
            initial = history[0]["params"]
            final = history[-1]["params"]
            l1 = 0.0
            for rnd, metrics in initial.items():
                if rnd not in final:
                    continue
                for k, v0 in metrics.items():
                    v1 = final[rnd].get(k, v0)
                    l1 += abs(float(v1) - float(v0))
            by_arch[arch].append(l1)
    return {a: float(np.mean(v)) for a, v in by_arch.items()}


# ---------------------------------------------------------------------------
# Per-phase aggregator
# ---------------------------------------------------------------------------

def aggregate_phase(db_path: str) -> Dict[str, Any]:
    """Run every metric over every run in the DB. Returns per-seed lists."""
    conn = sqlite3.connect(db_path)
    try:
        run_ids = list_run_ids(conn)
        if not run_ids:
            raise RuntimeError(f"No runs found in {db_path}")

        per_run: List[Dict[str, Any]] = []
        for rid in run_ids:
            seed = get_seed(conn, rid)
            r, trust_scores, final_stacks = compute_trust_profit_correlation(
                conn, rid
            )
            tei = compute_tei(conn, rid)
            cs = compute_context_sensitivity(conn, rid)
            oa = compute_opponent_adaptation(conn, rid)
            ns = compute_nonstationarity(conn, rid)
            su = compute_unpredictability(conn, rid)
            tma = compute_trust_manipulation(conn, rid)
            beh = compute_behavioral_fingerprints(conn, rid)
            stacks = compute_final_stacks(conn, rid)
            last_window = compute_last_window_profit(conn, rid)
            opp_matrix = compute_opponent_profit_matrix(conn, rid)
            per_run.append({
                "run_id": rid,
                "seed": seed,
                "r": r,
                "trust_scores": trust_scores,
                "final_stacks": final_stacks,
                "tei": tei,
                "cs": cs,
                "oa": oa,
                "ns": ns,
                "su": su,
                "tma": tma,
                "beh": beh,
                "stacks": stacks,
                "last_window": last_window,
                "opp_matrix": opp_matrix,
            })
        return {"db_path": db_path, "runs": per_run}
    finally:
        conn.close()


def collect_per_archetype(
    runs: List[Dict[str, Any]], key: str, sub: str = None
) -> Dict[str, List[float]]:
    """Collect a per-archetype scalar across runs. ``key`` indexes into the
    run dict; ``sub`` (optional) indexes into the per-archetype value."""
    out: Dict[str, List[float]] = {a: [] for a in ARCHETYPES}
    for r in runs:
        d = r[key]
        for arch in ARCHETYPES:
            v = d.get(arch, 0.0)
            if isinstance(v, dict):
                v = v.get(sub, 0.0) if sub else 0.0
            out[arch].append(float(v))
    return out


def collect_scalar(runs: List[Dict[str, Any]], key: str) -> List[float]:
    """Collect a global scalar across runs (e.g. trust-profit r)."""
    return [float(r[key]) for r in runs]


# ---------------------------------------------------------------------------
# Table renderers
# ---------------------------------------------------------------------------

def _section(out: StringIO, title: str) -> None:
    out.write("\n" + "=" * 78 + "\n")
    out.write(title + "\n")
    out.write("=" * 78 + "\n")


def render_table0_headline(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 0 -- HEADLINE SCORECARD (Phase 1 vs Phase 2)")
    out.write(
        "\n  All values are mean +/- std across 3 seeds (42, 137, 256).\n"
    )

    # global r
    r_p1 = collect_scalar(p1["runs"], "r")
    r_p2 = collect_scalar(p2["runs"], "r")

    def mean_per_arch(runs, k, sub=None):
        vals = []
        for r in runs:
            d = r[k]
            for arch in ARCHETYPES:
                v = d.get(arch, 0.0)
                if isinstance(v, dict):
                    v = v.get(sub, 0.0) if sub else 0.0
                vals.append(float(v))
        return vals  # all runs x archs flattened

    def per_run_mean(runs, k, sub=None):
        out_vals = []
        for r in runs:
            d = r[k]
            inner = []
            for arch in ARCHETYPES:
                v = d.get(arch, 0.0)
                if isinstance(v, dict):
                    v = v.get(sub, 0.0) if sub else 0.0
                inner.append(float(v))
            out_vals.append(float(np.mean(inner)))
        return out_vals

    rows: List[Tuple[str, List[float], List[float], int]] = [
        ("Trust-Profit r", r_p1, r_p2, 3),
        ("Mean TEI",       per_run_mean(p1["runs"], "tei", "tei"),
                            per_run_mean(p2["runs"], "tei", "tei"), 3),
        ("Context Sensitivity (CS)",
            per_run_mean(p1["runs"], "cs"),
            per_run_mean(p2["runs"], "cs"), 3),
        ("Opponent Adaptation (OA)",
            per_run_mean(p1["runs"], "oa"),
            per_run_mean(p2["runs"], "oa"), 4),
        ("Non-Stationarity (NS)",
            per_run_mean(p1["runs"], "ns"),
            per_run_mean(p2["runs"], "ns"), 5),
        ("Unpredictability (SU bits)",
            per_run_mean(p1["runs"], "su"),
            per_run_mean(p2["runs"], "su"), 3),
        ("Trust Manipulation (TMA)",
            per_run_mean(p1["runs"], "tma"),
            per_run_mean(p2["runs"], "tma"), 3),
    ]

    out.write(f"\n  {'Metric':<30} {'Phase 1':>20} {'Phase 2':>20} {'Delta':>12}\n")
    out.write("  " + "-" * 30 + " " + "-" * 20 + " " + "-" * 20 + " " + "-" * 12 + "\n")
    for label, v1, v2, dig in rows:
        m1, m2 = float(np.mean(v1)), float(np.mean(v2))
        delta = m2 - m1
        out.write(
            f"  {label:<30} {fmt_meanstd(v1, dig):>20} "
            f"{fmt_meanstd(v2, dig):>20} {delta:>+12.{dig}f}\n"
        )


def render_table1_fingerprints(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 1 -- BEHAVIORAL FINGERPRINTS (VPIP / PFR / AF)")
    out.write(
        "\n  Per-archetype mean +/- std across 3 seeds. AF = (bets+raises)/calls.\n"
    )
    out.write(
        f"\n  {'Archetype':<10} "
        f"{'VPIP P1':>14} {'VPIP P2':>14} "
        f"{'PFR P1':>14} {'PFR P2':>14} "
        f"{'AF P1':>14} {'AF P2':>14}\n"
    )
    out.write("  " + "-" * 10 + (" " + "-" * 14) * 6 + "\n")
    for arch in ARCHETYPES:
        v1 = [r["beh"][arch] for r in p1["runs"]]
        v2 = [r["beh"][arch] for r in p2["runs"]]
        vpip1 = [d["vpip"] for d in v1]
        vpip2 = [d["vpip"] for d in v2]
        pfr1 = [d["pfr"] for d in v1]
        pfr2 = [d["pfr"] for d in v2]
        af1 = [d["af"] for d in v1]
        af2 = [d["af"] for d in v2]
        out.write(
            f"  {arch:<10} "
            f"{fmt_meanstd(vpip1, 3):>14} {fmt_meanstd(vpip2, 3):>14} "
            f"{fmt_meanstd(pfr1, 3):>14} {fmt_meanstd(pfr2, 3):>14} "
            f"{fmt_meanstd(af1, 2):>14} {fmt_meanstd(af2, 2):>14}\n"
        )


def render_table2_economic(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 2 -- ECONOMIC ORDERING (final stacks, rebuys, rank)")
    out.write(
        "\n  Final stack and rebuy count are mean +/- std across 3 seeds.\n"
        "  Rank: 1 = highest mean stack across seeds. Delta = P2 rank minus P1 rank\n"
        "        (negative = climbed, positive = fell).\n"
    )

    def mean_stacks(runs):
        return {arch: float(np.mean([r["stacks"][arch]["final_stack"]
                                      for r in runs])) for arch in ARCHETYPES}

    p1_means = mean_stacks(p1["runs"])
    p2_means = mean_stacks(p2["runs"])
    p1_rank = {a: rank for rank, (a, _) in enumerate(
        sorted(p1_means.items(), key=lambda kv: -kv[1]), start=1)}
    p2_rank = {a: rank for rank, (a, _) in enumerate(
        sorted(p2_means.items(), key=lambda kv: -kv[1]), start=1)}

    out.write(
        f"\n  {'Archetype':<10} "
        f"{'Stack P1':>16} {'Stack P2':>16} "
        f"{'Rebuys P1':>12} {'Rebuys P2':>12} "
        f"{'Rank P1':>8} {'Rank P2':>8} {'dRank':>6}\n"
    )
    out.write("  " + "-" * 10 + (" " + "-" * 16) * 2
              + (" " + "-" * 12) * 2 + (" " + "-" * 8) * 2 + " " + "-" * 6 + "\n")
    for arch in ARCHETYPES:
        s1 = [r["stacks"][arch]["final_stack"] for r in p1["runs"]]
        s2 = [r["stacks"][arch]["final_stack"] for r in p2["runs"]]
        rb1 = [r["stacks"][arch]["rebuys"] for r in p1["runs"]]
        rb2 = [r["stacks"][arch]["rebuys"] for r in p2["runs"]]
        d_rank = p2_rank[arch] - p1_rank[arch]
        out.write(
            f"  {arch:<10} "
            f"{fmt_meanstd_int(s1):>16} {fmt_meanstd_int(s2):>16} "
            f"{fmt_meanstd_int(rb1):>12} {fmt_meanstd_int(rb2):>12} "
            f"{p1_rank[arch]:>8d} {p2_rank[arch]:>8d} {d_rank:>+6d}\n"
        )


def render_table3_trust_profit(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 3 -- TRUST-PROFIT CORRELATION PER SEED")
    out.write(
        "\n  Pearson r between mean trust score (final hand) and final stack,\n"
        "  computed once per seed (n=8 archetypes per correlation).\n"
    )
    p1_runs = sorted(p1["runs"], key=lambda r: r["seed"])
    p2_runs = sorted(p2["runs"], key=lambda r: r["seed"])
    seeds_p1 = [r["seed"] for r in p1_runs]
    seeds_p2 = [r["seed"] for r in p2_runs]
    seeds = sorted(set(seeds_p1) | set(seeds_p2))

    out.write(f"\n  {'Seed':<8} {'Phase 1 r':>14} {'Phase 2 r':>14} {'Delta':>10}\n")
    out.write("  " + "-" * 8 + " " + "-" * 14 + " " + "-" * 14 + " " + "-" * 10 + "\n")
    p1_map = {r["seed"]: r["r"] for r in p1_runs}
    p2_map = {r["seed"]: r["r"] for r in p2_runs}
    p1_vals, p2_vals = [], []
    for s in seeds:
        a = p1_map.get(s)
        b = p2_map.get(s)
        a_str = f"{a:+.3f}" if a is not None else "n/a"
        b_str = f"{b:+.3f}" if b is not None else "n/a"
        delta_str = f"{b - a:+.3f}" if (a is not None and b is not None) else "n/a"
        if a is not None:
            p1_vals.append(a)
        if b is not None:
            p2_vals.append(b)
        out.write(f"  {s:<8d} {a_str:>14} {b_str:>14} {delta_str:>10}\n")
    out.write("  " + "-" * 8 + " " + "-" * 14 + " " + "-" * 14 + " " + "-" * 10 + "\n")
    if p1_vals and p2_vals:
        out.write(
            f"  {'mean':<8} {fmt_meanstd(p1_vals, 3):>14} "
            f"{fmt_meanstd(p2_vals, 3):>14} "
            f"{(np.mean(p2_vals) - np.mean(p1_vals)):>+10.3f}\n"
        )


def render_table4_trajectories(
    out: StringIO,
    optlog: Dict[str, Any],
    trajectories: Dict[str, Any],
) -> None:
    _section(out, "TABLE 4 -- PARAMETER TRAJECTORIES (hill-climbing summary)")
    out.write(
        "\n  Aggregated across all 3 seeds. Cycles/accepted/rejected are sums.\n"
        "  Most-moved (round, metric) is the (round, metric) with the largest\n"
        "  cumulative *accepted* delta (signed). Total L1 = mean across seeds\n"
        "  of sum-of-absolute-changes from initial to final params.\n"
    )

    summary = summarize_optlog(optlog)
    movement = total_param_movement(trajectories)

    out.write(
        f"\n  {'Archetype':<22} {'Cycles':>7} {'Accept':>7} {'Reject':>7} "
        f"{'Rate':>7} {'L1 dist':>8} {'Most-moved (rnd, metric, signed delta)':>42}\n"
    )
    out.write(
        "  " + "-" * 22 + " " + "-" * 7 + " " + "-" * 7 + " " + "-" * 7
        + " " + "-" * 7 + " " + "-" * 8 + " " + "-" * 42 + "\n"
    )
    for arch in sorted(summary.keys()):
        s = summary[arch]
        rnd, metric, signed = s["most_moved"]
        most_str = f"({rnd}, {metric}, {signed:+.3f})"
        # Map optlog 'archetype' (e.g. 'oracle', 'judge_cooperative') to a
        # base archetype for the trajectories dict, which keys by archetype
        # without state suffix (judge -> 'judge').
        traj_key = arch.split("_")[0] if arch.startswith("judge_") else arch
        l1 = movement.get(traj_key, 0.0)
        out.write(
            f"  {arch:<22} {s['cycles']:>7d} {s['accepted']:>7d} "
            f"{s['rejected']:>7d} {s['accept_rate']:>7.2%} "
            f"{l1:>8.3f} {most_str:>42}\n"
        )


def render_table5_adaptation(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 5 -- ADAPTATION SUCCESS (last-1000-hand profit + Firestorm)")
    out.write(
        f"\n  Per-archetype net chip flow over the FINAL {LAST_WINDOW_HANDS} hands\n"
        "  (mean +/- std across 3 seeds). Profit_vs_FS is chips invested into\n"
        "  hands Firestorm won at showdown (lower is better; emergent defense).\n"
    )

    out.write(
        f"\n  {'Archetype':<10} "
        f"{'Last-1000 P1':>20} {'Last-1000 P2':>20} {'Delta':>14} "
        f"{'Loss->FS P1':>14} {'Loss->FS P2':>14}\n"
    )
    out.write("  " + "-" * 10 + (" " + "-" * 20) * 2
              + " " + "-" * 14 + (" " + "-" * 14) * 2 + "\n")
    for arch in ARCHETYPES:
        v1 = [r["last_window"][arch] for r in p1["runs"]]
        v2 = [r["last_window"][arch] for r in p2["runs"]]
        loss_fs_1 = [r["opp_matrix"][arch]["firestorm"] for r in p1["runs"]]
        loss_fs_2 = [r["opp_matrix"][arch]["firestorm"] for r in p2["runs"]]
        delta = float(np.mean(v2) - np.mean(v1))
        out.write(
            f"  {arch:<10} "
            f"{fmt_meanstd_int(v1):>20} {fmt_meanstd_int(v2):>20} "
            f"{delta:>+14.0f} "
            f"{fmt_meanstd_int(loss_fs_1):>14} {fmt_meanstd_int(loss_fs_2):>14}\n"
        )


def render_table6_aberration(
    out: StringIO, p1: Dict[str, Any], p2: Dict[str, Any]
) -> None:
    _section(out, "TABLE 6 -- ABERRATION INDEX (drift in normalized VPIP/PFR/AF)")
    out.write(
        "\n  L2 distance in normalized (VPIP, PFR, AF) space between Phase 2's\n"
        "  observed end-of-run behavior and the Phase 1 archetype baseline.\n"
        "  Normalization: each axis divided by Phase-1 cross-archetype std,\n"
        "  so a unit equals 'one P1 archetype-spread' on each behavioral axis.\n"
        "  Higher = larger behavioral drift from the archetype spec.\n"
    )

    # Build per-archetype mean (vpip, pfr, af) for each phase
    def mean_vec(runs: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        return {
            arch: np.array([
                float(np.mean([r["beh"][arch]["vpip"] for r in runs])),
                float(np.mean([r["beh"][arch]["pfr"] for r in runs])),
                float(np.mean([r["beh"][arch]["af"] for r in runs])),
            ]) for arch in ARCHETYPES
        }

    p1_vec = mean_vec(p1["runs"])
    p2_vec = mean_vec(p2["runs"])

    # Cross-archetype std on each axis from Phase 1, used as the unit.
    p1_matrix = np.array([p1_vec[a] for a in ARCHETYPES])  # 8x3
    axis_std = p1_matrix.std(axis=0)
    axis_std = np.where(axis_std < 1e-9, 1.0, axis_std)  # guard

    out.write(
        f"\n  {'Archetype':<10} "
        f"{'P1 (V,P,AF)':>26} {'P2 (V,P,AF)':>26} "
        f"{'L2 drift':>10} {'dVPIP':>8} {'dPFR':>8} {'dAF':>8}\n"
    )
    out.write("  " + "-" * 10 + (" " + "-" * 26) * 2 + (" " + "-" * 10)
              + (" " + "-" * 8) * 3 + "\n")
    drifts = []
    for arch in ARCHETYPES:
        v1 = p1_vec[arch]
        v2 = p2_vec[arch]
        diff = (v2 - v1) / axis_std
        l2 = float(np.sqrt(np.sum(diff * diff)))
        drifts.append(l2)
        out.write(
            f"  {arch:<10} "
            f"({v1[0]:.2f},{v1[1]:.2f},{v1[2]:.2f}){'':>10}"
            f"({v2[0]:.2f},{v2[1]:.2f},{v2[2]:.2f}){'':>10}"
            f"{l2:>10.3f} "
            f"{v2[0] - v1[0]:>+8.3f} {v2[1] - v1[1]:>+8.3f} "
            f"{v2[2] - v1[2]:>+8.2f}\n"
        )
    out.write(
        f"\n  Mean Aberration Index across archetypes: {np.mean(drifts):.3f}\n"
        f"  Max archetype drift: {max(drifts):.3f} "
        f"({ARCHETYPES[int(np.argmax(drifts))]})\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase1-db", default="runs_phase1_ref.sqlite",
        help="Phase 1 reference SQLite path.",
    )
    parser.add_argument(
        "--phase2-db", default="runs_phase2_adaptive.sqlite",
        help="Phase 2 adaptive SQLite path.",
    )
    parser.add_argument(
        "--trajectories",
        default="phase2/adaptive/param_trajectories.json",
        help="Per-agent param history JSON.",
    )
    parser.add_argument(
        "--optlog",
        default="phase2/adaptive/optimization_log.json",
        help="Hill-climber per-cycle log JSON.",
    )
    parser.add_argument(
        "--output", default="reports/phase2_scorecard.txt",
        help="Output path for the formatted scorecard.",
    )
    args = parser.parse_args(argv)

    # Load run artifacts
    if not Path(args.phase1_db).exists():
        print(f"ERROR: Phase 1 DB not found: {args.phase1_db}", file=sys.stderr)
        return 1
    if not Path(args.phase2_db).exists():
        print(f"ERROR: Phase 2 DB not found: {args.phase2_db}", file=sys.stderr)
        return 1
    with open(args.trajectories, "r", encoding="utf-8") as f:
        trajectories = json.load(f)
    with open(args.optlog, "r", encoding="utf-8") as f:
        optlog = json.load(f)

    print(f"Aggregating Phase 1 runs from {args.phase1_db} ...", flush=True)
    p1 = aggregate_phase(args.phase1_db)
    print(f"Aggregating Phase 2 runs from {args.phase2_db} ...", flush=True)
    p2 = aggregate_phase(args.phase2_db)

    buf = StringIO()
    buf.write("Phase 1 (frozen) vs Phase 2 (adaptive hill-climbing) scorecard\n")
    buf.write(f"  Phase 1 DB: {args.phase1_db}  ({len(p1['runs'])} runs)\n")
    buf.write(f"  Phase 2 DB: {args.phase2_db}  ({len(p2['runs'])} runs)\n")

    render_table0_headline(buf, p1, p2)
    render_table1_fingerprints(buf, p1, p2)
    render_table2_economic(buf, p1, p2)
    render_table3_trust_profit(buf, p1, p2)
    render_table4_trajectories(buf, optlog, trajectories)
    render_table5_adaptation(buf, p1, p2)
    render_table6_aberration(buf, p1, p2)

    text = buf.getvalue()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"\nScorecard written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

