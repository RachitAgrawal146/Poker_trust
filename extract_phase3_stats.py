"""Extract per-seed trust-profit r and per-seat stats from a Phase 3 SQLite,
dump as JSON for cross-phase comparison.

Usage:
    python3 extract_phase3_stats.py --db runs_phase3_long.sqlite --out phase3_stats.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np

ARCHETYPES = ["oracle", "sentinel", "firestorm", "wall",
              "phantom", "predator", "mirror", "judge"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--out", default="phase3_stats.json")
    args = p.parse_args()

    c = sqlite3.connect(args.db)
    out: dict = {"seeds": []}

    for (run_id,) in c.execute("SELECT run_id FROM runs ORDER BY run_id"):
        seed = c.execute(
            "SELECT seed FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()[0]

        ts, ss, per_seat = [], [], []
        for seat in range(8):
            t = c.execute(
                "SELECT AVG(trust) FROM trust_snapshots "
                "WHERE run_id=? AND target_seat=? "
                "AND hand_id=(SELECT MAX(hand_id) FROM trust_snapshots "
                "WHERE run_id=?)",
                (run_id, seat, run_id),
            ).fetchone()[0] or 0.5
            stats = c.execute(
                "SELECT archetype, final_stack, rebuys, hands_dealt, "
                "       showdowns, showdowns_won "
                "FROM agent_stats WHERE run_id=? AND seat=?",
                (run_id, seat),
            ).fetchone()
            arch, stack, rebuys, hands, sd, sd_won = stats
            ts.append(float(t))
            ss.append(int(stack))
            per_seat.append({
                "seat": seat, "archetype": arch, "trust": float(t),
                "final_stack": int(stack), "rebuys": int(rebuys),
                "hands_dealt": int(hands), "showdowns": int(sd),
                "showdowns_won": int(sd_won),
            })

        r = float(np.corrcoef(ts, ss)[0, 1])

        # Per-archetype VPIP/PFR/AF
        beh = {}
        for seat, arch in enumerate(ARCHETYPES):
            counts = c.execute(
                "SELECT action_type, COUNT(*) FROM actions "
                "WHERE run_id=? AND seat=? AND betting_round='preflop' "
                "AND action_type NOT IN ('post_sb','post_bb') "
                "GROUP BY action_type",
                (run_id, seat),
            ).fetchall()
            preflop = dict(counts)
            preflop_total = sum(preflop.values())
            vpip_actions = (preflop.get('call', 0) + preflop.get('bet', 0)
                            + preflop.get('raise', 0))
            pfr_actions = preflop.get('bet', 0) + preflop.get('raise', 0)
            hands_in = c.execute(
                "SELECT COUNT(DISTINCT hand_id) FROM actions "
                "WHERE run_id=? AND seat=?",
                (run_id, seat),
            ).fetchone()[0] or 1

            all_counts = c.execute(
                "SELECT action_type, COUNT(*) FROM actions "
                "WHERE run_id=? AND seat=? "
                "AND action_type NOT IN ('post_sb','post_bb') "
                "GROUP BY action_type",
                (run_id, seat),
            ).fetchall()
            all_d = dict(all_counts)
            agg = all_d.get('bet', 0) + all_d.get('raise', 0)
            calls = max(all_d.get('call', 0), 1)
            af = agg / calls

            beh[arch] = {
                "vpip": vpip_actions / hands_in,
                "pfr": pfr_actions / hands_in,
                "af": af,
            }

        out["seeds"].append({
            "seed": seed, "run_id": run_id, "r": r,
            "trust_scores": ts, "final_stacks": ss,
            "per_seat": per_seat, "behavioral": beh,
        })

    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    rs = [s["r"] for s in out["seeds"]]
    print(f"Phase 3 trust-profit r per seed:")
    for s in out["seeds"]:
        print(f"  seed={s['seed']:5d}  r={s['r']:+.3f}")
    print(f"  mean = {np.mean(rs):+.3f} +/- {np.std(rs):.3f}")
    print(f"\nWrote: {args.out}")


if __name__ == "__main__":
    main()
