"""Three-way model comparison across logistic regression, random forest, and MLP.

Loads all trained models, evaluates on the test set, and produces a
side-by-side accuracy comparison plus feature importance analysis.

Usage::

    python -m ml.evaluate_models --datadir ml/data/ --modeldir ml/models/
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
from typing import Dict, List, Tuple

import numpy as np

from phase2.ml.feature_engineering import ARCHETYPES, ACTION_LABELS


def _load_csv(path: str) -> Tuple[np.ndarray, np.ndarray]:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    X = np.array([[float(v) for v in row[:-1]] for row in rows], dtype=np.float64)
    y = np.array([int(row[-1]) for row in rows], dtype=np.int32)
    return X, y, header[:-1]


def evaluate_all(datadir: str, modeldir: str) -> str:
    """Evaluate all model types against test data. Returns report text."""
    from sklearn.metrics import accuracy_score
    import joblib

    model_types = ["logreg", "rf", "nn"]
    results: Dict[str, Dict[str, float]] = {mt: {} for mt in model_types}
    importances: Dict[str, Dict[str, List[float]]] = {}  # arch -> {feat: imp}

    for archetype in ARCHETYPES:
        test_path = os.path.join(datadir, f"{archetype}_test.csv")
        if not os.path.exists(test_path):
            continue

        X_test, y_test, feat_names = _load_csv(test_path)

        for mt in model_types:
            model_path = os.path.join(modeldir, mt, f"{archetype}.pkl")
            if not os.path.exists(model_path):
                continue
            model = joblib.load(model_path)
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            results[mt][archetype] = acc

            # Feature importances for RF
            if mt == "rf" and hasattr(model, "feature_importances_"):
                importances[archetype] = {
                    name: float(imp)
                    for name, imp in zip(feat_names, model.feature_importances_)
                }

    # Build report
    lines: List[str] = []
    lines.append("PHASE 2 MODEL COMPARISON")
    lines.append("=" * 70)
    lines.append("")

    # Accuracy table
    lines.append("TEST SET ACCURACY")
    lines.append("-" * 60)
    header = f"  {'Archetype':<15}" + "".join(f"  {mt:>8}" for mt in model_types) + "    Best"
    lines.append(header)
    lines.append("  " + "-" * 55)
    for arch in ARCHETYPES:
        cells = []
        best_mt = ""
        best_acc = -1
        for mt in model_types:
            acc = results[mt].get(arch)
            if acc is not None:
                cells.append(f"  {acc * 100:7.1f}%")
                if acc > best_acc:
                    best_acc = acc
                    best_mt = mt
            else:
                cells.append("     ---")
        lines.append(f"  {arch:<15}" + "".join(cells) + f"    {best_mt}")
    # Mean
    means = []
    for mt in model_types:
        vals = list(results[mt].values())
        means.append(f"  {sum(vals) / len(vals) * 100:7.1f}%" if vals else "     ---")
    lines.append(f"  {'MEAN':<15}" + "".join(means))
    lines.append("")

    # Feature importance table (RF)
    if importances:
        lines.append("FEATURE IMPORTANCE (Random Forest)")
        lines.append("-" * 70)
        all_feats = list(next(iter(importances.values())).keys())
        header = f"  {'Feature':<22}" + "".join(f"  {a[:8]:>8}" for a in ARCHETYPES)
        lines.append(header)
        lines.append("  " + "-" * (22 + 10 * len(ARCHETYPES)))
        for feat in all_feats:
            cells = []
            for arch in ARCHETYPES:
                imp = importances.get(arch, {}).get(feat)
                cells.append(f"  {imp:8.3f}" if imp is not None else "     ---")
            lines.append(f"  {feat:<22}" + "".join(cells))
        lines.append("")

        # Top feature per archetype
        lines.append("TOP FEATURE PER ARCHETYPE (RF)")
        lines.append("-" * 50)
        for arch in ARCHETYPES:
            if arch not in importances:
                continue
            top = max(importances[arch].items(), key=lambda x: x[1])
            lines.append(f"  {arch:<15}  {top[0]} ({top[1]:.3f})")

    report_text = "\n".join(lines)
    report_path = os.path.join(modeldir, "model_comparison.txt")
    with open(report_path, "w") as f:
        f.write(report_text + "\n")
    print(report_text)
    print(f"\nSaved to {report_path}")
    return report_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datadir", default="ml/data/")
    parser.add_argument("--modeldir", default="ml/models/")
    args = parser.parse_args(argv)
    evaluate_all(args.datadir, args.modeldir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
