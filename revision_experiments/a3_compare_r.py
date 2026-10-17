"""A3: per-seed trust-profit r of regenerated databases vs r_by_phase.json.

Calls analysis.compute_metrics.compute_trust_profit_correlation for EVERY
run_id in each database (the module's CLI reads only the last run).

usage: python3 revision_experiments/a3_compare_r.py DB_DIR --out FILE.json
DB_DIR holds files named <dataset>_seed<seed>.sqlite.
"""
import argparse, json, os, re, sqlite3, sys, platform
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from analysis.compute_metrics import compute_trust_profit_correlation

PUBLISHED_KEY = {
    "phase1": "Phase 1 (frozen rules)",
    "phase2_bounded": "Phase 2 (bounded HC)",
    "phase2_unb_weak": None,   # resolved by substring below
    "phase2_unb_aggr": None,
}

def published(dataset, seed, table):
    phases = table["phases"]
    key = PUBLISHED_KEY.get(dataset)
    if key is None:
        want = "aggr" if dataset.endswith("aggr") else "weak"
        cands = [k for k in phases if "unbounded" in k.lower() and want in k.lower()]
        key = cands[0] if cands else None
    if key is None or key not in phases:
        return None, key
    p = phases[key]
    return (p["r"][p["seeds"].index(seed)] if seed in p["seeds"] else None), key

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db_dir"); ap.add_argument("--out", required=True)
    ap.add_argument("--published", default="paper_resources/data/r_by_phase.json")
    a = ap.parse_args()
    table = json.load(open(a.published))
    rows = []
    for f in sorted(os.listdir(a.db_dir)):
        m = re.match(r"(.+)_seed(\d+)\.sqlite$", f)
        if not m:
            continue
        dataset, seed = m.group(1), int(m.group(2))
        conn = sqlite3.connect(os.path.join(a.db_dir, f))
        for run_id, run_seed, git_sha in conn.execute("SELECT run_id, seed, git_sha FROM runs"):
            r, trust, stacks = compute_trust_profit_correlation(conn, run_id)
            pub, key = published(dataset, run_seed, table)
            rows.append({
                "dataset": dataset, "seed": run_seed, "run_id": run_id, "git_sha": git_sha,
                "r_regenerated": round(r, 6), "published_key": key, "r_published": pub,
                "match_3dp": (pub is not None and round(r, 3) == round(pub, 3)),
                "abs_diff": (None if pub is None else round(abs(r - pub), 6)),
                "mean_trust": [round(t, 6) for t in trust], "final_stack": stacks,
            })
    out = {"rows": rows,
           "n_match_3dp": sum(r["match_3dp"] for r in rows), "n_rows": len(rows),
           "versions": {"python": platform.python_version(), "numpy": np.__version__,
                        "treys": __import__("importlib.metadata").metadata.version("treys")}}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{out['n_match_3dp']}/{out['n_rows']} per-seed r match r_by_phase.json to 3 dp")

if __name__ == "__main__":
    main()
