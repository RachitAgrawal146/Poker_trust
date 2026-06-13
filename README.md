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
| **3.1** | LLM + chain-of-thought + memory + adaptive specs | **−0.094** | **Trap attenuates — rank-order weakens, but underpowered (n=5)** |

Every phase reuses the **same game engine**, **same trust posterior**, and
**same metrics framework**. Only the agent's `decide_action` changes.

The Polygence research paper is built from
[`paper_resources/manuscript/main.tex`](paper_resources/manuscript/main.tex)
(compiled `main.pdf`, editable `main.docx`); supporting
materials — figures, LaTeX tables, CSV data, story-hand transcripts, and
topical notes — live in [`paper_resources/`](paper_resources/). See
[`paper_resources/README.md`](paper_resources/README.md) for the index. The
single best one-page summary of the quantitative findings is
[`reports/phase31_long_scorecard.txt`](reports/phase31_long_scorecard.txt);
the closest thing to a written-up draft of the results lives in
[`phase3/phase3_report.md`](phase3/phase3_report.md) (Phase 3 + 3.1
combined) and [`phase2/adaptive/phase2_report.md`](phase2/adaptive/phase2_report.md).

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
python tests/test_trust_model.py             # Trust posterior unit tests (27)
python tests/test_engine_sidepot.py          # Side-pot algorithm unit tests (18)

# Headline CIs on the trust-profit r ladder
python analysis/bootstrap_ci.py              # Mean-r CIs + per-seed Fisher-z
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
│   └── (the earlier ML-imitation Phase 2 was removed in May 2026 once
│        the adaptive redesign superseded it — see docs/CHANGELOG.md)
│
├── phase3/                   # ── PHASE 3 + 3.1 ─────────────────────────────
│   ├── README.md
│   ├── phase3_report.md      # Combined Phase 3 + 3.1 writeup
│   ├── personality_specs/    # 8 archetype system prompts
│   ├── llm_chat_agent.py     # LLMChatAgent + LLMChatJudge (with --phase31 mode)
│   ├── run_phase3_chat.py    # API-backed runner (--provider anthropic|ollama|claude-cli)
│   ├── dealer.py             # Game-integrity layer
│   └── validate_phase31.py   # 50-check unit suite for Phase 3.1
│
├── ── SHARED CORE (used by every phase) ──────────────────────
│
├── engine/                   # Game mechanics (game.py, table.py, deck.py, evaluator.py, actions.py)
├── agents/                   # All archetype agent classes (BaseAgent + 8 archetypes)
├── trust/bayesian_model.py   # Posterior updates, decay, trust, entropy
├── data/                     # SQLite logger + CSV exporter + visualizer JSON
├── analysis/                 # All analysis scripts (deep_analysis, bootstrap_ci,
│                             #   compute_metrics, compare_phases, extract_phase3_stats,
│                             #   make_paper_figures / _tables, nash_convergence, etc.)
├── visualizer/poker_table.html  # 1927-line single-file viewer
├── tests/                    # test_trust_model.py + test_engine_sidepot.py
│
├── ── SHARED CONFIG (must stay at repo root for `from config import …`) ──
│
├── config.py                 # All simulation parameters
├── archetype_params.py       # Per-round probability tables (DO NOT MODIFY)
├── preflop_lookup.py         # 169-hand preflop bucketing (DO NOT MODIFY)
│
├── ── PAPER MATERIALS ────────────────────────────────────────────
│
├── paper_resources/          # Everything needed to write the paper externally (Overleaf)
│   ├── README.md             # Index: what each file is and how to regenerate
│   ├── figures/              # PNG figures (180 dpi, ready to \includegraphics)
│   ├── tables/               # LaTeX tabular snippets
│   ├── data/                 # CSV source data + phase3_stats.json / phase31_stats.json
│   ├── interesting_hands/    # Categorized per-phase story hands + EVOLUTION_STORY.md
│   └── notes/                # Topical writeups, Nash convergence, methods checklist
│
├── ── GENERATED OUTPUT ───────────────────────────────────────
│
├── reports/                  # All scorecards + per-run dealer audit dumps
│   ├── phase2_scorecard.txt              # Phase 2 lean (3 × 5000)
│   ├── phase2_scorecard_long.txt         # Phase 2 canonical (5 × 10000)
│   ├── phase2_unbounded_scorecard.txt              # Phase 2* unbounded weak HC (footnote)
│   ├── phase2_unbounded_scorecard_aggressive.txt   # Phase 2* unbounded aggressive (canonical)
│   ├── phase3_long_scorecard.txt         # Phase 3 canonical (5 × 500)
│   ├── phase31_long_scorecard.txt        # Phase 3.1 canonical (5 × 150)
│   ├── phase3_long_audit.json            # Phase 3 dealer audit dump
│   └── phase31_long_audit.json           # Phase 3.1 dealer audit dump
├── research_data/            # LFS-tracked SQLite databases + chunks
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
| [`phase3/phase3_report.md`](phase3/phase3_report.md) | 3 + 3.1 | — | LLM role-play baseline AND reasoning-scaffolding follow-up (combined) |
| [`reports/phase2_scorecard_long.txt`](reports/phase2_scorecard_long.txt) | 1 vs 2 | — | 7-table cross-phase scorecard |
| [`reports/phase31_long_scorecard.txt`](reports/phase31_long_scorecard.txt) | 1/2/3/3.1 | — | Cross-phase scorecard with all four tiers |
| [`reports/phase2_unbounded_scorecard_aggressive.txt`](reports/phase2_unbounded_scorecard_aggressive.txt) | 2* | — | Phase 2 unbounded HC sub-experiment (Nash falsification) |
| [`paper_resources/README.md`](paper_resources/README.md) | All | — | Paper-writing materials index (figures, tables, data, notes) |
| [`docs/schema.md`](docs/schema.md) | Shared | — | SQLite schema + research query cookbook |
| [`docs/worked_examples.md`](docs/worked_examples.md) | Shared | — | Hand walkthrough + Bayesian update |
| [`docs/stage5_identifiability.md`](docs/stage5_identifiability.md) | Phase 1 | — | Proof of classification ceiling |
| [`CLAUDE.md`](CLAUDE.md) | Meta | — | Project memory for future sessions |
