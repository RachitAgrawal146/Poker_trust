"""Gather per-seed R1 ledgers into one file per condition.

usage: python3 revision_experiments/collect_r1.py ART_DIR OUT_DIR PLAN.json

Writes OUT_DIR/<condition>.json ({"condition", "runs": [per-seed ledger, ...]})
and OUT_DIR/manifest.json listing, per condition, the seeds found, the seeds
the plan asked for, and any that are missing.
"""
import glob
import json
import os
import re
import sys

art, out, plan_file = sys.argv[1], sys.argv[2], sys.argv[3]
plan = json.load(open(plan_file))
os.makedirs(out, exist_ok=True)
by_cond = {}
for path in sorted(glob.glob(os.path.join(art, "*_seed*.json"))):
    m = re.match(r"(.+)_seed(\d+)\.json$", os.path.basename(path))
    if not m:
        continue
    by_cond.setdefault(m.group(1), []).append(json.load(open(path)))

manifest = {"label": plan["label"], "hands": plan["hands"], "conditions": {}}
for cond in plan["conditions"]:
    runs = sorted(by_cond.get(cond, []), key=lambda r: plan["seeds"].index(r["seed"]))
    found = [r["seed"] for r in runs]
    manifest["conditions"][cond] = {
        "seeds_found": found,
        "seeds_missing": [s for s in plan["seeds"] if s not in found],
        "hands_ok": all(r["hands"] == plan["hands"] for r in runs),
        "git_sha": sorted({r["git_sha"] for r in runs}),
        "hands_per_second": [round(r["hands"] / max(r["seconds"], 1e-9), 2) for r in runs],
    }
    if runs:
        json.dump({"condition": cond, "runs": runs}, open(os.path.join(out, f"{cond}.json"), "w"))
json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
missing = {c: v["seeds_missing"] for c, v in manifest["conditions"].items() if v["seeds_missing"]}
print(f"{len(by_cond)} conditions gathered; missing: {missing if missing else 'none'}")
