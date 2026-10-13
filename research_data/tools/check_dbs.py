#!/usr/bin/env python3
"""Integrity and shape check for a directory tree of simulation databases.

For every *.sqlite under ROOT: SHA-256, size, PRAGMA integrity_check,
the rows of `runs`, and row counts of the per-hand tables. Prints a
summary and writes JSON. Read-only: databases are opened with mode=ro.
"""
import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys

TABLES = ("hands", "actions", "showdowns", "trust_snapshots", "agent_stats")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    rec = {"integrity": con.execute("PRAGMA integrity_check").fetchone()[0]}
    names = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "runs" in names:
        cur = con.execute("SELECT * FROM runs")
        cols = [c[0] for c in cur.description]
        rec["runs"] = [dict(zip(cols, row)) for row in cur.fetchall()]
    for t in TABLES:
        if t in names:
            rec[f"n_{t}"] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    if "hands" in names:
        rec["hands_per_run"] = {str(r): n for r, n in con.execute(
            "SELECT run_id, COUNT(*) FROM hands GROUP BY run_id")}
    con.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-count", type=int)
    ap.add_argument("--expect-hands", type=int)
    a = ap.parse_args()

    root = pathlib.Path(a.root)
    files = sorted(root.rglob("*.sqlite"))
    report = {"root": str(root), "n_files": len(files), "files": []}
    ok = True
    for f in files:
        rec = {"path": str(f.relative_to(root)), "bytes": f.stat().st_size,
               "sha256": sha256(f)}
        rec.update(check(f))
        if rec["integrity"] != "ok":
            ok = False
        if a.expect_hands is not None:
            hp = rec.get("hands_per_run", {})
            rec["hands_as_expected"] = bool(hp) and all(
                n == a.expect_hands for n in hp.values())
        report["files"].append(rec)
        print(f"{rec['path']}: integrity={rec['integrity']} "
              f"hands={rec.get('hands_per_run')} runs={len(rec.get('runs', []))}")
    if a.expect_count is not None:
        report["count_as_expected"] = len(files) == a.expect_count
        ok &= report["count_as_expected"]
    if a.expect_hands is not None:
        report["all_hands_as_expected"] = all(
            r["hands_as_expected"] for r in report["files"])
        ok &= report["all_hands_as_expected"]
    report["all_ok"] = ok
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(report, fh, indent=1, default=str)
    print(f"{len(files)} files, all_ok={ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
