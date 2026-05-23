# Changelog

All notable changes to this project. Organized by stage, in build
order rather than reverse-chronological, because the research
milestones are easier to reason about that way.

## [Paper-writing scaffold + onboarding docs] &mdash; 2026-05-23

Three deliverables added in preparation for the next mentor meeting
and the actual paper-writing pass:

- `paper_resources/manuscript/main.tex` &mdash; LaTeX scaffold with
  every section, subsection, figure, table, math equation, and boxed
  hand-example pre-placed. Each section carries a `% PROSE:` marker
  block describing what paragraphs to write (the prose itself is the
  author&apos;s). Compiles via standard
  `pdflatex \rightarrow bibtex \rightarrow pdflatex^{\times 2}`
  pipeline; produces a 12-page draft with all figures embedded.
- `paper_resources/manuscript/references.bib` &mdash; bibliography
  stub with the load-bearing citations (Axelrod, Nowak, Resnick &amp;
  Zeckhauser, Bowling et al., Brown &amp; Sandholm, Bolton et al.,
  Park et al., etc.).
- `paper_resources/notes/PROJECT_ORIENTATION.md` &mdash; ground-up
  project documentation (~600 lines) written assuming the reader
  remembers nothing. Covers the research question, all eight
  archetypes, the full Bayesian trust-model math, every phase&apos;s
  setup and headline numbers, the metrics framework, the two
  &quot;money quote&quot; hands, real-world parallels, and a
  cheat-sheet of numbers to memorize.
- `paper_resources/notes/ARPIT_MEETING_FAQ.md` &mdash; 32 anticipated
  mentor questions with prepared answers, grouped by topic (headline
  finding, statistical rigor, Nash falsification, methodology, trap
  mechanism, limitations, future work) plus quick-recall flashcards.

## [Root layout cleanup] &mdash; 2026-05-22 (final)

Reduced repo-root entries from 16 to 7 (5 ignoring dotfiles). Removed
the &quot;For mentor review&quot; section from the README. The root now
contains only artifacts that *must* be there for the existing import
patterns: `config.py`, `archetype_params.py`, `preflop_lookup.py`,
plus `CLAUDE.md` and `README.md`.

Moves (all preserve git history via `git mv`):
- `compute_metrics.py`  &rarr; `analysis/compute_metrics.py`
- `compare_phases.py`   &rarr; `analysis/compare_phases.py`
- `extract_phase3_stats.py` &rarr; `analysis/extract_phase3_stats.py`
- `run_phase3_scorecard.sh` &rarr; `analysis/run_phase3_scorecard.sh`
- `phase3_stats.json`   &rarr; `paper_resources/data/phase3_stats.json`
- `phase31_stats.json`  &rarr; `paper_resources/data/phase31_stats.json`
- `phase3_long_audit.json`  &rarr; `reports/phase3_long_audit.json`
- `phase31_long_audit.json` &rarr; `reports/phase31_long_audit.json`
- `runs_phase3_long.sqlite` (LFS pointer) &rarr;
  `research_data/runs_phase3_long.sqlite` &mdash; consolidates with the
  existing `research_data/runs_v3.sqlite.part_*` LFS pointers.

Code reference updates:
- `phase2/adaptive/phase2_comparison.py`: `from compute_metrics import &hellip;`
  &rarr; `from analysis.compute_metrics import &hellip;`
- `analysis/make_paper_figures.py` and `make_paper_tables.py`: stats
  JSON paths now resolve to `paper_resources/data/&hellip;`.
- `analysis/extract_phase3_stats.py`: default `--out` now points at
  `paper_resources/data/phase3_stats.json`.
- `analysis/run_phase3_scorecard.sh`: `cd`s to repo root and invokes
  `python3 analysis/compute_metrics.py`.

Doc updates: README.md, CLAUDE.md, paper_resources/README.md,
reports/README.md, phase3/README.md, phase3/phase3_report.md all
point at the new paths.

Verification:
- 27/27 trust model tests
- 18/18 side-pot tests
- `make_paper_figures.py` and `make_paper_tables.py` regenerate
  cleanly with the new JSON paths
- `analysis/compute_metrics.py`, `compare_phases.py`,
  `extract_phase3_stats.py` all import OK from their new location
- `phase2/adaptive/phase2_comparison.py` (the only cross-module
  consumer of `compute_metrics`) imports OK

## [Publication-readiness pass] &mdash; 2026-05-22 (later)

Four-track parallel re-audit (engine + agents + Phase 3 + analysis).
Engine, agents, and analysis layers cleared as publication-ready.
Two follow-up items closed here.

- `tests/test_engine_sidepot.py` (new): five targeted unit tests of
  the `engine/game.py::_showdown` side-pot algorithm. Constructs each
  scenario explicitly (three-way all-in at three levels, short stack
  with the best hand, folded chips cascading into lower side pots,
  single contribution level, tied hands with odd-chip remainder).
  18/18 assertions pass. Includes an explicit regression guard against
  the pre-fix behavior (the short stack with the best hand collecting
  the full pot).
- `phase3/dealer.py`, `phase3/README.md`, `phase3/llm_chat_agent.py`:
  documentation updated to match what the canonical Phase 3 runner
  actually does. The `Dealer` class is a **post-hoc audit layer**
  (chip conservation, anomaly detection, end-of-run JSON dump) and is
  *not* on the decision hot path; action legality is enforced in two
  layers (`LLMChatAgent.decide_action` proactive fix +
  `engine.game.Hand` coercion). The audit-mode `validate_action` hook
  is preserved but is no longer documented as the active path.
- `paper_resources/README.md`: data table now lists 13 CSVs (was 12);
  `r_bootstrap_ci.csv` is documented as backing the headline-r
  confidence-interval claim.

## [Repo finalization] &mdash; 2026-05-22

- Paper artifacts moved out of the repo. `paper.md` and `paper/` are
  deleted; the paper itself is now written externally (Overleaf).
  Supporting materials &mdash; figures, LaTeX tables, CSV data, story
  hands, topical notes &mdash; live in `paper_resources/`.
- Stale Phase 3 file-I/O orchestration removed: `file_io_agent.py`,
  `run_phase3_fileio.py`, `orchestrate.py`, `SESSION_PROMPT*.md`. The
  canonical Phase 3 runner is `phase3/run_phase3_chat.py`.
- Removed redundant `docs/Implementation Doc.pdf` (4.2 MB image-encoded
  duplicate of the canonical `docs/Claude_Code_Implementation_Prompt.md`).
- Added `docs/DesignStatement.md` &mdash; opinionated north-star brief
  complementing the token-level `docs/DesignCues`.
- Removed `phase2/_imitation_archive/` (the original ML-imitation Phase 2)
  along with `agents/ml_agent.py`. The archive was superseded by
  `phase2/adaptive/` and its ML training/eval scripts had broken
  internal imports (`from phase2.ml.X` references after the rename to
  `phase2._imitation_archive.ml.X`), so it could not actually be run.
  The headline number it produced (r = &minus;0.825 vs Phase 1&apos;s
  &minus;0.837, ~1.4&nbsp;% reproduction) is preserved in
  `phase2/adaptive/phase2_report.md` as a sanity-check baseline.
- Removed `analysis/analyze_runs.py` &mdash; the 487-line 9-section
  standard report. `analysis/deep_analysis.py` (1524 lines, 31 sections)
  is the superset and the canonical analysis script.
- Engine: implemented proper side-pot accounting in `engine/game.py`.
  Previously, a short-stacked player who could only call part of a
  required bet still collected the full pot at showdown; the engine now
  builds side pots by contribution level and awards each separately.
  This is a chip-EV correctness fix; historical Phase 1 and Phase 2
  scorecards no longer reproduce byte-for-byte and would need a fresh
  run to match.
- Bug fixes from the May 2026 audit pass:
  - `analysis/compare_phases.py`, `analysis/deep_analysis.py`: aggression factor
    SQL now uses `NULLIF(calls, 0)` instead of `CASE WHEN calls&gt;0
    THEN calls ELSE 1 END`, so AF is `NULL` (not raw bet+raise count)
    when a player never calls.
  - `analysis/compute_metrics.py::compute_trust_manipulation`: past and future
    windows around index `i` are now disjoint (future starts at
    `i+1`), removing an off-by-one that contaminated the TMA delta.
  - `phase3/llm_chat_agent.py`: pinned `temperature=0.0` on the
    Anthropic client path (was using the SDK default of 1.0).
  - `phase3/llm_chat_agent.py::_parse_action`: switched from
    substring-priority matching (which returned CALL for inputs like
    "I won&apos;t call, I bet") to word-boundary regex + last-match
    preference, matching the final-line `ACTION:` convention.
  - `phase3/dealer.py`: docstring of `post_hand_audit` corrected to
    match what the audit actually checks (only the &quot;at least one
    winner&quot; invariant; hand-rank verification is delegated to
    `treys.Evaluator`).
  - `agents/mirror.py`: stale docstring about `weak_call` being
    mirrored removed; the code (correctly) does *not* blend it.
  - `data/csv_exporter.py`, `data/visualizer_export.py`: added
    `encoding=&quot;utf-8&quot;` to all `open()` calls (Windows
    cp1252 risk).
- Added `analysis/bootstrap_ci.py` &mdash; per-phase mean-r CIs via
  t-interval and 10 000-resample bootstrap, with per-seed Fisher-z
  intervals on the underlying 8-archetype correlations.
- `phase1/run_sim.py`: SQLite logger now wrapped in `try/finally` so
  a mid-run `KeyboardInterrupt` or exception still marks the run row
  finalized with the partial hand count.

## [Phase 2* unbounded sub-experiment] &mdash; 2026-05-04

Tests Arpit's "do economically-motivated agents converge to a
Nash-equilibrium profile if given full parameter freedom?" hypothesis.

- `phase2/adaptive/bounds.py::make_unbounded_bounds()` &mdash; helper
  that returns `(0.0, 1.0)` on every (round, metric) slot.
- `phase2/adaptive/hill_climber.py` &mdash; accepts a `bounds=`
  parameter so the optimizer can run unconstrained.
- `phase2/adaptive/run_adaptive.py` &mdash; new `--unbounded` flag.

**Result (5 seeds × 10 000 hands, aggressive HC: &delta;=0.15,
eval_window=50):**
- Mean trust&ndash;profit r = &minus;0.609 &plusmn; 0.221 (essentially
  equal to bounded P2 at &minus;0.637)
- Cluster spread (mean pairwise L1 between all 8 agents in 36-dim
  parameter space) *grew* from 5.82 to 7.5+ on every seed
- Mean convergence index = 1.324 &mdash; agents diverge, not converge
- Mean per-agent drift = 3.4 L1 (11&times; the bounded run); agents
  moved, just not toward each other
- Economic ordering preserved: Firestorm 6 512 chips (6&times; next),
  Wall 179 chips with 28 rebuys

A weak-HC variant at r = &minus;0.779 is preserved as a methodology
footnote (`reports/phase2_unbounded_scorecard.txt`,
`paper_resources/notes/phase2_unbounded_writeup.md`). The aggressive
variant is canonical
(`reports/phase2_unbounded_scorecard_aggressive.txt`,
`paper_resources/notes/phase2_unbounded_writeup_aggressive.md`).

**Implication:** the bound boxes were not the binding constraint. The
stationary trust posterior itself is. See
`paper_resources/notes/nash_convergence_aggressive.md`.

## [Phase 3.1 Complete] &mdash; 2026-05-01

### Phase 3.1 &mdash; LLM agents with reasoning scaffolding

The headline finding of the project. Adds three opt-in features behind a
single `--phase31` flag in `phase3/run_phase3_chat.py`:

- **Chain-of-thought prompts.** System prompt asks the agent to reason in
  at most 2 short sentences before emitting an `ACTION:` marker line.
  Output token budget raised from 16 → 96.
- **Persistent per-opponent memory.** Every 10 hands the agent reduces
  its `_opp_action_log` (populated from the existing `observe_action`
  hook) to short text summaries per opponent ("aggressive 8/12, called
  2/12") and injects them into the user message.
- **Adaptive personality specs.** Every 25 hands the agent makes one
  extra LLM call asking itself to update its `_strategy_notes` field;
  notes are appended to subsequent decision prompts.

**Result (5 seeds × 150 hands, $17 total cost):**
- Trust–profit r drops from −0.510 (Phase 3) to **−0.094** (Phase 3.1) —
  statistically indistinguishable from zero
- Δr = +0.416 — larger than the previous three phase transitions combined
- 2 of 5 seeds show *positive* r (trap inversion)
- Wall (most trusted) climbs from rank 8 to rank 1 in economic ordering
- 4 of 6 behavioral metric targets met (vs Phase 3's 2/6); SU > 1.5
  bits for the first time, TMA jumps to +0.242

**Validation:** `phase3/validate_phase31.py` — 50-check unit suite
exercising every new code path with mock client (no API spend).

**Artifacts:** `reports/phase31_long_scorecard.txt`,
`phase3/phase3_report.md` (Phase 3.1 sub-section appended to the
combined report), `phase31_stats.json`, `phase31_long_audit.json`

## [Phase 3 Complete] &mdash; 2026-04-29

### Phase 3 &mdash; LLM personality role-players

8 independent LLM agents (claude-haiku-4-5) replace the rule-based and
adaptive agents from Phases 1/2. Each agent gets an archetype-specific
personality spec as its system prompt and returns one of `FOLD CHECK
CALL BET RAISE` per decision.

- `phase3/personality_specs/<archetype>.md` — qualitative + quantitative
  spec for each of the 8 archetypes
- `phase3/llm_chat_agent.py` — `LLMChatAgent` + `LLMChatJudge` wrapping
  Anthropic / Ollama / claude-cli backends. All trust + observation +
  hand-strength caching machinery inherited from Phase 1 BaseAgent
- `phase3/run_phase3_chat.py` — runner with `--provider` and `--model`
  flags. Supports prompt caching (commit `230d6ab`) for ~38% cost
  reduction
- `phase3/dealer.py` — game-integrity layer that validates LLM actions
  and substitutes a legal default if the LLM emits something illegal

**Result (5 seeds × 500 hands, $33.10 total cost):**
- Trust–profit r softens to **−0.510** (Δr = +0.127 from Phase 2)
- High variance (σ = 0.268, ~2× Phase 2)
- 4 of 6 behavioral metric targets MISSED — three move backward
- Phantom climbs from rank 7 to rank 1; Firestorm falls from 1 to 5;
  Sentinel falls from 3 to 7
- Diagnostic finding: LLMs faithfully role-play personality specs
  but do not spontaneously develop opponent-conditional, time-varying,
  or unpredictable behavior

**Artifacts:** `reports/phase3_long_scorecard.txt`,
`phase3/phase3_report.md`, `phase3_stats.json`,
`extract_phase3_stats.py`

## [Phase 2 Complete] &mdash; 2026-04-29

### Phase 2 (canonical) &mdash; Bounded online optimization (adaptive)

Replaces the original imitation-based Phase 2 with a per-cycle hill
climber that tunes each agent's parameters within an archetype-shaped
bound box. The earlier ML-imitation Phase 2 (which reproduced Phase 1
by construction) is preserved at `phase2/_imitation_archive/`.

- `phase2/adaptive/bounds.py` &mdash; `ARCHETYPE_BOUNDS` dict defining
  `(lo, hi)` per `(archetype, round, metric)`. Tight (Sentinel, Wall):
  ±10–15 %. Moderate (Oracle, Predator, Mirror, Judge cooperative):
  ±20–25 %. Loose (Firestorm, Phantom, Judge retaliatory): ±30–40 %.
  Identity-locked metrics clamped near zero so archetype shape survives.
- `phase2/adaptive/adaptive_agent.py` &mdash; `AdaptiveAgent` and
  `AdaptiveJudge` classes wrapping `BaseAgent` with mutable parameters
  and a `record_snapshot` hook for trajectory logging.
- `phase2/adaptive/hill_climber.py` &mdash; per-agent online optimizer.
  Every 200 hands: baseline phase, then trial phase with one perturbed
  `(round, metric)` parameter, accept if windowed profit improves.
  δ decays 0.995 per cycle, floor 0.005.
- `phase2/adaptive/run_adaptive.py` &mdash; simulation runner. Supports
  multi-seed serial execution with per-seed `chip_delta` audit.
- `phase2/adaptive/phase2_comparison.py` &mdash; cross-phase scorecard
  generator. Produces 7 tables comparing Phase 1 reference vs Phase 2
  adaptive across r, behavioral fingerprints, economic ordering,
  parameter trajectories, and Aberration Index.

**Result (5 seeds × 10 000 hands):**
- Trust–profit r softens to **−0.637** (Δr = +0.116 from Phase 1)
- Direction consistent across all 5 seeds
- Opponent Adaptation stays at OA = 0.0003 — bounded numerical
  optimization on aggregate reward cannot produce per-opponent strategy
- Aberration Index 0.193 — bound boxes preserve archetype identity
- Mentor briefing doc: `phase2/adaptive/PHASE2_REDESIGN_PLAN.md`

**Artifacts:** `reports/phase2_scorecard_long.txt` (canonical 5 × 10000),
`reports/phase2_scorecard.txt` (lean 3 × 5000),
`phase2/adaptive/phase2_report.md`,
`phase2/adaptive/param_trajectories.json`,
`phase2/adaptive/optimization_log.json`

## [Phase 1 Complete] &mdash; 2026-04-11

### Stage 12 &mdash; Sensitivity analysis scaffold

- `run_sensitivity.py` CLI for sweeping trust-model hyper-parameters
  (`lambda_decay`, `epsilon_noise`, `third_party_weight`) across a grid
  of values and seeds.
- Measures mean trust, mean posterior entropy, and per-archetype
  identification rate at the end of each (value, seed) cell.
- Restores `config.TRUST` and the cached module-level constants in
  `trust.bayesian_model` in a `try/finally` so a crashed cell can't
  contaminate subsequent runs.
- Stage 6 support: tracks adaptive-agent identification rates
  (`predator_id_rate`, `mirror_id_rate`, `judge_id_rate`) alongside
  the static archetypes when `--stage 6` (the default).

### Stage 11 &mdash; ML-ready CSV exports

- `data/csv_exporter.py` with three stdlib-csv writers:
  - `write_actions_csv` &mdash; one row per `ActionRecord`, carrying
    Oracle's live trust/entropy/top-archetype view of the acting seat
    so per-action rows are ready for downstream feature engineering.
  - `write_hands_csv` &mdash; one row per hand, with `mean_trust_into_seat_0..7`
    columns for cross-agent trust analysis.
  - `write_agent_stats_csv` &mdash; one row per (run, seat) with final
    VPIP / PFR / AF / showdowns / stack / rebuys.
- `stage_extras.stage11_extras` (10 assertions) validates row counts,
  header consistency, no empty required cells, and round-trip
  `csv.DictReader` parsing.

### Stage 10 &mdash; Multi-seed orchestration

- `run_multiseed.py` CLI that plays multiple seeds serially and
  writes the full Stage 11 CSV triple per seed.
- Two cross-seed aggregate CSVs:
  - `seed_aggregate.csv` &mdash; one row per (archetype, seat, seed)
  - `seed_aggregate_mean.csv` &mdash; one row per archetype with cross-seed
    mean and sample standard deviation
- `stage_extras.stage10_extras` verifies seed subdirectories, CSV
  shape, chip conservation across all seeds, and byte-identical
  reproducibility of the same `--seeds` input.

### Stage 9 &mdash; Viewer polish: heatmap, stats, entropy bars

- `visualizer/poker_table.html` grows from 1244 to 1927 lines with
  three new view modes.
- **Trust Heatmap panel** (`06 — Trust Heatmap`): 8&times;8 grid of
  (observer, target) trust cells reusing the gold &rarr; rust palette.
  Diagonal blacked out. Per-cell hover shows
  `observer &rarr; target: trust T.TTT, top_archetype top_p%, entropy`.
- **Agent Stats panel** (`07 — Agent Stats`): one compact row per
  seat with live VPIP / PFR / AF / stack. Stats computed by walking
  the action log from hand 0 through the current frame. Matches the
  definitions in `agents/base_agent.py`.
- **Entropy bars**: each non-observer seat's trust ring now has a
  horizontal posterior-entropy bar underneath it (0&ndash;3 bits,
  color-banded by confidence).
- Segmented view-mode picker at the top of the sidebar toggles
  between Trust Lens / Heatmap / Stats. Backwards-compatible with
  Stage 2&ndash;4 `data.js` files (just shows hidden trust rings).

### Stage 8 &mdash; `run_sim.py` full research simulation

- `run_sim.py` CLI for the canonical 10 000-hand &times; 5-seed
  research run with per-seed SQLite logging.
- Progress bar with real-time hand/sec and ETA, updated on every hand.
- Chip conservation assertion at the end of each seed:
  `sum(final_stack) = num_seats * starting_stack + rebuys * starting_stack`.
- Stage 6 roster support added in hotfix `fedbd29`: registers
  `_stage6_roster()` returning the full 8-archetype canonical roster
  (Oracle / Sentinel / Firestorm / Wall / Phantom / Predator / Mirror /
  Judge). The CLI's default stage is the highest registered, so post-
  hotfix `--stage 6` is the default.

### Stage 7 &mdash; Persistent SQLite hand logger

- `data/sqlite_logger.py` with the `SQLiteLogger` class
  (`start_run`, `log_hand`, `log_agent_stats`, `close`).
- `data/schema.sql` with six tables (`runs`, `hands`, `actions`,
  `showdowns`, `trust_snapshots`, `agent_stats`) and composite-key
  indexes on `(run_id, hand_id)` for the hot per-hand join columns.
- `engine/table.py` gains optional `logger` and `run_id` kwargs; when
  both are set, `play_hand` forwards the just-played Hand after the
  dealer rotates. Zero changes to the existing engine logic.
- `stage_extras.stage7_extras` (7 assertions) runs a 50-hand in-memory
  SQLite simulation and verifies: runs table count, hands table count,
  actions row count matches summed action-log lengths,
  `trust_snapshots` count (50 hands &times; 8 observers &times; 7
  targets = 2800), chip conservation across rebuys, and foreign-key
  integrity on `actions.hand_id`.

### Stage 6 &mdash; Adaptive agents: Predator / Mirror / Judge

- `agents/predator.py` &mdash; reads `self.posteriors` for every active
  opponent, finds the one with the highest top-archetype probability,
  and blends `ARCHETYPE_PARAMS["predator_baseline"]` toward
  `PREDATOR_EXPLOIT[top_target]` using
  `alpha = min(1, (max_prob - 0.60) / 0.30)`. Facing-bet sub-policies
  fall through unchanged so the reaction plan stays coherent.
- `agents/mirror.py` &mdash; accumulates `observed_vpip`, `observed_br`,
  `observed_cr` per opponent via a new `BaseAgent` hook
  (`_observe_opponent_action`). At `get_params` time, picks the single
  most-active opponent and copies their headline metrics into its own
  params. Falls back to `mirror_default` when no stats exist.
- `agents/judge.py` &mdash; permanent per-opponent grievance ledger. At
  showdown, for every revealed opponent that bet/raised on a
  confirmed Weak bucket against the Judge, `grievance[seat] += 1`.
  When grievance crosses `tau = 5` the Judge flips `triggered[seat]`
  permanently and serves `judge_retaliatory` params whenever any
  triggered opponent is active. No decay, no forgiveness.
- `agents/base_agent.py` gains a 17-line `_observe_opponent_action`
  hook (no-op default) so adaptive agents can accumulate state
  without touching the audited Stage 5 trust-update flow.
- `stage_extras.stage6_extras` (44 assertions) runs a 1000-hand full
  8-archetype table and verifies: Predator posterior for Firestorm
  &gt; 0.60 and exploit-regime br values, Mirror VPIP &gt; 30% with
  observed stats tracking the correct opponents, Judge grievance
  ledger reaching &ge; 1 for Firestorm, retaliatory params served on
  trigger, plus per-agent invariants (PFR &le; VPIP, showdowns &le;
  saw_flop &le; hands_dealt) and full reproducibility.

### Stage 5 &mdash; Bayesian trust model

- `trust/bayesian_model.py` &mdash; vectorized Bayesian update primitives.
  - `initial_posterior` &mdash; uniform prior over the 8 archetype types
    in `TRUST_TYPE_LIST`.
  - `update_posterior` &mdash; one observation step with precomputed
    likelihood tables (indexed by round &times; bucket &times; action
    &times; archetype), trembling-hand smoothing, and an exponent
    for third-party weight. Hot path runs in ~10 microseconds per
    update.
  - `decay_posterior` &mdash; one lambda-decay step, applied once per
    hand (not per action) so evidence within a hand accumulates
    before the prior fades.
  - `trust_score` &mdash; `T = sum(P_k * honesty_k)` using the
    `HONESTY_SCORES` table from `archetype_params.py`.
  - `entropy` &mdash; `H = -sum(P_k * log2(P_k))` in bits.
  - `posterior_to_dict` / `dict_to_posterior` &mdash; named-key view
    helpers for code that prefers dicts.
- `config.TRUST` section: `lambda_decay = 0.95`, `epsilon_noise = 0.05`,
  `third_party_weight = 0.8`, `initial_prior = 1/8`.
- `BaseAgent` wiring:
  - `self.posteriors` lazy-initialized per opponent seat on first
    observation.
  - `observe_action` fires one live update per non-self action with
    `bucket=None` (marginal likelihood).
  - `observe_showdown` refines posteriors for every revealed opponent
    using the now-known bucket at each round, computed via a fast
    deterministic treys rank-class lookup (`_fast_bucket` &mdash; no
    Monte Carlo on the hot path).
  - `on_hand_end` applies one `decay_posterior` step per opponent.
  - Public accessors: `trust_score(seat)`, `entropy(seat)`,
    `get_posterior(seat)`, `get_trust_score(seat)`, `get_entropy(seat)`.
- Engine: `_showdown` threads `community_cards` through the
  `observe_showdown` broadcast so agents can recompute each revealed
  opponent's bucket at each round. `DummyAgent` signature updated to
  accept the new kwarg (no-op).
- `data/visualizer_export.py` extended to emit `trust_snapshot`,
  `entropy_snapshot`, and `top_archetype_snapshot` per hand (nested
  `{observer_seat: {target_seat: value}}` dicts).
- **Viewer Stage 5 redesign** (1244 lines): DesignCues dark-editorial
  aesthetic &mdash; Cormorant Garamond italic display + Inter body +
  DM Mono labels + gold accent + noise overlay + hairline dividers.
  New Trust Lens panel with observer dropdown, per-seat trust rings,
  and top-archetype labels.
- `stage_extras.stage5_extras` (6 assertions) passes cleanly. Canonical
  `test_stage_5.3` aspirational threshold (Sentinel entropy &lt; 2.2
  bits) is mathematically unachievable due to the Sentinel /
  Mirror / Judge cluster identifiability. See
  `notes/stage5_identifiability.md`.

### Stage 4 &mdash; Static archetypes: Sentinel / Firestorm / Wall / Phantom

- `agents/sentinel.py` &mdash; Tight-Aggressive (TAG).
- `agents/firestorm.py` &mdash; Loose-Aggressive (LAG / Maniac).
- `agents/wall.py` &mdash; Passive calling station.
- `agents/phantom.py` &mdash; Deceiver / false-signal generator.
- All four are thin BaseAgent subclasses: only `get_params` is
  overridden, returning the per-round dict from `ARCHETYPE_PARAMS`.
- Viewer: archetype accent colors on seat cards, archetype chip
  labels, reserved slots for Predator / Mirror / Judge.
- `stage_extras.stage4_extras` (38 assertions) runs a 500-hand full
  5-archetype table and verifies: per-agent invariants, loose
  absolute VPIP/PFR bounds (wider than the spec's aspirational
  ranges because the spec assumes a "weak hands raise at rate BR"
  interpretation that makes the parameter table internally
  inconsistent), and the **relative personality orderings** that
  actually matter for trust dynamics (Firestorm VPIP &gt; Sentinel
  VPIP, Wall PFR = min, etc.).

### Stage 3 &mdash; BaseAgent + Oracle + per-action viewer stepping

- `agents/base_agent.py` with the shared `decide_action` flow: hand-
  strength caching per street, cost-to-call-aware decision branching
  (fixes the preflop BB option), VPIP/PFR/AF stat tracking,
  `on_hand_start`/`on_hand_end` lifecycle hooks.
- `agents/oracle.py` &mdash; first concrete archetype, pulls static
  per-round params from `ARCHETYPE_PARAMS["oracle"]`.
- Engine: `Table` injects the seeded RNG into every agent, calls
  lifecycle hooks around each hand. `engine/game.py`: BET with an
  existing current_bet auto-upgrades to RAISE (fixes the preflop
  BB-option case).
- Visualizer: per-action stepping with two control rows (hand
  navigation on top, within-hand action navigation on bottom), acting
  seat blue glow, current-action highlight in the feed, keyboard
  shortcuts.
- `stage_extras.stage3_extras` (10 assertions) runs Oracle vs 7
  dummies for 500 hands.

### Stage 2 &mdash; Single-hand game engine + Table manager

- `engine/actions.py` &mdash; `ActionType` enum + `ActionRecord` dataclass.
- `engine/game.py` &mdash; `GameState` + `Hand` playing exactly one hand
  with four betting rounds, bet cap enforcement, dealer-relative
  action order, RAISE reopening action for all other active players,
  showdown evaluation with deterministic tie-break, walkover when
  only one player remains.
- `engine/table.py` &mdash; 8-seat `Table` with rebuy logic, dealer
  rotation, seeded RNG, `last_hand` reference for external tooling.
- `agents/dummy_agent.py` &mdash; `DummyAgent` / `FolderAgent` /
  `RaiserAgent` scripted stand-ins.
- `stage_extras.stage2_extras` (17 assertions) covers pot math, bet-
  cap enforcement, fold-to-walkover detection, dealer rotation,
  rebuys, and reproducibility.

### Stage 1 &mdash; Card / Deck / Hand evaluator

- `engine/deck.py` &mdash; seeded Deck over `treys.Card` ints, shuffled
  via `numpy.random.Generator` (not `treys.Deck`, which uses the
  module-level random state).
- `engine/evaluator.py` &mdash; `get_hand_strength(hole, community, rng, seed, num_samples)`
  returns "Strong" / "Medium" / "Weak". Preflop: 169-hand lookup.
  Postflop: Monte Carlo equity vs one random opponent with the
  0.66 / 0.33 thresholds from `config.HAND_STRENGTH`.
- `stage_extras.stage1_extras` &mdash; 8 assertions on card parsing,
  deck shuffling reproducibility, and hand-strength bucket bounds.

## Documentation and tooling (this commit)

- `README.md` full rewrite covering all 12 stages + 5 runner CLIs.
- `CLAUDE.md` &mdash; persistent project memory for future sessions,
  including the non-negotiable conventions, file layout, known
  limitations, and the 4-track parallel-development pattern.
- `notes/stage5_identifiability.md` &mdash; research note explaining
  why the Sentinel entropy test is mathematically unachievable.
- `tests/test_trust_model.py` &mdash; 27 unit tests for
  `trust.bayesian_model` primitives (runs in &lt;1 second).
- `docs/schema.md` &mdash; SQLite schema reference with example
  research queries.
- `CHANGELOG.md` &mdash; this file.

## Versioning

This project does not use semantic versioning. Stages are the unit
of progress. Every stage has a canonical test, a real-assertion test,
and at least one integration point with the runner CLIs.
