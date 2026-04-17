# Phase 1 — Rule-Based Archetype Agents

Everything specific to the rule-based simulation lives here. Shared engine/
trust/analysis packages stay at the repo root (they are reused by every phase).

## Contents

| File | Purpose |
|------|---------|
| `run_sim.py` | Full research simulation — writes to SQLite |
| `run_demo.py` | 30-hand visualizer demo — regenerates `visualizer/data.js` |
| `run_multiseed.py` | Multi-seed CSV export for ML training |
| `run_sensitivity.py` | λ / ε / TPW parameter sweeps |
| `run_tests.py` | Stage-aware test runner (1–11) |
| `smoke_test.py` | Pre-run validation across all 8 archetypes |
| `test_cases.py` | Canonical per-stage test spec (do NOT edit) |
| `stage_extras.py` | Real assertions for each stage (append-only) |
| `requirements.txt` | Phase 1 deps (treys, numpy) |
| `phase1_report.md` | 943-line research report |

## Quick Start

```bash
pip install -r phase1/requirements.txt

# Smoke test
python phase1/smoke_test.py

# 30-hand viewer demo
python phase1/run_demo.py --stage 6

# Full test suite
python phase1/run_tests.py --stage all

# Research run (hours)
python phase1/run_sim.py --seeds 42,137,256,512,1024 --hands 10000 \
    --db runs.sqlite --stage 6
```

## Output

- SQLite databases → repo root (gitignored except `research_data/runs_v3.sqlite.part_*`)
- Visualizer data → `../visualizer/data.js`
- Reports → `../reports/`
