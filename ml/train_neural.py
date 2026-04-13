"""Train neural network (MLP) models for each archetype using sklearn.

Uses sklearn's MLPClassifier — no PyTorch/TensorFlow dependency. Architecture
is deliberately small (9→64→32→5) since the feature space is only 7-8
dimensions with 600K-1.1M training examples per archetype.

Usage::

    python -m ml.train_neural --datadir ml/data/ --outdir ml/models/
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

from ml.feature_engineering import ARCHETYPES, ACTION_LABELS, get_feature_names


def _load_csv(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load a feature CSV into (X, y) numpy arrays."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    X = np.array([[float(v) for v in row[:-1]] for row in rows], dtype=np.float64)
    y = np.array([int(row[-1]) for row in rows], dtype=np.int32)
    return X, y


NN_PARAMS = {
    "hidden_layer_sizes": (64, 32),
    "activation": "relu",
    "solver": "adam",
    "max_iter": 200,
    "batch_size": 256,
    "learning_rate": "adaptive",
    "learning_rate_init": 0.001,
    "early_stopping": True,
    "validation_fraction": 0.1,
    "random_state": 42,
    "verbose": False,
}


def train_all(datadir: str, outdir: str) -> str:
    """Train neural network models for all archetypes. Returns report text."""
    from sklearn.neural_network import MLPClassifier
    from sklearn.metrics import accuracy_score, classification_report
    import joblib

    model_dir = os.path.join(outdir, "nn")
    os.makedirs(model_dir, exist_ok=True)

    report_lines: List[str] = []
    report_lines.append("PHASE 2 TRAINING REPORT — NEURAL NETWORK (MLP)")
    report_lines.append("=" * 60)
    report_lines.append(f"Architecture: {NN_PARAMS['hidden_layer_sizes']}")
    report_lines.append(f"Activation: {NN_PARAMS['activation']}")
    report_lines.append(f"Max iterations: {NN_PARAMS['max_iter']}")
    report_lines.append("")

    accuracies: Dict[str, float] = {}

    for archetype in ARCHETYPES:
        train_path = os.path.join(datadir, f"{archetype}_train.csv")
        test_path = os.path.join(datadir, f"{archetype}_test.csv")

        if not os.path.exists(train_path) or not os.path.exists(test_path):
            print(f"  {archetype}: SKIP (missing CSV)")
            report_lines.append(f"\n  {archetype}: SKIPPED\n")
            continue

        print(f"  Training nn/{archetype}...", end=" ", flush=True)
        t0 = time.time()

        X_train, y_train = _load_csv(train_path)
        X_test, y_test = _load_csv(test_path)

        model = MLPClassifier(**NN_PARAMS)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        elapsed = time.time() - t0
        n_iter = model.n_iter_

        model_path = os.path.join(model_dir, f"{archetype}.pkl")
        joblib.dump(model, model_path)

        print(f"acc={acc:.3f}  epochs={n_iter}  ({elapsed:.1f}s)")

        accuracies[archetype] = acc

        cr = classification_report(
            y_test, y_pred,
            labels=list(range(5)),
            target_names=ACTION_LABELS,
            zero_division=0,
        )
        report_lines.append(f"Archetype: {archetype}")
        report_lines.append(f"  Train: {len(y_train):,}  Test: {len(y_test):,}")
        report_lines.append(f"  Accuracy: {acc * 100:.1f}%")
        report_lines.append(f"  Epochs: {n_iter}  Time: {elapsed:.1f}s")
        report_lines.append(f"  Classification report:\n{cr}")

    # Summary
    report_lines.append("=" * 60)
    report_lines.append("ACCURACY SUMMARY — NEURAL NETWORK")
    report_lines.append("=" * 60)
    for arch in ARCHETYPES:
        acc = accuracies.get(arch)
        acc_str = f"{acc * 100:.1f}%" if acc is not None else "---"
        report_lines.append(f"  {arch:<15}  {acc_str:>8}")
    if accuracies:
        mean_acc = sum(accuracies.values()) / len(accuracies)
        report_lines.append(f"  {'MEAN':<15}  {mean_acc * 100:.1f}%")

    report_text = "\n".join(report_lines)
    report_path = os.path.join(outdir, "training_report_nn.txt")
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
    args = parser.parse_args(argv)

    train_all(args.datadir, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
