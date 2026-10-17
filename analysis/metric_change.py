"""B2: the trust-profit association under final stack and under net winnings.

For every run in the given databases: the R0 trust statistic (mean over
observers of trust at the final hand's snapshot, exactly as
analysis/compute_metrics.compute_trust_profit_correlation) against (a)
final stack, the R0 outcome, and (b) net winnings from analysis/winrate.py,
which counts rebuys. Pearson and Spearman for each. Also per-archetype
win rates (winrate.summarise).

usage: python3 analysis/metric_change.py DB [DB ...] --label NAME --out FILE.json
"""
import argparse
import json
import os
import sqlite3
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis import winrate  # noqa: E402
from analysis.compute_metrics import compute_trust_profit_correlation  # noqa: E402


def tvals(x):
    x = np.asarray(x, float)
    n = len(x)
    m, sd_pop = x.mean(), x.std()
    se = x.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
    t = stats.t.ppf(0.975, n - 1) if n > 1 else float("nan")
    return {"n": n, "mean": m, "sd_pop": sd_pop, "ci95_t": [m - t * se, m + t * se],
            "n_positive": int((x > 0).sum())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dbs", nargs="+")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    runs = winrate.load_runs(a.dbs)
    per_run = []
    for r in runs:
        conn = sqlite3.connect(next(p for p in a.dbs if os.path.basename(p) == r["file"]))
        r_stack, trust, stacks = compute_trust_profit_correlation(conn, r["run_id"])
        net = r["net"].sum(axis=0)
        per_run.append({
            "file": r["file"], "run_id": r["run_id"], "seed": r["seed"],
            "archetypes": r["archetypes"], "trust": trust, "final_stack": stacks,
            "net_chips": [int(v) for v in net],
            "pearson_stack": r_stack,
            "pearson_net": float(stats.pearsonr(trust, net)[0]),
            "spearman_stack": float(stats.spearmanr(trust, stacks)[0]),
            "spearman_net": float(stats.spearmanr(trust, net)[0]),
        })
    summary = {k: tvals([p[k] for p in per_run])
               for k in ("pearson_stack", "pearson_net", "spearman_stack", "spearman_net")}
    out = {"label": a.label, "n_runs": len(per_run), "summary": summary,
           "per_run": per_run, "archetypes": winrate.summarise(runs)}
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    for k, v in summary.items():
        print(f"{a.label:24s} {k:15s} mean {v['mean']:+.3f} sd {v['sd_pop']:.3f} "
              f"CI [{v['ci95_t'][0]:+.3f}, {v['ci95_t'][1]:+.3f}] positive {v['n_positive']}/{v['n']}")


if __name__ == "__main__":
    main()
