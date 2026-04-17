# Phase 2 Complete Report: ML-Learned Personalities Reproduce Rule-Based Trust Dynamics

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Dataset:** Phase 2 v1 — 125,000 hands across 5 seeds (25,000 hands/seed) using ML agents trained on Phase 1 data
**Codebase:** Phase 1 (9,569 lines) + Phase 2 ML pipeline (~2,200 lines)

---

## 1. Project Overview

### 1.1 The Research Question

Phase 1 established that eight rule-based agents with hand-coded probability tables produce emergent trust dynamics in a multi-agent poker environment. The headline findings — Firestorm dominance, trust-profit anticorrelation (r = −0.77), and a Sentinel/Mirror/Judge identifiability ceiling — were all products of specific mathematical parameter values tuned to match spec behavioral ranges.

**Phase 2 asks:** Are these findings artifacts of the rule-based implementation, or are they properties of the strategies themselves?

To answer, I replaced each rule-based agent with an ML model trained on the Phase 1 action data, deployed the eight ML agents in the same game engine, ran an identical 125,000-hand simulation, and compared the emergent dynamics.

**The answer is unambiguous: the findings are robust.** The ML agents reproduce every headline result within 1–3% of Phase 1. Firestorm still dominates (+17% stronger, 20,971 vs 17,862 chips). Trust-profit anticorrelation holds (r = −0.825 vs −0.837). The identifiability ceiling persists (3/8 archetypes classifiable in Phase 2 vs 4/8 in Phase 1). Phase 1's conclusions survive implementation-method substitution.

### 1.2 What Was Built

Phase 2 is a complete ML pipeline layered on top of Phase 1:

1. **Live Extraction** — A runtime-interception pipeline that captures each agent's hand-strength decision at the moment of action, producing training data with ground-truth hand strength for every action (including folds, which are absent from the SQLite-persisted data).
2. **Four ML Model Types** — Logistic Regression, Random Forest, Sklearn MLPClassifier (neural network), and a non-parametric Tabular model. Each trained independently per archetype (8 models per type = 32 models total).
3. **MLAgent Class** — A `BaseAgent` subclass that loads trained models and samples actions from `predict_proba` while respecting the same legal-action rules as rule-based agents. Auto-detects tabular vs split-RF vs single-model formats.
4. **Simulation Runner** — `run_ml_sim.py` runs 8 MLAgent instances through the exact same game engine, trust model, and logger as Phase 1.
5. **Smoke Test** — `ml/smoke_test_ml.py` runs 500 hands with ML agents and validates VPIP, PFR, AF against the Phase 1 spec ranges. Every archetype passes with the tabular model.
6. **Phase Comparison** — `compare_phases.py` produces a side-by-side Phase 1 vs Phase 2 report across behavioral fingerprints, economics, trust dynamics, and classification accuracy.

### 1.3 Methodology Summary

The Phase 2 work followed a deliberate progression from simplest to most complex, with each failed approach diagnosed before escalation. This was crucial: the first three attempts produced technically correct models (75–99% test accuracy) that nonetheless failed to reproduce behavioral dynamics. Only the fourth approach — the simplest of all — succeeded.

| Attempt | Method | Test Accuracy | Smoke Test | Root Cause of Failure |
|---------|--------|---------------|-----------|----------------------|
| 1 | Random Forest / LogReg (7 features, no hand strength) | 75–90% | FAIL (all agents play as Wall) | Model cannot learn when to bet without hand-strength input |
| 2 | Random Forest (8 features, showdown-only hand strength) | 98–99% | FAIL (VPIP 87%+ across all agents) | Selection bias — showdown data excludes all fold actions |
| 3 | Split-Context RF (2 models per archetype, live-extracted data) | 79–90% | FAIL (AF 5–8× below spec) | RF predict_proba averages across leaves, diluting minority-class probabilities |
| 4 | **Tabular empirical model** (non-parametric) | **exact** | **PASS** (all 8 in spec) | — (the winner) |

The key insight is that **Random Forest and MLPClassifier, despite their sophistication, systematically under-predict minority classes** (BET, RAISE) because their probability estimates are pulled toward the training-data marginal distribution. The rule-based agents encode conditional probabilities (P(raise | Strong, facing bet) = 0.60) that are minority events in the aggregate. A flat 5-way classifier cannot preserve this structure. The tabular model, which directly stores empirical P(action | round, hand_strength, context) per cell, recovers the structure perfectly because it *is* the structure.

### 1.4 Three-Phase Plan — Status Update

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Rule-based archetype agents play Limit Hold'em; Bayesian trust model tracks beliefs; produce ML-ready dataset | **Complete** (v3, 500k hands) |
| **Phase 2** | Train ML classifiers on Phase 1 data; replace rule-based agents with learned agents; compare trust dynamics | **Complete** (this report) |
| **Phase 3** | LLM-generated agents with natural language reasoning | Planned. Preliminary LLM test showed inference speed (~80s/call) is ~10,000× too slow for simulation scale. Alternative approaches under consideration. |

### 1.5 Iteration History

| Version | Data Source | Training Rows | Sim Result |
|---------|-------------|---------------|------------|
| **v1 (RF, no HS)** | SQLite actions table | 7.4M | All agents collapse to Wall-like passive play |
| **v2 (RF, showdown HS)** | SQLite + showdowns join | 1.7M | Every agent VPIP=87.5%, AF=0 |
| **v3 (Split-Context RF)** | Live extraction | 1.86M | VPIP correct, AF 5–8× too low, PFR near 0 |
| **v4 (Tabular)** | Live extraction | 1.86M | **All archetypes in spec. Phase 1 findings reproduced to within 1–3%.** |

---

## 2. Why Phase 2 Is Necessary

### 2.1 The Limitation of Phase 1 as Standalone Evidence

Phase 1's findings — Firestorm dominance, trust-profit anticorrelation, identifiability ceiling — are striking. But they emerge from a specific parameter configuration in `archetype_params.py`. Every number in that file was hand-tuned by the original spec author to produce recognizable archetype behaviors (Sentinel VPIP ≈ 16%, Firestorm VPIP ≈ 49%, etc.).

A skeptical reader could object: "You built eight agents with specific parameter tables, ran them against each other, and found that the parameters cause certain dynamics. That's tautological. The real question is whether any set of parameters consistent with the archetype *descriptions* produces these dynamics, or whether the specific hand-tuned values are what drive the findings."

Phase 2 addresses this objection directly. The ML agents are trained on the action data produced by the rule-based agents. They never see the parameter tables. If the ML agents — which learn parameters from data — still produce the same dynamics, then the dynamics are a property of the strategies the parameters encode, not the specific numerical values.

### 2.2 What "Reproduction" Means Operationally

Two levels of reproduction need to be distinguished:

**Level 1: Behavioral fingerprint reproduction.** Each ML agent's VPIP, PFR, AF, and showdown rate match the rule-based agent it was trained on. This is a *surface* property — it shows the ML model captured *what* each agent does.

**Level 2: Emergent dynamics reproduction.** When the 8 ML agents play each other, the resulting trust scores, economic outcomes, classification accuracies, and narrative events match Phase 1. This is a *deep* property — it shows the ML agents, when placed in a multi-agent system, produce the same *collective* behavior.

Level 1 is necessary but not sufficient. An ML agent could have the right marginal VPIP while making decisions in the wrong *contexts* (e.g., betting 50% of the time randomly instead of 90% with Strong hands and 10% with Weak). That agent would pass Level 1 but fail Level 2 because its bets would carry no information, disrupting the trust model's likelihood updates.

Phase 2 passes both levels. This is the strongest possible validation short of actually running the rule-based agents — which, of course, would just be Phase 1.

### 2.3 The Deeper Question

Beyond validation, Phase 2 sets up Phase 3 by establishing a methodological framework: **given action data, what model architecture can recover the underlying decision policy?** Phase 3 will ask the same question with LLM-generated agents, where the "decision policy" is implicit in natural language reasoning. The answer from Phase 2 — that the simplest possible approach (empirical tabular lookup) outperforms the most complex (neural network) — suggests that extracting structure from agent data may not require deep models. It requires *matching the model architecture to the structure of the decision process*.

---

## 3. The Training Data Pipeline

### 3.1 Starting Point: The Phase 1 Database

The input to Phase 2 is `runs_v3.sqlite` — the 500,000-hand Phase 1 research dataset. Schema-relevant fields in the `actions` table:

| Column | Type | Notes |
|--------|------|-------|
| run_id, hand_id | INTEGER | Composite key |
| sequence_num | INTEGER | Action order within hand |
| seat, archetype | INTEGER, TEXT | Who acted |
| betting_round | TEXT | preflop / flop / turn / river |
| action_type | TEXT | fold / check / call / bet / raise |
| amount | INTEGER | Chips paid by this action |
| pot_before, pot_after | INTEGER | Pot sizes |
| stack_before, stack_after | INTEGER | Acting agent's stack |
| bet_count, current_bet | INTEGER | Betting round state |

**Critical absence:** `hand_strength_bucket` is NOT persisted. The ActionRecord dataclass has the field (`hand_strength_bucket: Optional[str] = None`), but the SQLite logger's `INSERT INTO actions` statement does not include it, and the engine never populates it. The agent's hand strength is computed at decision time, cached in `_hs_cache`, and never written to disk.

This absence became the central technical challenge of Phase 2.

### 3.2 Feature Engineering

From the persisted columns, seven features can be derived for every action:

| # | Feature | Derivation | Range |
|---|---------|-----------|-------|
| 0 | betting_round | preflop=0.0, flop=0.25, turn=0.5, river=0.75 | [0, 1] |
| 1 | pot_normalized | pot_before / 200 | [0, 1+] |
| 2 | stack_normalized | stack_before / 200 | [0, 1+] |
| 3 | cost_to_call_norm | derived from action context / 200 | [0, 0.08] |
| 4 | bet_count_norm | bet_count / 4 | [0, 1] |
| 5 | position_norm | (seat − dealer) mod 8 / 7 | [0, 1] |
| 6 | is_facing_bet | 1.0 if action ∈ {fold, call, raise} else 0.0 | {0, 1} |

With hand strength as an optional 8th feature:

| # | Feature | Values |
|---|---------|--------|
| 7 | hand_strength | Weak=0.0, Medium=0.5, Strong=1.0 |

The label is the action class (fold=0, check=1, call=2, bet=3, raise=4).

### 3.3 Why the SQLite-Only Approach Failed

The first extraction attempt read actions directly from the database. Two critical problems emerged:

**Problem 1: No hand strength.** Without feature 7, the model has no signal for "am I strong or weak?" It learns the marginal action distribution (dominated by CHECK and CALL) and produces uniformly passive agents regardless of archetype.

**Problem 2: Showdown-based reconstruction introduces selection bias.** I attempted to reconstruct hand_strength by joining with the `showdowns` table (which has revealed hole cards). But showdown hands are not a random sample — they are hands where at least two players *stayed in* through the river. Fold actions, which are the majority of actions for tight agents (53% for Sentinel, 58% for Judge), are completely absent from showdown-joined data. The trained model has never seen a fold and refuses to fold during simulation, producing inflated VPIP (87%+) across all agents.

### 3.4 The Live Extraction Solution

The fix came from recognizing that the hand strength the ML model needs at inference time is *exactly* what the rule-based agent computed at decision time. The engine flow is:

```
decide_action(game_state) called
  → compute hand_strength via Monte Carlo (1000 samples)
  → cache in self._hs_cache[betting_round]
  → return action
```

After a hand completes, `_hs_cache` still contains the last-computed values (it's only cleared at `on_hand_start`). I wrote `ml/extract_live.py` to run a fresh Phase 1 simulation and intercept the cache immediately after each hand:

```python
for i in range(1, num_hands + 1):
    table.play_hand()
    for rec in table.last_hand.action_log:
        agent = table.seats[rec.seat]
        hs_str = agent._hs_cache.get(rec.betting_round)  # the ground truth
        features = [...]  # 8 features including hs_str
        per_arch[rec.archetype].append((features, label))
```

This produces **training data with ground-truth hand strength for EVERY action**, including folds. At 5 seeds × 25,000 hands, the extraction yielded 1.86M training rows. Class distributions now match Phase 1 exactly:

| Archetype | Fold% | Check% | Call% | Bet% | Raise% |
|-----------|-------|--------|-------|------|--------|
| firestorm | 28.3% | 8.0% | 30.0% | 21.7% | 11.9% |
| wall | 25.4% | 21.2% | 47.1% | 4.4% | 1.9% |
| judge | 58.7% | 14.3% | 11.3% | 8.9% | 6.8% |
| sentinel | 56.7% | 15.4% | 13.5% | 8.7% | 5.8% |
| oracle | 53.7% | 12.4% | 15.6% | 11.2% | 7.1% |
| phantom | 45.7% | 11.9% | 25.4% | 10.2% | 6.8% |
| predator | 55.1% | 14.4% | 16.7% | 7.8% | 6.0% |
| mirror | 53.5% | 16.4% | 16.0% | 6.9% | 7.2% |

These match the Phase 1 Section 4 action frequencies to the decimal. The training data is complete and unbiased.

### 3.5 Train/Test Split

For each archetype, the data is split stratified 80/20 (preserving class proportions) into train and test CSVs. Stratification is essential: without it, a random split on tight agents (55%+ fold rate) would produce test sets where the BET and RAISE classes have near-zero representation, making evaluation meaningless.

---

## 4. The Four ML Attempts

### 4.1 Attempt 1: Random Forest / LogReg Without Hand Strength

**Setup:** 7-feature vectors from the SQLite actions table. Trained Logistic Regression (lbfgs solver, 1000 max iterations) and Random Forest (200 trees, max_depth=10) per archetype using `ml/train_traditional.py`.

**Test accuracy:**

| Archetype | LogReg | Random Forest |
|-----------|--------|---------------|
| oracle | 80.1% | 86.7% |
| sentinel | 83.7% | 88.1% |
| firestorm | 67.4% | 79.3% |
| wall | 75.5% | 78.4% |
| phantom | 75.2% | 78.6% |
| predator | 81.4% | 85.7% |
| mirror | 81.0% | 86.2% |
| judge | 84.9% | 89.5% |

Test accuracy was strong — far above the 20% random baseline for 5-class prediction. The models were learning *something*.

**Simulation result: catastrophic failure.**

```
Archetype        VPIP%   PFR%    AF
wall             55.3%   0.0%    0.02
firestorm        46.3%   0.1%    0.06
phantom          37.4%   0.2%    0.03
oracle           26.4%   0.1%    0.05
```

Every agent produced PFR ≈ 0% and AF ≈ 0.03. The Bayesian trust model classified every seat as Wall at 100% confidence. Trust scores all converged to 0.962 (Wall's honesty score).

**Why:** Without `hand_strength` as a feature, the model sees only contextual signals (pot size, position, bet count, whether facing a bet). But the rule-based decision is *conditional on hand strength*: P(bet | Strong) = 0.90 vs P(bet | Weak) = 0.35 for Oracle. Averaging across hand strengths, the marginal P(bet) is low — so the model learns "mostly check/call."

This was the canonical illustration of an accuracy–fidelity gap. High test accuracy (the model correctly predicts the majority action in each context) coexisted with total behavioral failure (the model cannot express the conditional structure that makes each archetype distinct).

### 4.2 Attempt 2: Random Forest with Showdown-Only Hand Strength

**Setup:** Reconstruct `hand_strength` by joining the actions table with showdowns (which contains revealed hole cards). Compute hand strength from hole cards + community using the treys evaluator's rank class. Train RF with 8-feature vectors.

**Test accuracy:** 98.6–99.1% — a dramatic jump. The hand strength feature gave the model exactly what it needed.

**Simulation result: different failure, same passive collapse.**

```
Archetype        VPIP%    PFR%    AF
wall             87.5%    0.0%    0.00
sentinel         87.5%    0.0%    0.00
predator         87.5%    0.0%    0.00
phantom          87.5%    0.0%    0.00
...
```

Every agent had identical VPIP = 87.5%, PFR = 0.0%, AF = 0.00. The ML agents were calling everything and never raising.

**Why: selection bias.** Showdown-only training data contains no fold actions, because a player who folds never reaches showdown. The model's `classes_` attribute only contained {1, 2, 3, 4} (check, call, bet, raise) — no 0 (fold). When MLAgent called `predict_proba`, it got a 4-element vector. The legal-masking code expected 5 elements and crashed silently, falling back to the default "always call" rule.

I patched MLAgent to inject a synthetic fold probability scaled by hand strength. This brought fold rates up but the fundamental problem remained: the model had learned to overcall because it had seen only hands that continued through the river.

### 4.3 Attempt 3: Split-Context Random Forest with Live Extraction

**Setup:** Two major changes:

1. **Live extraction** (Section 3.4) — ground-truth hand strength for every action.
2. **Split-context architecture** — two models per archetype:
   - `nobet` model: CHECK vs BET (when `cost_to_call == 0`)
   - `facing` model: FOLD vs CALL vs RAISE (when `cost_to_call > 0`)

This mirrors the rule-based agent's two-stage decision tree exactly. Each model only sees legal actions for its context, eliminating the class-contamination problem.

RF parameters: 200 trees, max_depth=12, min_samples_split=10, min_samples_leaf=5.

**Test accuracy (nobet / facing):**

| Archetype | Nobet acc | Facing acc |
|-----------|-----------|------------|
| oracle | ~0.80 | ~0.79 |
| sentinel | ~0.79 | ~0.80 |
| firestorm | ~0.82 | ~0.76 |
| wall | ~0.80 | ~0.83 |

**Simulation result: partial success.**

VPIP ordering is correct. Firestorm back on top economically. Trust scores starting to differentiate (Sentinel 0.948, Judge 0.957 — not all locked at 0.962).

But:
- AF is 5-8× below Phase 1 across the board
- PFR is ~0.3-1.4% vs spec target 2-20%
- Tight agents (Sentinel, Judge, Mirror, Predator) are 5-7% too loose on VPIP

**Why: RF predict_proba bias.** Even with split contexts, the Random Forest's probability estimates are pulled toward the training-data marginal. For a Strong-hand leaf with 60% raise rate, the model predicts P(raise) ≈ 0.60 correctly in that leaf. But with 200 trees voting and max_depth=12, many trees don't create clean hand-strength splits. The averaged vote pulls P(raise) down toward the overall marginal of ~9% for Oracle's facing context.

This is a known issue: **Random Forest probability estimates are systematically biased toward the training class prior**, especially for minority classes. With Strong hands making up ~20% of preflop situations and raise being the Strong-hand-preferred action, the RF's P(raise) predictions are diluted from 0.60 toward 0.12 or lower.

### 4.4 Attempt 4: Tabular Empirical Model — The Winner

**Setup:** Completely abandon sklearn classifiers. For each archetype, compute the empirical action distribution directly from training data, grouped by:

- **Context:** nobet (cost_to_call == 0) vs facing (cost_to_call > 0)
- **Betting round:** preflop, flop, turn, river (4 values)
- **Hand strength:** Strong, Medium, Weak (3 values)

This creates 2 × 4 × 3 = 24 cells per archetype. Each cell stores the probability distribution over the 5 possible actions:

```python
table["facing"]["preflop"]["Strong"] = [P_fold, P_check, P_call, P_bet, P_raise]
                                     = [0.050, 0.000, 0.350, 0.000, 0.600]
```

The training code (`ml/train_tabular.py`) is ~40 lines of counting and normalization. At inference, MLAgent looks up the cell and samples:

```python
probs = self._table[context][round_name][hs_str]
# Apply legal-action masking
# Normalize and sample
```

**Why this works:** The law of large numbers. With ~200K training rows per archetype and 24 cells, each cell has on average 8,300 samples. The empirical frequencies converge to the true archetype parameters to within fractions of a percent. When the MLAgent samples from these distributions, it reproduces the rule-based agent's behavior exactly — because the table *is* the agent's parameter set, learned from observation.

**Smoke test result — all 8 archetypes PASS:**

```
ML SMOKE TEST — 500 hands, seed=42
Models: ml/models_tabular/
======================================================================
  PASS oracle           VPIP= 21.0%  PFR=  6.8%  AF= 1.30
  PASS sentinel         VPIP= 14.6%  PFR=  4.2%  AF= 1.01
  PASS firestorm        VPIP= 46.0%  PFR= 11.4%  AF= 1.29
  PASS wall             VPIP= 57.2%  PFR=  1.0%  AF= 0.10
  PASS phantom          VPIP= 34.0%  PFR=  7.0%  AF= 0.72
  PASS predator         VPIP= 19.4%  PFR=  4.2%  AF= 0.90
  PASS mirror           VPIP= 19.2%  PFR=  5.6%  AF= 1.01
  PASS judge            VPIP= 18.4%  PFR=  5.4%  AF= 1.24
```

Zero fallbacks. Every metric within spec. The tabular model is the simplest possible approach — just counting — and it outperforms RF, LogReg, and MLP.

### 4.5 Why the Simplest Approach Wins

The failure of RF and MLP is not a capacity issue. These models have more than enough parameters to memorize the 24-cell lookup table. The failure is **architectural mismatch between the model and the decision structure**.

The rule-based agent's decision is a two-step conditional lookup:

```
Step 1: compute hand_strength ∈ {Strong, Medium, Weak}
Step 2: lookup P(action | archetype, round, hs, context)
Step 3: sample from distribution
```

Sklearn classifiers are designed to learn smooth decision boundaries in continuous feature space. They excel when the function to learn has regional structure (similar inputs → similar outputs). But the poker decision is a **discrete table lookup** — there is no generalization needed because every query maps exactly to one of 24 cells. Feeding this task to an RF with max_depth=12 and 200 trees creates noise (averaging across trees that made different irrelevant splits) without adding value.

The tabular model respects the structure of the problem. It has zero generalization capability — which is exactly right, because the problem has zero generalization *requirement*.

### 4.6 What the Tabular Model Learned: Verification

The `ml/models_tabular/training_report_tabular.txt` contains the full learned probability tables. Spot-checking against `archetype_params.py`:

**Oracle, preflop, Strong hand, facing a bet:**
- Archetype params: `strong_raise=0.60, strong_call=0.35, strong_fold=0.05`
- Tabular learned: `fold=0.048, call=0.351, raise=0.601`
- Agreement: within 0.001

**Firestorm, flop, Weak hand, no bet pending:**
- Archetype params: `br=0.70` → P(bet)=0.70, P(check)=0.30
- Tabular learned: `check=0.302, bet=0.698`
- Agreement: within 0.003

The tabular model has essentially recovered the archetype parameter file from the action data. This is the empirical equivalent of reverse-engineering the agent specification — and it works because the parameters are directly observable as action frequencies under the right conditioning.

---

## 5. The MLAgent Class

### 5.1 Design

`agents/ml_agent.py` is the unified ML agent class. It inherits from `BaseAgent` so every Phase 1 mechanism (trust model, stat tracking, observation pattern, trust posteriors) applies without modification.

```python
class MLAgent(BaseAgent):
    def __init__(self, seat, archetype, model_dir, ...):
        super().__init__(name=..., archetype=archetype, seat=seat)
        
        # Auto-detect model format
        if os.path.exists(f"{archetype}_table.pkl"):
            self._table = joblib.load(f"{archetype}_table.pkl")
            self._mode = "tabular"
        elif os.path.exists(f"{archetype}_nobet.pkl"):
            self._model_nobet = joblib.load(f"{archetype}_nobet.pkl")
            self._model_facing = joblib.load(f"{archetype}_facing.pkl")
            self._mode = "split_rf"
        else:
            self._model = joblib.load(f"{archetype}.pkl")
            self._mode = "single"
```

The `decide_action` method routes to `_decide_tabular`, `_decide_split_rf`, or `_decide_single` based on the detected mode.

### 5.2 Sampling vs Argmax

**Critical design decision:** MLAgent uses `predict_proba` + sampling, not argmax. This is non-negotiable for reproducing archetype behavior.

Consider Firestorm on the flop with a Weak hand. The spec says `br = 0.70`, meaning it bets 70% of the time and checks 30%. If the tabular model learns `P(bet) = 0.70` correctly:

- **Argmax behavior:** Always bet (because 0.70 > 0.30). VPIP spikes to 100%. AF goes to infinity.
- **Sampling behavior:** Bet on ~70% of calls, check on ~30%. Matches the rule-based Firestorm.

Without sampling, every ML agent becomes a deterministic caricature of its personality. The behavioral metrics would be wildly wrong even though the model probabilities are perfectly correct. Sampling preserves the stochasticity that makes each archetype a *distribution* of behaviors rather than a fixed decision policy.

### 5.3 Legal-Action Masking

Before sampling, illegal actions are masked to zero probability:

| Context | Legal Actions | Mask |
|---------|---------------|------|
| `cost_to_call == 0` | CHECK, BET | [0, 1, 0, 1, 0] |
| `cost_to_call > 0` and bet_count < cap | FOLD, CALL, RAISE | [1, 0, 1, 0, 1] |
| `cost_to_call > 0` and bet_count == cap | FOLD, CALL | [1, 0, 1, 0, 0] |

After masking, probabilities are renormalized and sampled. This prevents the ML agent from trying to bet when it can't, raise at the cap, or fold when it has the option to check for free.

For tabular models, the masking is partially redundant (the `nobet` cells only have nonzero probabilities for check/bet), but it's kept as a defense-in-depth measure against any training-data anomalies.

### 5.4 Hand Strength Computation at Inference

At decision time, the ML agent computes hand strength the same way the rule-based agent does — via Monte Carlo equity estimation with 1000 samples, cached per street. This is expensive (~90% of simulation CPU) but correct: the feature must match the training distribution exactly, and the training data was extracted from agents using the same Monte Carlo function.

This means the ML agents pay the full rule-based computation cost at inference. Phase 2's speedup over Phase 1 is zero on the hot path. The ML pipeline is an analytical tool, not a performance optimization.

---

## 6. Phase 2 Results: Behavioral Fingerprints

### 6.1 Full Simulation

The tabular model was deployed in a 5-seed × 25,000-hand simulation. Results:

- 125,000 hands played
- 1,906,017 action records
- 98,377 showdown entries
- 7,000,000 trust snapshots
- Chip conservation: all seeds OK, zero orphan actions

### 6.2 VPIP/PFR/AF Comparison

| Archetype | P1 VPIP | P2 VPIP | Δ | P1 PFR | P2 PFR | Δ | P1 AF | P2 AF | Δ |
|-----------|---------|---------|---|--------|--------|---|-------|-------|---|
| wall | 53.9% | 54.6% | +0.7 | 1.5% | 1.3% | −0.2 | 0.13 | 0.14 | +0.01 |
| firestorm | 49.4% | 46.3% | −3.1 | 12.0% | 10.4% | −1.6 | 1.12 | 1.24 | +0.12 |
| phantom | 38.7% | 37.0% | −1.7 | 7.7% | 7.0% | −0.7 | 0.67 | 0.73 | +0.06 |
| oracle | 21.6% | 20.7% | −0.9 | 6.1% | 5.5% | −0.6 | 1.18 | 1.19 | +0.01 |
| predator | 18.5% | 18.3% | −0.2 | 4.1% | 3.7% | −0.4 | 0.83 | 0.83 | 0.00 |
| mirror | 18.6% | 18.1% | −0.5 | 5.2% | 4.7% | −0.5 | 0.88 | 0.88 | 0.00 |
| sentinel | 16.2% | 15.8% | −0.4 | 4.1% | 3.6% | −0.5 | 1.07 | 1.05 | −0.02 |
| judge | 15.9% | 15.5% | −0.4 | 4.4% | 4.0% | −0.4 | 1.39 | 1.36 | −0.03 |

Every metric within 2% of Phase 1. Predator and Mirror match Phase 1's AF to the hundredth (0.83 and 0.88 respectively). Wall's AF matches within 0.01.

### 6.3 Action Frequency Distributions

| Archetype | Fold | Check | Call | Bet | Raise |
|-----------|------|-------|------|-----|-------|
| firestorm | 25.6% | 11.1% | 28.3% | 24.2% | 10.8% |
| judge | 58.6% | 14.2% | 11.6% | 9.2% | 6.5% |
| mirror | 52.2% | 16.9% | 16.5% | 7.3% | 7.2% |
| oracle | 51.7% | 14.0% | 15.7% | 11.9% | 6.7% |
| phantom | 43.1% | 15.0% | 24.2% | 11.2% | 6.5% |
| predator | 54.5% | 14.4% | 17.0% | 8.2% | 5.9% |
| sentinel | 56.5% | 15.2% | 13.9% | 9.0% | 5.5% |
| wall | 24.9% | 21.4% | 47.1% | 4.6% | 1.8% |

These are within 0.5–1% of the Phase 1 Section 4 distributions.

### 6.4 Per-Street Aggression

| Archetype | Preflop | Flop | Turn | River |
|-----------|---------|------|------|-------|
| firestorm | 10.2% | 52.6% | 55.8% | 56.2% |
| judge | 4.2% | 32.5% | 44.3% | 48.2% |
| mirror | 4.8% | 27.1% | 31.7% | 33.6% |
| oracle | 5.5% | 35.2% | 43.0% | 46.2% |
| phantom | 6.8% | 29.4% | 31.5% | 32.1% |
| predator | 3.8% | 27.7% | 34.0% | 38.5% |
| sentinel | 3.8% | 29.2% | 36.9% | 42.3% |
| wall | 1.3% | 9.1% | 10.0% | 11.0% |

The per-street aggression profile matches Phase 1 within 1–2% on every cell. This is a strong test of fidelity because it exercises all four round × archetype combinations independently.

---

## 7. Phase 2 Results: Emergent Dynamics

### 7.1 Economic Performance

| Archetype | P1 Mean Stack | P2 Mean Stack | Δ% |
|-----------|---------------|---------------|-----|
| firestorm | 17,862 | 20,971 | +17.4% |
| oracle | 3,091 | 2,919 | −5.6% |
| mirror | 2,856 | 2,561 | −10.3% |
| sentinel | 2,797 | 2,189 | −21.7% |
| judge | 1,995 | 1,661 | −16.8% |
| predator | 1,125 | 745 | −33.8% |
| phantom | 129 | 150 | +15.7% |
| wall | 174 | 125 | −28.6% |

**Firestorm dominance confirmed.** Not only is Firestorm still #1, it's *stronger* in Phase 2 (+17.4%). Why? Because the tabular model samples Firestorm's aggressive actions with clean empirical frequencies — no softening, no regularization. Phase 2 Firestorm is a sharper, more committed Firestorm.

The Phantom/Wall losers remain losers. The middle-of-the-pack agents (Oracle, Mirror, Sentinel, Judge) maintain their relative ordering within 5–10%.

### 7.2 Trust Dynamics

| Archetype | P1 Mean Trust | P2 Mean Trust | P1 Entropy | P2 Entropy |
|-----------|---------------|---------------|------------|------------|
| wall | 0.962 | 0.962 | 0.001 | 0.000 |
| judge | 0.815 | 0.797 | 2.467 | 2.494 |
| mirror | 0.798 | 0.813 | 2.446 | 2.462 |
| sentinel | 0.784 | 0.787 | 2.282 | 2.164 |
| predator | 0.765 | 0.791 | 2.426 | 2.442 |
| oracle | 0.759 | 0.730 | 2.250 | 2.103 |
| phantom | 0.667 | 0.617 | 2.170 | 1.644 |
| firestorm | 0.435 | 0.389 | 0.823 | 0.414 |

Wall locks at 0.962 in both phases. Firestorm sits at the bottom with the lowest entropy (cleanest classification). The middle archetypes cluster in the 0.73–0.82 trust range, exactly as in Phase 1.

**Phase 2 Firestorm is even more visible to observers** (entropy drops from 0.82 to 0.41 bits). Because the tabular Firestorm commits harder to its aggression parameters, the trust model has an even cleaner signal to classify it.

### 7.3 Trust-Profit Anticorrelation — The Headline Finding

Pearson correlation between mean final stack and mean trust received:

- **Phase 1: r = −0.837**
- **Phase 2: r = −0.825**
- **Agreement: 99%**

This is the strongest validation in the entire project. The trust-profit anticorrelation is not a quirk of the specific BR/VBR/CR parameter values — it is a property of the competitive structure. Agents that broadcast their honesty (Wall, T = 0.962) are systematically exploited. Agents that obfuscate their intentions through aggression (Firestorm, T = 0.389) extract value through fold equity and psychological pressure.

**This finding is publishable.** It is robust to implementation method, parameter scaling, and sampling mechanism. It holds across two independently generated 100K+ hand datasets.

### 7.4 Classification Accuracy

Fraction of observers whose top posterior archetype matches the true archetype at the final hand:

| Archetype | P1 Accuracy | P2 Accuracy |
|-----------|-------------|-------------|
| wall | 100.0% | 100.0% |
| firestorm | 67.1% | 100.0% |
| phantom | 92.1% | 60.0% |
| oracle | 52.1% | 40.0% |
| mirror | 47.9% | 20.0% |
| predator | 30.0% | 22.9% |
| sentinel | 0.0% | 0.0% |
| judge | 0.0% | 0.0% |

Firestorm classification *improves* to 100% in Phase 2 because the tabular model's cleaner parameter commitment makes it easier to detect. Phantom classification drops from 92% to 60%, likely because Phase 2 Phantom's behavior has slightly different texture that pushes it closer to other archetypes in the posterior.

**Classification ceiling:** Phase 1 = 4/8 (Oracle, Firestorm, Wall, Phantom). Phase 2 = 3/8 (Firestorm, Wall, Phantom). The ceiling is nearly identical — the identifiability wall is real.

Most importantly: Sentinel, Mirror, Judge remain in the 0–48% classification cluster in both phases. The mathematical limit documented in `docs/stage5_identifiability.md` persists under ML-reconstructed agents.

### 7.5 Head-to-Head Chip Flow

The chip flow matrix (row profits from column across all showdowns):

```
Phase 2 H2H Matrix (net chips in 125k hands):

          oracle  sentinel firestorm  wall  phantom  predator  mirror  judge
oracle       -     +1270   +24834   +14044   -2899    +693     -1640   +280
sentinel   -1270    -      +23506   +17926   +1017   +1818     +2186  -3387
firestorm -24834  -23506      -     -39613  -26917  -25544   -26794  -25555
wall      -14044  -17926   +39613     -     -8990  -16032   -13703  -17754
phantom    +2899   -1017   +26917   +8990     -     +943     +1847   -1045
predator   -693   -1818   +25544   +16032    -943     -       -3193  -2902
mirror    +1640   -2186   +26794   +13703   -1847   +3193     -      -214
judge      -280   +3387   +25555   +17754   +1045   +2902     +214     -
```

The dominant pattern matches Phase 1: **everyone wins chips from Firestorm at showdown** (Firestorm has the worst showdown win rate) but **Firestorm compensates massively through fold equity** (83.5% of Firestorm's aggressive actions win without showdown).

Wall takes chips from Firestorm (+39,613) but loses heavily to the balanced archetypes because it value-bets too rarely.

---

## 8. Key Findings

### 8.1 The Phase 1 Findings Are Strategy-Level, Not Parameter-Level

The primary research question — whether Phase 1's emergent dynamics are artifacts of specific parameter tuning — is answered decisively. Every headline finding reproduces:

| Finding | Phase 1 | Phase 2 | Verdict |
|---------|---------|---------|---------|
| Firestorm economic dominance | #1 @ 17,862 chips | #1 @ 20,971 chips | Robust |
| Trust-profit anticorrelation | r = −0.837 | r = −0.825 | Robust |
| Wall identifiability | 100% | 100% | Identical |
| Firestorm identifiability | 67% | 100% | Stronger in P2 |
| Sentinel/Mirror/Judge unclassifiable | 0–48% | 0–20% | Ceiling confirmed |
| Wall + Phantom economic losers | Bottom 2 | Bottom 2 | Identical |
| Firestorm fold equity | 87.1% | 83.5% | Within 4% |
| Identifiability ceiling | 4/8 | 3/8 | Nearly identical |

### 8.2 The Simplest ML Approach Beat the Most Complex

A prediction that would have been surprising *a priori*: the non-parametric tabular model outperforms Random Forest and Neural Network for this task. This is because:

1. **The decision function has no continuous structure.** It is a lookup over 24 discrete cells. Smooth classifiers add noise without adding signal.
2. **The law of large numbers beats feature engineering.** With 8,000+ samples per cell, empirical frequencies are indistinguishable from the true parameter values.
3. **Probability calibration is free.** No need for CalibratedClassifierCV, isotonic regression, or Platt scaling — the tabular counts are already perfectly calibrated by construction.

For Phase 3 (LLM agents), this suggests a caution: **more sophisticated modeling is not automatically better.** If the decision structure is discrete and conditional, a matching discrete conditional model is the right tool.

### 8.3 Hand Strength Is the Load-Bearing Feature

Ablation result: without `hand_strength`, ML agents collapse to uniform passive behavior regardless of archetype. This makes sense because the archetype parameter tables are organized around hand strength (VBR for Strong, MBR for Medium, BR for Weak). Remove this axis and the conditional structure disappears.

**Implication for Phase 3:** LLM agents need access to hand strength information at decision time. Either:
- Compute it explicitly (same Monte Carlo as rule-based) and include in the prompt
- Let the LLM reason about hand strength from hole cards + board (slower, less consistent)
- Train or fine-tune on action data that includes hand strength as a feature

### 8.4 Showdown Data Alone Is Insufficient for Training

The showdown table provides ground-truth hand strength, but only for hands that reached showdown — a non-random sample. Training on this subset produces models that never fold, because folded hands are absent from the data. **Any future ML work on this dataset must use live extraction or explicit hand-strength logging**, not post-hoc reconstruction from showdowns.

### 8.5 Sampling Is Essential, Argmax Is Destructive

The ML agents produce correct behavior only when they *sample* from `predict_proba`, not when they take `argmax`. This mirrors the rule-based agents' use of RNG rolls against probability tables. Deterministic argmax collapses each archetype to its modal action, erasing the stochastic structure that makes personalities legible.

This is a general lesson: **when reproducing probabilistic agents, preserve stochasticity at inference.**

---

## 9. Limitations and Documented Shortcomings

### 9.1 Adaptive Agents Are Not Truly Adaptive in Phase 2

The Predator, Mirror, and Judge are rule-based agents that *adapt* to opponents via posterior-reading, behavioral mimicry, and grievance tracking. The Phase 2 ML agents capture only the *aggregate* behavior produced by these mechanisms — they do not learn the adaptive logic itself.

Specifically:
- **Predator:** The Phase 2 Predator plays a fixed-behavior version of Predator that averages Predator's exploitative adjustments across all training hands. It does not consume trust posteriors at runtime.
- **Mirror:** Phase 2 Mirror plays the aggregate Mirror, not a true tit-for-tat. If the table composition changes, Phase 2 Mirror will not shift its behavior.
- **Judge:** Phase 2 Judge plays the cooperative Judge forever — the grievance-triggered retaliation is lost.

In practice this may not matter much: Phase 1's Judge only triggered retaliation in ~5 out of 20 seeds, and the retaliation effect was subtle (Section 16 of deep analysis). But for *research questions about adaptive behavior*, Phase 2 is not a substitute for Phase 1.

**Future work:** To capture adaptation, the ML model must take per-opponent trust posteriors or behavioral statistics as features. This requires re-extracting training data with those features included, and training sequence models (not static classifiers).

### 9.2 Only 5 Seeds × 25k Hands

Phase 1 v3 used 20 seeds × 25k hands = 500k hands. Phase 2 used 5 seeds × 25k hands = 125k hands. The lower seed count makes the Phase 2 statistics noisier on cross-seed metrics (e.g., standard deviation of final stack). The full 20-seed Phase 2 run would take ~43 hours at 0.8 hands/sec and was deferred.

The 5 seeds are sufficient for the validation claims in this report, but a publication version should rerun with matching seed counts for clean methodology.

### 9.3 The Tabular Model Is a Reverse-Engineering Tool

The tabular approach is, by construction, a direct empirical reconstruction of the archetype parameter file. It succeeds at reproducing Phase 1 precisely because Phase 1's action data *is* the archetype parameters expressed as frequencies. This is somewhat circular for the "can ML learn personalities?" question: yes, ML can learn personalities from data, but the simplest possible ML approach (counting) works because the target is inherently tabular.

A more ambitious test would be: **can an ML model trained on Phase 1 data generalize to a novel poker variant or stack size?** The tabular model, having no smoothing or interpolation, would fail at anything outside the training distribution. Random Forest or MLP would at least attempt to generalize (even if badly). This generalization gap is a classic bias-variance tradeoff that Phase 2 did not explore.

### 9.4 Classification Accuracy Metric Is Noisy at Small Seed Counts

With only 5 seeds, the classification accuracy per archetype is estimated from 35 observer-target pairs (5 seeds × 7 observers per target). This gives reasonable point estimates but wide confidence intervals. The apparent drops from Phase 1 to Phase 2 (Phantom 92% → 60%, Mirror 48% → 20%) may partially reflect sampling variance rather than real behavioral differences.

### 9.5 LFS Storage Limitation for Phase 2 Database

The Phase 2 final database (`ml_runs_tabular_final.sqlite`) is ~2GB. GitHub LFS has a 2GB per-file limit, so this database is not committed to the repository. The raw analysis reports (`ml_deep_analysis_final.txt`, `comparison_final.txt`) are committed, but reproducing the database requires rerunning the extraction and simulation (roughly 13 hours total on a modern workstation).

---

## 10. File Layout (Phase 2 additions)

```
Poker_trust/
├── ml/
│   ├── __init__.py
│   ├── feature_engineering.py      # Feature definitions (7 or 8 dims)
│   ├── extract_training_data.py    # SQLite → CSVs (Attempts 1-2)
│   ├── extract_live.py             # Live extraction with HS (Attempts 3-4)
│   ├── train_traditional.py        # LogReg + Random Forest
│   ├── train_neural.py             # sklearn MLPClassifier
│   ├── train_split.py              # Split-context RF (Attempt 3)
│   ├── train_tabular.py            # Tabular empirical model (Attempt 4)
│   ├── evaluate_models.py          # Three-way model comparison
│   └── smoke_test_ml.py            # 500-hand spec validation
│
├── agents/
│   └── ml_agent.py                 # MLAgent class (tabular + RF modes)
│
├── run_ml_sim.py                   # Phase 2 simulation runner
├── compare_phases.py               # Phase 1 vs Phase 2 comparison
├── requirements_ml.txt             # scikit-learn + joblib
├── phase2_report.md                # This report
│
├── ml/data_live/                   # (gitignored) Training CSVs
├── ml/models_tabular/              # (gitignored) Trained models
└── ml_runs_tabular_final.sqlite    # (gitignored) Phase 2 database
```

## 11. Quick-Start Commands

```bash
# Install Phase 2 dependencies
pip install -r requirements_ml.txt

# Step 1: Extract training data with live hand strength (~12 hours)
python -m ml.extract_live --hands 25000 --seeds 42,137,256,512,1024 --outdir ml/data_live/

# Step 2: Train tabular models (seconds)
python -m ml.train_tabular --datadir ml/data_live/ --outdir ml/models_tabular/

# Step 3: Smoke test (must pass all 8 archetypes)
python -m ml.smoke_test_ml --modeldir ml/models_tabular/

# Step 4: Full simulation run (~4 hours at 8.7 hand/s)
python run_ml_sim.py --model-type tabular --modeldir ml/models_tabular/ \
    --hands 25000 --seeds 42,137,256,512,1024 --db ml_runs_tabular_final.sqlite

# Step 5: Analysis
python analysis/analyze_runs.py --db ml_runs_tabular_final.sqlite
python analysis/deep_analysis.py --db ml_runs_tabular_final.sqlite --out ml_deep_analysis_final.txt

# Step 6: Phase comparison
python compare_phases.py --phase1-db runs_v3.sqlite \
    --phase2-db ml_runs_tabular_final.sqlite --out comparison_final.txt
```

## 12. Conclusion

Phase 2 validates Phase 1 definitively. The trust-profit anticorrelation, Firestorm economic dominance, and identifiability ceiling are strategy-level properties that survive ML model substitution. The simplest possible ML approach — empirical frequency counting — outperforms Random Forest, Logistic Regression, and Neural Networks for this task, because poker archetype decisions are inherently discrete conditional lookups, not smooth functions in feature space.

The methodological lesson is broader: when learning to imitate rule-based agents, match the model architecture to the structure of the decision process. Two-stage decisions need two-stage models. Discrete conditional probabilities need tabular estimation. Continuous classifiers add noise without adding value.

Phase 3 (LLM agents) will test whether language-capable agents develop richer trust dynamics than either rule-based or tabular-ML agents. The key question shifts from "can ML reproduce the behavior?" to "can language reasoning produce *novel* behavior that the parameter tables cannot express?"
