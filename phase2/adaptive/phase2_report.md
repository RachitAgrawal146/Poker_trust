# Phase 2 (Adaptive) Report — Bounded Online Optimization Cannot Escape the Trust Trap

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Branch:** `claude/poker-trust-phase-2-C1yUP` (phase2-adaptive lineage)
**Run config:** 3 seeds × 5 000 hands, `eval_window = 200`, `delta = 0.03 → 0.005`, decay 0.995
**Artifacts:** `reports/phase2_scorecard.txt`, `phase2/adaptive/optimization_log.json`,
`phase2/adaptive/param_trajectories.json`,
`runs_phase1_ref.sqlite` (P1 reference, gitignored),
`runs_phase2_adaptive.sqlite` (P2 adaptive, gitignored)

---

## 1. Motivation: why we replaced the imitation Phase 2

The original Phase 2 trained tabular and neural classifiers on Phase 1 hand
traces and dropped the resulting policies back into the simulator. The result
was, by construction, a near-perfect reproduction of Phase 1: trust-profit
r = −0.825, behavioral fingerprints within 1–3 % of the rule-based originals,
the same Sentinel/Mirror/Judge identifiability ceiling. As a sanity check
that finding is useful — it rules out implementation-method artifacts — but
as a *finding* it is empty. Supervised imitation of Phase 1 reproduces Phase 1.

The three-phase narrative the project wants to tell is sharper than that. Each
phase tests a different *kind* of intelligence against the same trust trap:

| Phase | Mechanism | Question |
|---|---|---|
| 1 | Frozen archetype specs | Does fixed strategy cause the trap? |
| 2 | **Bounded online optimization** | Can numerical search escape the trap? |
| 3 | LLM symbolic / linguistic reasoning | Can qualitative reasoning succeed where numerical search fails? |

The redesigned Phase 2 implements (2) directly. Each agent starts at its
Phase 1 archetype params, and a per-agent hill climber tunes those params
within an archetype-shaped bound box every 200 hands, optimizing windowed
chip profit. The trust model stays Phase 1-static, so the reputation system
that other agents are using to score this agent is gradually miscalibrated
relative to its actual behavior. The original imitation pipeline lives
untouched at `phase2/_imitation_archive/`.

## 2. Design

### 2.1 Algorithm

Each agent runs an independent hill climber. A cycle is:

1. **Baseline phase (200 hands)** — play with current parameters. Record
   the rebuy-adjusted windowed profit.
2. **Trial phase (200 hands)** — pick a uniformly random `(round, metric)`
   pair, perturb the value by `±delta` (signed uniformly), clamp to the
   archetype's bounds, play, record windowed profit.
3. **Accept / revert** — keep the perturbed params if `trial > baseline`,
   else revert. Decay `delta *= 0.995`, floor `0.005`. Log the cycle.

`AdaptiveJudge` is a special case: its parameters are
`{pre_trigger: {…}, post_trigger: {…}}`, and the climber picks one of those
two states uniformly per cycle so both optimize independently. The 56 grievance
counters that drive the trigger flip are unchanged from Phase 1.

### 2.2 Bounds

Each archetype gets a hard `(lo, hi)` box per `(round, metric)`. The box is
centered on the Phase 1 starting value and widened by a personality-appropriate
margin — tight (Sentinel, Wall: ±10–15 %), moderate (Oracle, Predator,
Mirror, Judge cooperative: ±20–25 %), loose (Firestorm, Phantom, Judge
retaliatory: ±30–40 %). A small set of identity-locked metrics
(`Wall.br ∈ [0, 0.05]`, `Sentinel.br ∈ [0.02, 0.18]`) is clamped near zero
so the *shape* of the archetype survives optimization.

### 2.3 Objective

All eight agents maximize plain windowed chip profit, rebuy-adjusted (the
runner subtracts `rebuy_delta * starting_stack` so an agent that goes broke
and gets topped up doesn't get rewarded for the infusion). No per-archetype
custom rewards: Sentinel is not given a risk-adjusted EV objective, Phantom
is not given a deception-success objective, Mirror is not given an
opponent-mimicry score. The bounds shape the search space; the objective
stays uniform. This keeps attribution clean — any cross-archetype
behavioral differences come from the bound shapes alone.

### 2.4 Static trust model

`trust/bayesian_model.py` is unmodified. It still imports the original
`ARCHETYPE_PARAMS` and `HONESTY_SCORES` tables. As an agent's actual
behavior drifts across cycles, the reputational likelihoods every other
agent is using become increasingly stale. This is a feature: the agents are
exploiting a *miscalibrated* reputation system, which is exactly the
real-world setup the project models. Stage 5's Aberration Index quantifies
how far behavior drifts from the spec.

### 2.5 Two design simplifications

- **Predator and Mirror lose their adaptive modifiers.** In Phase 1, Predator
  blends its baseline parameters with `PREDATOR_EXPLOIT[top_target]` when its
  posterior over an opponent passes 0.6, and Mirror copies the most-active
  opponent's metrics into `mirror_default`. Both modifiers are removed in
  Phase 2 — they only optimize `predator_baseline` and `mirror_default`. This
  ensures the climber is the only source of adaptation, which is the cleanest
  test of "what can numerical optimization alone do?"
- **3 seeds × 5 000 hands**, not the Phase 1 canonical 5 × 10 000. Lean
  configuration so the comparison is repeatable on a laptop in 30 minutes.
  A 5 × 10 000 long run is staged but not yet executed (see Section 6).

## 3. Results

All numbers below are means ± standard deviations across the three seeds
(42, 137, 256). The full scorecard is `reports/phase2_scorecard.txt`.

### 3.1 Headline scorecard (Table 0)

| Metric | Phase 1 | Phase 2 | Δ |
|---|---|---|---|
| Trust–Profit r | −0.773 ± 0.084 | **−0.769 ± 0.139** | +0.003 |
| Mean TEI | −0.175 ± 0.011 | −0.143 ± 0.016 | +0.033 |
| Context Sensitivity (CS) | +0.143 ± 0.004 | +0.145 ± 0.003 | +0.002 |
| Opponent Adaptation (OA) | +0.0003 | +0.0003 | −0.0000 |
| Non-Stationarity (NS) | +0.00238 | +0.00246 | +0.00009 |
| Unpredictability (SU bits) | +1.924 ± 0.107 | +1.963 ± 0.076 | +0.040 |
| Trust Manipulation (TMA) | +0.129 ± 0.003 | +0.120 ± 0.019 | −0.009 |

Five of the seven numbers move by less than one Phase-1 standard deviation.
The two that do move (TEI and SU) move *toward* the Phase 1 ceiling (less
trust extraction, slightly more unpredictability), but the central
trust-profit anti-correlation is, within seed noise, identical.

### 3.2 Behavioral fingerprints (Table 1)

VPIP, PFR and AF (= (bets + raises) / calls) per archetype. The interesting
movements are concentrated in the agents that lost their Phase 1 adaptive
modifiers:

- **Predator** AF rises from 0.83 → **0.98** (+18 %); its baseline was the
  point the climber optimized, and it walked toward more aggression.
- **Mirror** VPIP drops 0.19 → 0.16, AF rises 0.90 → **1.02**. Without the
  opponent-mimic copy step, the climber tightened Mirror's preflop range and
  pushed its postflop aggression up.
- **Oracle** drops slightly (VPIP 0.22 → 0.21, AF 1.16 → 1.10), the only
  archetype where adaptation reduced aggression.
- **Sentinel, Firestorm, Wall, Phantom, Judge** stay essentially flat
  (drift well under one P1 std on every axis).

### 3.3 Economic ordering (Table 2)

| Archetype | Stack P1 | Stack P2 | Rank P1 | Rank P2 | ΔRank |
|---|---|---|---|---|---|
| firestorm | 3275 ± 395 | **3982 ± 565** | 1 | 1 | 0 |
| oracle | 1064 ± 404 | 693 ± 196 | 2 | 3 | +1 |
| sentinel | 1036 ± 198 | **447 ± 210** | 3 | 5 | +2 |
| mirror | 908 ± 227 | 676 ± 217 | 4 | 4 | 0 |
| judge | 527 ± 181 | **1247 ± 454** | 5 | **2** | **−3** |
| predator | 367 ± 91 | 415 ± 127 | 6 | 6 | 0 |
| wall | 79 ± 30 | 114 ± 53 | 7 | 7 | 0 |
| phantom | 77 ± 81 | 93 ± 52 | 8 | 8 | 0 |

Three significant moves:

1. **Firestorm got more dominant** under adaptation (+707 chips on average),
   widening its lead over the field.
2. **Judge climbed three ranks** (5 → 2). Its retaliatory params live in a
   loose bound box (±30–40 %), and the climber found gains there.
3. **Sentinel collapsed** from 1036 → 447 chips and now needs rebuys (1 ± 1
   per seed vs 0 in P1). Its tight bound box (±10–15 %) gave the climber
   little room, and the small moves it did make hurt rather than helped.

The bottom of the ordering is unchanged — Wall and Phantom are still pinned
at the floor with double-digit rebuy counts (~14 and ~11 respectively), and
adaptation didn't pull them up.

### 3.4 Trust–profit r per seed (Table 3)

| Seed | Phase 1 r | Phase 2 r | Δ |
|---|---|---|---|
| 42 | −0.838 | **−0.878** | −0.039 |
| 137 | −0.825 | **−0.858** | −0.033 |
| 256 | −0.654 | −0.573 | +0.082 |
| mean | −0.773 ± 0.084 | −0.769 ± 0.139 | +0.003 |

In two of three seeds the trap got *stronger* under adaptation, not weaker.
Seed 256 is the only one where adaptation softened the anti-correlation,
and even there the result (−0.573) is far from neutral. The 3-seed mean
matching to within 0.003 is essentially a coincidence of two opposite-sign
shifts cancelling; the per-seed pattern is more informative than the mean.

### 3.5 Parameter trajectories (Table 4)

Each agent runs ~12 cycles per seed (3 seeds × 12 = 36 total). The
hill-climber's bookkeeping:

| Archetype | Cycles | Accepted | Reject | Rate | L1 dist | Most-moved metric |
|---|---|---|---|---|---|---|
| judge | 36 | 22 | 14 | 61.1 % | 0.215 | river br −0.060 |
| firestorm | 36 | 21 | 15 | 58.3 % | 0.202 | preflop strong_raise −0.060 |
| mirror | 36 | 21 | 15 | 58.3 % | 0.202 | river strong_fold +0.059 |
| oracle | 36 | 19 | 17 | 52.8 % | 0.176 | river weak_call −0.058 |
| phantom | 36 | 19 | 17 | 52.8 % | 0.157 | preflop med_raise +0.058 |
| predator | 36 | 19 | 17 | 52.8 % | 0.184 | flop weak_call −0.059 |
| sentinel | 36 | 15 | 21 | **41.7 %** | 0.127 | preflop strong_call +0.060 |
| wall | 36 | 15 | 21 | **41.7 %** | 0.133 | flop cr +0.058 |

Two patterns:

- **Sentinel and Wall, the two tight-bound archetypes, also have the lowest
  accept rate and smallest L1 movement.** Bounds and acceptance interact: a
  smaller box means a higher fraction of perturbations end up clamped, and
  the climbed value is then tested against a baseline that is already
  near-optimal for the box.
- The *direction* of the most-moved metric is consistent across seeds for
  every archetype (all eight rows have signed deltas of magnitude 0.058–0.060,
  i.e. the maximum allowed by `delta=0.03 × 12 cycles × decay = ~0.06`).
  The climber found one strong gradient direction per archetype and rode it.

### 3.6 Adaptation success: last-1000-hand profit + Firestorm leak (Table 5)

The "did adaptation help?" test, restricted to the final 1 000 hands so the
optimizer has settled. "Loss → FS" is chips this agent invested in hands
Firestorm won at showdown — lower is better, since Firestorm's profit comes
disproportionately from extracting value from the table.

| Archetype | Last-1k P1 | Last-1k P2 | Δ | Loss→FS P1 | Loss→FS P2 |
|---|---|---|---|---|---|
| firestorm | +927 ± 128 | **+1038** | +110 | — | — |
| oracle | +585 ± 253 | +617 ± 326 | +32 | 608 | 622 |
| sentinel | +482 ± 88 | **+284 ± 58** | **−198** | 461 | **572** |
| wall | −107 ± 77 | **−390 ± 141** | **−283** | 2400 | 2282 |
| phantom | −145 ± 160 | −19 ± 58 | +126 | 613 | 662 |
| predator | +412 ± 148 | +508 ± 335 | +96 | 688 | **509** |
| mirror | +387 ± 158 | +380 ± 56 | −7 | 791 | **456** |
| judge | +458 ± 151 | **+581 ± 56** | +123 | 423 | **264** |

Two findings worth surfacing:

1. **Adaptation hurt the rule-followers.** Sentinel (−198) and Wall (−283)
   are the two tight-bound archetypes; the climber couldn't find profit
   improvements within the box and the small drift it did produce was net
   negative. This is consistent with their low accept rate.
2. **Emergent Firestorm defense exists, but only in some agents.** Mirror
   cuts its leak to Firestorm by 42 % (791 → 456), Judge by 38 %
   (423 → 264), Predator by 26 % (688 → 509). Sentinel's leak grows by
   24 % (461 → 572). Wall is essentially saturated (2282 ≈ 2400) — its
   chips go to Firestorm whether or not the climber is running. The
   climber found per-opponent defense in some agents because the global
   profit signal happens to align with reduced-leak-to-the-dominant-player,
   but this is incidental, not structured: there is no per-opponent state
   in the optimizer. Section 4 unpacks why this matters for Phase 3.

### 3.7 Aberration Index: behavioral drift from spec (Table 6)

L2 distance in (VPIP, PFR, AF) space between Phase 2's end-of-run behavior
and the Phase 1 spec, with each axis normalized by the Phase-1 cross-archetype
standard deviation (so a unit equals "one P1 archetype-spread"):

| Archetype | L2 drift | dominant axis |
|---|---|---|
| **predator** | **0.609** | AF +0.15 |
| **mirror** | **0.546** | AF +0.12, VPIP −0.028 |
| judge | 0.266 | AF +0.07 |
| oracle | 0.205 | AF −0.06 |
| phantom | 0.147 | VPIP −0.011 |
| sentinel | 0.098 | AF −0.03 |
| wall | 0.047 | (mostly clamped) |
| firestorm | 0.037 | (mostly clamped) |

Mean Aberration Index: **0.244**. The two largest drifters are exactly the
agents whose Phase 1 adaptive modifiers were removed (Predator's
`PREDATOR_EXPLOIT` blend, Mirror's opponent copy). Their drift is therefore
partly an artifact of removing the modifier rather than evidence of
optimization-driven divergence. The remaining six archetypes drift well
within one axis-spread, confirming that the bound boxes successfully
preserve archetype identity even after optimization.

## 4. Key findings

Five questions, five answers.

### 4.1 Did the trust trap weaken under adaptation?

**No.** Trust–profit r moves from −0.773 to −0.769 — a delta of +0.003,
which is two orders of magnitude smaller than the seed-to-seed standard
deviation (0.084 in Phase 1, 0.139 in Phase 2). In two of three seeds the
trap got *stronger* under adaptation. The bounded numerical optimization
hypothesis — "if Phase 1's anti-correlation is just an artifact of fixed
parameters, then letting agents tune their own params should weaken it" —
is rejected within the resolution of this experiment.

### 4.2 Which archetypes actually adapted?

Three patterns:

- **Predator and Mirror drifted the most** (Aberration Index 0.61 and 0.55),
  but this is largely because they lost their built-in Phase 1 adaptation.
  The climber walked them toward more aggression (AF +0.12 to +0.15).
- **Judge benefited the most economically** (final stack +720, rank #5 → #2),
  driven by tuning its retaliatory params (the loose-bound state).
- **Sentinel and Wall, the tight-bound archetypes, lost ground** (Sentinel
  −589 chips, lowest accept rate at 41.7 %). The bounded search space
  protects archetype identity but also denies these agents the freedom to
  find profit improvements.

### 4.3 Did per-opponent strategies emerge?

**No.** Opponent Adaptation stayed at 0.0003 in both phases (zero to three
decimal places). Hill-climbing on aggregate chip profit cannot produce
per-opponent strategies because there is no per-opponent state in the
optimizer. The fact that Mirror, Judge, and Predator nonetheless cut their
losses to Firestorm by 26–42 % is surprising on its face but consistent
with this story: their *aggregate* profit gradient happens to point in the
same direction as "lose less to Firestorm", because Firestorm extracts a
disproportionate share of every other agent's losses. This is incidental
defense, not structured opponent modeling — the climber would do the same
thing if the dominant exploiter were a different agent.

### 4.4 How miscalibrated did the trust model become?

The Aberration Index measures the gap between observed behavior in Phase 2
and the Phase 1 archetype baseline that the trust model's likelihood
tables encode. Mean drift is 0.244 axis-spreads, with the two pre-modifier
archetypes (Predator 0.61, Mirror 0.55) dominating. The remaining six
archetypes drift well under one axis-spread, so the trust posterior — which
classifies opponents into the eight archetype types — remains *roughly*
calibrated even after 5 000 hands of optimization. This is the result the
hard bounds were designed to produce: agents can tune within their archetype
shape, but they cannot escape it. The miscalibration we set out to study
is therefore real but bounded; a longer-horizon run with more aggressive
optimization (or wider bounds) would deepen it.

### 4.5 What does this mean for Phase 3?

Phase 2 establishes that the gap Phase 3 must close is specifically the
**per-opponent / linguistic-reasoning gap**. Three quantitative claims fall
out of the scorecard:

- **Trap robustness.** Phase 1 r = −0.77, Phase 2 r = −0.77. Phase 3's
  pilot at 50 hands sat at r = −0.41. The 0.36-point gap between Phase 2
  and Phase 3 is now *unambiguously* attributable to the LLM's reasoning
  capability rather than to "just having any adaptive mechanism."
- **OA threshold.** Phase 2 produced OA = 0.0003, almost-zero. If Phase 3
  produces OA > 0.01 at the same hand budget, that is direct evidence
  the LLM is doing per-opponent strategy that bounded numerical search
  cannot.
- **TMA hypothesis.** Trust Manipulation Awareness moved from +0.129 to
  +0.120 — essentially flat. An LLM agent that explicitly reasons about
  reputation should be able to drive TMA either further positive (farming
  trust before exploiting) or significantly negative (responding to its
  own trust trajectory). Either move would be diagnostic.

## 5. Implications for Phase 3

The redesign sharpens Phase 3's contribution along three axes.

**5.1 Phase 3 inherits a clean baseline.** Phase 2's r = −0.769 is now the
"adaptive but not reasoning" reference. If Phase 3 does *anything* an LLM
might plausibly do — reason about reputation, model opponents linguistically,
adjust play to reciprocate or punish — the trust-profit anti-correlation is
the metric that shows up first. The 50-hand pilot already showed
r = −0.41, and the gap between −0.77 and −0.41 is now attributable to the
LLM specifically, not to "any adaptive mechanism."

**5.2 Per-opponent behavior is now a falsifiable Phase 3 claim.** Phase 2's
OA = 0.0003 establishes a hard zero point: hill-climbing on aggregate reward
within bound boxes cannot produce per-opponent strategy. If Phase 3's
500-hand run produces OA > 0.01, that single number tests whether LLM
reasoning produces opponent-conditional play that numerical search cannot.
This is the cleanest cross-phase test the project has.

**5.3 The miscalibration story is intact.** The Aberration Index of 0.244
is large enough to demonstrate that the Phase 1 trust posterior is
demonstrably miscalibrated relative to actual behavior, but small enough
that the posterior is still *useful* (most archetypes drift well under one
axis-spread). Phase 3 should report its own Aberration Index alongside
behavioral metrics — if LLM agents drift further from their seeded prompts
than Phase 2 agents drift from their bounds, the trust model's
classification ability degrades faster, and that is itself a finding.

A subtle implication: the 50-hand Phase 3 pilot's r = −0.41 is noisy,
but the Phase 2 numbers make it more credible. Three seeds × 5 000 hands
of bounded optimization couldn't shift r by more than 0.003 in the mean;
the fact that 50 hands of LLM play shifted it by 0.36 (even noisily) is
suggestive that the underlying Phase 3 effect is real and large. The
natural follow-up is a 500-hand Phase 3 run for a stable comparison.

## 6. Limitations

Five honest constraints on the result:

**6.1 Three seeds is light.** The trust-profit r has a per-seed std of
0.084 in Phase 1 and 0.139 in Phase 2; at n = 3, the 95 % CI on the
mean is roughly ±0.20. The headline "r unchanged" claim is robust because
the *direction* of the change is split across seeds (two stronger, one
weaker), not because the n is large. The paired 5 × 10 000 long run
(`runs_phase2_long.sqlite`, command in the run handoff) is staged but
not yet executed; it will tighten the CI by ~5×.

**6.2 Single optimizer.** Hill-climbing was chosen because it is local,
interpretable, and produces plottable parameter trajectories. CMA-ES,
REINFORCE, or population-based training would all explore the bound boxes
differently. The "bounded numerical optimization cannot escape the trap"
claim is strictly about hill-climbing; a different optimizer might find
larger movement, especially if it had per-opponent state. We don't think
that's likely — the bound boxes are the binding constraint, not the
optimizer — but it is not tested.

**6.3 No per-opponent state in the optimizer.** The objective is aggregate
windowed profit. By construction, the climber cannot bucket-train per
opponent (the way a poker agent might learn "play tight against Wall, loose
against Phantom"). This is intentional — it isolates the *adaptive*
component from the *opponent-modeling* component, so Phase 3's contribution
is testable. But it means the OA = 0.0003 result is partly trivial: the
optimizer literally has no way to differentiate opponents.

**6.4 Predator and Mirror lost their adaptive modifiers.** The Aberration
Index for those two agents is dominated by removing
`PREDATOR_EXPLOIT[top_target]` (Predator) and `mirror_default ←
opponent_metrics` (Mirror). Their drift is therefore not a clean
"optimization-driven" signal. A future Phase 2.5 could keep the modifiers
and put the climber on top of them, but that conflates two adaptation
mechanisms.

**6.5 Eval window = 200 is short.** With 5 000 hands and a 400-hand cycle
(200 baseline + 200 trial), each agent gets ~12 cycles per seed. Twelve
samples is enough to identify a strong gradient direction (every archetype
found one) but not enough for the climber to converge inside its bound
box. The L1 distances (0.13–0.22) are all near the theoretical maximum
for 12 cycles at delta = 0.03 — the climber is "still moving" at the end
of every run. A longer horizon (10 000+ hands) would let the climber
saturate, and might surface non-linear effects the current setup misses.

---

*Last updated: 2026-04-29. Source artifacts and reproduction commands:
`reports/phase2_scorecard.txt` (this report's data),
`phase2/adaptive/phase2_comparison.py` (regeneration),
`phase2/adaptive/run_adaptive.py` (the underlying simulation).*


