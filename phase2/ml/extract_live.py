"""Live extraction: run a fresh Phase 1 simulation and capture hand strength
directly from each agent's decision cache.

Unlike ``extract_training_data.py`` (which reads from SQLite and lacks hand
strength for non-showdown hands), this runs the actual simulation and
intercepts each agent's ``_hs_cache`` at decision time. Every action gets
ground-truth hand strength — including folds, which never appear in
showdown-based extraction.

This eliminates both failure modes:
  - Without HS: models can't distinguish when to bet → all play passive
  - Showdown-only HS: selection bias → models learn to overcall, never fold

Usage::

    python -m ml.extract_live --hands 2000 --seeds 42,137,256 --outdir ml/data_live/

Then train as usual::

    python -m ml.train_traditional --datadir ml/data_live/ --outdir ml/models_live/
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
import warnings

warnings.filterwarnings("ignore")
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

from phase2.ml.feature_engineering import (
    ARCHETYPES,
    ACTION_LABELS,
    ACTION_TO_INT,
    get_feature_names,
)


def _intercept_actions(table, hand_number: int, per_arch: Dict[str, List]):
    """After a hand is played, walk the action log and pair each action
    with the acting agent's cached hand strength for that round.

    The key insight: ``BaseAgent._hs_cache`` is populated during
    ``decide_action()`` and cleared at the NEXT ``on_hand_start()``.
    At the time ``play_hand()`` returns, every agent still has its
    cache from the just-completed hand.
    """
    hand = table.last_hand
    if hand is None:
        return

    for rec in hand.action_log:
        agent = table.seats[rec.seat]
        archetype = rec.archetype

        # Get hand strength from the agent's cache for this round.
        # DummyAgents don't have _hs_cache, but we only care about
        # BaseAgent subclasses (the 8 archetypes).
        hs_cache = getattr(agent, "_hs_cache", {})
        hs_str = hs_cache.get(rec.betting_round)

        if hs_str is None:
            # Agent didn't compute HS for this round (e.g., folded before
            # acting, or it's a dummy agent). Skip this action.
            continue

        hs_map = {"Strong": 1.0, "Medium": 0.5, "Weak": 0.0}
        hs_val = hs_map.get(hs_str)
        if hs_val is None:
            continue

        label = ACTION_TO_INT.get(rec.action_type.value)
        if label is None:
            continue

        round_map = {"preflop": 0.0, "flop": 0.25, "turn": 0.5, "river": 0.75}

        # Derive cost_to_call from game state, NOT from the action taken.
        # This must match what MLAgent sees at inference time:
        #   cost_to_call = max(0, current_bet - round_contribution)
        # Since we don't have per-agent round_contribution in the log, we
        # use the action semantics:
        #   BET/CHECK: agent wasn't facing a bet → cost_to_call = 0
        #   CALL: amount = the cost they paid to match
        #   RAISE: they faced a cost before raising. The cost they faced is
        #          (current_bet_before_raise - their_contribution). We can
        #          approximate: current_bet after raise minus the raise
        #          increment = the bet level before they raised.
        #   FOLD: they faced a cost but didn't pay. Similar to raise logic.
        #
        # The key rule: is_facing_bet must be 1.0 whenever cost_to_call > 0,
        # matching the inference-side logic in MLAgent.decide_action.
        action = rec.action_type.value
        bet_size = 2 if rec.betting_round in ("preflop", "flop") else 4

        if action in ("check", "bet"):
            cost = 0.0
            is_facing = 0.0
        elif action == "call":
            cost = rec.amount / 200.0
            is_facing = 1.0
        elif action == "raise":
            # Cost they faced = current_bet (after raise) - bet_size = level before raise
            cost_before = max(rec.current_bet - bet_size, 0)
            cost = min(cost_before, 16) / 200.0
            is_facing = 1.0 if cost > 0 else 0.0
        elif action == "fold":
            # They faced a cost and folded. Use current_bet as the level.
            cost = min(rec.current_bet, 16) / 200.0
            is_facing = 1.0
        else:
            cost = 0.0
            is_facing = 0.0

        position = ((rec.seat - hand.dealer_seat) % 8) / 7.0

        features = [
            round_map.get(rec.betting_round, 0.0),
            rec.pot_before / 200.0,
            rec.stack_before / 200.0,
            cost,
            rec.bet_count / 4.0,
            position,
            is_facing,
            hs_val,
        ]

        per_arch.setdefault(archetype, []).append((features, label))


def _stratified_split(
    data: List[Tuple[List[float], int]],
    test_fraction: float = 0.2,
    seed: int = 42,
) -> Tuple[List, List, List, List]:
    """Stratified train/test split preserving class proportions."""
    rng = np.random.default_rng(seed)
    by_class: Dict[int, List[int]] = defaultdict(list)
    for i, (_, label) in enumerate(data):
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

    X_train = [data[i][0] for i in train_idx]
    y_train = [data[i][1] for i in train_idx]
    X_test = [data[i][0] for i in test_idx]
    y_test = [data[i][1] for i in test_idx]
    return X_train, y_train, X_test, y_test


def _write_csv(
    path: str,
    header: List[str],
    features: List[List[float]],
    labels: List[int],
) -> int:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header + ["label"])
        for feat, label in zip(features, labels):
            writer.writerow([f"{v:.6f}" for v in feat] + [label])
    return len(features)


def extract_live(
    num_hands: int = 2000,
    seeds: List[int] = None,
    outdir: str = "ml/data_live/",
    test_fraction: float = 0.2,
) -> str:
    """Run Phase 1 simulations and extract training data with full hand
    strength for every action."""
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from agents.predator import Predator
    from agents.mirror import Mirror
    from agents.judge import Judge
    from engine.table import Table

    if seeds is None:
        seeds = [42, 137, 256]

    os.makedirs(outdir, exist_ok=True)

    per_arch: Dict[str, List] = {}
    total_hands = 0

    for seed in seeds:
        agents = [
            Oracle(seat=0),
            Sentinel(seat=1),
            Firestorm(seat=2),
            Wall(seat=3),
            Phantom(seat=4),
            Predator(seat=5),
            Mirror(seat=6),
            Judge(seat=7),
        ]
        table = Table(agents, seed=seed)

        print(f"  Running seed={seed}, {num_hands} hands...", end=" ", flush=True)
        t0 = time.time()
        for i in range(1, num_hands + 1):
            table.play_hand()
            _intercept_actions(table, i, per_arch)
            if i % 500 == 0:
                print(f"{i}", end=" ", flush=True)
        elapsed = time.time() - t0
        total_hands += num_hands
        print(f"done ({elapsed:.1f}s, {num_hands/elapsed:.1f} hand/s)")

    # Write per-archetype CSVs
    feature_names = get_feature_names(include_hand_strength=True)
    report_lines = [
        "LIVE EXTRACTION REPORT",
        "=" * 60,
        f"Seeds: {seeds}",
        f"Hands per seed: {num_hands}",
        f"Total hands: {total_hands}",
        f"Features: {feature_names}",
        "",
    ]

    for archetype in ARCHETYPES:
        data = per_arch.get(archetype, [])
        if not data:
            print(f"  {archetype}: NO DATA")
            report_lines.append(f"{archetype}: NO DATA\n")
            continue

        X_train, y_train, X_test, y_test = _stratified_split(
            data, test_fraction=test_fraction
        )

        train_path = os.path.join(outdir, f"{archetype}_train.csv")
        test_path = os.path.join(outdir, f"{archetype}_test.csv")
        n_train = _write_csv(train_path, feature_names, X_train, y_train)
        n_test = _write_csv(test_path, feature_names, X_test, y_test)

        # Class distribution
        class_counts = defaultdict(int)
        for _, label in data:
            class_counts[label] += 1

        print(f"  {archetype}: {len(data):,} rows → {n_train:,} train, {n_test:,} test")
        report_lines.append(f"Archetype: {archetype}")
        report_lines.append(f"  Total: {len(data):,}  Train: {n_train:,}  Test: {n_test:,}")
        for cls_idx in sorted(class_counts):
            cls_name = ACTION_LABELS[cls_idx]
            cnt = class_counts[cls_idx]
            pct = 100.0 * cnt / len(data)
            print(f"    {cls_name:8s}: {cnt:>8,} ({pct:5.1f}%)")
            report_lines.append(f"    {cls_name:8s}: {cnt:>8,} ({pct:5.1f}%)")
        report_lines.append("")

    report_text = "\n".join(report_lines)
    report_path = os.path.join(outdir, "extraction_report.txt")
    with open(report_path, "w") as f:
        f.write(report_text + "\n")
    print(f"\nReport: {report_path}")
    return report_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--hands", type=int, default=2000,
                        help="Hands per seed (default: 2000)")
    parser.add_argument("--seeds", default="42,137,256",
                        help="Comma-separated seeds (default: 42,137,256)")
    parser.add_argument("--outdir", default="ml/data_live/",
                        help="Output directory (default: ml/data_live/)")
    args = parser.parse_args(argv)

    seeds = [int(s.strip()) for s in args.seeds.split(",")]
    extract_live(args.hands, seeds, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
