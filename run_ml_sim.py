"""Phase 2: Run 8 ML-powered agents through the same game engine.

Uses the SAME engine, SAME trust model, SAME analysis pipeline as Phase 1.
Only the agents are different — each seat is an MLAgent that loads a trained
sklearn model and samples from ``predict_proba`` for every decision.

Usage::

    python run_ml_sim.py --model-type rf --hands 25000 --seeds 42,137,256,512,1024 \\
        --db ml_runs_rf.sqlite --modeldir ml/models/rf/

    python run_ml_sim.py --model-type nn --hands 25000 --seeds 42,137,256,512,1024 \\
        --db ml_runs_nn.sqlite --modeldir ml/models/nn/

After the run, use the SAME analysis scripts as Phase 1::

    python analyze_runs.py --db ml_runs_rf.sqlite
    python deep_analysis.py --db ml_runs_rf.sqlite --out ml_analysis_rf.txt
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import argparse
import os
import sys
import time
from typing import Dict, List

from agents.ml_agent import MLAgent
from config import SIMULATION
from data.sqlite_logger import SQLiteLogger
from engine.table import Table
from ml.feature_engineering import ARCHETYPES


def build_ml_agents(model_dir: str) -> List[MLAgent]:
    """Build 8 ML agents, one per archetype, matching Phase 1 seating."""
    agents = []
    for seat, archetype in enumerate(ARCHETYPES):
        # Check for any model type: tabular, split RF, or single model
        table_path = os.path.join(model_dir, f"{archetype}_table.pkl")
        nobet_path = os.path.join(model_dir, f"{archetype}_nobet.pkl")
        single_path = os.path.join(model_dir, f"{archetype}.pkl")
        if not any(os.path.exists(p) for p in [table_path, nobet_path, single_path]):
            raise FileNotFoundError(
                f"No trained model for {archetype} in {model_dir}. "
                f"Run train_tabular.py, train_split.py, or train_traditional.py first."
            )
        agents.append(MLAgent(
            seat=seat,
            archetype=archetype,
            model_dir=model_dir,
        ))
    return agents


def _fmt_eta(seconds: float) -> str:
    if seconds <= 0 or seconds != seconds:
        return "--:--"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _print_progress(seed: int, hand_i: int, total: int, started: float):
    elapsed = time.time() - started
    rate = hand_i / elapsed if elapsed > 0 else 0.0
    remaining = (total - hand_i) / rate if rate > 0 else 0.0
    pct = 100.0 * hand_i / total if total else 100.0
    bar_width = 30
    filled = int(bar_width * hand_i / total) if total else bar_width
    bar = "#" * filled + "." * (bar_width - filled)
    msg = (
        f"\r  seed {seed:>5} [{bar}] {hand_i:>6}/{total:<6} "
        f"{pct:5.1f}% · {rate:6.1f} hand/s · ETA {_fmt_eta(remaining)}"
    )
    sys.stdout.write(msg)
    sys.stdout.flush()


def run_one_seed(
    seed: int,
    num_hands: int,
    model_dir: str,
    logger: SQLiteLogger,
    label: str,
) -> Dict:
    """Build ML agents, play hands, log everything. Returns summary dict."""
    agents = build_ml_agents(model_dir)
    num_seats = len(agents)
    starting_stack = SIMULATION["starting_stack"]

    run_id = logger.start_run(
        seed=seed,
        num_hands=num_hands,
        label=label,
        agents=agents,
    )
    table = Table(agents, seed=seed, logger=logger, run_id=run_id)

    started = time.time()
    for i in range(1, num_hands + 1):
        table.play_hand()
        if i % 100 == 0 or i == num_hands:
            _print_progress(seed, i, num_hands, started)
    sys.stdout.write("\n")
    sys.stdout.flush()

    logger.log_agent_stats(run_id, table)

    # Print ML prediction stats
    for a in agents:
        stats = a.prediction_stats()
        if stats["fallbacks"] > 0:
            print(f"    {a.name}: {stats['predictions']} predictions, "
                  f"{stats['fallbacks']} fallbacks ({stats['fallback_rate']:.1%})")

    # Chip conservation check
    cur = logger.conn.cursor()
    stack_sum = cur.execute(
        "SELECT COALESCE(SUM(final_stack), 0) FROM agent_stats WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    rebuy_sum = cur.execute(
        "SELECT COALESCE(SUM(rebuys), 0) FROM agent_stats WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    expected_stack = (num_seats + rebuy_sum) * starting_stack
    chip_delta = int(stack_sum) - expected_stack

    return {
        "seed": seed,
        "run_id": run_id,
        "num_hands": num_hands,
        "chip_delta": chip_delta,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-type", default="rf",
                        help="Model subdirectory name (default: rf)")
    parser.add_argument("--modeldir", default=None,
                        help="Full path to model directory (overrides --model-type)")
    parser.add_argument("--seeds", default="42,137,256,512,1024",
                        help="Comma-separated seeds")
    parser.add_argument("--hands", type=int, default=25000,
                        help="Hands per seed (default: 25000)")
    parser.add_argument("--db", default=None,
                        help="SQLite output path (default: ml_runs_<model-type>.sqlite)")
    parser.add_argument("--label", default=None)
    args = parser.parse_args(argv)

    model_dir = args.modeldir or os.path.join("ml", "models", args.model_type)
    db_path = args.db or f"ml_runs_{args.model_type}.sqlite"
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    label = args.label or f"phase2-{args.model_type}-{args.hands}h"

    print(f"Phase 2 ML Simulation")
    print(f"  Model dir: {model_dir}")
    print(f"  Seeds: {seeds}")
    print(f"  Hands/seed: {args.hands}")
    print(f"  Output: {db_path}")
    print()

    logger = SQLiteLogger(db_path)
    summaries = []
    for seed in seeds:
        summary = run_one_seed(seed, args.hands, model_dir, logger, label)
        summaries.append(summary)
    logger.close()

    # Final summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = True
    for s in summaries:
        ok = s["chip_delta"] == 0
        all_ok = all_ok and ok
        print(f"  seed={s['seed']:<6} chip_delta={s['chip_delta']:<4} {'OK' if ok else 'FAIL'}")
    print("=" * 60)
    print(f"Chip conservation: {'all OK' if all_ok else 'FAILED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
