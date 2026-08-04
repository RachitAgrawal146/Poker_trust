#!/usr/bin/env python3
"""Recompute every Phase 3.1 exhibit statistic from the n=20 databases.

The n=20 replication (workflow run #6) replaced the canonical Phase 3.1
*correlation* data, but the per-archetype exhibits -- economic table,
behavioral fingerprints, TMA, the trust-vs-stack scatter -- still derived
from the original five-seed run, because no per-seat extraction existed
for the twenty new databases. This script is that extraction.

It reads the twenty single-seed SQLite databases produced by the run
(one per matrix job, downloaded from the run's artifact), applies the
same queries `analysis/extract_phase3_stats.py` uses plus the six
secondary metrics from `analysis/compute_metrics.py`, and writes ONE
JSON with:

  * ``seeds``      -- per-seed per-seat detail, shape-compatible with
                      ``phase31_stats.json`` so the trust-vs-stack figure
                      can read it unchanged;
  * ``aggregates`` -- per-archetype cross-seed means/SDs (stack, rebuys,
                      trust, VPIP/PFR/AF, TMA, TEI, CS, OA, NS, SU) and
                      final-stack ranks, which the table/figure
                      generators load instead of hardcoded dicts.

Usage::

    python3 analysis/recompute_p31_n20.py \
        --db-glob 'artifacts/**/*.sqlite' \
        --out paper_resources/data/phase31_n20_stats.json
"""

from __future__ import annotations

import argparse
import glob
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis.compute_metrics import (  # noqa: E402
    compute_tei,
    compute_context_sensitivity,
    compute_opponent_adaptation,
    compute_nonstationarity,
    compute_unpredictability,
    compute_trust_manipulation,
)

ARCHETYPES = ["oracle", "sentinel", "firestorm", "wall",
              "phantom", "predator", "mirror", "judge"]


def _completed_run_id(conn: sqlite3.Connection, num_hands: int) -> int | None:
    """The last run in this DB with the full hand count (resume-safe)."""
    cur = conn.cursor()
    best = None
    for (run_id,) in cur.execute("SELECT run_id FROM runs ORDER BY run_id"):
        n = cur.execute("SELECT COUNT(*) FROM hands WHERE run_id=?",
                        (run_id,)).fetchone()[0]
        if n >= num_hands:
            best = run_id
    return best


def _extract_seed(conn: sqlite3.Connection, run_id: int) -> dict:
    """Per-seat + behavioral extraction, mirroring extract_phase3_stats."""
    c = conn.cursor()
    seed = c.execute("SELECT seed FROM runs WHERE run_id=?",
                     (run_id,)).fetchone()[0]

    ts, ss, per_seat = [], [], []
    for seat in range(8):
        t = c.execute(
            "SELECT AVG(trust) FROM trust_snapshots "
            "WHERE run_id=? AND target_seat=? "
            "AND hand_id=(SELECT MAX(hand_id) FROM trust_snapshots "
            "WHERE run_id=?)",
            (run_id, seat, run_id),
        ).fetchone()[0] or 0.5
        arch, stack, rebuys, hands, sd, sd_won = c.execute(
            "SELECT archetype, final_stack, rebuys, hands_dealt, "
            "       showdowns, showdowns_won "
            "FROM agent_stats WHERE run_id=? AND seat=?",
            (run_id, seat),
        ).fetchone()
        ts.append(float(t)); ss.append(int(stack))
        per_seat.append({
            "seat": seat, "archetype": arch, "trust": float(t),
            "final_stack": int(stack), "rebuys": int(rebuys),
            "hands_dealt": int(hands), "showdowns": int(sd),
            "showdowns_won": int(sd_won),
        })
    r = float(np.corrcoef(ts, ss)[0, 1])

    beh = {}
    for seat, arch in enumerate(ARCHETYPES):
        preflop = dict(c.execute(
            "SELECT action_type, COUNT(*) FROM actions "
            "WHERE run_id=? AND seat=? AND betting_round='preflop' "
            "AND action_type NOT IN ('post_sb','post_bb') "
            "GROUP BY action_type", (run_id, seat)).fetchall())
        hands_in = c.execute(
            "SELECT COUNT(DISTINCT hand_id) FROM actions "
            "WHERE run_id=? AND seat=?", (run_id, seat)).fetchone()[0] or 1
        alla = dict(c.execute(
            "SELECT action_type, COUNT(*) FROM actions "
            "WHERE run_id=? AND seat=? "
            "AND action_type NOT IN ('post_sb','post_bb') "
            "GROUP BY action_type", (run_id, seat)).fetchall())
        beh[arch] = {
            "vpip": (preflop.get('call', 0) + preflop.get('bet', 0)
                     + preflop.get('raise', 0)) / hands_in,
            "pfr": (preflop.get('bet', 0) + preflop.get('raise', 0)) / hands_in,
            "af": (alla.get('bet', 0) + alla.get('raise', 0))
                  / max(alla.get('call', 0), 1),
        }

    return {"seed": int(seed), "run_id": int(run_id), "r": r,
            "per_seat": per_seat, "behavioral": beh}


def _metrics_seed(conn: sqlite3.Connection, run_id: int) -> dict:
    """The six secondary metrics for one run, keyed by archetype."""
    tei = compute_tei(conn, run_id)
    return {
        "tei": {a: tei[a]["tei"] for a in ARCHETYPES},
        "cs":  compute_context_sensitivity(conn, run_id),
        "oa":  compute_opponent_adaptation(conn, run_id),
        "ns":  compute_nonstationarity(conn, run_id),
        "su":  compute_unpredictability(conn, run_id),
        "tma": compute_trust_manipulation(conn, run_id),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db-glob", required=True)
    p.add_argument("--hands", type=int, default=150)
    p.add_argument("--out", default=str(
        _REPO_ROOT / "paper_resources" / "data" / "phase31_n20_stats.json"))
    args = p.parse_args()

    dbs = sorted(glob.glob(args.db_glob, recursive=True))
    if not dbs:
        print(f"ERROR: no databases matched {args.db_glob}", file=sys.stderr)
        return 2

    seeds, metrics = [], []
    for db in dbs:
        conn = sqlite3.connect(db)
        try:
            run_id = _completed_run_id(conn, args.hands)
            if run_id is None:
                print(f"  {db}: no completed {args.hands}-hand run — skipped")
                continue
            s = _extract_seed(conn, run_id)
            m = _metrics_seed(conn, run_id)
            seeds.append(s); metrics.append(m)
            print(f"  {db}: seed {s['seed']}  r={s['r']:+.3f}")
        finally:
            conn.close()

    if not seeds:
        print("ERROR: nothing extracted", file=sys.stderr)
        return 2
    seeds.sort(key=lambda s: s["seed"])

    # ---------------- cross-seed aggregates ----------------
    agg = {}
    for arch in ARCHETYPES:
        stacks  = [e["final_stack"] for s in seeds for e in s["per_seat"]
                   if e["archetype"] == arch]
        rebuys  = [e["rebuys"] for s in seeds for e in s["per_seat"]
                   if e["archetype"] == arch]
        trust   = [e["trust"] for s in seeds for e in s["per_seat"]
                   if e["archetype"] == arch]
        agg[arch] = {
            "stack": float(np.mean(stacks)),
            "stack_std": float(np.std(stacks)),
            "rebuys": float(np.mean(rebuys)),
            "trust": float(np.mean(trust)),
            "vpip": float(np.mean([s["behavioral"][arch]["vpip"] for s in seeds])),
            "pfr":  float(np.mean([s["behavioral"][arch]["pfr"] for s in seeds])),
            "af":   float(np.mean([s["behavioral"][arch]["af"] for s in seeds])),
            **{k: float(np.mean([m[k][arch] for m in metrics]))
               for k in ("tei", "cs", "oa", "ns", "su", "tma")},
        }

    # Final-stack ranks, 1 = richest.
    order = sorted(ARCHETYPES, key=lambda a: -agg[a]["stack"])
    for i, arch in enumerate(order, 1):
        agg[arch]["rank_p31"] = i

    out = {
        "_provenance": (
            f"Recomputed from {len(seeds)} single-seed databases of the "
            f"n=20 temperature-0 Phase 3.1 replication (workflow run "
            f"30788234686, artifact all-databases-phase31-n20) by "
            f"analysis/recompute_p31_n20.py."),
        "n_seeds": len(seeds),
        "hands_per_seed": args.hands,
        "aggregates": agg,
        "seeds": seeds,
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}  ({len(seeds)} seeds)")

    print("\nPer-archetype summary (mean across seeds):")
    print(f"  {'arch':<10} {'stack':>7} {'rebuys':>6} {'trust':>6} "
          f"{'vpip':>6} {'pfr':>6} {'af':>5} {'tma':>7} rank")
    for arch in order:
        a = agg[arch]
        print(f"  {arch:<10} {a['stack']:>7.0f} {a['rebuys']:>6.1f} "
              f"{a['trust']:>6.3f} {a['vpip']:>6.3f} {a['pfr']:>6.3f} "
              f"{a['af']:>5.2f} {a['tma']:>+7.3f} {a['rank_p31']:>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
