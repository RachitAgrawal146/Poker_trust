"""Extract per-archetype training CSVs from the Phase 1 database.

Reads every action row, joins with the hands table for dealer position,
optionally enriches with hand-strength from showdown reveals, and writes
stratified 80/20 train/test splits per archetype.

Usage::

    python -m ml.extract_training_data --db runs_v3.sqlite --outdir ml/data/
    python -m ml.extract_training_data --db runs_v3.sqlite --outdir ml/data/ --with-hs

Output::

    ml/data/
    ├── oracle_train.csv       (80% of oracle actions)
    ├── oracle_test.csv        (20% of oracle actions)
    ├── ...                    (16 files total: 8 archetypes x train/test)
    └── extraction_report.txt
"""

from __future__ import annotations

# Ensure repo root is on sys.path
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))


import argparse
import csv
import math
import os
import sqlite3
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from phase2.ml.feature_engineering import (
    ARCHETYPES,
    ACTION_LABELS,
    action_row_to_features,
    get_feature_names,
)


def _connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found.", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def _build_dealer_map(db: sqlite3.Connection) -> Dict[Tuple[int, int], int]:
    """Return {(run_id, hand_id): dealer_seat} for every hand."""
    rows = db.execute("SELECT run_id, hand_id, dealer FROM hands").fetchall()
    return {(r["run_id"], r["hand_id"]): r["dealer"] for r in rows}


def _build_showdown_hs_map(
    db: sqlite3.Connection,
) -> Dict[Tuple[int, int, int], str]:
    """Return {(run_id, hand_id, seat): hand_strength_bucket} for showdown
    participants, using the treys rank to bucket.

    Rank classes (from treys, lower = better):
        1 Straight Flush, 2 Quads, 3 Full House, 4 Flush, 5 Straight,
        6 Trips → Strong
        7 Two Pair, 8 Pair → Medium
        9 High Card → Weak
    """
    rows = db.execute(
        "SELECT run_id, hand_id, seat, hand_rank FROM showdowns"
    ).fetchall()
    hs_map: Dict[Tuple[int, int, int], str] = {}
    for r in rows:
        rank = r["hand_rank"]
        # treys rank_class thresholds (approximate from rank value):
        # Rank 1-322: Straight Flush (class 1)
        # 323-? : Quads, Full House, etc.
        # We use the Evaluator's class boundaries. Since we don't have the
        # Evaluator here, use the rank directly:
        #   rank <= 1609  → Strong (trips or better = top ~21.5%)
        #   rank <= 3325  → Medium (two pair or pair of aces-level)
        #   rank > 3325   → Weak (most pairs and high cards)
        # These thresholds approximate the treys rank_class boundaries:
        #   class 1-6 (SF through trips): rank 1..1609
        #   class 7-8 (two pair, pair): rank 1610..6185
        #   class 9 (high card): rank 6186..7462
        if rank <= 1609:
            bucket = "Strong"
        elif rank <= 6185:
            bucket = "Medium"
        else:
            bucket = "Weak"
        hs_map[(r["run_id"], r["hand_id"], r["seat"])] = bucket
    return hs_map


def _stratified_split(
    features: List[List[float]],
    labels: List[int],
    test_fraction: float = 0.2,
    seed: int = 42,
) -> Tuple[List[List[float]], List[int], List[List[float]], List[int]]:
    """Stratified train/test split preserving class proportions."""
    import numpy as np

    rng = np.random.default_rng(seed)
    by_class: Dict[int, List[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        by_class[label].append(i)

    train_idx: List[int] = []
    test_idx: List[int] = []
    for cls in sorted(by_class):
        indices = by_class[cls]
        rng.shuffle(indices)
        n_test = max(1, int(len(indices) * test_fraction))
        test_idx.extend(indices[:n_test])
        train_idx.extend(indices[n_test:])

    rng.shuffle(train_idx)
    rng.shuffle(test_idx)

    X_train = [features[i] for i in train_idx]
    y_train = [labels[i] for i in train_idx]
    X_test = [features[i] for i in test_idx]
    y_test = [labels[i] for i in test_idx]
    return X_train, y_train, X_test, y_test


def _write_csv(
    path: str,
    header: List[str],
    features: List[List[float]],
    labels: List[int],
) -> int:
    """Write features + label to CSV. Returns row count."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header + ["label"])
        for feat, label in zip(features, labels):
            writer.writerow([f"{v:.6f}" for v in feat] + [label])
    return len(features)


def extract(
    db_path: str,
    outdir: str,
    with_hand_strength: bool = False,
    test_fraction: float = 0.2,
) -> str:
    """Run the full extraction pipeline. Returns the report text."""
    os.makedirs(outdir, exist_ok=True)
    db = _connect(db_path)

    print("Loading dealer map...")
    dealer_map = _build_dealer_map(db)
    print(f"  {len(dealer_map):,} hands indexed.")

    hs_map: Dict[Tuple[int, int, int], str] = {}
    if with_hand_strength:
        print("Loading showdown hand-strength map...")
        hs_map = _build_showdown_hs_map(db)
        print(f"  {len(hs_map):,} showdown entries indexed.")

    feature_names = get_feature_names(with_hand_strength)
    report_lines: List[str] = []
    report_lines.append("PHASE 2 DATA EXTRACTION REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Database: {db_path}")
    report_lines.append(f"Hand strength: {'from showdowns' if with_hand_strength else 'not included'}")
    report_lines.append(f"Features: {feature_names}")
    report_lines.append(f"Test fraction: {test_fraction}")
    report_lines.append("")

    total_rows = 0
    total_skipped = 0

    for archetype in ARCHETYPES:
        print(f"\nExtracting {archetype}...")
        t0 = time.time()

        # Stream actions for this archetype
        cursor = db.execute(
            "SELECT * FROM actions WHERE archetype = ? ORDER BY run_id, hand_id, sequence_num",
            (archetype,),
        )

        features: List[List[float]] = []
        labels: List[int] = []
        skipped = 0
        processed = 0

        for row in cursor:
            processed += 1
            key = (row["run_id"], row["hand_id"])
            dealer = dealer_map.get(key)
            if dealer is None:
                skipped += 1
                continue

            hs: Optional[str] = None
            if with_hand_strength:
                hs_key = (row["run_id"], row["hand_id"], row["seat"])
                hs = hs_map.get(hs_key)
                if hs is None:
                    skipped += 1
                    continue

            result = action_row_to_features(dict(row), dealer, hs)
            if result is None:
                skipped += 1
                continue

            feat, label = result
            features.append(feat)
            labels.append(label)

        elapsed = time.time() - t0
        total_rows += len(features)
        total_skipped += skipped

        # Class distribution
        class_counts = defaultdict(int)
        for label in labels:
            class_counts[label] += 1

        # Stratified split
        X_train, y_train, X_test, y_test = _stratified_split(
            features, labels, test_fraction=test_fraction
        )

        # Write CSVs
        train_path = os.path.join(outdir, f"{archetype}_train.csv")
        test_path = os.path.join(outdir, f"{archetype}_test.csv")
        n_train = _write_csv(train_path, feature_names, X_train, y_train)
        n_test = _write_csv(test_path, feature_names, X_test, y_test)

        print(f"  {len(features):>10,} rows ({skipped:,} skipped) in {elapsed:.1f}s")
        print(f"  Train: {n_train:,}  Test: {n_test:,}")
        for cls_idx in sorted(class_counts):
            cls_name = ACTION_LABELS[cls_idx]
            cnt = class_counts[cls_idx]
            pct = 100.0 * cnt / len(labels) if labels else 0
            print(f"    {cls_name:8s}: {cnt:>10,} ({pct:5.1f}%)")

        # Report
        report_lines.append(f"Archetype: {archetype}")
        report_lines.append(f"  Processed: {processed:,}  Featurized: {len(features):,}  Skipped: {skipped:,}")
        report_lines.append(f"  Train: {n_train:,}  Test: {n_test:,}")
        for cls_idx in sorted(class_counts):
            cls_name = ACTION_LABELS[cls_idx]
            cnt = class_counts[cls_idx]
            pct = 100.0 * cnt / len(labels) if labels else 0
            report_lines.append(f"    {cls_name:8s}: {cnt:>10,} ({pct:5.1f}%)")
        report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append(f"TOTAL: {total_rows:,} featurized rows, {total_skipped:,} skipped")

    report_text = "\n".join(report_lines)
    report_path = os.path.join(outdir, "extraction_report.txt")
    with open(report_path, "w") as f:
        f.write(report_text + "\n")
    print(f"\nReport written to {report_path}")
    print(f"Total: {total_rows:,} featurized, {total_skipped:,} skipped")

    db.close()
    return report_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", required=True, help="Path to Phase 1 SQLite database")
    parser.add_argument("--outdir", default="ml/data/", help="Output directory for CSVs")
    parser.add_argument("--with-hs", action="store_true",
                        help="Include hand_strength from showdown data (limits to showdown hands)")
    parser.add_argument("--test-fraction", type=float, default=0.2,
                        help="Fraction held out for test (default: 0.2)")
    args = parser.parse_args(argv)

    extract(args.db, args.outdir, with_hand_strength=args.with_hs,
            test_fraction=args.test_fraction)
    return 0


if __name__ == "__main__":
    sys.exit(main())
