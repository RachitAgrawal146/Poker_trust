# Poker Trust Simulation

Multi-agent Bayesian trust dynamics in 8-player Limit Texas Hold'em. Eight
archetype agents play hundreds of thousands of hands while every agent
maintains a live posterior over what *kind* of player everyone else is.

**Phase 1** — Rule-based agents with hand-coded probability tables.
**Phase 2** — ML models trained on Phase 1 data, deployed in the same engine.
Both phases produce matching emergent dynamics, validating the findings.

---

## Key Findings

### Phase 1 (500k hands, 20 seeds — rule-based agents)
- **Trust-profit anticorrelation** (r = −0.837): being trusted = being exploitable
- **Firestorm dominance**: 87.1% fold equity, worst showdown win rate (38.5%), highest stack (17,862)
- **Classification ceiling**: only 3-4 of 8 archetypes reliably identified by the Bayesian model
- Full report: [`phase1_report.md`](phase1_report.md)

### Phase 2 (125k hands, 5 seeds — ML agents)
- **All Phase 1 findings reproduced** within 1-3%
- Trust-profit anticorrelation: r = −0.825 (vs −0.837)
- Firestorm still dominant: 20,971 chips (+17% stronger)
- Simplest ML approach (tabular frequency counting) outperforms RF, LogReg, and MLP
- Full report: [`phase2_report.md`](phase2_report.md)

---

## Quick Start

```bash
# Phase 1: Rule-based simulation
pip install -r requirements.txt
python smoke_test.py                    # validate all 8 archetypes
python run_demo.py --stage 6            # generate viewer data
python run_tests.py --stage all         # run all stage tests

# Phase 2: ML simulation
pip install -r requirements_ml.txt
python -m ml.extract_live --hands 5000 --seeds 42,137,256 --outdir ml/data_live/
python -m ml.train_tabular --datadir ml/data_live/ --outdir ml/models_tabular/
python -m ml.smoke_test_ml --modeldir ml/models_tabular/
python run_ml_sim.py --modeldir ml/models_tabular/ --hands 5000 --seeds 42 --db ml_test.sqlite
```

## The Eight Archetypes

| Seat | Agent | Type | Strategy | Honesty |
|------|-------|------|----------|---------|
| 0 | Oracle | Static | Nash equilibrium baseline | 0.75 |
| 1 | Sentinel | Static | Tight-aggressive; folds unless strong | 0.92 |
| 2 | Firestorm | Static | Loose-aggressive; bluffs constantly | 0.38 |
| 3 | Wall | Static | Calling station; never folds, never bluffs | 0.96 |
| 4 | Phantom | Static | Deceiver; bluffs then folds to resistance | 0.48 |
| 5 | **Predator** | Adaptive | Reads posteriors; exploits classified opponents | ~0.79 |
| 6 | **Mirror** | Adaptive | Tit-for-tat; mirrors most-active opponent | ~0.78 |
| 7 | **Judge** | Adaptive | Grudger; permanent retaliation at 5 confirmed bluffs | ~0.82 |

## Project Layout

```
Poker_trust/
│
├── ── CORE ENGINE ──────────────────────────────────────────
├── engine/                 # Game mechanics
│   ├── game.py             # Single hand: blinds, betting, showdown
│   ├── table.py            # 8-seat table manager, rebuys, dealer rotation
│   ├── deck.py             # Seeded 52-card deck (treys ints)
│   ├── evaluator.py        # Monte Carlo hand strength bucketing
│   └── actions.py          # ActionType enum + ActionRecord dataclass
│
├── ── PHASE 1: RULE-BASED AGENTS ───────────────────────────
├── agents/
│   ├── base_agent.py       # Abstract base: decision logic + trust model
│   ├── oracle.py           # Nash Equilibrium (static)
│   ├── sentinel.py         # Tight-Aggressive (static)
│   ├── firestorm.py        # Loose-Aggressive (static)
│   ├── wall.py             # Passive calling station (static)
│   ├── phantom.py          # Deceiver (static)
│   ├── predator.py         # Exploiter (adaptive — reads posteriors)
│   ├── mirror.py           # Tit-for-tat (adaptive — copies opponents)
│   ├── judge.py            # Grudger (adaptive — permanent retaliation)
│   ├── dummy_agent.py      # Scripted test agents
│   └── ml_agent.py         # Phase 2 ML-powered agent
│
├── trust/
│   ├── bayesian_model.py   # Posterior updates, decay, trust score, entropy
│   └── __init__.py         # Re-exports
│
├── ── PHASE 2: ML PIPELINE ─────────────────────────────────
├── ml/
│   ├── extract_live.py     # Live extraction with hand strength
│   ├── train_tabular.py    # Tabular empirical model (the winner)
│   ├── train_traditional.py# LogReg + Random Forest
│   ├── train_neural.py     # sklearn MLP
│   ├── train_split.py      # Split-context RF
│   ├── evaluate_models.py  # Three-way model comparison
│   ├── smoke_test_ml.py    # ML agent spec validation
│   └── feature_engineering.py
│
├── ── DATA & PERSISTENCE ───────────────────────────────────
├── data/
│   ├── sqlite_logger.py    # SQLite writer (6 tables)
│   ├── csv_exporter.py     # ML-ready CSV exports
│   ├── visualizer_export.py# JSON/JS for HTML viewer
│   └── schema.sql          # DDL for the 6-table schema
│
├── ── ANALYSIS ─────────────────────────────────────────────
├── analysis/
│   ├── analyze_runs.py     # 9-section standard report
│   ├── deep_analysis.py    # 31-section deep analysis + scorecard
│   ├── find_interesting_hands.py  # Narrative hand miner
│   └── *.txt               # Generated reports
│
├── ── VISUALIZER ───────────────────────────────────────────
├── visualizer/
│   └── poker_table.html    # 1927-line single-file viewer
│
├── ── TESTS ────────────────────────────────────────────────
├── tests/
│   └── test_trust_model.py # 27 unit tests for trust primitives
├── test_cases.py           # Canonical stage test suites
├── stage_extras.py         # Additional test assertions
├── run_tests.py            # Stage-aware test runner
├── smoke_test.py           # Pre-run validation
│
├── ── RUNNERS ──────────────────────────────────────────────
├── run_sim.py              # Phase 1 simulation (SQLite output)
├── run_ml_sim.py           # Phase 2 ML simulation
├── run_demo.py             # Visualizer data generator
├── run_multiseed.py        # Multi-seed CSV orchestration
├── run_sensitivity.py      # Parameter sweep runner
├── compare_phases.py       # Phase 1 vs Phase 2 comparison
│
├── ── CONFIGURATION ────────────────────────────────────────
├── config.py               # All simulation parameters
├── archetype_params.py     # Per-round probability tables
├── preflop_lookup.py       # 169-hand preflop bucketing
├── requirements.txt        # treys + numpy
├── requirements_ml.txt     # scikit-learn + joblib
│
├── ── DOCUMENTATION ────────────────────────────────────────
├── docs/
│   ├── Claude_Code_Implementation_Prompt.md   # Full build spec
│   ├── The_Eight_Archetypes_Specification.docx
│   ├── worked_examples.md  # Hand walkthrough + Bayesian update
│   ├── schema.md           # SQLite schema + query cookbook
│   ├── stage5_identifiability.md  # Sentinel entropy proof
│   ├── DesignCues          # Viewer design system
│   └── CHANGELOG.md        # Stage milestones
│
├── phase1_report.md        # Complete Phase 1 report (943 lines)
├── phase2_report.md        # Complete Phase 2 report (719 lines)
├── CLAUDE.md               # Project memory for Claude Code sessions
└── README.md               # This file
```

## Environment

- Python 3.11+
- Phase 1: `treys>=0.1.8`, `numpy>=2.0`
- Phase 2: add `scikit-learn>=1.3.0`, `joblib>=1.3.0`

## Reports

| Report | Content |
|--------|---------|
| [`phase1_report.md`](phase1_report.md) | Complete Phase 1 documentation (943 lines) |
| [`phase2_report.md`](phase2_report.md) | Complete Phase 2 documentation (719 lines) |
| [`docs/schema.md`](docs/schema.md) | SQLite schema + research query cookbook |
| [`docs/worked_examples.md`](docs/worked_examples.md) | Hand walkthrough + Bayesian update |
| [`docs/stage5_identifiability.md`](docs/stage5_identifiability.md) | Mathematical proof of identifiability ceiling |
| [`CLAUDE.md`](CLAUDE.md) | Project memory for future sessions |
