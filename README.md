# Poker Trust Simulation

Multi-agent Bayesian trust dynamics in 8-player Limit Texas Hold'em. Eight
archetype agents play hundreds of thousands of hands while every agent
maintains a live posterior over what *kind* of player everyone else is.

The project tests a single research question across four agent architectures:
**does observation-based trust inference inherently reward exploitation
over cooperation, or is the trap dynamic dependent on agent capability?**

| Phase | Mechanism | Trust–profit r | Verdict |
|---|---|---|---|
| **1** | Frozen rule-based archetype agents | **−0.752** | Trap is real |
| **2** | Bounded online hill-climbing optimization | **−0.637** | Numerical adaptation chips at trap, doesn't break it |
| **3** | LLM personality role-players (Haiku) | **−0.510** | LLMs role-play archetypes faithfully but don't reason |
| **3.1** | LLM + chain-of-thought + memory + adaptive specs | **−0.094** | **Trap breaks: indistinguishable from zero** |

Every phase reuses the **same game engine**, **same trust posterior**, and
**same metrics framework**. Only the agent's `decide_action` changes.

---

## For mentor review — suggested reading order

This README is self-contained, but a 30-minute review of the project naturally goes:

1. **This README** (you are here) — research question, four-phase ladder, key findings, layout
2. **`paper.md`** — full Polygence research paper draft (~720 lines, 7 sections + references). Sections 5.7 and 5.8 cover Phase 3 and the trap-breaking Phase 3.1 result respectively; Section 7 is the conclusion + future work. Also available as `paper/paper.tex` for Overleaf.
3. **`reports/phase31_long_scorecard.txt`** — 6-table cross-phase scorecard with all four phases' per-seed r values, behavioral dimensions, economic ordering inversion, and TMA breakdown. **The single best one-page summary of the project's quantitative findings.**
4. **`phase3/phase3_report.md`** — paper-style writeup covering both the Phase 3 baseline (LLM role-play, r = −0.510) and the Phase 3.1 trap-breaking result (r = −0.094 with CoT + memory + adaptive specs). Self-contained; explains the three reasoning interventions, the trap-breaking finding, the Wall-wins economic inversion, and honest limitations.
5. *(optional)* `phase2/adaptive/phase2_report.md` — same paper-style writeup for the Phase 2 hill-climbing tier. Useful if the mentor wants to understand *why* each tier moves r by ~0.12–0.42 instead of asking "and the others did what?"
6. *(optional, deeper dive)* `phase2/adaptive/PHASE2_REDESIGN_PLAN.md` — design briefing for the Phase 2 redesign that replaced the original imitation-based Phase 2; explains *why* the canonical Phase 2 was rebuilt as bounded optimization rather than ML imitation.

If the mentor wants to *reproduce* anything, the **Quick Start** section below has every command. If they want to *audit* code correctness, `phase3/validate_phase31.py` runs a 50-check unit suite without spending API credit.

---

## Key Findings

### Phase 1 — frozen rule-based agents (5 seeds × 10 000 hands)
- **Trust–profit anticorrelation: r = −0.752**. Most-trusted agents (Wall, Sentinel) accumulate the least wealth; least-trusted aggressive agent (Firestorm) dominates.
- **Firestorm dominance via fold equity**: 87.1% of pots won without showdown. The threat of engagement is more valuable than the outcome of engagement.
- **Hard classification ceiling**: only 3–4 of 8 archetypes reliably identifiable through behavioral observation, no matter the sample size. Mathematical proof in [`docs/stage5_identifiability.md`](docs/stage5_identifiability.md).
- Full report: [`phase1/phase1_report.md`](phase1/phase1_report.md)

### Phase 2 — bounded online optimization (5 seeds × 10 000 hands)
- Each agent runs a per-cycle hill-climber that tunes its own decision parameters within an archetype-shaped bound box. **Trust–profit r softens to −0.637** (Δr = +0.116, consistent across all 5 seeds).
- **Opponent Adaptation stays at OA = 0.0003** — bounded numerical optimization on aggregate reward cannot produce per-opponent strategy.
- The earlier ML-imitation Phase 2 (which reproduced Phase 1 by construction) is preserved at [`phase2/_imitation_archive/`](phase2/_imitation_archive/).
- Full report: [`phase2/adaptive/phase2_report.md`](phase2/adaptive/phase2_report.md)

### Phase 3 — LLM personality role-players (5 seeds × 500 hands)
- 8 independent LLM agents (claude-haiku-4-5), each given a personality spec as system prompt. **Trust–profit r softens to −0.510** (Δr = +0.127 from Phase 2).
- **4 of 6 behavioral metric targets MISSED** (CS, OA, NS, SU). Three actually move *backward* — LLMs faithfully role-play archetypes but do not spontaneously develop opponent-conditional, time-varying, or unpredictable behavior.
- Cost: $33.10 for 43,943 LLM calls with prompt caching enabled.
- Full report: [`phase3/phase3_report.md`](phase3/phase3_report.md)

### Phase 3.1 — LLM with reasoning scaffolding (5 seeds × 150 hands)
- Same LLM agents + three additions: **chain-of-thought prompting**, **persistent per-opponent memory**, **adaptive personality specs** (post-hand strategy update).
- **Trust–profit r drops to −0.094** — statistically indistinguishable from zero. The Phase 3 → Phase 3.1 step (Δr = +0.416) is **larger than the previous three phase transitions combined**.
- **Trap inversion** in 2 of 5 seeds (positive r): trusted agents made *more* money than distrusted ones.
- **Wall (most trusted) wins** — climbs from rank 8 to rank 1 in economic ordering, with zero rebuys.
- 4 of 6 behavioral targets met (vs Phase 3's 2/6); SU now > 1.5 bits, TMA boosted to +0.242 with 6 of 8 archetypes "trust farming."
- Cost: $17 for 11,953 LLM calls.
- Full report (covers both Phase 3 and Phase 3.1): [`phase3/phase3_report.md`](phase3/phase3_report.md)

---

## Quick Start

```bash
# Install Phase 1 dependencies
pip install -r phase1/requirements.txt

# Phase 1: Rule-based simulation (canonical research run)
python phase1/run_sim.py --hands 10000 --seeds 42,137,256,512,1024 \
    --db runs_phase1.sqlite --stage 6

# Phase 2: Adaptive (bounded hill-climbing) simulation
python phase2/adaptive/run_adaptive.py --hands 10000 \
    --seeds 42,137,256,512,1024 --db runs_phase2.sqlite

# Phase 1 vs Phase 2 cross-comparison (generates the scorecard)
python phase2/adaptive/phase2_comparison.py \
    --phase1-db runs_phase1.sqlite --phase2-db runs_phase2.sqlite \
    --output reports/phase2_scorecard_long.txt

# Phase 3: LLM personality role-players (requires ANTHROPIC_API_KEY)
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python phase3/run_phase3_chat.py --provider anthropic \
    --model claude-haiku-4-5-20251001 \
    --hands 500 --seeds 42,137,256,512,1024 \
    --db runs_phase3.sqlite

# Phase 3.1: same as Phase 3 + reasoning scaffolding (CoT, memory, adaptive)
python phase3/run_phase3_chat.py --provider anthropic \
    --model claude-haiku-4-5-20251001 \
    --hands 150 --seeds 42,137,256,512,1024 \
    --db runs_phase31.sqlite --phase31

# Tests + validation
python phase1/run_tests.py --stage all       # Phase 1/2 stage tests
python phase3/validate_phase31.py            # Phase 3.1 unit-level checks (50 assertions)
python tests/test_trust_model.py             # Trust posterior unit tests
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
├── phase1/                   # ── PHASE 1: RULE-BASED ─────────────────────────
│   ├── README.md             # Phase 1 quick reference
│   ├── phase1_report.md      # 943-line research report
│   ├── run_sim.py            # Full research simulation
│   ├── run_demo.py           # Visualizer data generator
│   ├── run_multiseed.py      # Multi-seed CSV export
│   ├── run_sensitivity.py    # λ / ε / TPW parameter sweeps
│   ├── run_tests.py          # Stage-aware test runner
│   ├── smoke_test.py         # Pre-run validation
│   ├── test_cases.py         # Canonical stage test spec
│   ├── stage_extras.py       # Real per-stage assertions
│   └── requirements.txt      # treys + numpy
│
├── phase2/                   # ── PHASE 2 ───────────────────────────────────
│   ├── adaptive/             # CANONICAL Phase 2: bounded hill-climbing
│   │   ├── PHASE2_REDESIGN_PLAN.md  # Mentor briefing doc
│   │   ├── phase2_report.md         # Paper-style writeup
│   │   ├── bounds.py                # Per-archetype param ranges
│   │   ├── adaptive_agent.py        # AdaptiveAgent + AdaptiveJudge
│   │   ├── hill_climber.py          # Per-cycle optimizer
│   │   ├── run_adaptive.py          # Simulation runner
│   │   ├── phase2_comparison.py     # Phase 1 vs Phase 2 scorecard
│   │   ├── param_trajectories.json  # Per-agent param history
│   │   └── optimization_log.json    # Per-cycle hill-climber log
│   └── _imitation_archive/   # ARCHIVED: original imitation-based Phase 2
│       └── ml/, run_ml_sim.py, requirements_ml.txt, README.md
│
├── phase3/                   # ── PHASE 3 + 3.1 ─────────────────────────────
│   ├── README.md
│   ├── phase3_report.md      # Combined Phase 3 + 3.1 writeup
│   ├── personality_specs/    # 8 archetype system prompts
│   ├── llm_chat_agent.py     # LLMChatAgent + LLMChatJudge (with --phase31 mode)
│   ├── run_phase3_chat.py    # API-backed runner (--provider anthropic|ollama|claude-cli)
│   ├── file_io_agent.py      # File-IPC mode (use Claude Code as the LLM)
│   ├── run_phase3_fileio.py  # File-IPC runner
│   ├── orchestrate.py        # File-IPC orchestrator
│   ├── dealer.py             # Game-integrity layer
│   └── validate_phase31.py   # 50-check unit suite for Phase 3.1
│
├── ── SHARED CORE (used by every phase) ──────────────────────
│
├── engine/                   # Game mechanics (game.py, table.py, deck.py, evaluator.py, actions.py)
├── agents/                   # All archetype agent classes (BaseAgent + 8 archetypes)
├── trust/bayesian_model.py   # Posterior updates, decay, trust, entropy
├── data/                     # SQLite logger + CSV exporter + visualizer JSON
├── analysis/                 # 9-section standard report, 31-section deep analysis
├── visualizer/poker_table.html  # 1927-line single-file viewer
├── tests/test_trust_model.py    # 27 unit tests for trust primitives
│
├── ── SHARED CONFIG ──────────────────────────────────────────
│
├── config.py                 # All simulation parameters
├── archetype_params.py       # Per-round probability tables (DO NOT MODIFY)
├── preflop_lookup.py         # 169-hand preflop bucketing (DO NOT MODIFY)
├── compute_metrics.py        # 6-dimension scorecard generator
├── extract_phase3_stats.py   # Per-seed JSON extractor for Phase 3 / 3.1
│
├── ── PAPER ────────────────────────────────────────────────────
│
├── paper.md                  # Polygence research paper (Markdown source)
├── paper/paper.tex           # Pandoc-converted LaTeX (for Overleaf)
├── paper/paper_starter.tex   # Minimal LaTeX skeleton (alternative)
│
├── ── GENERATED OUTPUT ───────────────────────────────────────
│
├── reports/                  # All scorecards, audits, analysis dumps
│   ├── phase2_scorecard.txt        # Phase 2 lean (3 × 5000)
│   ├── phase2_scorecard_long.txt   # Phase 2 canonical (5 × 10000)
│   ├── phase3_scorecard.txt        # Phase 3 50-hand pilot (legacy)
│   ├── phase3_long_scorecard.txt   # Phase 3 canonical (5 × 500)
│   └── phase31_long_scorecard.txt  # Phase 3.1 canonical (5 × 150)
└── research_data/            # LFS chunks of runs_v3.sqlite (500k Phase 1 hands)
│
├── docs/                     # Design docs, specs, schema reference
├── CLAUDE.md                 # Project memory for Claude Code sessions
└── README.md                 # This file
```

## Environment

- Python 3.11+
- Phase 1 / Phase 2: `treys>=0.1.8`, `numpy>=2.0`
- Phase 3 / 3.1: `anthropic` (or `openai` for Ollama), plus `ANTHROPIC_API_KEY`

## Reports

| Report | Phase | Lines | Content |
|--------|-------|-------|---------|
| [`phase1/phase1_report.md`](phase1/phase1_report.md) | 1 | 943 | Phase 1 frozen-archetype documentation |
| [`phase2/adaptive/phase2_report.md`](phase2/adaptive/phase2_report.md) | 2 | 512 | Phase 2 adaptive (bounded hill-climbing) |
| [`phase2/_imitation_archive/phase2_report.md`](phase2/_imitation_archive/phase2_report.md) | 2 (archived) | — | Original ML-imitation Phase 2 |
| [`phase3/phase3_report.md`](phase3/phase3_report.md) | 3 + 3.1 | — | LLM role-play baseline AND reasoning-scaffolding follow-up (combined) |
| [`reports/phase2_scorecard_long.txt`](reports/phase2_scorecard_long.txt) | 1 vs 2 | — | 7-table cross-phase scorecard |
| [`reports/phase31_long_scorecard.txt`](reports/phase31_long_scorecard.txt) | 1/2/3/3.1 | — | Cross-phase scorecard with all four tiers |
| [`paper.md`](paper.md) | All | 719 | Polygence research paper (Markdown source) |
| [`docs/schema.md`](docs/schema.md) | Shared | — | SQLite schema + research query cookbook |
| [`docs/worked_examples.md`](docs/worked_examples.md) | Shared | — | Hand walkthrough + Bayesian update |
| [`docs/stage5_identifiability.md`](docs/stage5_identifiability.md) | Phase 1 | — | Proof of classification ceiling |
| [`CLAUDE.md`](CLAUDE.md) | Meta | — | Project memory for future sessions |
