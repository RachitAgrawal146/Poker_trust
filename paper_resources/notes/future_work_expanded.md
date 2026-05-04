# Future Work — Detailed Roadmap

> Expansion of paper.md Section 7.3. Each direction lists motivation,
> concrete experimental design, expected cost (where applicable), and
> the falsifiable claim it would test.

## A. Tightening the Phase 3.1 result (lowest risk, highest value)

### A1. n = 20 seed replication

**Motivation.** With σ = 0.30 and n = 5, the 95% CI on the Phase 3.1
mean spans roughly [-0.36, +0.18]. Two of five seeds invert the trap;
three do not. We cannot distinguish "trap consistently softened to
near zero" from "trap broken in 40% of populations and merely
weakened in 60%."

**Design.** Run Phase 3.1 with seeds 42, 137, 256, 512, 1024, 2048,
4096, 8192, 16384, 32768, 65536, 99991, 131071, 200003, 271828,
314159, 524287, 1048576, 2097143, 4194301 (15 new seeds, keeping the
canonical 5 first for backward comparison). 150 hands per seed.

**Cost.** ~$60 of API spend at the cached-prompt rate
($17 / 5 seeds × 20 seeds = $68).

**Falsifiable claim.** If 4+ of 20 seeds flip to positive r, the
trap is reliably broken in a substantial population fraction. If the
mean tightens to within ±0.05 of zero with n = 20, the trap is
formally indistinguishable from zero at p < 0.05.

### A2. Longer hand horizons (5 × 500 Phase 3.1)

**Motivation.** Two metrics persistently miss in Phase 3.1: NS
(non-stationarity) sits at 0 exactly, and CS (context sensitivity)
plateaus at 0.10 vs the 0.15 target. Both are time-windowed metrics
that need ≥ 200 hands per window to detect drift. At 150 hands per
seed, we have one effective window — these metrics literally cannot
fire.

**Design.** Same 5 seeds, 500 hands each. Other params unchanged.

**Cost.** ~$57 (3.3× the $17 of the 150-hand run).

**Falsifiable claim.** NS > 0 at 500 hands (the adaptive-spec updates
fire 20 times per seed, vs 6 per seed at 150 hands — drift should
become detectable). CS plateau ≥ 0.13 (closer to the 0.15 target).

### A3. Targeted opponent-conditional reward shaping

**Motivation.** OA (opponent adaptation) stays near zero (0.0007) in
Phase 3.1 because the per-opponent memory is *available* in the
prompt but not *behaviorally consequential* — agents have the data
but do not differentiate strongly across opponents. This is the
single largest unmet target.

**Design.** Phase 3.2 with the same scaffolding plus an additional
sentence in the system prompt: *"Play differently against each
opponent based on the notes — if Wall calls everything, value-bet
heavily; if Firestorm bluffs constantly, call light."* Test whether
explicit instruction unlocks behavioral differentiation.

**Cost.** ~$17 (5 × 150 hands at cached rate).

**Falsifiable claim.** OA > 0.005 in Phase 3.2 (about 7× the Phase
3.1 baseline). This would establish that LLM agents *can* condition
on opponents but only when explicitly instructed.

## B. Beyond Anthropic Haiku

### B1. Multi-LLM tournament

**Motivation.** Every Phase 3 / 3.1 call goes to one Haiku weights
set. Decisions are correlated through a single posterior. We cannot
distinguish "the trap softens with reasoning" from "Haiku
specifically softens the trap; another model would not."

**Design.** 8-seat table where each seat gets a different model:
- Oracle: Claude Sonnet 4.6 (the most capable in the family)
- Sentinel: GPT-4o (a different vendor's frontier model)
- Firestorm: Claude Haiku 4.5 (the Phase 3.1 baseline)
- Wall: open-weights Llama 3.1 70B (different training pipeline)
- Phantom: Mistral Large
- Predator: Gemini 1.5 Pro
- Mirror: Claude Haiku 4.5 (control comparison)
- Judge: Claude Sonnet 4.6

**Cost.** Higher and harder to estimate — multi-vendor API costs add
up. Rough budget: $100-200 for 5 × 150 hands.

**Falsifiable claim.** The Phase 3.1 Δr = +0.416 is robust to
heterogeneous model selection (within ±0.10 across the five
Haiku-equivalent models in the mix).

### B2. Reasoning-budget scaling

**Motivation.** Phase 3.1 uses a 2-sentence CoT cap. Earlier
verbose-CoT experiments inflated cost 5× and produced LLM
self-talked aggression, but were never run to completion. The
reasoning-vs-cost frontier is unmapped.

**Design.** Run Phase 3.1 at three CoT budgets in parallel:
- Tight (current): 2 sentences, max_output_tokens=96
- Medium: 5 sentences, max_output_tokens=256
- Verbose: unbounded reasoning (max_output_tokens=2048)

Same 5 seeds × 50 hands each (50 not 150 to keep cost bounded).

**Cost.** ~$60 total (verbose dominates).

**Falsifiable claim.** Trust-profit r is monotone in reasoning
budget; verbose CoT either further softens the trap (r → +0.1) or
inflates aggression so much it re-engages the trap (r → -0.5).

## C. Architectural variations

### C1. No-limit Hold'em

**Motivation.** Limit Hold'em constrains aggression — the bet cap is
4 raises, the bet sizes are fixed at 2 (small) and 4 (big). In
no-limit, Firestorm could shove all-in with any two cards, amplifying
fold-equity dynamics. The trap may be substantially deeper.

**Design.** Port the engine to no-limit. Re-run the same 4-tier
ladder (Phase 1 frozen, Phase 2 hill-climbing, Phase 3 LLM, Phase 3.1
LLM-with-reasoning). Same 5 seeds.

**Cost.** Engineering cost is non-trivial (1-2 weeks of careful
betting-round refactoring). API cost ~$20 for the LLM phases.

**Falsifiable claim.** The trust-profit r in no-limit Phase 1 is
more negative than -0.85, and the Phase 3.1 step is qualitatively
similar in size (Δr ≈ +0.4). If Δr is dramatically smaller, the
trap-breaking effect was Limit-specific.

### C2. Dynamic table composition

**Motivation.** Real reputation systems involve actors joining and
leaving (eBay sellers come and go, employees switch jobs). Our 8-seat
table is static for the entire simulation. Whether the trap depends
on this assumption is untested.

**Design.** Add a "rebuy with new identity" mechanism: when an agent
busts and rebuys, they get a fresh seat number and zero trust history
on every other agent. The trust model has to relearn from scratch.
Run Phase 1 (frozen rules) to see whether identity churn changes the
fundamental dynamic.

**Cost.** Small — engineering work only.

**Falsifiable claim.** If the trap softens substantially under
identity churn, then *persistent identity* is the key amplifier.
If it deepens, then long observation horizons are what enables
exploitation.

### C3. Adversarial archetypes

**Motivation.** Predator and Mirror are *meant* to be adaptive but
in practice barely differ from Oracle in our results. A purpose-built
"trust farmer" archetype — explicitly designed to look like Wall for
hands 1-50 then play like Firestorm afterward — would test whether
the trust model is fooled by explicit deception.

**Design.** Add a new archetype, "Chameleon": plays Wall's parameters
for the first 50 hands, then switches to Firestorm. Trust posterior
should classify it as Wall throughout the early phase, then either
update fast (good) or stay anchored (revealing trust-model
slowness as an exploitable weakness).

**Cost.** Engineering only. ~1 day.

**Falsifiable claim.** Chameleon's mean trust score stays > 0.7 even
after the strategy switch, demonstrating that the Bayesian model's
exponential decay (λ = 0.95) is too slow to catch behavioral pivots.

## D. Cross-domain validation

The strongest test of the central claim is whether the trust trap
appears in environments other than poker.

### D1. Iterated public-goods game

A simpler, more theoretically-grounded environment. 8 agents with
Wall/Firestorm/Phantom analogs, observation-based reputation, fixed
payoff matrix. Easier to derive the equilibrium and compare empirics
to theory. Implementation: ~1 week.

### D2. Sealed-bid auction with reputation

Agents bid in repeated single-item auctions. "Trust" = posterior over
each bidder's value distribution. Predict whether the trust trap
manifests in a domain with no aggression component. If it does, the
trap generalizes to passive-information games; if not, it requires
strategic action.

### D3. Cooperative dialogue benchmark

Replace the poker engine with a multi-LLM cooperative reasoning task
(e.g., Diplomacy without the betrayal layer). Re-run the trust model
on dialogue features. Tests whether reputation-as-exploitation
appears in pure-cooperation environments — our prediction is that
it does *not*, since cooperation has no aggression to exploit.

## E. Open questions left for future readers

1. Is there a theoretical lower bound on the residual r that any
   reasoning agent could achieve? Phase 3.1 hit -0.094 — is zero
   achievable? Is *positive* r achievable systematically rather than
   in 40% of seeds?
2. What is the relationship between the trust model's λ (forgetting
   rate) and the trap depth? A sweep would tell us whether faster
   forgetting helps defenders or hurts them.
3. Does Phase 3.1's effect persist when the Bayesian model is replaced
   by a neural classifier? If yes, the trap depends on the type of
   reasoning the agents have, not the type of trust model the
   environment uses.
4. Does the order in which agents reason matter? Phase 3.1 reasons in
   seat order each hand. A randomized order or a "spotlight" order
   (most-trusted reasons last) would probe whether positional
   reasoning advantages exist.
