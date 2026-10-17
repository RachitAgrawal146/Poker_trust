"""One-line JSON summary of a finished run database, for the run log.

usage: python3 revision_experiments/db_summary.py DB SECONDS
Prints integrity check, runs rows, hands count, rebuys, chip conservation
and hands per second. Exits non-zero if the database fails a check.
"""
import json
import os
import sqlite3
import sys

db, seconds = sys.argv[1], int(sys.argv[2])
c = sqlite3.connect(db)
integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
runs = [dict(zip(("run_id", "seed", "num_hands", "label", "git_sha"), r))
        for r in c.execute("SELECT run_id, seed, num_hands, label, git_sha FROM runs")]
hands = c.execute("SELECT COUNT(*) FROM hands").fetchone()[0]
stats = c.execute("SELECT run_id, SUM(final_stack), SUM(rebuys), COUNT(*) FROM agent_stats GROUP BY run_id").fetchall()
conservation = []
for run_id, total_stack, total_rebuys, seats in stats:
    # Each seat starts with 200 and every rebuy adds 200 (engine/table.py).
    expected = 200 * (seats + (total_rebuys or 0))
    conservation.append({"run_id": run_id, "total_stack": total_stack,
                         "expected": expected, "ok": total_stack == expected})
out = {
    "file": os.path.basename(db), "integrity": integrity, "runs": runs,
    "hands": hands, "seconds": seconds,
    "hands_per_second": round(hands / seconds, 2) if seconds else None,
    "chip_conservation": conservation,
}
print(json.dumps(out))
bad = integrity != "ok" or any(not x["ok"] for x in conservation) or \
    any(hands != sum(r["num_hands"] for r in runs) for _ in [0])
sys.exit(1 if bad else 0)
