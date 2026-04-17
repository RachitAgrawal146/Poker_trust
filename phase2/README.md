# Phase 2 — ML-Powered Agents

Everything specific to the ML pipeline lives here. Phase 2 replaces the
rule-based decision logic from Phase 1 with trained models while reusing the
same engine, trust model, and analysis pipeline.

## Contents

| File / Dir | Purpose |
|------------|---------|
| `run_ml_sim.py` | Run 8 ML agents through the Phase 1 engine |
| `ml/` | Feature engineering, training scripts, smoke test |
| `requirements_ml.txt` | ML deps (scikit-learn, joblib) on top of Phase 1 |
| `phase2_report.md` | 719-line Phase 2 report |

## `ml/` subpackage

| Script | Purpose |
|--------|---------|
| `feature_engineering.py` | 7/8-feature vector definition + action labels |
| `extract_live.py` | Live extraction with hand strength (the winner) |
| `extract_training_data.py` | Legacy SQLite post-hoc extraction |
| `train_tabular.py` | **Tabular empirical model (best results)** |
| `train_split.py` | Split-context RF (nobet / facing) |
| `train_traditional.py` | Logistic Regression + Random Forest |
| `train_neural.py` | sklearn MLPClassifier |
| `evaluate_models.py` | Three-way model comparison |
| `smoke_test_ml.py` | 500-hand spec validation for trained models |

## Quick Start

```bash
# Install Phase 2 deps (on top of Phase 1's)
pip install -r phase1/requirements.txt
pip install -r phase2/requirements_ml.txt

# 1. Extract live training data (needs Phase 1 code on path — done automatically)
python -m phase2.ml.extract_live --hands 5000 --seeds 42,137,256 \
    --outdir phase2/ml/data_live/

# 2. Train the tabular (winning) model
python -m phase2.ml.train_tabular --datadir phase2/ml/data_live/ \
    --outdir phase2/ml/models_tabular/

# 3. Smoke test the trained model
python -m phase2.ml.smoke_test_ml --modeldir phase2/ml/models_tabular/

# 4. Run the ML simulation
python phase2/run_ml_sim.py --modeldir phase2/ml/models_tabular/ \
    --hands 5000 --seeds 42 --db ml_test.sqlite
```

## Relation to Phase 1

Phase 2 **imports** Phase 1's building blocks without modifying them:
- `engine.table.Table` — same game loop
- `agents.ml_agent.MLAgent` — uses Phase 1's `BaseAgent` trust machinery
- `trust.bayesian_model` — same posterior updates
- `data.sqlite_logger.SQLiteLogger` — same persistence

Every Phase 1 finding was reproduced within 1–3% after training on 16k hands.
See `phase2_report.md` for details.
