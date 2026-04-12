# Poker Trust Simulation

Multi-agent Bayesian trust dynamics in 8-player Limit Texas Hold'em. Eight
rule-based archetype agents play tens of thousands of hands against each
other while every agent maintains a live posterior over what *kind* of
player everyone else is. No machine learning &mdash; just game theory,
Monte Carlo equity, and Bayesian updates.

This is Phase 1 of a two-phase research project. Phase 1 is the
complete data-generation pipeline + research toolchain; Phase 2 (not in
this repo) trains ML models on the datasets this produces.

## Build status

All 12 stages complete. Every stage has both a canonical placeholder
test in `test_cases.py` and a real-assertion test in `stage_extras.py`
registered through `run_tests.py`.

| Stage | Deliverable | Status |
|---|---|---|
| 1 | Card / Deck / Hand evaluator | ✅ |
| 2 | Game engine + Table + scripted agents | ✅ |
| 3 | `BaseAgent` + `Oracle` + per-action viewer stepping | ✅ |
| 4 | Static archetypes: Sentinel / Firestorm / Wall / Phantom | ✅ |
| 5 | Bayesian trust model + per-agent posteriors | ✅ |
| 6 | Adaptive archetypes: Predator / Mirror / Judge | ✅ |
| 7 | SQLite persistent hand logger | ✅ |
| 8 | `run_sim.py` full 10 000-hand research CLI | ✅ |
| 9 | Viewer polish: Trust Lens + Heatmap + Stats + Entropy bars | ✅ |
| 10 | `run_multiseed.py` orchestration + aggregates | ✅ |
| 11 | `data.csv_exporter` ML-ready CSV dumps | ✅ |
| 12 | `run_sensitivity.py` parameter sweeps | ✅ |

**One known caveat:** the canonical `test_stage_5.3` aspirational
threshold (Sentinel posterior entropy &lt; 2.2 bits after 500 hands) is
mathematically unachievable because `sentinel`, `mirror_default`, and
`judge_cooperative` share identical average parameters. See
`notes/stage5_identifiability.md` for the full derivation. All other
Stage 5 invariants pass.

## Quick start

```bash
python3 -m pip install -r requirements.txt   # treys + numpy

# Run every stage's tests (1-5 pass, 5.3 aspirational fails, 6/7/10/11 pass)
python3 run_tests.py --stage all

# Generate a 30-hand Stage 6 demo for the replay viewer
python3 run_demo.py --stage 6 --hands 30 --seed 42

# Open visualizer/poker_table.html in any modern browser
```

## Runner CLIs

Five scripts, each with a well-defined purpose. All default to the
highest available stage and take `--seed`/`--hands` flags.

### `run_tests.py` &mdash; test runner

Dispatches to `test_cases.test_stage_N` + `stage_extras.stageN_extras`
for every registered stage.

```bash
python3 run_tests.py --stage all
python3 run_tests.py --stage 6
```

### `run_demo.py` &mdash; viewer data generator

Plays a short run and writes `visualizer/data.js` (git-ignored). Re-run
after each stage to refresh the viewer's observer list + trust data.

```bash
python3 run_demo.py --stage 6 --hands 60 --seed 42
# Then open visualizer/poker_table.html
```

### `run_sim.py` &mdash; full research simulation with SQLite logging

The heavy-duty runner for the Stage 8 research dataset. Plays each seed
serially, logs every hand / action / showdown / trust snapshot into a
persistent SQLite database, and asserts chip conservation at the end of
each seed.

```bash
# Smoke test (~90s)
python3 run_sim.py --seeds 42 --hands 500 --db smoke.sqlite --stage 6

# Full research run (multiple hours — the canonical Phase 1 dataset)
python3 run_sim.py \
    --seeds 42,137,256,512,1024 \
    --hands 10000 \
    --db runs.sqlite \
    --stage 6
```

At ~5-9 hand/s on a modern laptop, one seed of 10 000 hands takes
~20-30 minutes. Output database size: ~120 MB per seed. See
`docs/schema.md` for the full schema and query examples.

### `run_multiseed.py` &mdash; stdlib CSV export for ML pipelines

Plays multiple seeds and writes the Stage 11 ML-ready CSV triple
(`actions.csv`, `hands.csv`, `agent_stats.csv`) per seed plus two
cross-seed aggregates. No SQLite, no pandas.

```bash
python3 run_multiseed.py \
    --seeds 42,137,256,512,1024 \
    --hands 10000 \
    --outdir research_runs
```

Produces `research_runs/seed_42/actions.csv` etc. plus
`research_runs/seed_aggregate.csv` (one row per (archetype, seed)) and
`research_runs/seed_aggregate_mean.csv` (mean + std dev per archetype).

### `run_sensitivity.py` &mdash; trust-model parameter sweeps

Stage 12. Sweeps `lambda_decay`, `epsilon_noise`, or `third_party_weight`
while holding everything else fixed. Measures mean trust, mean entropy,
and per-archetype identification rate at the end of each cell.

```bash
python3 run_sensitivity.py --param lambda  --values 0.90,0.93,0.95,0.97,1.0 --hands 1000 --seeds 42,137,256
python3 run_sensitivity.py --param epsilon --values 0.00,0.025,0.05,0.10,0.15 --hands 1000 --seeds 42,137,256
python3 run_sensitivity.py --param tpw     --values 0.4,0.6,0.8,1.0           --hands 1000 --seeds 42,137,256
```

Restores `config.TRUST` in a `try/finally` so a crashed cell can't
poison subsequent runs.

## The eight archetypes

| Seat | Agent | Type | One-liner |
|---|---|---|---|
| 0 | Oracle | Static | Nash-ish equilibrium baseline |
| 1 | Sentinel | Static | Tight-aggressive (TAG); folds unless strong |
| 2 | Firestorm | Static | Loose-aggressive (LAG / maniac); bluffs constantly |
| 3 | Wall | Static | Calling station; never folds, never bluffs |
| 4 | Phantom | Static | Deceiver; mixes strong value with trashy bluffs |
| 5 | **Predator** | Adaptive | Exploiter &mdash; reads `self.posteriors` and blends toward `PREDATOR_EXPLOIT[target_type]` once `max_prob > 0.60` |
| 6 | **Mirror** | Adaptive | Tit-for-tat &mdash; copies the most-active opponent's observed br/cr/vbr |
| 7 | **Judge** | Adaptive | Grudger &mdash; maintains a permanent grievance ledger; switches to retaliatory params at grievance &gt;= 5 |

Static agents override only `get_params(betting_round, state)` to
return a fixed dict from `archetype_params.ARCHETYPE_PARAMS`. Adaptive
agents override the same method but compute the dict from their own
accumulated state (posteriors for Predator, observed_stats for Mirror,
grievance for Judge). Decision logic &mdash; branching on
`cost_to_call`, caching hand strength per street, VPIP/PFR/AF tracking
&mdash; lives once in `BaseAgent` and is shared by every archetype.

## Bayesian trust model

Every agent maintains `self.posteriors[opponent_seat]` as an 8-element
numpy array over the 8 archetype types in `trust.TRUST_TYPE_LIST`. The
update rule (see `trust/bayesian_model.py` and
`worked_examples.md` Example 2):

```
adjusted_likelihood = (1 - epsilon) * raw_likelihood + epsilon * (1/num_actions)
decayed_prior       = prior ** lambda_decay            (applied once per hand)
unnormalized        = decayed_prior * (adjusted_likelihood ** weight)
posterior           = unnormalized / sum(unnormalized)
```

- `lambda_decay = 0.95` &mdash; applied once per hand in `on_hand_end`, not
  per action, so evidence within a hand accumulates before the prior fades.
- `epsilon_noise = 0.05` &mdash; trembling-hand smoothing.
- `third_party_weight = 0.8` &mdash; weight exponent on `adjusted_likelihood`
  when the observer had folded before this action (only sees it as an
  outsider).
- **Live updates** fire on every observed non-self action with
  `bucket=None` (marginal likelihood over {Strong, Medium, Weak}).
- **Showdown updates** fire once per revealed opponent per round they
  acted, using the now-known bucket from the revealed hole cards +
  visible community. Fast deterministic `treys` rank-class bucketing, no
  Monte Carlo on the hot path.

Trust score: `T = sum(P_k * (1 - average_BR_k))` &mdash; expected
honesty under the current posterior. Max entropy for 8 types =
`log2(8) = 3` bits.

## Project layout

```
Poker_trust/
├── engine/
│   ├── deck.py              # seeded Deck over treys.Card ints
│   ├── evaluator.py         # get_hand_strength (preflop lookup + MC)
│   ├── actions.py           # ActionType enum + ActionRecord dataclass
│   ├── game.py              # GameState + Hand (one hand of Limit Hold'em)
│   └── table.py             # 8-seat Table, rebuys, logger hook, RNG
├── agents/
│   ├── base_agent.py        # shared BaseAgent with decide_action + stats
│   ├── oracle.py            # Nash-equilibrium static
│   ├── sentinel.py          # tight-aggressive static
│   ├── firestorm.py         # loose-aggressive static
│   ├── wall.py              # calling station static
│   ├── phantom.py           # deceiver static
│   ├── predator.py          # adaptive exploiter (reads posteriors)
│   ├── mirror.py            # adaptive tit-for-tat (reads opponent stats)
│   ├── judge.py             # adaptive grudger (grievance ledger)
│   └── dummy_agent.py       # DummyAgent / FolderAgent / RaiserAgent (scripted, Stage 2 tests)
├── trust/
│   ├── __init__.py
│   └── bayesian_model.py    # vectorized posterior update + trust_score + entropy
├── data/
│   ├── visualizer_export.py # played hand → window.POKER_DATA dict for the viewer
│   ├── sqlite_logger.py     # persistent SQLite hand logger (Stage 7)
│   ├── schema.sql           # runs / hands / actions / showdowns / trust_snapshots / agent_stats
│   └── csv_exporter.py      # stdlib CSV dumps (Stage 11)
├── visualizer/
│   ├── poker_table.html     # single-file DesignCues viewer w/ Trust Lens + Heatmap + Stats + Entropy
│   └── data.js              # generated by run_demo.py (gitignored)
├── notes/
│   └── stage5_identifiability.md   # why the 5.3 aspirational test can't pass
├── docs/
│   └── schema.md            # SQLite schema reference + query cookbook
├── tests/
│   └── test_trust_model.py  # unit tests for trust/bayesian_model.py primitives
├── config.py                # HAND_STRENGTH / SIMULATION / TRUST / NUM_PLAYERS
├── archetype_params.py      # per-round per-archetype parameters (spec file)
├── preflop_lookup.py        # 169-hand preflop bucketing (spec file)
├── test_cases.py            # canonical spec tests (mostly aspirational past Stage 1)
├── stage_extras.py          # real assertions layered on top, one function per stage
├── run_tests.py             # stage-aware test runner
├── run_demo.py              # per-stage viewer data generator
├── run_sim.py               # Stage 8 full-simulation CLI (SQLite output)
├── run_multiseed.py         # Stage 10 multi-seed orchestration (CSV output)
├── run_sensitivity.py       # Stage 12 parameter-sweep CLI
├── worked_examples.md       # spec: complete hand walkthrough + Bayesian update example
├── The_Eight_Archetypes_Specification.docx
├── Claude_Code_Implementation_Prompt.md     # full build spec
├── DesignCues                                # dark-editorial design system for the viewer
├── CLAUDE.md                                 # persistent project memory for future sessions
├── CHANGELOG.md
└── README.md
```

## Reproducing the canonical research dataset

The Phase 1 research run is 5 seeds × 10 000 hands at Stage 6 with
SQLite logging on. Everything is seed-deterministic, so identical
`--seeds` produces identical outputs at the byte level.

```bash
python3 run_sim.py \
    --seeds 42,137,256,512,1024 \
    --hands 10000 \
    --db runs.sqlite \
    --stage 6
```

Expected output: `runs.sqlite` ~600 MB containing ~800 000 actions,
~50 000 hands, ~2.8 M trust snapshots across 5 runs. Chip conservation
is asserted at the end of every seed; if `chip_delta != 0` the run is
discarded.

Query examples live in `docs/schema.md`.

## Visualizer

`visualizer/poker_table.html` is a single-file HTML / vanilla-JS replay
viewer. Loads `data.js` (generated by `run_demo.py`) via a `<script src>`
tag so it works over `file://` with zero build step.

Three view modes (segmented picker in the sidebar):

1. **Trust Lens** &mdash; default. One observer selected via dropdown;
   every other seat shows a trust ring (gold → rust) + top archetype
   guess + entropy bar.
2. **Heatmap** &mdash; 8 × 8 grid of (observer, target) trust scores.
   Cells hoverable; diagonal blacked out.
3. **Stats** &mdash; live VPIP / PFR / AF per seat computed by walking
   the action log up to the current frame.

Per-action stepping via arrow keys; Shift+arrows jump whole hands;
space toggles autoplay. Cormorant Garamond italic display + Inter body +
DM Mono labels, noise overlay, hairline dividers, gold accent. All the
aesthetic decisions are documented in the `DesignCues` file at the
repo root.

## Environment

- Python 3.11 or 3.12
- `treys` 0.1.8+
- `numpy` 2.0+

No other dependencies. No pandas, no matplotlib (viewer uses inline
SVG/CSS), no build step.

## Further reading

- `CLAUDE.md` &mdash; project memory for future Claude sessions
- `CHANGELOG.md` &mdash; chronological summary of what each stage delivered
- `docs/schema.md` &mdash; SQLite schema reference + research query cookbook
- `notes/stage5_identifiability.md` &mdash; the math behind the Sentinel/Mirror/Judge cluster
- `worked_examples.md` &mdash; complete hand walkthrough + Bayesian update example
- `Claude_Code_Implementation_Prompt.md` &mdash; full Phase 1 build spec
