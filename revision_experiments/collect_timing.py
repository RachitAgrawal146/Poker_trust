"""Gather the per-job db_summary JSON files into one run log.

usage: python3 revision_experiments/collect_timing.py ART_DIR OUT.json
"""
import glob
import json
import os
import sys

rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(sys.argv[1], "timing_*.json")))]
json.dump({"jobs": rows, "n_jobs": len(rows)}, open(sys.argv[2], "w"), indent=1)
print(f"{len(rows)} job summaries -> {sys.argv[2]}")
