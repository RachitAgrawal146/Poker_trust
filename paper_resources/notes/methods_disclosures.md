# Methods Disclosures — checklist for the paper

A short list of methodological points that need to appear in the
paper's Methods section so a careful reviewer can reproduce the
work. Each item is a one-line claim the paper needs to state plus the
file/commit you can cite.

## 1. LLM sampling temperature

**Disclose:** Phase 3 and Phase 3.1 LLM calls were issued with the
Anthropic SDK's default sampling temperature (1.0). The repo now pins
`temperature=0.0` at `phase3/llm_chat_agent.py:349` (commit
`57cca9a1`, 2026-05-22) so subsequent runs are deterministic, but the
canonical 43 943-call Phase 3 dataset (`runs_phase3_long.sqlite`,
$33.10) and the 11 953-call Phase 3.1 dataset
(`runs_phase31_long.sqlite`, ~$17) were produced before the pin.

**Why this matters:** without the disclosure a reviewer who pulls the
repo and re-runs Phase 3.1 will get systematically lower seed-to-seed
variance (σ on r drops) and the headline mean shifts by a few
percentage points either way.

**Optional re-run cost:** 6.9 h wall + ~$17 to regenerate the Phase
3.1 dataset under the pin. The headline mean r = −0.094 ±0.30 is the
right shape under either temperature — the trap-breaking finding is
robust — but a deterministic rerun produces narrower variance and a
cleaner CI.

## 2. n=5 sample size and CI derivation

**Disclose:** all per-phase means are computed across the canonical
five seeds (42, 137, 256, 512, 1024). 95% CIs come from two sources:

- Student t-interval with `df = n − 1 = 4`, critical value 2.776
- 10 000-resample non-parametric percentile bootstrap

**Cite:** `analysis/bootstrap_ci.py` (commit `57cca9a1`). Output CSV
at `paper_resources/data/r_bootstrap_ci.csv`.

The headline Phase 3.1 r = −0.094 has t-interval [−0.51, +0.32] and
bootstrap [−0.32, +0.20]. Both contain zero, supporting the
"statistically indistinguishable from zero" framing already in the
scorecard. Per-seed Fisher-z CIs (n = 8 archetype pairs) are also
emitted by the same script.

## 3. Engine side-pot accounting

**Disclose:** the engine awards pots via per-contribution-level side
pots (`engine/game.py::_showdown`, commit `57cca9a1`). Previously
(through commit `7ab1996`) a short-stacked player who could only call
part of a required bet still collected the full pot at showdown.
Phase 1 and Phase 2 SQLite scorecards produced before `57cca9a1`
reflect the old behavior; the side-pot fix shifts per-archetype EV
slightly near stack exhaustion. Phase 3 and Phase 3.1 LLM datasets
are unaffected (LLM runs are not reproducible anyway).

## 4. Per-seed r values — provenance

**Disclose:** the `R_BY_PHASE` table in
`analysis/make_paper_figures.py` (and the matching values in
`analysis/bootstrap_ci.py`) is the literal copy of the per-seed
Pearson r column from `reports/phase31_long_scorecard.txt` and
`reports/phase2_unbounded_scorecard_aggressive.txt`. Both modules
carry an explicit provenance comment naming the source scorecards and
the reconciliation date/commit.

## 5. Trust posterior is stationary across all numerical phases

**Disclose:** Phases 1, 2 (bounded), and 2\* (unbounded) all use the
Phase 1 likelihood tables in the trust model. Adapting agents in
Phase 2 / Phase 2\* are intentionally exploiting a stale reputation
system; this is the experimental control. The decay parameter is
`λ = 0.95`, the noise floor `ε = 0.05`, and the third-party-weight
`tpw = 0.8` (evidence observed after the observer folded enters the
update with its likelihood raised to the 0.8 power, i.e. slightly
discounted relative to directly contested evidence); all are exposed
in `config.TRUST`. Sensitivity sweeps
over these constants live in `phase1/run_sensitivity.py`.

## 6. Reproducibility caveats already in CLAUDE.md

- Stage 5.3 entropy test fails by design — Sentinel / Mirror-default
  / Judge-cooperative have byte-identical mean parameters, so the
  Bayesian posterior cannot resolve them below `log2(3) ≈ 1.58` bits.
  See `docs/stage5_identifiability.md`.
- Stage 6.1 Predator classification threshold fails for the same
  identifiability cluster reason. The two non-cluster archetypes
  (Wall, Firestorm) are classified at 1.00 and ~0.82 respectively.
- These are aspirational tests left in place to mark the
  identifiability ceiling, not regressions.
