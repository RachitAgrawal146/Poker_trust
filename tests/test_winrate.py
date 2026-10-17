"""Tests for analysis/winrate.py (runbook step B1).

Builds a short Stage 6 run with rebuys pressure, then checks that the
ledger reconciles exactly, that tampering is caught, and that showdown and
non-showdown winnings add up to the total.

usage: python3 tests/test_winrate.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analysis import winrate  # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(f"{'PASS' if cond else 'FAIL'} {name}{': ' + detail if detail else ''}")


def main():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "t.sqlite")
    subprocess.run([sys.executable, os.path.join(ROOT, "phase1", "run_sim.py"), "--stage", "6",
                    "--seeds", "42,137", "--hands", "150", "--db", db],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    conn = sqlite3.connect(db)
    run_ids = [r for (r,) in conn.execute("SELECT run_id FROM runs")]
    check("two runs logged", len(run_ids) == 2)

    for rid in run_ids:
        _, net, sd = winrate.per_hand_net(conn, rid)
        rec = winrate.reconcile(conn, rid, net)
        check(f"run {rid}: every hand sums to zero", rec["hands_not_zero_sum"] == 0)
        check(f"run {rid}: seat totals equal final_stack - 200*(1+rebuys)", rec["max_seat_error"] == 0)
        check(f"run {rid}: showdown + non-showdown = total",
              np.array_equal(np.where(sd, net, 0).sum(0) + np.where(~sd, net, 0).sum(0), net.sum(0)))
        check(f"run {rid}: only showdown seats have a showdown flag",
              sd.sum() == conn.execute("SELECT COUNT(*) FROM showdowns WHERE run_id=?", (rid,)).fetchone()[0])
        bad = net.copy(); bad[0, 0] += 1
        try:
            winrate.reconcile(conn, rid, bad)
            check(f"run {rid}: tampered ledger is rejected", False)
        except winrate.ReconciliationError:
            check(f"run {rid}: tampered ledger is rejected", True)

    rebuys = conn.execute("SELECT SUM(rebuys) FROM agent_stats").fetchone()[0]
    print(f"INFO rebuys in test runs: {rebuys}")

    runs = winrate.load_runs([db])
    s = winrate.summarise(runs)
    check("eight archetypes summarised", len(s) == 8)
    check("block bootstrap used below 10 seeds",
          all("block bootstrap" in v["interval_method"] for v in s.values()))
    tot = sum(v["net_chips_total"] for v in s.values())
    check("archetype net chips sum to zero", abs(tot) < 1e-9, f"{tot}")
    lo_hi = [v["ci95_boot_chips_per_100"] for v in s.values()]
    check("intervals contain the point estimate",
          all(lo <= v["win_rate_chips_per_100"] <= hi for (lo, hi), v in zip(lo_hi, s.values())))

    print("=" * 60)
    print(f"RESULT: {sum(results)}/{len(results)} tests passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
