"""Expand a run-matrix JSON into a GitHub Actions matrix (one job per entry x seed).

usage: python3 revision_experiments/plan_matrix.py MATRIX.json  >> $GITHUB_OUTPUT
"""
import json
import sys

m = json.load(open(sys.argv[1]))
for key in ("include", "seeds", "release", "asset_prefix"):
    if key not in m:
        sys.exit(f"{sys.argv[1]}: missing key {key!r}")
jobs = [dict(e, seed=s) for e in m["include"] for s in m["seeds"]]
if len(jobs) > 256:
    sys.exit(f"{len(jobs)} jobs exceeds the Actions matrix limit of 256")
print("matrix=" + json.dumps({"include": jobs}))
