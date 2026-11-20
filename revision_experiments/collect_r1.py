"""Gather per-seed R1 ledgers into one file per condition.

usage: python3 revision_experiments/collect_r1.py ART_DIR OUT_DIR PLAN.json

Writes OUT_DIR/<condition>.json ({"condition", "runs": [per-seed ledger, ...]})
and OUT_DIR/manifest.json listing, per condition, the seeds found, the seeds
the plan asked for, and any that are missing.

If OUT_DIR/<condition>.json already exists, its seeds are kept and only seeds
absent from it are added: a seed that has a committed ledger is never
replaced. A rerun plan can therefore list just the missing seeds.
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

all_seeds = plan.get("all_seeds", plan["seeds"])
order = {s: i for i, s in enumerate(all_seeds)}
manifest_path = os.path.join(out, "manifest.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {"conditions": {}}
manifest.update({"label": plan["label"], "hands": plan["hands"]})
for cond in plan["conditions"]:
    path = os.path.join(out, f"{cond}.json")
    kept = json.load(open(path))["runs"] if os.path.exists(path) else []
    have = {r["seed"] for r in kept}
    added = [r for r in by_cond.get(cond, []) if r["seed"] not in have]
    runs = sorted(kept + added, key=lambda r: (order.get(r["seed"], len(order)), r["seed"]))
    found = [r["seed"] for r in runs]
    manifest["conditions"][cond] = {
        "seeds_found": found,
        "seeds_missing": [s for s in all_seeds if s not in found],
        "hands_ok": all(r["hands"] == plan["hands"] for r in runs),
        "git_sha": sorted({r["git_sha"] for r in runs}),
        "hands_per_second": [round(r["hands"] / max(r["seconds"], 1e-9), 2) for r in runs],
    }
    if runs:
        json.dump({"condition": cond, "runs": runs}, open(os.path.join(out, f"{cond}.json"), "w"))
json.dump(manifest, open(manifest_path, "w"), indent=1)
missing = {c: v["seeds_missing"] for c, v in manifest["conditions"].items() if v["seeds_missing"]}
print(f"{len(by_cond)} conditions gathered; missing: {missing if missing else 'none'}")
