"""Train logistic regression and random forest models for each archetype.

Reads per-archetype train/test CSVs produced by ``extract_training_data.py``
and trains two model types per archetype: multinomial logistic regression
and random forest. Saves models via joblib and writes a training report.

Usage::

    python -m ml.train_traditional --datadir ml/data/ --outdir ml/models/
    python -m ml.train_traditional --datadir ml/data/ --outdir ml/models/ --model-type rf
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
import os
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

from phase2.ml.feature_engineering import ARCHETYPES, ACTION_LABELS, get_feature_names


def _load_csv(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load a feature CSV into (X, y) numpy arrays."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    X = np.array([[float(v) for v in row[:-1]] for row in rows], dtype=np.float64)
    y = np.array([int(row[-1]) for row in rows], dtype=np.int32)
    return X, y


def train_all(
    datadir: str,
    outdir: str,
    model_types: List[str] = None,
) -> str:
    """Train models for all archetypes. Returns the report text."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    import joblib

    if model_types is None:
        model_types = ["logreg", "rf"]

    CONFIGS = {
        "logreg": {
            "class": LogisticRegression,
            "params": {
                "solver": "lbfgs",
                "max_iter": 1000,
                "C": 1.0,
                "random_state": 42,
            },
        },
        "rf": {
            "class": RandomForestClassifier,
            "params": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 20,
                "min_samples_leaf": 10,
                "random_state": 42,
                "n_jobs": -1,
            },
        },
    }

    report_lines: List[str] = []
    report_lines.append("PHASE 2 TRAINING REPORT — TRADITIONAL ML")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Summary table collected across all archetypes
    summary: Dict[str, Dict[str, float]] = {}  # model_type -> arch -> accuracy

    for mt in model_types:
        if mt not in CONFIGS:
            print(f"Unknown model type: {mt}")
            continue

        cfg = CONFIGS[mt]
        model_dir = os.path.join(outdir, mt)
        os.makedirs(model_dir, exist_ok=True)

        report_lines.append(f"MODEL TYPE: {mt.upper()}")
        report_lines.append("-" * 40)
        summary[mt] = {}

        for archetype in ARCHETYPES:
            train_path = os.path.join(datadir, f"{archetype}_train.csv")
            test_path = os.path.join(datadir, f"{archetype}_test.csv")

            if not os.path.exists(train_path) or not os.path.exists(test_path):
                print(f"  {archetype}: SKIP (missing CSV)")
                report_lines.append(f"\n  {archetype}: SKIPPED — missing data\n")
                continue

            print(f"  Training {mt}/{archetype}...", end=" ", flush=True)
            t0 = time.time()

            X_train, y_train = _load_csv(train_path)
            X_test, y_test = _load_csv(test_path)

            model = cfg["class"](**cfg["params"])
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            elapsed = time.time() - t0

            # Save model
            model_path = os.path.join(model_dir, f"{archetype}.pkl")
            joblib.dump(model, model_path)

            print(f"acc={acc:.3f}  ({elapsed:.1f}s)")

            summary[mt][archetype] = acc

            # Detailed report
            report_lines.append(f"\nArchetype: {archetype}")
            report_lines.append(f"  Train: {len(y_train):,}  Test: {len(y_test):,}")
            report_lines.append(f"  Accuracy: {acc * 100:.1f}%")
            report_lines.append(f"  Time: {elapsed:.1f}s")
            cr = classification_report(
                y_test, y_pred,
                labels=list(range(5)),
                target_names=ACTION_LABELS,
                zero_division=0,
            )
            report_lines.append(f"  Classification report:\n{cr}")

            # Feature importances (RF only)
            if mt == "rf" and hasattr(model, "feature_importances_"):
                # Detect which feature set was used from CSV header
                with open(train_path) as f:
                    header = next(csv.reader(f))
                feat_names = header[:-1]  # everything except 'label'
                importances = model.feature_importances_
                report_lines.append("  Feature importances:")
                for name, imp in sorted(
                    zip(feat_names, importances), key=lambda x: -x[1]
                ):
                    report_lines.append(f"    {name:25s}  {imp:.4f}")

        report_lines.append("")

    # Summary table
    report_lines.append("=" * 60)
    report_lines.append("ACCURACY SUMMARY")
    report_lines.append("=" * 60)
    header = f"  {'Archetype':<15}" + "".join(f"  {mt:>8}" for mt in model_types)
    report_lines.append(header)
    report_lines.append("  " + "-" * (15 + 10 * len(model_types)))
    for arch in ARCHETYPES:
        cells = []
        for mt in model_types:
            acc = summary.get(mt, {}).get(arch)
            cells.append(f"  {acc * 100:7.1f}%" if acc is not None else "     ---")
        report_lines.append(f"  {arch:<15}" + "".join(cells))
    # Mean
    means = []
    for mt in model_types:
        vals = [v for v in summary.get(mt, {}).values()]
        means.append(f"  {sum(vals) / len(vals) * 100:7.1f}%" if vals else "     ---")
    report_lines.append(f"  {'MEAN':<15}" + "".join(means))

    report_text = "\n".join(report_lines)
    report_path = os.path.join(outdir, "training_report_traditional.txt")
    with open(report_path, "w") as f:
        f.write(report_text + "\n")
    print(f"\nReport: {report_path}")

    return report_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datadir", default="ml/data/",
                        help="Directory with per-archetype CSVs")
    parser.add_argument("--outdir", default="ml/models/",
                        help="Output directory for saved models")
    parser.add_argument("--model-type", default="logreg,rf",
                        help="Comma-separated model types to train (default: logreg,rf)")
    args = parser.parse_args(argv)

    model_types = [m.strip() for m in args.model_type.split(",")]
    train_all(args.datadir, args.outdir, model_types)
    return 0


if __name__ == "__main__":
    sys.exit(main())
