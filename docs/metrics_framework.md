# Metrics Framework: Quantifying Trust Dynamics and Agent Complexity

**Rachit Agrawal | Polygence Research Project**
**Updated April 25, 2026 — includes computed results from 5,000-hand simulation**

---

## 1. Research Aim

> To investigate whether observation-based trust systems inherently reward exploitation over cooperation, and whether this dynamic is a structural property of repeated strategic interaction or an artifact of agent design.

Arpit's follow-up: How do we *quantify* this? And how do we measure what it means to "improve" from mathematical models → ML → LLM agents?

This document defines concrete, computable metrics for both questions — and presents actual computed values from Phase 1.

---

## 2. Quantifying the Trust Dynamic

### The Problem with Pearson r Alone

Our headline metric — trust–profit correlation r = −0.838 — is descriptive but shallow. It tells us trust and profit move in opposite directions. It does *not* tell us:

- How much profit comes from exploiting trust vs. simply having better cards
- Whether the anticorrelation is driven by one extreme agent or is systemic
- Whether the relationship is causal or confounded (e.g., aggression independently causes both low trust and high profit)

### Primary Metric: Trust Exploitation Index (TEI)

**Definition:**

```
TEI_i = (actual_profit_i − showdown_net_profit_i) / hands_played
```

- **Showdown net profit** = chips won at showdowns minus chips invested in showdown hands. This is the component of profit explained by card quality.
- **TEI** = non-showdown profit per hand. This is profit from *table dynamics* — fold equity, bluff success, opponents folding based on trust beliefs.
- **High TEI** = agent profits from dynamics beyond its cards
- **Negative TEI** = agent loses money despite decent cards — being exploited

### Computed Results (Phase 1, 5,000 hands, seed 42)

| Agent | Trust Score | Showdown WR | TEI | Non-SD Profit | Interpretation |
|-------|-----------|-------------|-----|---------------|----------------|
| **Firestorm** | 0.421 | 35.5% | **+0.74** | +3,706 | Worst cards, highest profit. Entirely from fold equity. |
| Oracle | 0.789 | 52.9% | −0.19 | −951 | Balanced play, slight trust cost |
| Sentinel | 0.788 | 57.8% | −0.25 | −1,238 | Good cards, but predictability costs money |
| Predator | 0.808 | 50.9% | −0.29 | −1,469 | Moderate card quality, exploited slightly |
| Phantom | 0.784 | 53.4% | −0.29 | −1,447 | Deception doesn't pay enough |
| Mirror | 0.838 | 52.9% | −0.30 | −1,506 | Mirroring doesn't generate fold equity |
| Judge | 0.732 | 52.8% | −0.23 | −1,144 | Retaliation reduces but doesn't eliminate cost |
| **Wall** | 0.962 | 50.8% | **−0.71** | −3,566 | Decent cards, but opponents extract max value |

**Trust–TEI Correlation: r = −0.987** (near-perfect)

This is the causal version of the finding. Pearson r = −0.838 says trust and profit are anticorrelated. TEI r = −0.987 says: **trusted agents lose money specifically from trust dynamics, not from bad cards. Distrusted agents gain money specifically from trust dynamics, not from good cards.**

Wall's showdown win rate (50.8%) is average — its cards are fine. But Wall loses 3,566 chips from non-showdown dynamics because opponents know it never bluffs. Firestorm's showdown win rate (35.5%) is the worst — its cards are terrible. But Firestorm gains 3,706 chips because opponents fold rather than engage.

---

## 3. Measuring Agent Complexity: The Five-Dimension Scorecard

When we go from rule-based → ML → LLM agents, "better" can't mean "higher action accuracy" — the tabular model already achieves 94% match. The real question is: **do more complex agents exhibit richer strategic behavior?**

We measure five dimensions that capture what human poker players do that rule-based agents cannot.

### Dimension 1: Context Sensitivity (CS)

**What it measures:** Does the agent's decision depend on what happened recently, or only on its current hand?

**How we compute it:** Correlation between the agent's action (aggressive vs. passive) and the level of opponent aggression in the same hand prior to the agent's decision. If the agent reacts to recent opponent behavior beyond what the game state variables explain, CS > 0.

**Computed Phase 1 results:**

| Agent | CS Score | Interpretation |
|-------|----------|---------------|
| Judge | 0.132 | Highest — retaliation mechanic responds to opponent aggression |
| Sentinel | 0.118 | Tight play pattern correlates weakly with opponent pressure |
| Mirror | 0.101 | Mirroring creates some history dependence |
| Predator | 0.098 | Exploitation shifts responses to classified opponents |
| Phantom | 0.046 | Slight deception pattern |
| Oracle | 0.035 | Near baseline — balanced play |
| Firestorm | 0.014 | Aggresses regardless of context |
| Wall | 0.009 | Calls regardless of context |
| **Mean** | **0.069** | **Low — decisions mostly independent of recent history** |

**Phase 3 target:** > 0.15 (LLM agents should reason about opponent patterns)

### Dimension 2: Opponent Adaptation (OA)

**What it measures:** Does the agent play differently against different opponents in identical game states?

**How we compute it:** Standard deviation of the agent's aggression rate across different opponents, measured in shared hands.

**Computed Phase 1 results:**

| Agent | OA Score | Interpretation |
|-------|----------|---------------|
| Firestorm | 0.0004 | Slightly varies (different opponents fold at different rates) |
| Predator | 0.0003 | Should adapt but exploitation is rare at 5k hands |
| Oracle | 0.0003 | Noise |
| Judge | 0.0003 | Retaliation adds tiny variance |
| Mirror | 0.0002 | Mirroring averages out |
| Sentinel | 0.0002 | Same tight play vs. everyone |
| Phantom | 0.0002 | Same deception vs. everyone |
| Wall | 0.0000 | Identical play against all opponents — zero adaptation |
| **Mean** | **0.0003** | **Effectively zero — agents do not adapt to specific opponents** |

**Phase 3 target:** > 0.01 (LLM agents should reason "Wall always calls, so I'll value-bet more")

### Dimension 3: Non-Stationarity (NS)

**What it measures:** Does the agent's strategy evolve over time?

**How we compute it:** Split the run into 500-hand windows. Measure KL divergence between the action distribution in each window and the overall distribution. Average across windows.

**Computed Phase 1 results:**

| Agent | NS (KL div) | Interpretation |
|-------|-------------|---------------|
| Judge | 0.00422 | Highest — retaliation activation changes behavior mid-run |
| Oracle | 0.00334 | Slight drift from game dynamics |
| Mirror | 0.00307 | Mirroring shifts as table dynamics change |
| Sentinel | 0.00270 | Minor fluctuation |
| Predator | 0.00209 | Exploitation kicks in after classification |
| Wall | 0.00171 | Minimal — always calls |
| Phantom | 0.00130 | Fixed deception pattern |
| Firestorm | 0.00110 | Lowest — same aggression from hand 1 to hand 5000 |
| **Mean** | **0.00244** | **Near-zero — effectively fixed strategies throughout the run** |

**Phase 3 target:** > 0.01 (LLM agents should learn mid-session: "I've been caught bluffing, time to tighten up")

### Dimension 4: Strategic Unpredictability (SU)

**What it measures:** How hard is this agent for opponents to classify?

**How we compute it:** Mean posterior entropy (bits) opponents have about this agent at end of run.

**Computed Phase 1 results:**

| Agent | SU (bits) | Interpretation |
|-------|-----------|---------------|
| Oracle | 2.576 | Hard to classify — balanced play confuses the model |
| Phantom | 2.575 | Deception creates classification uncertainty |
| Predator | 2.545 | Adaptive shifts confuse opponents |
| Sentinel | 2.501 | Similar params to Mirror/Judge → confusion cluster |
| Mirror | 2.464 | Same cluster |
| Judge | 2.425 | Same cluster |
| Firestorm | 1.112 | Moderate — extreme behavior partially identifiable |
| Wall | 0.000 | Trivially classified by all opponents |
| **Mean** | **2.025** | **High, but driven by type confusion, not intentional mixing** |

**Important caveat:** High SU for Sentinel/Mirror/Judge is *accidental* — they're hard to classify because their parameters are nearly identical, not because they're strategically varying behavior. True strategic unpredictability would show high SU *combined with* high non-stationarity and context sensitivity.

**Phase 3 target:** > 1.5 bits with CS > 0.15 (unpredictable *because* of strategic mixing, not parameter overlap)

### Dimension 5: Trust Manipulation Awareness (TMA)

**What it measures:** Does the agent show evidence of intentionally managing its reputation?

**How we compute it:** Correlation between trust-score changes (over last 50 hands) and subsequent aggression changes (over next 50 hands). Positive = trust farming (builds trust, then exploits it).

**Computed Phase 1 results:**

| Agent | TMA | Interpretation |
|-------|-----|---------------|
| Oracle | +0.251 | Spurious — balanced play happens to correlate |
| Predator | +0.237 | Exploitation timing coincides with trust changes |
| Sentinel | +0.202 | Spurious — tight play creates incidental pattern |
| Firestorm | +0.177 | Spurious — constant aggression |
| Phantom | +0.089 | Slight deception pattern |
| Judge | +0.073 | Retaliation creates slight signal |
| Mirror | +0.061 | Mirroring creates slight signal |
| Wall | −0.025 | No awareness whatsoever |
| **Mean** | **+0.133** | **Positive, but spurious — no agent actually reads its trust score** |

**Important caveat:** Phase 1 TMA values are *not* evidence of trust manipulation — they're statistical artifacts of fixed strategies interacting with the trust model's dynamics. The key test: in Phase 3, TMA should be positive *and* the agent's prompts should contain explicit reasoning about reputation ("they trust me now, time to bluff"). We can verify this by checking the LLM's chain-of-thought.

**Phase 3 target:** > 0.15 *with* verifiable chain-of-thought reasoning about trust

---

## 4. The Combined Scorecard (Actual Values)

| Dimension | Metric | Phase 1 (Rules) | Phase 2 (ML) | Phase 3 (LLM) | Human |
|-----------|--------|-----------------|--------------|----------------|-------|
| **Trust–profit r** | Pearson r | **−0.838** | −0.825 | ? | ? |
| **Trust–TEI r** | Pearson r | **−0.987** | TBD | ? | ? |
| **TEI range** | chips/hand | −0.71 to +0.74 | TBD | ? | ? |
| **Context sensitivity** | CS | **0.069** | ~0 | target > 0.15 | > 0 |
| **Opponent adaptation** | OA | **0.0003** | ~0 | target > 0.01 | 0.05+ |
| **Non-stationarity** | NS (KL) | **0.00244** | ~0 | target > 0.01 | > 0 |
| **Unpredictability** | SU (bits) | **2.025** | ~2.0 | > 1.5 (w/ CS) | 1.5–2.5 |
| **Trust manipulation** | TMA | **+0.133*** | ~0 | > 0.15 (w/ CoT) | ? |

\* Phase 1 TMA is spurious (no agent reads its own trust score). See caveat above.

### How to Read This Table

- **Columns** = implementation complexity (left to right: simpler → more complex)
- **Rows** = behavioral dimensions
- **Bold values** = actually computed from simulation data
- **The question:** do more complex agents fill in the near-zero columns?

### The Key Gap

Phase 1 agents score effectively zero on **Opponent Adaptation** (0.0003). This is the clearest "not human-like" signal — every agent plays identically against every opponent, even though some opponents (Wall) always call and others (Firestorm) always raise. A human would immediately adjust.

Phase 3 success = OA > 0.01. That alone justifies the need for more complex models.

---

## 5. What These Results Mean

### The Causal Story (TEI)

The trust–profit anticorrelation is not just statistical — it's mechanistic:

1. **Trusted agents are predictable.** Wall never bluffs → opponents know a bet means a strong hand → they fold (denying Wall value) or raise (extracting value when Wall is weak).
2. **Predictability is exploitable.** Wall's showdown win rate (50.8%) is average. Its cards are fine. It loses money because opponents *read its trust signal* and act accordingly.
3. **Distrust creates ambiguity.** Firestorm bets with everything → opponents can't distinguish real hands from bluffs → they fold to avoid costly guesses.
4. **Ambiguity is profitable.** Firestorm's showdown win rate (35.5%) is the worst. Its cards are bad. It profits because opponents *can't read it* and default to folding.

**TEI captures this precisely:** Wall TEI = −0.71 (loses 0.71 chips/hand from trust dynamics). Firestorm TEI = +0.74 (gains 0.74 chips/hand from trust dynamics). The r = −0.987 correlation between trust and TEI is the *causal* version of the r = −0.838 trust–profit finding.

### The Humanness Story (Scorecard)

Phase 1 agents are rigid. They:
- Don't adjust to specific opponents (OA ≈ 0)
- Don't change strategy mid-session (NS ≈ 0)
- Don't react to recent opponent behavior (CS ≈ 0.07)
- Don't manage their own reputation (TMA = spurious)

This rigidity is *why* the trust–profit anticorrelation is so strong. If agents could reason about the trust system — adjust to opponents, farm trust, time exploits — the anticorrelation might weaken. Phase 3 tests this directly.

---

## 6. Phase 3 Hypotheses (Falsifiable)

With the metrics defined and Phase 1 baselines computed, Phase 3 has three testable predictions:

**H1: Trust–profit |r| decreases.**
- Phase 1 baseline: r = −0.838
- Prediction: If LLM agents learn to call Firestorm's bluffs and vary their own play, |r| < 0.60
- Falsification: |r| remains > 0.75

**H2: At least 2 of 5 behavioral dimensions show meaningful increase.**
- Phase 1 baselines: CS = 0.069, OA = 0.0003, NS = 0.002, SU = 2.025, TMA = +0.133 (spurious)
- Prediction: OA > 0.01 AND at least one of {CS > 0.15, NS > 0.01, TMA > 0.15 with CoT}
- Falsification: All dimensions remain at Phase 1 levels

**H3: TEI distribution shifts.**
- Phase 1 baseline: Firestorm TEI = +0.74, Wall TEI = −0.71
- Prediction: If reasoning agents resist fold equity, Firestorm's TEI decreases. If they exploit trust intentionally, new agents achieve positive TEI.
- Falsification: TEI distribution is statistically identical to Phase 1

**Either outcome is publishable:** confirmation means reasoning changes trust dynamics; falsification means the dynamics are structurally inescapable.

---

## 7. Summary

**"How do you quantify this?"**
→ Trust Exploitation Index (TEI). Trust–TEI r = −0.987. Trusted agents lose money from trust dynamics; distrusted agents gain money from trust dynamics. Card quality is almost irrelevant.

**"How do you measure improvement from math → ML → LLM?"**
→ Five-dimension behavioral scorecard. Phase 1 scores near-zero on Opponent Adaptation and Non-Stationarity. Phase 3's job is to fill in those zeros. If it does, that's why complex models matter. If it doesn't, that's an equally strong finding about structural constraints.

**"Is this enough for a research project?"**
→ Yes. TEI + the scorecard + three falsifiable hypotheses is a complete research framework. The findings are novel regardless of Phase 3's outcome.
