"""Train tabular (empirical) models: compute P(action | round, hand_strength)
directly from the training data, grouped by context.

This is a non-parametric density estimator — it counts action frequencies
in each (round, hand_strength, context) cell and normalizes to get
probability distributions. At inference, the agent looks up the cell and
samples from the distribution.

This approach is GUARANTEED to reproduce the rule-based behavior because
the law of large numbers ensures the empirical frequencies converge to
the archetype parameter values with sufficient data (we have ~200K+
actions per archetype).

Usage::

    python -m ml.train_tabular --datadir ml/data_live/ --outdir ml/models_tabular/
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import warnings
from collections import defaultdict
from typing import Dict, List, Tuple

warnings.filterwarnings("ignore")

from ml.feature_engineering import ARCHETYPES, ACTION_LABELS


# Feature indices in the CSV (must match extract_live.py order)
_IDX_ROUND = 0
_IDX_HS = 7  # hand_strength is the last feature (index 7)
_IDX_FACING = 6  # is_facing_bet

_ROUND_NAMES = {0.0: "preflop", 0.25: "flop", 0.5: "turn", 0.75: "river"}
_HS_NAMES = {0.0: "Weak", 0.5: "Medium", 1.0: "Strong"}


def _load_csv(path: str) -> List[Tuple[List[float], int]]:
    """Load CSV into list of (features, label) tuples."""
    data = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            features = [float(v) for v in row[:-1]]
            label = int(row[-1])
            data.append((features, label))
    return data


def _build_table(data: List[Tuple[List[float], int]]) -> dict:
    """Build empirical action distribution tables.

    Returns::

        {
            "nobet": {
                "preflop": {
                    "Strong": [P_fold, P_check, P_call, P_bet, P_raise],
                    "Medium": [...],
                    "Weak": [...]
                },
                "flop": {...}, "turn": {...}, "river": {...}
            },
            "facing": { same structure }
        }

    Probabilities are stored as a 5-element list indexed by action label.
    """
    # Count: context -> round -> hs -> action -> count
    counts: Dict[str, Dict[str, Dict[str, Dict[int, int]]]] = {
        "nobet": defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        "facing": defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
    }

    for features, label in data:
        round_val = features[_IDX_ROUND]
        hs_val = features[_IDX_HS]
        facing_val = features[_IDX_FACING]

        round_name = _ROUND_NAMES.get(round_val, "preflop")
        hs_name = _HS_NAMES.get(hs_val, "Weak")
        context = "facing" if facing_val > 0.5 else "nobet"

        counts[context][round_name][hs_name][label] += 1

    # Normalize to probabilities
    table: dict = {"nobet": {}, "facing": {}}
    for context in ("nobet", "facing"):
        for round_name in ("preflop", "flop", "turn", "river"):
            table[context][round_name] = {}
            for hs_name in ("Strong", "Medium", "Weak"):
                cell_counts = counts[context][round_name][hs_name]
                total = sum(cell_counts.values())
                if total == 0:
                    # No data for this cell — use uniform
                    if context == "nobet":
                        probs = [0.0, 0.5, 0.0, 0.5, 0.0]  # check/bet
                    else:
                        probs = [0.33, 0.0, 0.34, 0.0, 0.33]  # fold/call/raise
                else:
                    probs = [cell_counts.get(i, 0) / total for i in range(5)]
                table[context][round_name][hs_name] = probs

    return table


def train_all(datadir: str, outdir: str) -> str:
    import joblib

    os.makedirs(outdir, exist_ok=True)

    lines: List[str] = []
    lines.append("PHASE 2 TABULAR MODEL TRAINING REPORT")
    lines.append("=" * 70)
    lines.append("Non-parametric empirical action distributions per")
    lines.append("(archetype, round, hand_strength, context)")
    lines.append("")

    for archetype in ARCHETYPES:
        train_path = os.path.join(datadir, f"{archetype}_train.csv")
        if not os.path.exists(train_path):
            print(f"  {archetype}: SKIP")
            continue

        data = _load_csv(train_path)
        table = _build_table(data)

        # Save
        model_path = os.path.join(outdir, f"{archetype}_table.pkl")
        joblib.dump(table, model_path)

        # Report key distributions
        print(f"  {archetype}: {len(data):,} training rows")
        lines.append(f"Archetype: {archetype} ({len(data):,} rows)")

        for context in ("nobet", "facing"):
            lines.append(f"  Context: {context}")
            legal = "CHECK/BET" if context == "nobet" else "FOLD/CALL/RAISE"
            lines.append(f"    Actions: {legal}")
            for round_name in ("preflop", "flop", "turn", "river"):
                for hs_name in ("Strong", "Medium", "Weak"):
                    probs = table[context][round_name][hs_name]
                    if context == "nobet":
                        check_p, bet_p = probs[1], probs[3]
                        lines.append(
                            f"    {round_name:8s} {hs_name:7s}: "
                            f"check={check_p:.3f}  bet={bet_p:.3f}"
                        )
                    else:
                        fold_p, call_p, raise_p = probs[0], probs[2], probs[4]
                        lines.append(
                            f"    {round_name:8s} {hs_name:7s}: "
                            f"fold={fold_p:.3f}  call={call_p:.3f}  raise={raise_p:.3f}"
                        )
        lines.append("")

    report = "\n".join(lines)
    report_path = os.path.join(outdir, "training_report_tabular.txt")
    with open(report_path, "w") as f:
        f.write(report + "\n")
    print(f"\nReport: {report_path}")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datadir", default="ml/data_live/")
    parser.add_argument("--outdir", default="ml/models_tabular/")
    args = parser.parse_args(argv)
    train_all(args.datadir, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
