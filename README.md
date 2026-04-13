# Poker Trust Simulation

Multi-agent Bayesian trust dynamics in 8-player Limit Texas Hold'em. Eight
rule-based archetype agents play hundreds of thousands of hands while every
agent maintains a live posterior over what *kind* of player everyone else is.

**Phase 1** (this repo) is the complete simulation + analysis pipeline.
Phase 2 trains ML classifiers on the resulting dataset.

## Key Findings (v3 — 500k hands, 20 seeds)

- **Trust-profit anticorrelation** (r = −0.770): being trusted = being exploitable
- **Firestorm dominance**: 87.1% fold equity, worst showdown win rate (38.5%), highest stack (17,862)
- **Classification ceiling**: only 3 of 8 archetypes reliably identified by the Bayesian model
- **Full report**: [`phase1_report.md`](phase1_report.md)

## Quick Start

```bash
pip install -r requirements.txt   # treys + numpy

python smoke_test.py              # validate all 8 archetypes
python run_demo.py --stage 6      # generate viewer data
# Open visualizer/poker_table.html in any browser

python run_tests.py --stage all   # run all stage tests
```

## The Eight Archetypes

| Seat | Agent | Type | One-liner |
|------|-------|------|-----------|
| 0 | Oracle | Static | Nash equilibrium baseline |
| 1 | Sentinel | Static | Tight-aggressive; folds unless strong |
| 2 | Firestorm | Static | Loose-aggressive; bluffs constantly |
| 3 | Wall | Static | Calling station; never folds, never bluffs |
| 4 | Phantom | Static | Deceiver; bluffs then folds to resistance |
| 5 | **Predator** | Adaptive | Reads posteriors; exploits classified opponents |
| 6 | **Mirror** | Adaptive | Tit-for-tat; mirrors most-active opponent |
| 7 | **Judge** | Adaptive | Grudger; permanent retaliation at 5 confirmed bluffs |

## Running Simulations

```bash
# Smoke test (~30s)
python run_sim.py --seeds 42 --hands 500 --db test.sqlite --stage 6

# Full research run (~40 min per seed)
python run_sim.py --seeds 42,137,256,512,1024 --hands 25000 --db runs.sqlite --stage 6

# Multi-seed CSV exports for ML
python run_multiseed.py --seeds 42,137 --hands 10000 --outdir runs/

# Parameter sweeps
python run_sensitivity.py --param lambda --values 0.90,0.95,0.98,1.0 --hands 1000 --seeds 42,137
```

## Analysis

```bash
python analysis/analyze_runs.py --db runs.sqlite           # 9-section report
python analysis/deep_analysis.py --db runs.sqlite --out report.txt  # 31-section deep analysis
```

## Project Layout

```
Poker_trust/
├── engine/              # Game mechanics: deck, evaluator, hand, table
├── agents/              # 8 archetype agents + base class
├── trust/               # Bayesian trust model (posterior updates, decay, entropy)
├── data/                # SQLite logger, CSV exporter, visualizer JSON export
├── visualizer/          # Single-file HTML replay viewer (Trust Lens / Heatmap / Stats)
├── analysis/            # Analysis scripts + v3 output reports
├── tests/               # Unit tests for trust model
├── docs/                # Specs, schema reference, design docs, changelog
│   ├── schema.md                              # SQLite schema + query cookbook
│   ├── worked_examples.md                     # Hand walkthrough + Bayesian update
│   ├── stage5_identifiability.md              # Why Sentinel can't be identified
│   ├── Claude_Code_Implementation_Prompt.md   # Full build spec
│   ├── The_Eight_Archetypes_Specification.docx
│   └── CHANGELOG.md
├── research_data/       # v3 database (LFS chunks — reassemble with cat/copy)
│
├── config.py            # All simulation parameters
├── archetype_params.py  # Per-round probability tables for all archetypes
├── preflop_lookup.py    # 169-hand preflop strength bucketing
├── run_sim.py           # Main simulation runner (SQLite output)
├── run_multiseed.py     # Multi-seed orchestration (CSV output)
├── run_demo.py          # Visualizer data generator
├── run_sensitivity.py   # Parameter sweep runner
├── run_tests.py         # Stage-aware test runner
├── smoke_test.py        # Pre-run validation
├── test_cases.py        # Canonical test suites
├── stage_extras.py      # Additional test assertions per stage
├── phase1_report.md     # Complete Phase 1 research report
├── CLAUDE.md            # Project memory for Claude Code sessions
└── README.md
```

## Environment

- Python 3.11+
- `treys` 0.1.8+, `numpy` 2.0+
- No other dependencies. No pandas, no build step.

## Further Reading

- [`phase1_report.md`](phase1_report.md) — complete Phase 1 documentation (943 lines)
- [`CLAUDE.md`](CLAUDE.md) — project memory for future sessions
- [`docs/schema.md`](docs/schema.md) — SQLite schema + research query cookbook
- [`docs/worked_examples.md`](docs/worked_examples.md) — hand walkthrough + Bayesian update
