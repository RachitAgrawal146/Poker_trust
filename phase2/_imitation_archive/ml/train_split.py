"""Train split-context models: one for 'no bet pending' (check/bet) and
one for 'facing a bet' (fold/call/raise), per archetype.

This mirrors the rule-based agent's two-stage decision tree exactly:
  1. cost_to_call == 0 → binary: BET or CHECK
  2. cost_to_call >  0 → three-way: FOLD, CALL, or RAISE

A single 5-way classifier fails because the majority class (fold, ~55%
for tight agents) pulls probability mass away from bet/raise even in
contexts where fold is illegal. Splitting eliminates this cross-contamination
and produces correct AF/PFR.

Usage::

    python -m ml.train_split --datadir ml/data_live/ --outdir ml/models_split/
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
import warnings
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np

warnings.filterwarnings("ignore")

from phase2.ml.feature_engineering import ARCHETYPES, ACTION_LABELS


def _load_csv(path: str) -> Tuple[np.ndarray, np.ndarray]:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    X = np.array([[float(v) for v in row[:-1]] for row in rows], dtype=np.float64)
    y = np.array([int(row[-1]) for row in rows], dtype=np.int32)
    return X, y


def _split_by_context(X: np.ndarray, y: np.ndarray, is_facing_col: int = 6):
    """Split data into nobet (is_facing==0) and facing (is_facing==1) subsets."""
    nobet_mask = X[:, is_facing_col] < 0.5
    facing_mask = ~nobet_mask
    return (X[nobet_mask], y[nobet_mask]), (X[facing_mask], y[facing_mask])


def train_all(datadir: str, outdir: str) -> str:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    import joblib

    RF_PARAMS = {
        "n_estimators": 200,
        "max_depth": 12,
        "min_samples_split": 10,
        "min_samples_leaf": 5,
        "random_state": 42,
        "n_jobs": -1,
    }

    model_dir = os.path.join(outdir, "rf")
    os.makedirs(model_dir, exist_ok=True)

    lines: List[str] = []
    lines.append("PHASE 2 SPLIT-CONTEXT TRAINING REPORT")
    lines.append("=" * 60)
    lines.append("Two models per archetype:")
    lines.append("  nobet:  CHECK(1) vs BET(3)        — when cost_to_call == 0")
    lines.append("  facing: FOLD(0) vs CALL(2) vs RAISE(4) — when cost_to_call > 0")
    lines.append("")

    for archetype in ARCHETYPES:
        train_path = os.path.join(datadir, f"{archetype}_train.csv")
        test_path = os.path.join(datadir, f"{archetype}_test.csv")
        if not os.path.exists(train_path):
            print(f"  {archetype}: SKIP (missing CSV)")
            continue

        print(f"  {archetype}:", end=" ", flush=True)
        t0 = time.time()

        X_train, y_train = _load_csv(train_path)
        X_test, y_test = _load_csv(test_path)

        # Split into contexts
        (X_nb_train, y_nb_train), (X_fb_train, y_fb_train) = _split_by_context(X_train, y_train)
        (X_nb_test, y_nb_test), (X_fb_test, y_fb_test) = _split_by_context(X_test, y_test)

        # Train nobet model (check=1 vs bet=3)
        model_nb = RandomForestClassifier(**RF_PARAMS)
        model_nb.fit(X_nb_train, y_nb_train)
        y_nb_pred = model_nb.predict(X_nb_test)
        acc_nb = accuracy_score(y_nb_test, y_nb_pred)

        # Train facing model (fold=0 vs call=2 vs raise=4)
        model_fb = RandomForestClassifier(**RF_PARAMS)
        model_fb.fit(X_fb_train, y_fb_train)
        y_fb_pred = model_fb.predict(X_fb_test)
        acc_fb = accuracy_score(y_fb_test, y_fb_pred)

        elapsed = time.time() - t0

        # Save both models
        joblib.dump(model_nb, os.path.join(model_dir, f"{archetype}_nobet.pkl"))
        joblib.dump(model_fb, os.path.join(model_dir, f"{archetype}_facing.pkl"))

        print(f"nobet={acc_nb:.3f} ({len(y_nb_train):,} train)  "
              f"facing={acc_fb:.3f} ({len(y_fb_train):,} train)  ({elapsed:.1f}s)")

        # Class distributions
        nb_classes = defaultdict(int)
        for label in y_nb_train:
            nb_classes[label] += 1
        fb_classes = defaultdict(int)
        for label in y_fb_train:
            fb_classes[label] += 1

        lines.append(f"Archetype: {archetype}")
        lines.append(f"  Nobet model: acc={acc_nb:.3f}  train={len(y_nb_train):,}  test={len(y_nb_test):,}")
        lines.append(f"    Classes: " + ", ".join(
            f"{ACTION_LABELS[k]}={v}" for k, v in sorted(nb_classes.items())
        ))
        bet_pct = nb_classes.get(3, 0) / max(len(y_nb_train), 1) * 100
        lines.append(f"    Bet rate in training data: {bet_pct:.1f}%")
        lines.append(f"  Facing model: acc={acc_fb:.3f}  train={len(y_fb_train):,}  test={len(y_fb_test):,}")
        lines.append(f"    Classes: " + ", ".join(
            f"{ACTION_LABELS[k]}={v}" for k, v in sorted(fb_classes.items())
        ))
        raise_pct = fb_classes.get(4, 0) / max(len(y_fb_train), 1) * 100
        fold_pct = fb_classes.get(0, 0) / max(len(y_fb_train), 1) * 100
        lines.append(f"    Raise rate: {raise_pct:.1f}%  Fold rate: {fold_pct:.1f}%")

        # Feature importances for facing model (most interesting)
        feat_names = None
        with open(train_path) as f:
            feat_names = next(csv.reader(f))[:-1]
        if feat_names and hasattr(model_fb, "feature_importances_"):
            lines.append(f"  Facing model feature importances:")
            for name, imp in sorted(
                zip(feat_names, model_fb.feature_importances_), key=lambda x: -x[1]
            ):
                lines.append(f"    {name:25s}  {imp:.4f}")
        lines.append("")

    report = "\n".join(lines)
    report_path = os.path.join(outdir, "training_report_split.txt")
    with open(report_path, "w") as f:
        f.write(report + "\n")
    print(f"\nReport: {report_path}")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datadir", default="ml/data_live/")
    parser.add_argument("--outdir", default="ml/models_split/")
    args = parser.parse_args(argv)
    train_all(args.datadir, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
