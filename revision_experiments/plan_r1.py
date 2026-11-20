"""Expand the R1 run plan into a GitHub Actions matrix.

usage: python3 revision_experiments/plan_r1.py revision_experiments/r1_plan.json >> $GITHUB_OUTPUT

One job per (condition, chunk of seeds); each job runs its seeds in parallel
processes. Fails if a condition is not defined in r1_conditions.json.
"""
import json
import sys
from pathlib import Path

plan = json.load(open(sys.argv[1]))
known = json.load(open(Path(__file__).with_name("r1_conditions.json")))["conditions"]
chunk = int(plan.get("seeds_per_job", 4))
seeds = plan["seeds"]
jobs = []
for cond in plan["conditions"]:
    if cond not in known:
        sys.exit(f"unknown condition {cond!r}")
    for i in range(0, len(seeds), chunk):
        part = seeds[i:i + chunk]
        jobs.append({"condition": cond, "chunk": i // chunk,
                     "seeds": ",".join(str(s) for s in part),
                     "hands": int(plan["hands"]), "procs": len(part)})
if len(jobs) > 256:
    sys.exit(f"{len(jobs)} jobs exceeds the Actions matrix limit of 256")
print("matrix=" + json.dumps({"include": jobs}))
print("label=" + plan["label"])
