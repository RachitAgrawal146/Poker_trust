# CLAUDE.md

> **Layout note (2026-04):** Phase-specific files now live under `phase1/`
> and `phase2/`. Shared engine/trust/analysis packages stay at the repo
> root. All command examples below have been updated — `run_sim.py` is
> now `phase1/run_sim.py`, `run_ml_sim.py` is now `phase2/run_ml_sim.py`,
> etc. Imports inside moved scripts resolve via a small `sys.path`
> fixup that adds the repo root at import time.


Project memory for Claude Code sessions (and humans) working on this
repo. Read this first before touching any code.

## Project overview

**Poker Trust Simulation** &mdash; a four-tier research build. Eight
archetype agents play Limit Texas Hold'em against each other while every
agent maintains a Bayesian posterior over what archetype every other
agent is.

**Status as of 2026-05-01:** all four phases complete. Headline result
is the four-tier ladder of trust-profit r values:

  Phase 1 (frozen rule-based)              r = -0.752
  Phase 2 (bounded hill-climbing)          r = -0.637
  Phase 3 (LLM personality role-play)      r = -0.510
  Phase 3.1 (LLM + CoT + memory + adaptive) r = -0.094 (trap broken)

Detailed reports in `phase1/phase1_report.md`,
`phase2/adaptive/phase2_report.md`, `phase3/phase3_report.md`,
`phase3/phase31_report.md`. Cross-phase scorecards in
`reports/phase31_long_scorecard.txt` (the most recent / most complete).
The Polygence paper draft is at `paper.md` (Markdown source) and
`paper/paper.tex` (Pandoc-converted LaTeX for Overleaf).

All 12 Phase 1 stages are complete. The canonical Phase 1 dataset is produced
by `run_sim.py` with 5 seeds × 10 000 hands at Stage 6.

## Non-negotiable conventions

1. **Never edit `test_cases.py`, `archetype_params.py`, or `preflop_lookup.py`.**
   These are spec files. Their contents are aspirational in places and
   known-imperfect in others (see "Known limitations" below), but they
   are the authoritative spec. Layer real assertions on top via
   `stage_extras.py`, never by modifying the spec file.

2. **Stage tests live in two places.** The canonical
   `test_cases.test_stage_N` function is usually a set of placeholder
   `TEST ...` strings that produce no assertions. The real assertions
   live in `stage_extras.stageN_extras(modules)`, which is registered
   in `run_tests.STAGE_EXTRAS[N]`. The runner concatenates both outputs
   when you run `python3 run_tests.py --stage N`.

3. **Never modify `base_agent.py`'s Stage 5 trust flow** without very
   good reason. It is audited and every archetype subclass depends on
   the exact sequence: `observe_action` applies the live posterior
   update first, then calls `_observe_opponent_action` (a Stage 6 hook
   with a no-op default) so Mirror/Judge can accumulate per-opponent
   stats *without* disturbing the trust math. Adding new behavior
   belongs in a subclass override of `_observe_opponent_action` or
   `observe_showdown`, not in `BaseAgent` itself.

4. **Commits follow the stage-style format established by the merge
   history.** One-line subject identifying the stage and feature, then
   a blank line, then a detailed HEREDOC body describing what changed,
   why, and what the test results looked like. Look at
   `git log --format='%B' 461505a` for a reference.

5. **Never force-push. Never amend.** If you hit a pre-commit hook
   failure, fix the issue and make a new commit. Amending loses work
   when hooks have already rejected the previous attempt.

6. **The working branch is `claude/poker-trust-simulation-6h3xR`** on
   `origin` (`rachitagrawal146/poker_trust`). Four sub-branches
   (`stage6-adaptive`, `stage7-logging`, `stage9-viewer`,
   `stage10-research`) were used during parallel development but are
   now all merged and should not be checked out.

## File layout (critical)

```
engine/         # Pure game-mechanics. Stable. Don't modify unless you
                # find a real bug in the rules of Limit Hold'em.
  game.py       # Hand.play() is the top of the per-hand loop. It
                # broadcasts every action to every agent via
                # a.observe_action(record) AND every showdown via
                # a.observe_showdown(data, community_cards=...).
                # The broadcast is the *only* hook Stage 5+ uses for
                # trust-state propagation.
  table.py      # Owns the seeded numpy RNG, injects it into every
                # agent's .rng attribute, rotates the dealer button,
                # handles rebuys, and optionally forwards played hands
                # to a SQLite logger (Stage 7 hook).
  actions.py    # ActionType enum + ActionRecord dataclass (every
                # field the logger / visualizer / trust model reads).
  evaluator.py  # get_hand_strength(hole, community, rng) → "Strong" |
                # "Medium" | "Weak". Preflop: 169-hand lookup. Postflop:
                # 1000-sample Monte Carlo. This is ~90% of simulation
                # CPU. Don't call it from the trust refinement hot
                # path — use the deterministic treys class bucket
                # (agents/base_agent.py::_fast_bucket) instead.

agents/         # One file per archetype. All inherit from BaseAgent.
  base_agent.py # decide_action, observe_action, observe_showdown,
                # on_hand_start, on_hand_end, VPIP/PFR/AF accessors,
                # trust_score/entropy accessors. The abstract surface
                # concrete agents override is get_params(round, state).
  oracle.py     # Static: returns ARCHETYPE_PARAMS["oracle"][round]
  sentinel.py   # Static: ARCHETYPE_PARAMS["sentinel"][round]
  firestorm.py  # Static: ARCHETYPE_PARAMS["firestorm"][round]
  wall.py       # Static: ARCHETYPE_PARAMS["wall"][round]
  phantom.py    # Static: ARCHETYPE_PARAMS["phantom"][round]
  predator.py   # Adaptive: reads self.posteriors, blends baseline →
                # PREDATOR_EXPLOIT[top_target] when max_prob > 0.60.
  mirror.py     # Adaptive: overrides _observe_opponent_action to
                # accumulate observed_vpip/br/cr per opponent, then at
                # get_params time copies the most-active opponent's
                # metrics into mirror_default.
  judge.py      # Adaptive: overrides observe_showdown to maintain a
                # grievance ledger. Triggered at 5 confirmed bluffs
                # against Judge from the same opponent. Switches to
                # judge_retaliatory params per-opponent permanently.
  dummy_agent.py # DummyAgent / FolderAgent / RaiserAgent: the
                 # scripted agents used in Stage 2 engine tests. Not
                 # BaseAgent subclasses; they don't have trust state.

trust/
  bayesian_model.py
                # Pure functions over numpy arrays. No state. The
                # posterior is a length-8 float64 array indexed by
                # TRUST_TYPE_LIST. Vectorized so the hot path runs in
                # ~10 microseconds per update. Precomputed likelihood
                # tables built once at module import.

data/
  visualizer_export.py  # hand_to_dict + run_and_export (JSON-style)
  sqlite_logger.py      # SQLiteLogger(start_run/log_hand/log_agent_stats)
  schema.sql            # 6-table persistent schema
  csv_exporter.py       # write_actions_csv / write_hands_csv /
                        # write_agent_stats_csv (stdlib csv only)

visualizer/
  poker_table.html      # 1927 lines, single file, vanilla JS, inline
                        # CSS. Three view modes: Trust Lens / Heatmap /
                        # Stats. Loads data.js via <script src>. The
                        # DesignCues file at the repo root is the
                        # authoritative style guide.

docs/
  schema.md             # SQLite schema reference + query cookbook
  stage5_identifiability.md  # why the Sentinel entropy test can't pass
  worked_examples.md    # hand walkthrough + Bayesian update example
  CHANGELOG.md          # stage milestones
  Claude_Code_Implementation_Prompt.md  # full build spec
  The_Eight_Archetypes_Specification.docx
  DesignCues            # dark-editorial design system

analysis/
  analyze_runs.py       # 9-section standard report
  deep_analysis.py      # 31-section deep analysis + scorecard

tests/
  test_trust_model.py   # Unit tests for trust primitives (run with
                        # python3 -m pytest tests/ OR just import it)
```

## Running tests

```bash
# Every registered stage (1, 2, 3, 4, 5, 6, 7, 10, 11)
python3 phase1/run_tests.py --stage all

# One specific stage
python3 phase1/run_tests.py --stage 6

# Trust model unit tests
python3 tests/test_trust_model.py
```

Expected output: every stage passes **except** the aspirational
**Stage 5.3** and **Stage 6.1** canonical-test failures (see "Known
limitations" #1 and #4). Any other failure is a regression and must
be investigated before committing.

## Running simulations

```bash
# 30-hand viewer demo (fast)
python3 phase1/run_demo.py --stage 6 --hands 30 --seed 42

# Full research dataset (hours)
python3 phase1/run_sim.py --seeds 42,137,256,512,1024 --hands 10000 \
                   --db runs.sqlite --stage 6

# Multi-seed CSV exports for Phase 2
python3 phase1/run_multiseed.py --seeds 42,137,256,512,1024 --hands 10000 \
                          --outdir research_runs

# Parameter sweeps
python3 phase1/run_sensitivity.py --param lambda \
                            --values 0.90,0.93,0.95,0.97,1.0 \
                            --hands 1000 --seeds 42,137,256

# Phase 2 ML simulation
python3 phase2/run_ml_sim.py --modeldir phase2/ml/models_tabular/ \
                              --hands 5000 --seeds 42 --db ml_test.sqlite
```

## Known limitations (intentional, documented)

### 1. Stage 5.3 canonical test is aspirational

`test_cases.test_stage_5` asserts that "average posterior entropy
about Sentinel after 500 hands &lt; 2.2 bits". This is **mathematically
unachievable** because `sentinel`, `mirror_default`, and
`judge_cooperative` have byte-identical average parameters in
`archetype_params.ARCHETYPE_AVERAGES`:

```
sentinel:           {br: 0.083, vbr: 0.900, cr: 0.325, mbr: 0.225}
mirror_default:     {br: 0.088, vbr: 0.850, cr: 0.320, mbr: 0.225}
judge_cooperative:  {br: 0.083, vbr: 0.900, cr: 0.325, mbr: 0.225}
```

The Bayesian posterior for a true Sentinel is bounded below by the
3-way ambiguity, so entropy converges to roughly `log2(3) ≈ 1.58`
bits in the best case and ~2.5 bits in practice (with leakage from
Phantom, which also has tight cr). Stage 5 tests that ARE achievable
(all stage5_extras, Firestorm and Wall identification at 100%, trust
bounds, reproducibility) all pass cleanly. See
`docs/stage5_identifiability.md` for the full derivation.

**Do not "fix" this by weakening the threshold.** Leave the aspirational
test in place as a reminder of the identifiability wall.

### 2. Spec VPIP/PFR ranges are calibration-off

`test_cases.py` asserts Oracle PFR ∈ [14%, 26%] among other ranges.
Under the spec-worked-example-consistent decision path
(see `worked_examples.md` Example 1), the Oracle's actual PFR with
the current `ARCHETYPE_PARAMS["oracle"]` table is ~5%. The spec
ranges assume a "weak hands raise at rate BR" interpretation that
makes `raise_p + call_p > 1` in several slots. `stage_extras.stage4_extras`
uses wider, empirically-derived bounds that match what the simulation
actually produces and asserts **relative** orderings (Firestorm VPIP &gt;
Sentinel VPIP, Wall PFR = min, etc.) which are the invariants that
actually matter for trust dynamics.

### 3. Monte Carlo hand strength is the runtime bottleneck

`get_hand_strength` runs 1000 MC samples per call and dominates
simulation runtime (~90% of CPU). `BaseAgent` caches the result per
(agent, betting_round) for the duration of a hand, so each agent only
pays the cost once per street. **Never call `get_hand_strength` from
the showdown refinement hot path** &mdash; use
`agents/base_agent.py::_fast_bucket` instead, which uses the
deterministic treys rank class (O(1)) for revealed hands.

### 4. Stage 6.1 Predator classification threshold is aspirational

`test_cases.test_stage_6` asserts that the Predator confidently
classifies at least 3 of 7 opponents (posterior > 0.60) after 1000
hands. In practice the Predator only classifies 2: Wall (1.00) and
Firestorm (~0.82). The same Sentinel/Mirror/Judge identifiability
cluster that blocks Stage 5.3 prevents the Predator from reaching
0.60 confidence on any cluster member. This is the same root cause
as limitation #1 above.

**Do not "fix" this by lowering the threshold.** The test documents
the intended classification capability; the identifiability ceiling
is the real constraint.

### 5. Stage 6.3b Judge probe test requires live hand context

`stage_extras.stage6_extras` test 6.3b constructs a synthetic
`GameState` with Firestorm in `active_opponent_seats` and expects
Judge to return retaliatory params. However, Judge's `get_params`
checks `self._bluff_candidates` (populated during live
`_observe_opponent_action` calls within a hand), not
`active_opponent_seats`. A synthetic probe between hands has an
empty `_bluff_candidates` dict, so the Judge always returns
cooperative params. The test seeds `_bluff_candidates` before the
probe to match the live-play contract. During actual simulation
play, retaliation fires correctly when triggered opponents aggress.

## The 4-track parallel development pattern

Stages 6 through 12 were built in four parallel Claude sub-sessions
that each worked on a dedicated sub-branch:

- Track A: `claude/stage6-adaptive` &mdash; Predator / Mirror / Judge
- Track B: `claude/stage7-logging` &mdash; SQLite + `run_sim.py`
- Track C: `claude/stage9-viewer` &mdash; Heatmap + Stats + Entropy bars
- Track D: `claude/stage10-research` &mdash; CSV exports + sensitivity

A supervisor session ran the audit playbook (scope check → compile
check → Stage-N tests → regression on stages 1-5 → smoke-test the new
CLIs → cross-track conflict scan) on each branch before merging
them back into `claude/poker-trust-simulation-6h3xR` in dependency
order B → C → D → A.

**The conflict pattern:** every track appended to `stage_extras.py`
and added dict entries to `run_tests.py`. Git flagged these as
conflicts at merge time (even though `merge-tree` often reports zero),
but the resolution is mechanical: take the union of both sides'
additions, concatenate the new stage functions at the end of
`stage_extras.py`, and interleave the new stage keys into
`STAGE_BUILDERS` / `STAGE_EXTRAS`. The integrated base always ends up
with `STAGE_BUILDERS.keys() = {1, 2, 3, 4, 5, 6, 7, 10, 11}` and
`STAGE_EXTRAS.keys() = {2, 3, 4, 5, 6, 7, 10, 11}`.

**Cross-track coordination gap (lesson learned):** Tracks B and D
were built in parallel with Track A and hardcoded Stage 5 rosters
into their runner CLIs, so running `run_sim.py --stage 6` after the
merge errored out with "No roster registered for stage 6". The fix
(commit `fedbd29`) added Stage 6 rosters to all three research
runners. Moral: when delegating parallel work, the supervisor must
smoke-test the runner CLIs at every stage, not just the unit tests.

## Adding a new stage

1. Write the feature on a new sub-branch.
2. Add a `_build_stage_N` function to `run_tests.py` and register it
   in `STAGE_BUILDERS`.
3. Add `stageN_extras(modules)` to the bottom of `stage_extras.py`.
   **Append only.** Never edit earlier stage functions.
4. Register `N: stage_extras.stageN_extras` in `STAGE_EXTRAS`.
5. Add a `_stageN_agents()` builder to `run_demo.py` + register in
   `STAGE_DEMOS`.
6. If the new stage needs a new CLI, mirror the pattern in
   `run_sim.py`'s `_STAGE_ROSTERS` registry.
7. Update `CHANGELOG.md` with the stage's deliverables.
8. Run `python3 run_tests.py --stage all` and verify every previously
   passing stage still passes.

## When merging parallel work

1. `git fetch origin`
2. `git worktree add /tmp/audit-X origin/claude/stage-X-branch`
3. In the worktree, run `python3 -c "import module1, module2, ..."` to
   catch import errors early.
4. Run `python3 run_tests.py --stage N` for the new stage.
5. Run `python3 run_tests.py --stage all` for a regression sanity check.
6. Smoke-test any new CLIs end-to-end with a small seed count.
7. Check `git diff --stat $(git merge-base base branch)..branch` to
   verify no files outside the authorized scope were touched.
8. Remove the worktree, then `git merge branch --no-ff -m "$(cat <<'EOF' ...)"`.
9. Resolve `stage_extras.py` / `run_tests.py` conflicts by
   concatenation (see "4-track parallel development pattern" above).
10. Run the full test suite one more time on the integrated tree.
11. `git push origin claude/poker-trust-simulation-6h3xR`.

## Known pitfalls

1. **Windows PowerShell + Tee-Object mangles the `\r` progress bar**
   in `run_sim.py`. Each progress tick becomes a new line in both the
   console and the log file. Cosmetic only &mdash; the sim runs fine.
   Use `chcp 65001` before the run to fix the Unicode rendering.

2. **The Windows console code page** (437 by default) can't render the
   progress-bar Unicode characters (`×`, `·`). You'll see `╫` and `╖`
   instead. Same fix: `chcp 65001`.

3. **`run_demo.py --stage 6 --hands 30`** is the smallest end-to-end
   smoke test that exercises the full 8-archetype table. It takes
   ~6 seconds and regenerates `visualizer/data.js` with all three
   Stage 5 snapshot types populated.

4. **The visualizer loads `data.js` via `<script src="data.js">`, not
   via `fetch`**, so it works over `file://` in every browser without
   CORS issues. Do not change this to `fetch`.

5. **`test_stage_3_4` not `test_stage_3` + `test_stage_4`.** The
   canonical `test_cases.py` has a combined function for stages 3 and
   4; `run_tests.py` uses `getattr(test_cases, f"test_stage_{stage}")`
   which returns `None` for both 3 and 4, so the runner skips the
   canonical portion for those stages and only runs the extras.
   This is intentional &mdash; don't "fix" it by splitting the
   canonical function.

6. **`config.TRUST` is cached on import in `trust.bayesian_model`** as
   module-level constants `_LAMBDA`, `_EPS`, `_TPW`. If you override
   `config.TRUST` at runtime (e.g. from `run_sensitivity.py`), you
   must also patch the cached constants in `trust.bayesian_model`.
   `run_sensitivity._apply_override` does this correctly via
   `_PARAM_MAP`; if you write new sweep tooling, follow the same pattern.

## Emergency checklist

- Tests fail: run `python3 phase1/run_tests.py --stage N` for the failing
  stage in isolation. Every stage test is self-contained.
- Simulation hangs: check `ps aux | grep python` — if a runner is
  stuck in `get_hand_strength`, it's probably a rare infinite-loop in
  `treys.Evaluator`. Nothing to do but restart; the bug is upstream.
- SQLite database is corrupted: `sqlite3 runs.sqlite "PRAGMA integrity_check;"`.
  If corruption is confirmed, delete and rerun. SQLite writes are
  atomic at the hand level, so you can safely recover a partial run
  up to the last completed hand.
- Viewer is blank: the fallback message ("Run `python3 run_demo.py`")
  should display when `data.js` is missing. If the page is truly blank
  with no fallback, there's a JavaScript error — check the browser
  console.
- Chip conservation failure in `run_sim.py`: the run is contaminated.
  Investigate before using any downstream data. The most likely
  causes are (a) side-pot logic regression in `engine/game.py` or
  (b) rebuy accounting bug in `engine/table.py`.

## Where to find things

- The full build spec: `Claude_Code_Implementation_Prompt.md`
- Archetype definitions: `The_Eight_Archetypes_Specification.docx`
- Worked hand + Bayesian update example: `docs/worked_examples.md`
- Design system for the viewer: `DesignCues` (at the repo root)
- Stage milestones: `docs/CHANGELOG.md`
- Research dataset schema: `docs/schema.md`
- Stage 5.3 math: `docs/stage5_identifiability.md`
