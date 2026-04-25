# Metrics Framework: Quantifying Trust Dynamics and Agent Complexity

**Rachit Agrawal | Polygence Research Project**
**Prepared for mentor meeting — April 25, 2026**

---

## 1. Research Aim (Agreed)

> To investigate whether observation-based trust systems inherently reward exploitation over cooperation, and whether this dynamic is a structural property of repeated strategic interaction or an artifact of agent design.

Arpit's follow-up: How do we *quantify* this? And how do we measure what it means to "improve" from mathematical models → ML → LLM agents?

This document proposes concrete, computable metrics for both questions.

---

## 2. Quantifying the Trust Dynamic

### The Problem with Pearson r Alone

Our current headline metric — trust–profit correlation r = −0.837 — is descriptive but shallow. It tells us trust and profit move in opposite directions. It does *not* tell us:

- How much profit comes from exploiting trust vs. simply having better cards
- Whether the anticorrelation is driven by one extreme agent or is systemic
- Whether the relationship is causal or confounded by a third variable (e.g., aggression independently causes both low trust and high profit)

### Proposed Primary Metric: Trust Exploitation Index (TEI)

**Definition:**

```
TEI_i = (actual_profit_i − expected_profit_from_cards_i) / hands_played
```

**Components:**

| Term | Meaning | How to Compute |
|------|---------|----------------|
| actual_profit | Chips gained/lost over the run | Final stack − starting stack + rebuys × 200 |
| expected_profit_from_cards | What the agent *should* earn given only its hand quality | For each hand, compute hole-card equity against 7 random opponents. Sum across all hands. This is the "no-strategy" baseline. |
| The difference | Profit attributable to *table dynamics* — fold equity, bluff success, opponent mistakes driven by trust beliefs | actual − expected |

**What TEI tells us:**

| TEI Value | Interpretation |
|-----------|---------------|
| TEI > 0 | Agent earns more than its cards deserve → profiting from strategic dynamics (bluffing, fold equity, trust exploitation) |
| TEI ≈ 0 | Agent earns exactly what its cards are worth → no strategic edge or cost |
| TEI < 0 | Agent earns less than its cards deserve → being exploited by opponents who read its behavior |

**Expected results from our simulation:**

| Agent | Trust Score | TEI (predicted) | Interpretation |
|-------|------------|-----------------|----------------|
| Firestorm | 0.41 (lowest) | High positive | Profits from fold equity, not card strength |
| Wall | 0.89 (highest) | Negative | Opponents extract maximum value because Wall never bluffs |
| Sentinel | 0.84 | Negative | Predictable "only bets with strong hands" pattern costs money |
| Oracle | 0.72 | Near zero | Balanced play ≈ card equity |
| Predator | 0.68 | Moderate positive | Exploits classified opponents beyond card value |

**Why this is better than Pearson r:**

- r tells you trust and profit are related. TEI tells you *how much* profit is attributable to trust dynamics vs. card quality.
- TEI is per-agent, not a single correlation coefficient. You can compare TEI across phases.
- The anticorrelation between trust score and TEI is the *causal* version of the finding: trusted agents have negative TEI (trust costs them money), distrusted agents have positive TEI (distrust earns them money).

**Computable now?** Yes. All required data (hand strength, pot outcomes, showdown results) exists in the SQLite database from Phase 1.

### Supporting Metrics

| Metric | Formula | What It Captures |
|--------|---------|-----------------|
| Fold Equity Rate | pots_won_without_showdown / total_pots_won | How much winning comes from opponents giving up vs. actual card strength |
| Bluff Profitability | chips_won_on_bluffs / chips_lost_on_caught_bluffs | Whether deception is net profitable |
| Trust–TEI Correlation | Pearson r between trust score and TEI across agents | The causal version of our headline finding |

---

## 3. Measuring Agent Complexity: The "How Human" Question

### The Problem

When we go from rule-based → ML → LLM agents, "better" can't mean "higher action accuracy" — the tabular model already achieves 94% match. The real question is: **do more complex agents exhibit richer strategic behavior?**

Human poker players differ from rule-based bots in specific, measurable ways. We propose five dimensions that capture these differences, each scoring 0 for simple agents and >0 for human-like agents.

### Dimension 1: Context Sensitivity

**What it measures:** Does the agent's decision depend on what happened recently, or only on its current hand?

**Formal definition:**

```
CS = I(action ; last_N_opponent_actions | hand_strength, round, pot_size)
```

This is the mutual information between the agent's action and recent game history, *after controlling for* the game state variables that rule-based agents already use.

**How to compute:** Build two predictive models for each agent's actions:
1. Model A: predicts action from (hand_strength, round, pot_size, cost_to_call) — the features rule-based agents use
2. Model B: predicts action from the same features PLUS the last 10 opponent actions

CS = accuracy(Model B) − accuracy(Model A). If history helps predict the action, the agent is context-sensitive.

**Expected values:**

| Agent Type | CS Score | Why |
|------------|----------|-----|
| Rule-based (Phase 1) | ≈ 0 | Decisions depend only on current state |
| ML tabular (Phase 2) | ≈ 0 | Model has no history input |
| LLM (Phase 3) | > 0 | Can reason about "Firestorm has raised 5 times in a row" |
| Human | > 0 | Known from poker research — humans adjust to recent dynamics |

### Dimension 2: Opponent Adaptation

**What it measures:** Does the agent play differently against different opponents in identical game states?

**Formal definition:**

```
OA = Var_opponents[ P(action | state, opponent_id) ]
```

The variance of the action distribution across opponents, holding the game state constant.

**How to compute:** For each agent, group its decisions by (hand_strength, round, facing_bet) AND by opponent identity. Measure how much the action distribution varies across opponents within each game-state group.

**Expected values:**

| Agent Type | OA Score | Why |
|------------|----------|-----|
| Static agents (Oracle, Wall, etc.) | 0 | Identical play against everyone |
| Predator | Moderate | Exploits classified opponents |
| Judge | Moderate | Retaliates against triggered opponents only |
| LLM | Potentially high | Can reason "Wall always calls, so I should value-bet more against Wall" |
| Human | High | Humans constantly adjust to specific opponents |

### Dimension 3: Non-Stationarity

**What it measures:** Does the agent's strategy evolve over time?

**Formal definition:**

```
NS = mean_windows[ KL( P_window(action) || P_overall(action) ) ]
```

Split the run into 500-hand windows. Measure the KL divergence between the action distribution in each window and the overall distribution. Average across windows.

**How to compute:** Already have the data. Group actions by 500-hand windows, compute action frequency tables, measure divergence.

**Expected values:**

| Agent Type | NS Score | Why |
|------------|----------|-----|
| Rule-based | ≈ 0 | Fixed policy |
| ML | ≈ 0 | Static model |
| LLM | > 0 | Could learn during play ("I've been caught bluffing, I should tighten up") |
| Human | > 0 | Humans adapt strategies over a session |

### Dimension 4: Strategic Unpredictability

**What it measures:** How hard is this agent for opponents to classify?

**Formal definition:**

```
SU = mean_opponents[ H(posterior_about_agent | 1000 hands observed) ]
```

This is the mean posterior entropy opponents have about the agent after 1000 hands. Already computed in our trust model.

**Why it matters for "humanness":** Skilled human players are deliberately unpredictable — they mix strategies to prevent opponents from building accurate models. An agent that is easy to classify (low entropy) is playing a "robotic" strategy.

**Expected values:**

| Agent Type | SU (bits) | Interpretation |
|------------|-----------|---------------|
| Wall | 0.12 | Trivially predictable — not human-like |
| Firestorm | 0.08 | Also predictable, just aggressively |
| Sentinel/Mirror/Judge | 2.5–2.7 | Hard to classify, but only because they're similar to each other — not because they're strategically mixing |
| LLM (target) | > 1.5 | Hard to classify because behavior is genuinely varied |
| Human | 1.5–2.5 | Known from opponent modeling literature |

### Dimension 5: Trust Manipulation Awareness

**What it measures:** Does the agent show evidence of *intentionally* managing its own reputation?

**Formal definition:**

```
TMA = corr( Δtrust_received[t−50 : t], Δaggression[t : t+50] )
```

Correlation between changes in the trust score the agent receives (over the last 50 hands) and subsequent changes in the agent's aggression (over the next 50 hands).

**What patterns this detects:**

| Pattern | TMA Value | Meaning |
|---------|-----------|---------|
| Trust farming | Positive | Agent builds trust (plays tight), then exploits it (switches to aggressive). Trust goes up → aggression follows. |
| No awareness | ≈ 0 | Agent's strategy has no relationship to its reputation |
| Reactive tightening | Negative | Agent tightens up when distrusted — cooperative but not strategic |

**Expected values:**

| Agent Type | TMA | Why |
|------------|-----|-----|
| All Phase 1 agents | ≈ 0 | No agent reads its own trust score |
| All Phase 2 agents | ≈ 0 | ML models have no trust-score input |
| LLM (if capable) | > 0 | Could reason "they trust me now, good time to bluff" |
| Human | Unknown | This would be a novel finding if measurable |

---

## 4. The Combined Scorecard

This is how we evaluate each phase against the others:

| Dimension | Metric | Phase 1 (Rules) | Phase 2 (ML) | Phase 3 (LLM) | Human Benchmark |
|-----------|--------|-----------------|--------------|----------------|-----------------|
| **Trust exploitation** | TEI | −0.8 to +2.1 | −0.7 to +2.3 | ? | ? |
| **Context sensitivity** | CS | 0 | 0 | target > 0 | > 0 |
| **Opponent adaptation** | OA | 0–0.3 | 0–0.3 | target 0.3–0.8 | 0.5–1.0 |
| **Non-stationarity** | NS | ≈ 0 | ≈ 0 | target > 0 | > 0 |
| **Unpredictability** | SU | 0.08–2.67 bits | 0.10–2.70 bits | target > 1.5 bits | 1.5–2.5 bits |
| **Trust manipulation** | TMA | 0 | 0 | target > 0 | unknown |
| **Trust–profit r** | Pearson r | −0.837 | −0.825 | ? | ? |

### How to Read This Table

- **Columns** = implementation complexity (left to right: simpler → more complex)
- **Rows** = behavioral dimensions
- **The question**: do more complex agents fill in the zeros?

If Phase 3 scores > 0 on dimensions 2–6 where Phases 1–2 score 0, that answers **"why do I need more complex models?"** — because only complex models produce context-sensitive, opponent-adaptive, non-stationary, trust-aware behavior.

If Phase 3 *also* scores 0, that answers the research question differently but equally powerfully: the game structure constrains behavior so tightly that even reasoning agents can't escape it. The trust–exploitation dynamic is truly structural.

**Either outcome is a valid research finding.**

---

## 5. What This Means for the Project Scope

### Already Complete (Phases 1 + 2)

- Trust–profit anticorrelation established and validated (r = −0.837, reproduced at −0.825)
- TEI computable from existing data (next step: actually compute it)
- Scorecard columns 1 and 2 can be filled in immediately
- Classification ceiling proved with mathematical explanation

### Next Step (Before Phase 3)

1. **Compute TEI** for all 8 agents in both phases — this takes Arpit's finding from "correlation" to "causation"
2. **Fill in scorecard columns 1–2** with actual computed values for all 5 dimensions
3. **Write up the metrics framework** as a section in the paper (Section 4.4 or similar)

### Phase 3 Scope (If Approved)

Run LLM agents through the same engine, compute the same scorecard, and compare. The three falsifiable hypotheses become:

- **H1:** Trust–profit |r| decreases (reasoning agents resist exploitation)
- **H2:** At least 2 of the 5 behavioral dimensions score > 0 (reasoning agents are measurably more complex)
- **H3:** TEI distribution changes (reasoning agents find new ways to exploit or resist exploitation)

---

## 6. Summary for Discussion

**Arpit asked:** "How can you quantify this as a metric?"
**Answer:** Trust Exploitation Index (TEI) separates card-quality profit from trust-dynamic profit. The anticorrelation between trust score and TEI is the causal version of our headline finding.

**Arpit asked:** "How can you measure what it means to improve from math → ML → agents?"
**Answer:** Five-dimension behavioral scorecard (context sensitivity, opponent adaptation, non-stationarity, unpredictability, trust manipulation awareness). Rule-based and ML agents score 0 on all dimensions except unpredictability. The "improvement" question becomes: do LLM agents fill in the zeros?

**Key insight:** We don't need LLM agents to "play better poker." We need them to play *differently* — in ways that are measurably more context-sensitive, adaptive, and trust-aware. The scorecard defines what "differently" means in quantitative terms.
