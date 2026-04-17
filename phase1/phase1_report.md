# Phase 1 Complete Report: Multi-Agent Trust Dynamics in 8-Player Limit Hold'em

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Dataset:** v3 — 500,000 hands across 20 seeds (25,000 hands/seed)
**Codebase:** 9,569 lines of Python + 1,927-line HTML visualizer

---

## 1. Project Overview

### 1.1 Research Question

How does trust emerge, evolve, and collapse in a multi-agent strategic environment where deception is a legitimate tool, information is incomplete, and reputation must be inferred from noisy behavioral signals?

This project formalizes trust as a Bayesian belief system and studies it in the context of 8-player Limit Texas Hold'em poker, where eight rule-based archetype agents — each embodying a distinct strategic philosophy from game theory and behavioral economics — play hundreds of thousands of hands against each other. Every agent maintains a probability distribution over every other agent's type, updating beliefs after every observed action. The resulting dataset of 28 million trust snapshots constitutes a machine-learning-ready corpus for Phase 2 classifier training.

### 1.2 What Was Built

Phase 1 is a complete simulation pipeline:

1. **Game Engine** — A faithful implementation of 8-player Limit Texas Hold'em with seeded RNG, action broadcasting, and per-hand lifecycle hooks.
2. **Eight Archetype Agents** — Five static agents (Oracle, Sentinel, Firestorm, Wall, Phantom) and three adaptive agents (Predator, Mirror, Judge), each parameterized by per-round probability tables.
3. **Bayesian Trust Model** — Per-opponent posterior distributions over 8 archetype types, updated via precomputed likelihood tables with trembling-hand noise (ε = 0.05) and exponential decay (λ = 0.95).
4. **Data Pipeline** — SQLite persistent logging (6 tables), ML-ready CSV exports (3 files per seed), and JSON export for a browser-based replay visualizer.
5. **Analysis Framework** — A 9-section standard report and a 31-section deep analysis with a 5-dimension simulation quality scorecard.
6. **Replay Visualizer** — A 1,927-line single-file HTML viewer with Trust Lens, Heatmap, and Stats modes.

### 1.3 Key Inspirations

- **Nicky Case's "The Evolution of Trust"** — An interactive exploration of iterated Prisoner's Dilemma strategies. The eight archetypes map directly to Case's characters: Oracle ≈ baseline, Sentinel ≈ Always Cooperate (with aggression), Firestorm ≈ Always Cheat, Wall ≈ Always Cooperate (passive), Phantom ≈ Detective (partial), Predator ≈ Detective, Mirror ≈ Copycat, Judge ≈ Grudger.
- **Robert Axelrod's "The Evolution of Cooperation"** — Tournament analysis showing that strategies which are *nice* (cooperate first), *retaliatory* (punish cheating), *forgiving* (return to cooperation), and *clear* (easy to understand) tend to win. The Mirror agent embodies all four properties.

### 1.4 Three-Phase Plan

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Rule-based archetype agents play Limit Hold'em; Bayesian trust model tracks beliefs; produce ML-ready dataset | **Complete** (this report) |
| **Phase 2** | Train ML classifiers on Phase 1 trust snapshots; replace rule-based agents with learned agents; compare trust dynamics | Planned |
| **Phase 3** | LLM-generated agents with natural language reasoning; study whether language-capable agents develop richer trust dynamics | Planned |

### 1.5 Iteration History Summary

| Version | Hands | Key Changes | Headline Finding |
|---------|-------|-------------|-----------------|
| **v1** | 200,000 (20×10k) | Initial run | Mirror VPIP 59.8% (broken — calling station), Phantom VPIP 19.8% (broken — too tight) |
| **v2** | 200,000 (20×10k) | Mirror 0.6/0.4 blend fix, Phantom weak_call tuned | Trust-profit anticorrelation r = −0.748; Firestorm still dominant at 7,149 stack |
| **v3** | 500,000 (20×25k) | Judge per-opponent retaliation via `_bluff_candidates` | Trust-profit r = −0.770; Firestorm 17,862 stack; Judge AF drops from 2.71 to 1.39 |

---

## 2. Game Environment

### 2.1 Why Limit Hold'em

Limit Hold'em was chosen over simpler games (Kuhn Poker, Leduc Hold'em) and more complex games (No-Limit Hold'em) for three reasons:

1. **Fixed bet sizes** eliminate bet-sizing as a signal dimension, isolating *action choice* (fold/check/call/bet/raise) as the sole observable behavior. This simplifies the trust model's likelihood function.
2. **Bet cap** (4 bets per round) bounds the maximum pot size per hand, preventing catastrophic single-hand losses that would dominate the economic signal.
3. **8-player tables** create a rich multi-agent environment where third-party observation, reputation cascades, and coalition dynamics can emerge — phenomena absent in heads-up games.

### 2.2 Complete Rules as Implemented

**Players:** 8 agents seated at fixed positions (seats 0–7). All agents participate in every hand.

**Deck:** Standard 52 cards using `treys.Card` integer format, shuffled by `numpy.random.Generator` (seeded per-table for reproducibility). Each hand gets a fresh shuffle.

**Blinds:**
- Small Blind (SB) = 1 chip, posted by seat (dealer + 1) mod 8
- Big Blind (BB) = 2 chips, posted by seat (dealer + 2) mod 8

**Bet Sizes:**
- Preflop and Flop: small bet = 2 chips
- Turn and River: big bet = 4 chips

**Bet Cap:** 4 total bets+raises per betting round (1 initial bet + 3 raises). At cap, players may only call or fold; a RAISE at cap is silently downgraded to CALL.

**Dealing Order:**
- Hole cards: 2 per player, dealt clockwise starting left of dealer
- Community cards: Flop (3), Turn (1), River (1)

**Action Order:**
- **Preflop:** Under-the-gun (UTG = dealer + 3) clockwise to Big Blind. BB has the "option" to raise if action checks around.
- **Post-flop:** Left of dealer (dealer + 1) clockwise.

**Raise Reopens Action:** When a player bets or raises, all other players must act again (the `acted` set resets to only the raiser, and `to_act` is rebuilt from the next seat clockwise). This ensures every player has the opportunity to respond to new aggression.

**BB Option:** Preflop, the BB has already posted 2 chips. If action folds or calls to the BB with no raise, `cost_to_call = 0`. The agent can CHECK (end the round) or BET/RAISE (which reopens action). If the agent returns BET when `current_bet > 0`, it's auto-upgraded to RAISE.

**Showdown:** When 2+ players remain after the river betting round, all remaining players reveal hole cards. Best 5-card hand from 7 cards (2 hole + 5 community) wins. Ties split the pot evenly; remainder goes to the player closest to the left of the dealer. Hand evaluation uses `treys.Evaluator` where lower rank = better hand (1 = Royal Flush, 7462 = worst high card).

**Walkover:** When all but one player folds, the last remaining player wins the pot. Hole cards are NOT revealed.

**Action Visibility:** ALL actions by ALL players are visible to ALL agents. Every `ActionRecord` is broadcast to every seat via `observe_action()`. Showdown data (revealed hole cards + hand ranks) is broadcast to all 8 agents via `observe_showdown()`, including those who folded.

**Card Visibility:** Hole cards are private. They are ONLY revealed at showdown. Folded players' cards are never shown.

### 2.3 Hand Strength Bucketing

All archetype decision policies reference three hand-strength buckets:

| Bucket | Equity Threshold | Description | Preflop Examples |
|--------|-----------------|-------------|-----------------|
| **Strong** | > 66% vs random | Premium hands, top pair strong kicker, sets+ | AA, KK, QQ, JJ, AKs, AKo, AQs (7 combos) |
| **Medium** | 33%–66% vs random | Mid pairs, draws, suited connectors | TT–77, AJs–ATs, KQs–JTs, suited aces, 98s–65s (25 combos) |
| **Weak** | < 33% vs random | No pair, no draw, low cards | Everything else (~137 combos) |

**Preflop:** Deterministic lookup from the 169 canonical hand types (defined in `preflop_lookup.py`). No Monte Carlo needed.

**Post-flop:** Monte Carlo equity estimation with 1,000 random rollouts per evaluation. For each rollout: deal random opponent hole cards + remaining community cards, evaluate both hands with `treys.Evaluator`, count wins (my_rank < opp_rank) and ties (half credit). Win percentage determines bucket.

**Caching:** `BaseAgent` caches hand strength per (agent, betting_round) in `_hs_cache`, cleared at `on_hand_start`. Each agent pays the Monte Carlo cost at most once per street, not once per decision.

### 2.4 Stack and Rebuy Mechanics

- **Starting stack:** 200 chips (100 big blinds)
- **Rebuy:** When an agent's stack reaches 0, they receive a fresh 200-chip stack at the start of the next hand. The `rebuys` counter increments.
- **Chip conservation invariant:** At all times, `sum(stacks) + sum(rebuys) × 200 == num_seats × 200 + sum(rebuys) × 200`. This is verified after every seed in `run_sim.py`.
- **No side pots:** The engine does not implement side pots for short-stacked all-in situations. With 200-chip stacks and a maximum of 48 chips per hand (4 rounds × 4 bets × 4 chips at big-bet streets, less in practice due to small-bet streets), this is adequate.

### 2.5 Seating Arrangement

Fixed seats for reproducibility. Seat 0 is the first dealer.

| Seat | Agent | Archetype | Classification |
|------|-------|-----------|---------------|
| 0 | The Oracle | oracle | Nash Equilibrium |
| 1 | The Sentinel | sentinel | Tight-Aggressive (TAG) |
| 2 | The Firestorm | firestorm | Loose-Aggressive (LAG) |
| 3 | The Wall | wall | Passive / Calling Station |
| 4 | The Phantom | phantom | Deceiver |
| 5 | The Predator | predator_baseline | Exploiter (adaptive) |
| 6 | The Mirror | mirror_default | Tit-for-Tat (adaptive) |
| 7 | The Judge | judge_cooperative | Grudger (adaptive) |

---

## 3. The Eight Archetypes

Each agent inherits from `BaseAgent` (434 lines) and overrides only `get_params(betting_round, game_state) -> dict`. The base class handles all decision logic, stat tracking, and trust model updates. Static agents return fixed parameter dictionaries; adaptive agents compute parameters dynamically based on posteriors, opponent stats, or grievance state.

### 3.1 The Oracle — Nash Equilibrium (Seat 0)

**Personality:** The Oracle plays the mathematically balanced strategy. No personality, no adaptation. It cannot be exploited, but it cannot exploit others. It is the control group — every other archetype's performance is measured against it.

**Ncase Parallel:** Baseline. Neither cooperates nor defects — plays the exact ratio where opponents are indifferent.

**Decision Logic:** `Oracle.get_params()` returns `ARCHETYPE_PARAMS["oracle"][betting_round]` — a fixed dict per round.

**Per-Round Parameters:**

| Round | BR | VBR | CR | MBR | strong_raise | strong_call | med_raise | weak_call |
|-------|-----|------|-----|------|-------------|------------|-----------|-----------|
| Preflop | 0.33 | 0.95 | 0.33 | 0.50 | 0.60 | 0.35 | 0.05 | 0.15 |
| Flop | 0.33 | 0.90 | 0.33 | 0.45 | 0.60 | 0.35 | 0.05 | 0.15 |
| Turn | 0.33 | 0.85 | 0.33 | 0.40 | 0.55 | 0.38 | 0.05 | 0.12 |
| River | 0.33 | 0.80 | 0.33 | 0.35 | 0.50 | 0.40 | 0.05 | 0.10 |

**Expected Behavior:** VPIP 22–25%, moderate bluff rate (BR=0.33), balanced calling. Deception ratio BR/VBR ≈ 0.37 — bets are moderately correlated with strength.

**Measured Behavior (v3, 500k hands):** VPIP = 21.6%, PFR = 6.1%, AF = 1.18, SD% = 5.6%, SD Win% = 51.6%.

**Trust Profile:** Trust received = 0.758, entropy = 2.250. Correctly identified by observers 52.1% of the time (73/140 observer-seed pairs). Often confused with predator_baseline and mirror_default due to overlapping moderate parameters.

**Economic Performance:** Mean stack = 3,091 (2nd place). 0.6 mean rebuys. Fold equity = 68.5%. Profits primarily from value betting against loose opponents.

### 3.2 The Sentinel — Tight-Aggressive / TAG (Seat 1)

**Personality:** Discipline and selective aggression. Picks battles carefully — when it raises, it has the goods. In Axelrod's terminology, "nice" — never cheats first, never initiates deception. The most trustworthy archetype.

**Ncase Parallel:** Always Cooperate (with selective aggression). Cooperates by default through honest play but strikes hard with strength.

**Per-Round Parameters:**

| Round | BR | VBR | CR | MBR | strong_raise | strong_call | med_raise | weak_call |
|-------|-----|------|-----|------|-------------|------------|-----------|-----------|
| Preflop | 0.10 | 0.95 | 0.40 | 0.30 | 0.65 | 0.30 | 0.05 | 0.10 |
| Flop | 0.10 | 0.90 | 0.35 | 0.25 | 0.60 | 0.35 | 0.05 | 0.08 |
| Turn | 0.08 | 0.90 | 0.30 | 0.20 | 0.55 | 0.38 | 0.03 | 0.06 |
| River | 0.05 | 0.85 | 0.25 | 0.15 | 0.50 | 0.40 | 0.02 | 0.04 |

**Measured Behavior (v3):** VPIP = 16.2%, PFR = 4.1%, AF = 1.07, SD% = 5.1%, SD Win% = 54.9%.

**Trust Profile:** Trust received = 0.784, entropy = 2.282. **Never correctly identified** — 0/140 accuracy. Observers' top guess is "oracle" (61/140) or "mirror_default" (38/140). The Sentinel is indistinguishable from the moderate cluster because its average BR (0.083) is nearly identical to mirror_default (0.088) and judge_cooperative (0.083).

**Economic Performance:** Mean stack = 2,797 (4th place). 0.5 mean rebuys. Fold equity = 69.6%. Reliable but not dominant.

### 3.3 The Firestorm — Loose-Aggressive / LAG (Seat 2)

**Personality:** Maximum aggression. Plays too many hands, bets too often, calls too frequently. The pressure cooker of the table. In Case's framework, "Always Cheat" — constantly applies pressure, never concedes.

**Ncase Parallel:** Always Cheat. Bets regardless of hand strength, flooding the signal channel with noise. Deception ratio BR/VBR ≈ 0.625/0.938 = 0.67 — bets weakly correlated with strength.

**Per-Round Parameters:**

| Round | BR | VBR | CR | MBR | strong_raise | strong_call | med_raise | weak_call |
|-------|-----|------|-----|------|-------------|------------|-----------|-----------|
| Preflop | 0.70 | 0.98 | 0.70 | 0.80 | 0.75 | 0.23 | 0.25 | 0.40 |
| Flop | 0.65 | 0.95 | 0.65 | 0.75 | 0.70 | 0.27 | 0.20 | 0.35 |
| Turn | 0.60 | 0.92 | 0.60 | 0.70 | 0.65 | 0.30 | 0.18 | 0.30 |
| River | 0.55 | 0.90 | 0.55 | 0.65 | 0.60 | 0.33 | 0.15 | 0.25 |

**Measured Behavior (v3):** VPIP = 49.4%, PFR = 12.0%, AF = 1.12, SD% = 14.8%, SD Win% = 38.5%.

**Trust Profile:** Trust received = 0.435 (lowest), entropy = 0.822 (second-lowest — high confidence in classification). Correctly identified 67.1% of the time (94/140) with avg probability 0.882. When misclassified, confused only with phantom.

**Economic Performance:** Mean stack = **17,862** (1st place by 5.8x over 2nd). 0.1 mean rebuys. **Fold equity = 87.1%** — the highest at the table. 102,055 walkovers (30.8% of all walkovers). Showdown win rate is the *worst* at 38.5% — the Firestorm rarely wins when cards are revealed. Its entire profit comes from opponents folding to aggression.

### 3.4 The Wall — Passive / Calling Station (Seat 3)

**Personality:** The immovable object. Never bluffs, never raises — but never folds either. Absorbs aggression by calling down every bet. Simultaneously the most trustworthy and most exploitable archetype.

**Ncase Parallel:** Always Cooperate (passive). Near-zero bluff rate means its rare bets are perfectly reliable signals. But passivity means it never punishes opponents and becomes an ATM for value-bettors.

**Per-Round Parameters:**

| Round | BR | VBR | CR | MBR | strong_raise | strong_call | med_raise | weak_call |
|-------|-----|------|-----|------|-------------|------------|-----------|-----------|
| Preflop | 0.05 | 0.55 | 0.80 | 0.15 | 0.15 | 0.80 | 0.02 | 0.55 |
| Flop | 0.05 | 0.50 | 0.75 | 0.12 | 0.12 | 0.82 | 0.02 | 0.50 |
| Turn | 0.03 | 0.45 | 0.70 | 0.10 | 0.10 | 0.82 | 0.01 | 0.42 |
| River | 0.02 | 0.40 | 0.65 | 0.08 | 0.08 | 0.82 | 0.01 | 0.35 |

**Measured Behavior (v3):** VPIP = 53.9%, PFR = 1.5%, AF = 0.13, SD% = 23.1%, SD Win% = 49.0%.

**Trust Profile:** Trust received = **0.962** (highest — near-maximum). Entropy = 0.001 (near-zero — observers are virtually certain). **100% identification accuracy** — all 140 observer-seed pairs correctly identify it as "wall" with probability 1.000. The Wall is the most legible archetype in the simulation.

**Economic Performance:** Mean stack = **174** (7th of 8). **78.9 mean rebuys** (second-worst). Goes broke approximately every 316 hands. The Wall's high trust is economically useless — opponents know it's honest and value-bet it relentlessly.

### 3.5 The Phantom — Deceiver / False Signal Generator (Seat 4)

**Personality:** The liar who cannot take a punch. Bluffs aggressively (high BR) but folds to resistance (low CR). Generates false signals then vanishes. The most corrosive archetype for the table's trust ecosystem — it corrupts the information environment.

**Ncase Parallel:** Detective (partial). Probes with deception but lacks commitment. Deception ratio BR/VBR ≈ 0.525/0.575 = 0.91 — bets carry almost zero information about hand strength.

**Per-Round Parameters:**

| Round | BR | VBR | CR | MBR | strong_raise | strong_call | med_raise | weak_call |
|-------|-----|------|-----|------|-------------|------------|-----------|-----------|
| Preflop | 0.60 | 0.65 | 0.30 | 0.55 | 0.40 | 0.45 | 0.08 | 0.35 |
| Flop | 0.55 | 0.60 | 0.25 | 0.50 | 0.35 | 0.45 | 0.06 | 0.30 |
| Turn | 0.50 | 0.55 | 0.20 | 0.45 | 0.30 | 0.45 | 0.04 | 0.22 |
| River | 0.45 | 0.50 | 0.15 | 0.40 | 0.25 | 0.45 | 0.03 | 0.15 |

*Note:* `weak_call` was tuned in v2 (from spec's 0.10 to 0.35 preflop, decreasing to 0.15 river) to hit the spec's target VPIP of 35–45%. The decreasing pattern matches the Phantom's "bets but doesn't commit" personality — enters pots loosely then gives up on later streets.

**Measured Behavior (v3):** VPIP = 38.7%, PFR = 7.7%, AF = 0.67, SD% = 6.4%, SD Win% = 54.9%.

**Trust Profile:** Trust received = 0.667, entropy = 2.170. Correctly identified **92.1%** of the time (129/140) with avg probability 0.447. The Phantom is the second-most identifiable archetype after the Wall, despite its deceptive intent — the combination of high BR + low CR produces a distinctive behavioral signature.

**Economic Performance:** Mean stack = **129** (last place). **58.1 mean rebuys** — goes broke every ~430 hands. Fold equity = 53.1% (lowest at the table). The Phantom's strategy is economically catastrophic: it bluffs into opponents who don't fold (Wall, Firestorm) and folds to opponents who do bluff back.

### 3.6 The Predator — Exploiter / Shark (Seat 5, Adaptive)

**Personality:** The adaptive hunter. Observes, classifies, exploits. Against passive players it attacks; against aggressive players it traps. The only agent that actively uses its Bayesian posteriors to modify play.

**Ncase Parallel:** Detective. Probes opponents, classifies tendencies, shifts to exploitation.

**Baseline Parameters (pre-classification):**

| Round | BR | VBR | CR | MBR |
|-------|-----|------|-----|------|
| Preflop | 0.25 | 0.90 | 0.35 | 0.40 |
| Flop | 0.25 | 0.85 | 0.35 | 0.35 |
| Turn | 0.20 | 0.80 | 0.30 | 0.30 |
| River | 0.15 | 0.80 | 0.30 | 0.25 |

**Adaptation Mechanism:**

1. For each active opponent, read the posterior (8-element array from Stage 5).
2. Find the argmax archetype and its probability `max_prob`.
3. If `max_prob > 0.60` (classification threshold), compute `α = min(1.0, (max_prob − 0.60) / 0.30)`.
4. Select the opponent with the largest α (most confidently classified).
5. Blend: `params[key] = α × PREDATOR_EXPLOIT[target][round][key] + (1 − α) × baseline[key]`.

At 60% confidence → α = 0 (pure baseline). At 90% → α = 1.0 (full exploit). The exploit table adjusts per target type:
- vs Sentinel: bluff more (BR↑), call less (CR↓) — TAG folds too much
- vs Firestorm: stop bluffing (BR↓), call down (CR↑) — catch bluffs
- vs Wall: never bluff (BR↓), max value bet (VBR↑) — Wall never folds
- vs Phantom: call down bluffs, raise to exploit fold-to-raise

**Measured Behavior (v3):** VPIP = 18.5%, PFR = 4.1%, AF = 0.83. Plays baseline most of the time because only Wall (1.00) and Firestorm (~0.82) exceed the 0.60 classification threshold. 5 of 7 opponents get unmodified baseline play.

**Trust Profile:** Trust received = 0.765. Correctly identified only 30.0% of the time (42/140). Hardest adaptive agent to classify because its adaptation makes it look different to different observers.

**Economic Performance:** Mean stack = 1,125 (6th place). 2.7 mean rebuys. The Predator underperforms expectations because the classification threshold is too conservative for the moderate cluster — it exploits only 2 of 7 opponents.

### 3.7 The Mirror — Tit-for-Tat / Reciprocator (Seat 6, Adaptive)

**Personality:** Reflects what it receives. Honest play begets honest play; deception begets deception. Axelrod's tournament champion translated into poker. Four properties: *nice* (cooperates first via TAG defaults), *retaliatory* (mirrors aggression), *forgiving* (returns to defaults when opponent calms), *clear* (behavioral pattern is transparent).

**Ncase Parallel:** Copycat — Axelrod's Tit-for-Tat.

**Default Parameters:** Identical to `mirror_default` in archetype_params.py (TAG-like, similar to Sentinel).

**Mirroring Mechanism:**

1. `_observe_opponent_action()` tracks per-opponent rolling stats: observed_br, observed_vbr, observed_cr, observed_mbr, observed_vpip.
2. In `get_params()`, selects the single most-active opponent (highest `observed_vpip`) among currently active seats.
3. Blends 4 keys (br, vbr, cr, mbr): `blended[key] = 0.6 × target_observed + 0.4 × default`.
4. All facing-bet keys (`strong_raise`, `strong_call`, `med_raise`, `weak_call`) stay at defaults — the Mirror keeps a coherent TAG raise policy.
5. `weak_call` is explicitly NOT mirrored. Since ~80% of preflop hands are Weak, copying an opponent's call rate into weak_call would make the Mirror a calling station (the v1 bug).

**Measured Behavior (v3):** VPIP = 18.6%, PFR = 5.2%, AF = 0.88. Looks TAG-like in aggregate because the 40% anchor to defaults dominates.

**Trust Profile:** Trust received = 0.798. Correctly identified 47.9% of the time (67/140 as mirror_default). Harder to classify than static types because behavior varies by opponent context.

**Economic Performance:** Mean stack = 2,856 (3rd place). 0.6 mean rebuys. Fold equity = 58.6%. The Mirror's TAG-anchored reciprocity produces stable, moderate profits.

### 3.8 The Judge — Grudger / Punisher (Seat 7, Adaptive)

**Personality:** Starts as an ally but keeps a ledger. Cross the line and the verdict is permanent. No appeal, no parole. Tests the hypothesis that trust is a finite, non-renewable resource.

**Ncase Parallel:** Grudger. Cooperates until cheated past threshold, then defects forever against that specific opponent.

**Cooperative Parameters:** Identical to Sentinel (BR 0.10→0.05, VBR 0.95→0.85, CR 0.40→0.25).

**Retaliatory Parameters:** Aggressive bluffer with extremely low CR (BR 0.70→0.55, VBR 0.95→0.85, CR 0.15→0.08). Spite-based play designed to punish, not to maximize EV.

**Grievance Mechanism:**

1. `_observe_opponent_action()`: When the Judge hasn't folded this hand, any opponent BET or RAISE is buffered in `_bluff_candidates[seat]` with the betting round name.
2. `observe_showdown()`: For each revealed opponent in `_bluff_candidates`, compute hand strength via `_fast_bucket()` (deterministic, no Monte Carlo). If the bucket at any buffered round is "Weak", increment `grievance[seat]`. Max one increment per opponent per hand.
3. **Trigger:** When `grievance[seat] >= τ` (default τ = 5), `triggered[seat] = True` permanently. No decay, no forgiveness.
4. `get_params()`: Iterates `_bluff_candidates` (opponents who have bet/raised THIS hand). If any are triggered, return RETALIATORY_PARAMS. Otherwise COOPERATIVE_PARAMS.

**v3 Fix:** In v2, `get_params` checked `active_opponent_seats` (all seated players) — the Judge was retaliatory in ~69% of hands because Firestorm and Phantom are almost always present. In v3, it checks `_bluff_candidates` (only opponents who have actually bet/raised this hand), producing selective retaliation.

**Measured Behavior (v3):** VPIP = 15.9%, PFR = 4.4%, AF = 1.39. The AF of 1.39 (down from 2.71 in v2) reflects the v3 fix — cooperative play dominates, with retaliatory bursts when triggered opponents aggress.

**Trust Profile:** Trust received = 0.815 (highest among adaptive agents). **Never correctly identified** — 0/140 accuracy. Observers' top guess is "mirror_default" (71/140). The Judge's cooperative mode (identical to Sentinel params) makes it indistinguishable from the Sentinel/Mirror cluster.

**Economic Performance:** Mean stack = 1,995 (5th place). 0.8 mean rebuys. Fold equity = 70.9%. Profitable via selective aggression against known deceivers.

---

## 4. The Trust Model

The trust model is implemented in `trust/bayesian_model.py` (260 lines). It is identical for all 8 archetypes — static types compute it but don't use it; adaptive types use it to modify play.

### 4.1 Bayesian Framework

Each agent maintains a **posterior distribution** over 8 archetype types for every other agent at the table. Stored as `posteriors: Dict[int, np.ndarray]` where each value is a length-8 float64 array indexed by `TRUST_TYPE_LIST`:

```
["oracle", "sentinel", "firestorm", "wall", "phantom",
 "predator_baseline", "mirror_default", "judge_cooperative"]
```

Note: `judge_retaliatory` is not a separate type — the Judge's state-dependent behavior is captured by the `judge_cooperative` slot (which represents the Judge's average behavior weighted by how often it's in each state).

### 4.2 Prior

At hand 0, every posterior is uniform: `P(type_k) = 1/8 = 0.125` for all k. No agent has privileged information. Initialized lazily — `posteriors[seat]` is created on the first observation of that seat.

### 4.3 Likelihood Function

Precomputed at module import via `_build_tables()`:

- `_KNOWN_L`: shape (4 rounds × 3 buckets × 5 actions × 8 types) — used when the opponent's hand strength bucket is known (at showdown).
- `_MARGINAL_L`: shape (4 rounds × 5 actions × 8 types) — uniform marginal over buckets, used during live play when the bucket is unknown.

For each (round, bucket, action, type) combination, the likelihood is computed from the archetype's parameter table. Example: P(bet | firestorm, river, Weak) = BR_river_firestorm = 0.55.

### 4.4 Trembling Hand Noise (ε = 0.05)

```
P_adjusted(action | type_k) = (1 − ε) × P_type(action) + ε × P_random(action)
```

Where `P_random = 1 / num_available_actions` (2 for check/bet decisions, 3 for fold/call/raise decisions). This prevents single surprising actions from destroying established beliefs. Mathematically: even if a Sentinel bluffs once (BR=0.05), the adjusted likelihood is `0.95 × 0.05 + 0.05 × 0.5 = 0.0725`, not 0.05 — the trembling-hand floor keeps the Sentinel hypothesis alive.

### 4.5 Exponential Decay (λ = 0.95)

Applied once per hand in `BaseAgent.on_hand_end()`:

```
decayed_prior = prior ^ λ    (elementwise)
posterior = decayed_prior / sum(decayed_prior)
```

Effect: raises each probability to the 0.95 power, slightly flattening the distribution toward uniform. This lets new evidence dominate over old, enabling detection of behavioral shifts (e.g., when the Judge triggers retaliation). Half-life ≈ 14 hands.

### 4.6 Update Formula

Given an observed action by opponent at seat `s`:

```
1. Select likelihood: lk = _MARGINAL_L[round, action] if bucket unknown
                      lk = _KNOWN_L[round, bucket, action] if bucket known
2. Trembling hand:    adj_lk = (1 − ε) × lk + ε × (1/num_available)
3. Third-party:       if observer had folded: adj_lk = adj_lk ^ 0.8
4. Bayes' rule:       raw = prior × adj_lk    (elementwise)
5. Normalize:         posterior = raw / sum(raw)
```

### 4.7 Trust Score

```
T(A → B) = Σ P(B = type_k) × (1 − BR_k)
         = posterior · HONESTY_SCORES     (dot product)
```

Honesty scores: wall=0.962, sentinel=0.917, judge_coop=0.917, mirror=0.912, predator=0.787, oracle=0.670, phantom=0.475, firestorm=0.375.

Range: ~0.375 (certain it's Firestorm) to ~0.962 (certain it's Wall).

### 4.8 Posterior Entropy

```
H(A about B) = −Σ P_k × log₂(P_k)    where P_k > 0
```

Maximum = log₂(8) = 3.0 bits (total uncertainty). Minimum = 0 (complete certainty). Low entropy = confident classification. High entropy = confused.

### 4.9 Showdown Refinement

When showdown reveals an opponent's hole cards, `BaseAgent.observe_showdown()` replays that opponent's action log with the now-known hand-strength bucket:

1. For each buffered action, compute the bucket at the relevant street using `_fast_bucket(hole, community_slice)` — a deterministic rank-class lookup (no Monte Carlo).
2. Call `update_posterior()` with `bucket=known_bucket` instead of `bucket=None`.

This produces much sharper updates than live observations because the known bucket selects from `_KNOWN_L` (specific likelihoods) rather than `_MARGINAL_L` (averaged likelihoods).

### 4.10 Worked Example (from worked_examples.md)

**Setup:** Predator (seat 5) observing Firestorm (seat 2) after 60 hands. Current posterior: P(firestorm) = 0.51, P(phantom) = 0.28, others small. Trust = 0.500, Entropy = 2.14 bits.

**Observation:** Hand #61 — Firestorm bet the river with a WEAK hand (confirmed at showdown).

**Step 1 — Likelihood:** P(river bet with Weak | type_k) = BR_river for each type. Firestorm = 0.55, Phantom = 0.45, Oracle = 0.33, Sentinel = 0.05, Wall = 0.02.

**Step 2 — Trembling Hand:** `adj = 0.95 × raw + 0.05 × 0.50`. Firestorm: 0.5475, Wall: 0.0440.

**Step 3 — Decay Prior:** `prior^0.95`. P(firestorm): 0.51→0.5238, P(phantom): 0.28→0.2913.

**Step 4 — Multiply:** raw(firestorm) = 0.5238 × 0.5475 = 0.2868. raw(wall) = 0.0112 × 0.0440 = 0.0005.

**Step 5 — Normalize:** P(firestorm) = 0.2868/0.4519 = **0.635** (was 0.51 ↑). P(phantom) = 0.292 (was 0.28 ↑). P(sentinel) = 0.004 (was 0.02 ↓↓).

**Result:** Trust drops 0.500 → **0.435**. Entropy drops 2.14 → **1.81 bits**. The Predator is now close to the 0.60 classification threshold for activating the exploit strategy.

---

## 5. Data Pipeline

### 5.1 SQLite Schema

Six tables defined in `data/schema.sql` (104 lines):

| Table | Primary Key | Rows (v3) | Description |
|-------|------------|-----------|-------------|
| `runs` | run_id (auto) | 20 | One row per seed. Stores seed, num_hands, started_at, label, git_sha. |
| `hands` | (run_id, hand_id) | 500,000 | One row per played hand. Stores dealer, sb_seat, bb_seat, final_pot, had_showdown, walkover_winner. |
| `actions` | — (indexed) | 7,420,045 | One row per action. Stores seat, archetype, betting_round, action_type, amount, pot_before/after, stack_before/after, bet_count, current_bet. |
| `showdowns` | — (indexed) | 357,127 | One row per showdown participant. Stores hole_cards (JSON), hand_rank, won, pot_won. |
| `trust_snapshots` | — (indexed) | 28,000,000 | One row per (observer, target) pair per hand. 56 rows per hand (8×7). Stores trust, entropy, top_archetype, top_prob. |
| `agent_stats` | (run_id, seat) | 160 | One row per seat at run end. Stores cumulative stats: hands_dealt, vpip_count, pfr_count, bets, raises, calls, folds, checks, showdowns, showdowns_won, final_stack, rebuys. |

Indexes on `(run_id, hand_id)` for actions, showdowns, and trust_snapshots.

### 5.2 What Gets Logged Per Hand

`Table.play_hand()` → `Hand.play()` → `SQLiteLogger.log_hand()`:

1. Insert into `hands`: dealer, blinds, final_pot, showdown flag, walkover winner.
2. Insert into `actions`: one row per `ActionRecord` from `hand.action_log` (sequence_num preserves order).
3. If showdown: insert into `showdowns` one row per contender with hole_cards and hand_rank.
4. Insert into `trust_snapshots`: for each of 8 observers × 7 targets, capture trust_score, entropy, top_archetype (argmax), top_prob. 56 rows per hand.

All writes for one hand are wrapped in a single SQLite transaction for atomicity.

### 5.3 CSV Exports

Three CSV files per seed, written by `data/csv_exporter.py` (269 lines):

- **actions.csv** (18 columns): One row per action. Includes Oracle's (seat 0) trust/entropy snapshot of the acting seat at hand-end.
- **hands.csv** (16 columns): One row per hand. Includes mean_trust_into_seat_N for each of the 8 seats.
- **agent_stats.csv** (12 columns): One row per seat at run-end with VPIP%, PFR%, AF.

### 5.4 Visualizer JSON

`data/visualizer_export.py` (235 lines) serializes hands to a JS file loaded by the browser viewer:

```javascript
window.POKER_DATA = {
  "meta": { "stage": 6, "seed": 42, "num_hands": 100, "agents": [...] },
  "hands": [
    {
      "hand_id": 1, "dealer": 0, "actions": [...],
      "hole_cards": {"0": ["Ah", "Kd"], ...},
      "community": {"flop": [...], "turn": [...], "river": [...]},
      "trust_snapshot": {"0": {"1": 0.752, ...}},
      "entropy_snapshot": {"0": {"1": 2.8, ...}},
      "top_archetype_snapshot": {"0": {"1": ["oracle", 0.45]}}
    }
  ]
}
```

Written as `<script src="data.js">` for CORS-free `file://` access.

### 5.5 Data Volume (v3)

| Metric | Value |
|--------|-------|
| Seeds | 20 |
| Hands per seed | 25,000 |
| Total hands | 500,000 |
| Total actions | 7,420,045 (mean 14.8/hand) |
| Showdown entries | 357,127 |
| Showdown hands | 168,736 (33.7%) |
| Walkover hands | 331,264 (66.3%) |
| Trust snapshots | 28,000,000 (56/hand) |
| Database size | 2.49 GB |

---

## 6. Simulation Infrastructure

### 6.1 Run Configuration

The v3 production dataset uses:
- **Seeds:** 42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432
- **Hands per seed:** 25,000
- **Stage:** 6 (full 8-archetype roster)
- **Run time:** ~40 minutes per seed at ~10 hand/s, ~14 hours total

### 6.2 Reproducibility

All randomness flows through a single `numpy.random.Generator` seeded per-table:
1. `Table.__init__` creates `np.random.default_rng(seed)`.
2. This RNG is injected into every agent's `.rng` attribute.
3. Each hand creates a `Deck(rng=table_rng)` which shuffles using the shared generator.
4. Agent decisions use `self.rng.random()` for probability rolls.

Because the RNG is consumed sequentially and deterministically, two runs with the same seed produce byte-identical action logs, posteriors, and stacks.

### 6.3 Lifecycle Hooks

| Hook | When Called | What It Does |
|------|-----------|--------------|
| `on_hand_start(hand_num)` | Before each hand | Clears `_hs_cache`, resets per-hand flags, increments `hands_dealt`, applies lambda-decay to posteriors |
| `receive_hole_cards(cards)` | After dealing | Stores hole cards for hand-strength evaluation |
| `observe_action(record)` | After every action | Updates self-stats (VPIP/PFR dedup), runs Bayesian update on opponent posteriors, calls `_observe_opponent_action()` (Stage 6 hook) |
| `observe_showdown(data, cards)` | After showdown | Updates showdown stats, replays opponent actions with known buckets for posterior refinement |
| `on_hand_end(hand_num)` | After each hand | Applies lambda-decay to all posteriors, updates `saw_flop` counter |

### 6.4 Observer Pattern

Every action is broadcast to all 8 agents via `a.observe_action(record)` in `Hand._record()`. This happens inline during the hand — each action record is broadcast immediately after it occurs. At showdown, `a.observe_showdown(data, community_cards=cards)` sends revealed hole cards and hand ranks to all agents, including those who folded.

The `is_direct` flag distinguishes direct evidence (observer was still in the hand) from third-party evidence (observer had folded), applying a 0.8 weight exponent to third-party likelihoods.

### 6.5 Runner CLIs

| Script | Purpose | Key Arguments |
|--------|---------|--------------|
| `run_sim.py` (327 lines) | Main simulation → SQLite | `--seeds`, `--hands`, `--db`, `--stage` |
| `run_multiseed.py` (316 lines) | Multi-seed → CSV exports | `--seeds`, `--hands`, `--outdir`, `--stage` |
| `run_demo.py` (169 lines) | Visualizer data generation | `--stage`, `--hands`, `--seed` |
| `run_sensitivity.py` (363 lines) | Parameter sweeps (λ, ε, TPW) | `--param`, `--values`, `--seeds`, `--hands` |
| `smoke_test.py` (168 lines) | Pre-run validation | `--hands`, `--seed` |

---

## 7. Analysis Framework

### 7.1 Basic Analysis (`analyze_runs.py`, 487 lines, 9 sections)

| Section | Measures |
|---------|---------|
| 1. Overview | Row counts, seeds, hands/seed |
| 2. Performance | Cross-seed mean stack, rebuys, showdown win rate per archetype |
| 3. Behavior | VPIP, PFR, AF, SD% per archetype |
| 4. Trust | Mean trust received per archetype at final hand |
| 5. Predator | Posterior evolution at milestones (h100→h10000) |
| 6. Judge | Rolling preflop bet rate (retaliation detection) |
| 7. Pots | Pot size by archetype involvement |
| 8. Sanity | Chip conservation, orphan actions, trust completeness |
| 9. Convergence | Trust trajectory matrix over time (run 1) |

### 7.2 Deep Analysis (`deep_analysis.py`, 1,458 lines, 31 sections)

Sections 1–25 cover economics, behavior, action frequency, street aggression, position, showdowns, walkovers, pots, trust/entropy matrices, identification accuracy, convergence trajectories, Predator/Judge/Mirror deep dives, temporal dynamics, head-to-head matchups, trust-profit correlation, cross-seed consistency, bet sizing, bluff success, rebuys, and sanity checks.

Sections 26–31 form the **Simulation Quality Scorecard**:

| Dimension | Section | What It Measures |
|-----------|---------|-----------------|
| 1. Personality Fidelity | §26 | Fraction of 200-hand windows where VPIP/PFR/AF all fall in spec range |
| 2. Ecological Footprint | §27 | How much each agent's presence shifts others' bet rates |
| 3. Trust Signature Distinctiveness | §28 | Euclidean distance between trust trajectory curves |
| 4. Information Dynamics | §29 | Trust delta per hand (signal generation) + consumption roles |
| 5. Narrative Coherence | §30 | Count of significant "plot point" events per seed |

---

## 8. Key Findings (v3 — 500,000 hands, 20 seeds)

### 8.1 Trust-Profit Anticorrelation (r = −0.770)

The most striking result. Pearson correlation between mean trust received and mean final stack across 8 archetypes is strongly negative:

| Archetype | Mean Stack | Mean Trust Received |
|-----------|-----------|-------------------|
| Firestorm | 17,862 | 0.435 |
| Oracle | 3,091 | 0.758 |
| Mirror | 2,856 | 0.798 |
| Sentinel | 2,797 | 0.784 |
| Judge | 1,995 | 0.815 |
| Predator | 1,125 | 0.765 |
| Wall | 174 | 0.962 |
| Phantom | 129 | 0.667 |

**Interpretation:** Trustworthiness = predictability = exploitability. Honest agents (Wall, Sentinel) produce reliable signals that opponents can exploit. Deceptive agents (Firestorm) produce noisy signals that force opponents to fold. In Limit Hold'em, fold equity dominates card strength.

**Caveat:** n = 8 data points (one per archetype). The correlation is directionally robust across seeds but not statistically significant by conventional standards. The ordinal pattern (Firestorm > Oracle > Mirror > Sentinel > Judge > Predator >> Wall ≈ Phantom) is stable across all 20 seeds.

**Ncase Connection:** "Always Cooperate" (Wall) loses to "Always Cheat" (Firestorm) when cooperation means honesty and cheating means deception — exactly as Case's framework predicts for non-iterated environments. But the Mirror (Copycat), which Case predicts should win, finishes 3rd — suggesting that poker's information asymmetry weakens the reciprocity advantage.

### 8.2 Firestorm Fold Equity Dominance (87.1%)

The Firestorm's profit mechanism is entirely fold equity:

- **87.1%** of aggressive actions (bets/raises) win without showdown
- **38.5%** showdown win rate — worst at the table
- **102,055 walkovers** — 30.8% of all walkovers at the table
- The H2H matrix (Section 19) shows Firestorm loses chips at showdown to **every single opponent**: −84,950 vs Oracle, −92,244 vs Sentinel, −143,963 vs Wall

The Firestorm's profit is 100% fold equity, 0% card strength. It wins by making opponents fold, not by having better cards.

### 8.3 Bayesian Classification Ceiling (3 of 8 archetypes)

Only 3 archetypes are reliably identified by the trust model after 25,000 hands:

| Archetype | Accuracy | Avg Confidence | Classification |
|-----------|----------|---------------|---------------|
| Wall | 100.0% | 1.000 | Perfect |
| Phantom | 92.1% | 0.447 | High accuracy, moderate confidence |
| Firestorm | 67.1% | 0.882 | Moderate accuracy, high confidence |
| Oracle | 52.1% | 0.357 | Barely above chance |
| Mirror | 47.9% | 0.251 | Near-random |
| Predator | 30.0% | 0.337 | Below chance |
| Sentinel | 0.0% | — | Never correctly identified |
| Judge | 0.0% | — | Never correctly identified |

The moderate cluster (Oracle, Sentinel, Mirror, Predator, Judge) have overlapping average behavioral parameters. The Sentinel's avg BR = 0.083 is virtually identical to mirror_default (0.088) and judge_cooperative (0.083). The trust model cannot distinguish archetypes with near-identical action frequencies from marginal observations alone.

### 8.4 Personality Fidelity (75–99%)

All agents stay in character the vast majority of 200-hand windows:

| Archetype | Fidelity | In Range / Total |
|-----------|----------|-----------------|
| Mirror | 99.1% | 24,569 / 24,801 |
| Phantom | 98.1% | 24,332 / 24,801 |
| Firestorm | 97.6% | 24,194 / 24,801 |
| Judge | 92.5% | 22,949 / 24,801 |
| Predator | 92.2% | 22,866 / 24,801 |
| Sentinel | 90.8% | 22,531 / 24,801 |
| Oracle | 88.2% | 21,869 / 24,801 |
| Wall | 75.2% | 18,640 / 24,801 |

Wall's lower score is because its VPIP (53.9%) occasionally exceeds the spec ceiling (48–62% range upper bound in the personality zone definition).

### 8.5 Judge Retaliation (v3 — Selective)

The v3 Judge fix (`_bluff_candidates` instead of `active_opponent_seats`) produces measurably different behavior:

- **v2 Judge AF:** 2.71 (globally aggressive — retaliatory in ~69% of hands)
- **v3 Judge AF:** 1.39 (selectively aggressive — retaliatory only when triggered opponents actively bet)

Section 16 of the deep analysis shows the Judge's aggression rate never exceeds 0.231 in any 200-hand window (run 1), confirming cooperative play dominates. The per-opponent split shows the Judge is actually *less* aggressive when opponents aggress (0.46–0.53) than when they're passive (0.59–0.62) — because in hands with no triggered aggression, the Judge bets its own strong hands freely.

### 8.6 Narrative Coherence (65% ideal-range seeds)

Mean 32.6 events per seed (scaled for 25,000 hands). 65% of seeds fall in the "ideal" narrative range (21–37 events). Consistent events across all seeds: Wall classified within 100 hands, Firestorm classified by hand 200. Variable events: Phantom classification timing, Judge trigger timing.

### 8.7 Economic Hierarchy

Stable ranking across 20 seeds:

```
Firestorm (17,862) >> Oracle (3,091) ≈ Mirror (2,856) ≈ Sentinel (2,797) > Judge (1,995) > Predator (1,125) >> Wall (174) ≈ Phantom (129)
```

Cross-seed behavioral consistency is tight (VPIP σ ≈ 0.2–0.4%) but economic variance is wider (stack σ = 79–1,195), reflecting the high variance inherent in poker outcomes.

---

## 9. Iteration History

### 9.1 v1 — Broken Mirror and Phantom (200,000 hands, 20 × 10k)

**What was wrong:**
- **Mirror** had no blend — `get_params()` directly copied the most-active opponent's observed stats (1.0× weight). Against the Wall (observed_cr ≈ 0.70), the Mirror became a calling station: VPIP = 59.8%, AF = 0.40. Spec target: VPIP 15–40%, AF 1.5–4.0.
- **Phantom** had `weak_call = 0.10` across all streets. Since ~80% of preflop hands are Weak, the Phantom folded 90% of its hands: VPIP = 19.8%. Spec target: 35–45%.

**What happened:**
- Firestorm dominated (stack 6,721) because two passive agents (broken Mirror + broken Phantom) fed it chips via fold equity.
- Judge showed AF = 2.66 and PFR = 10.2% — retaliatory numbers, but the analysis couldn't detect the behavioral split because Section 6 only checked preflop bet rate.

### 9.2 v2 — Mirror + Phantom Fixed (200,000 hands, 20 × 10k)

**Fixes applied:**
- **Mirror:** 0.6/0.4 blend (`_MIRROR_WEIGHT = 0.6`). Four keys (br, vbr, cr, mbr) blended; `weak_call` stays at defaults. VPIP dropped from 59.8% → 18.3%, AF rose from 0.40 → 0.85.
- **Phantom:** `weak_call` tuned to 0.35 (preflop), decreasing to 0.15 (river). VPIP rose from 19.8% → 38.8%.

**What changed:**
- Firestorm STILL dominated (stack 7,149) — even with fixed opponents, 87.1% fold equity sustains profits.
- **Trust-profit anticorrelation discovered:** r = −0.748.
- Judge global AF = 2.71 — retaliatory against everyone because `get_params` checked `active_opponent_seats`.

**What stayed the same:**
- Wall and Phantom remain the biggest losers (174 and 129 stacks respectively).
- Bayesian classification ceiling: only Wall, Firestorm, and sometimes Phantom identifiable.

### 9.3 v3 — Judge Per-Opponent Fix (500,000 hands, 20 × 25k)

**Fix applied:**
- **Judge:** `get_params` now iterates `_bluff_candidates` (opponents who have bet/raised THIS hand) instead of `active_opponent_seats`. Retaliation only fires when a triggered opponent is actively pressuring.

**What changed:**
- Judge AF dropped from 2.71 → 1.39 (cooperative play dominates).
- Firestorm stack increased to 17,862 (benefit of 2.5× more hands for compounding).
- Trust-profit r strengthened slightly: −0.748 → −0.770.
- 500k hands (vs 200k) gave tighter cross-seed confidence intervals.

**What stayed the same:**
- The economic hierarchy is identical across all three versions.
- The classification ceiling (3/8 identifiable) is unchanged.
- Firestorm dominance is a robust, version-independent finding.

---

## 10. Known Limitations and Future Work

### 10.1 PFR and AF Below Spec

All archetypes show PFR and AF below the spec's expected ranges. The spec predicts Oracle PFR 18–22%, measured 6.1%. Cause: the spec's worked examples show weak hands NOT raising when facing a bet (only calling or folding), which produces PFR ≈ 1/3 of the spec's "weak hands raise at BR" interpretation. The implementation follows the worked examples. **Relative orderings are correct** (Firestorm PFR > Oracle PFR > Sentinel PFR > Wall PFR).

### 10.2 Mirror Single-Target Selection

The Mirror copies the single highest-VPIP opponent instead of blending across all opponents weighted by pot contribution (as the spec suggests for multi-way pots). Effect: sharper behavioral swings, less smooth reciprocity. The single-target approach was chosen for simplicity and determinism.

### 10.3 Judge Any-Triggered-Who-Aggressed

The Judge retaliates when ANY triggered opponent has bet/raised this hand, not per-opponent policy selection. It cannot play cooperative with Sentinel and retaliatory with Firestorm in the same hand. This is a simplification — the spec implies per-opponent behavior within a hand, but the parameter system returns a single dict per `get_params` call.

### 10.4 Predator Classification Threshold

The 0.60 threshold is too high for the moderate cluster. Only Wall (1.00), Firestorm (~0.82), and sometimes Phantom (~0.51) get classified. 5/8 opponents receive unmodified baseline play, limiting the Predator's exploitation potential.

### 10.5 No Side Pots

The engine doesn't implement side pots for short-stacked all-in situations. Adequate for 200-chip stacks with the small bet sizes in Limit Hold'em.

### 10.6 Trust Model Resolution Limit

Action-frequency-based Bayesian classification can't distinguish archetypes with overlapping moderate behavioral profiles. More expressive features (timing, bet sizing patterns, multi-street sequences) or discriminative models (neural nets) could improve resolution. This is the core opportunity for Phase 2.

### 10.7 Mirror-Judge Tragedy Not Strongly Manifested

The spec's headline prediction — that the Mirror's reflected aggression triggers the Judge's grievance threshold — doesn't manifest strongly because the v2 Mirror fix anchors 40% to TAG defaults, reducing reflected bluffs. The tragedy requires the Mirror to bluff in pots with the Judge, which the TAG anchor makes rare. This is itself a valid finding: with a cooperative anchor, tit-for-tat avoids triggering the grudger.

---

## 11. Codebase Map

| File | Lines | Purpose | Stage |
|------|-------|---------|-------|
| `engine/__init__.py` | 0 | Package marker | 2 |
| `engine/actions.py` | 50 | ActionType enum + ActionRecord dataclass | 2 |
| `engine/deck.py` | 98 | Seeded deck over treys.Card ints | 1 |
| `engine/evaluator.py` | 115 | Hand strength bucketing (preflop + Monte Carlo) | 1 |
| `engine/game.py` | 534 | Hand: deal, betting rounds, showdown | 2 |
| `engine/table.py` | 120 | Table: seats, dealer rotation, rebuys, hooks | 2 |
| `agents/__init__.py` | 0 | Package marker | 3 |
| `agents/base_agent.py` | 434 | Abstract agent + trust model + decide_action | 3/5 |
| `agents/oracle.py` | 37 | Nash Equilibrium (static) | 3 |
| `agents/sentinel.py` | 36 | Tight-Aggressive (static) | 4 |
| `agents/firestorm.py` | 39 | Loose-Aggressive (static) | 4 |
| `agents/wall.py` | 39 | Calling Station (static) | 4 |
| `agents/phantom.py` | 41 | Deceiver (static) | 4 |
| `agents/predator.py` | 95 | Exploiter (adaptive) | 6 |
| `agents/mirror.py` | 235 | Tit-for-Tat (adaptive) | 6 |
| `agents/judge.py` | 170 | Grudger (adaptive) | 6 |
| `agents/dummy_agent.py` | 67 | Scripted test agents | 2 |
| `trust/__init__.py` | 34 | Public API re-exports | 5 |
| `trust/bayesian_model.py` | 260 | Posterior updates, decay, trust/entropy | 5 |
| `data/__init__.py` | 0 | Package marker | 7 |
| `data/sqlite_logger.py` | 337 | SQLite persistence | 7 |
| `data/schema.sql` | 104 | DDL for 6 tables | 7 |
| `data/csv_exporter.py` | 269 | ML-ready CSV exports | 11 |
| `data/visualizer_export.py` | 235 | JSON/JS for browser viewer | 3 |
| `config.py` | 70 | All simulation parameters | 1 |
| `archetype_params.py` | 409 | Per-round probability tables | 3 |
| `preflop_lookup.py` | 168 | 169-hand preflop bucketing | 1 |
| `run_sim.py` | 327 | Main simulation runner | 7/8 |
| `run_multiseed.py` | 316 | Multi-seed CSV orchestration | 10 |
| `run_demo.py` | 169 | Visualizer data generator | 3 |
| `run_tests.py` | 274 | Stage-aware test runner | 1 |
| `run_sensitivity.py` | 363 | Parameter sweep runner | 12 |
| `smoke_test.py` | 168 | Pre-run validation | 6.1 |
| `stage_extras.py` | 1,586 | Additional test assertions | 2–11 |
| `test_cases.py` | 529 | Canonical test suites | 1–8 |
| `analyze_runs.py` | 487 | 9-section standard report | 8 |
| `deep_analysis.py` | 1,458 | 31-section deep analysis + scorecard | 8 |
| `visualizer/poker_table.html` | 1,927 | Browser replay viewer | 5/9 |
| **TOTAL** | **~11,500** | | |

---

## 12. How to Reproduce

### 12.1 Setup

```bash
git clone https://github.com/RachitAgrawal146/Poker_trust.git
cd Poker_trust
pip install -r requirements.txt   # treys + numpy
```

### 12.2 Smoke Test

```bash
python smoke_test.py
```

Expected: all 8 archetypes PASS, Judge grievance against Firestorm ≥ 5 (triggered), chip conservation PASS.

### 12.3 Small Demo

```bash
python run_demo.py --stage 6 --hands 100
```

Opens `visualizer/data.js`. Then open `visualizer/poker_table.html` in any browser (works over `file://`). Toggle Trust Lens / Heatmap / Stats views.

### 12.4 Full Simulation (single seed)

```bash
python run_sim.py --seeds 42 --hands 25000 --db test.sqlite --stage 6
```

Takes ~40 minutes. Produces SQLite database with ~370k actions, ~1.4M trust snapshots.

### 12.5 Analysis

```bash
python analyze_runs.py --db test.sqlite
python deep_analysis.py --db test.sqlite --out test_report.txt
```

### 12.6 Reassemble v3 Database

The v3 database is split into two LFS chunks on GitHub:

```bash
# Linux/Mac
cat research_data/runs_v3.sqlite.part_* > runs_v3.sqlite

# Windows
cmd /c "copy /b research_data\runs_v3.sqlite.part_00+research_data\runs_v3.sqlite.part_01 runs_v3.sqlite"
```

### 12.7 Run All Tests

```bash
python run_tests.py --stage all
```

Expected: all stages pass except two known aspirational failures in `test_cases.py` (Stage 5.3 Sentinel entropy and Stage 6.1 Predator classification count).

---

## 13. Glossary

### Poker Metrics

| Term | Definition |
|------|-----------|
| **BR** (Bluff Rate) | P(bet or raise \| hand = Weak). How often the agent bets when bluffing. |
| **VBR** (Value Bet Rate) | P(bet or raise \| hand = Strong). How often the agent bets for value. |
| **CR** (Call Rate) | P(call \| facing a bet). Willingness to call regardless of hand strength. |
| **MBR** (Medium Bet Rate) | P(bet \| hand = Medium). How often medium hands bet unprompted. |
| **VPIP** | Voluntarily Put money In Pot — % of hands where player calls or raises preflop (excludes forced blinds). |
| **PFR** (Pre-Flop Raise) | % of hands where player raises preflop. PFR ≤ VPIP always. |
| **AF** (Aggression Factor) | (bets + raises) / calls, post-flop. AF < 1 = passive, AF > 2 = aggressive. |
| **WTSD** | Went To ShowDown — % of hands (where player saw flop) that reached showdown. |
| **SD%** | Showdown percentage — fraction of total hands that reach showdown. |
| **W$SD** / **SD Win%** | Won money at Showdown — % of showdowns won. |
| **Fold Equity** | % of aggressive actions (bets/raises) that win without showdown. |
| **Walkover** | A hand where all opponents fold; winner's cards are not revealed. |
| **Deception Ratio** | BR / VBR. Near 0 = honest bets. Near 1 = bets are meaningless. |

### Trust Model Terms

| Term | Definition |
|------|-----------|
| **Posterior** | P(opponent = type_k) for k = 1..8. A probability distribution over archetype types. |
| **Prior** | The posterior before a new observation. Starts uniform (1/8 each). |
| **Likelihood** | P(observed action \| type_k). How probable the action is under each archetype hypothesis. |
| **Entropy** | H = −Σ P_k × log₂(P_k). Measures uncertainty. Max = 3.0 bits (uniform). Min = 0 (certain). |
| **Trust Score** | T = Σ P_k × (1 − BR_k). Expected honesty of opponent. Range: ~0.375 to ~0.962. |
| **Trembling Hand** (ε) | Noise floor preventing zero likelihoods. Default ε = 0.05. |
| **Lambda Decay** (λ) | Exponential forgetting. Prior^λ each hand. Default λ = 0.95. Half-life ≈ 14 hands. |
| **Third-Party Weight** | Exponent applied to likelihood when observer had folded. Default = 0.8. |
| **Showdown Refinement** | Replaying opponent actions with revealed hand-strength buckets for sharper updates. |

### Agent Mechanics

| Term | Definition |
|------|-----------|
| **Grievance Ledger** | Judge's per-opponent counter of confirmed bluffs at showdown. No decay. |
| **τ (tau)** | Grievance threshold. Default = 5. Triggers permanent retaliation. |
| **_bluff_candidates** | Judge's per-hand buffer of opponents who have bet/raised while Judge is still in hand. |
| **Classification Threshold** | Predator's 0.60 posterior probability required to begin exploitation. |
| **α (alpha)** | Predator's blend factor: min(1.0, (max_prob − 0.60) / 0.30). |
| **_MIRROR_WEIGHT** | 0.6 — fraction of target's observed behavior in Mirror's blend. |

### Scorecard Dimensions

| Term | Definition |
|------|-----------|
| **Personality Fidelity** | Fraction of 200-hand windows where VPIP, PFR, AF all fall within spec range. |
| **Ecological Footprint** | Mean absolute shift in other agents' bet rates when this agent is present vs absent. |
| **Trust Signature Distinctiveness** | Minimum Euclidean distance between this archetype's trust trajectory and any other's. |
| **Information Dynamics** | Average trust delta caused per hand interval (signal generation rate). |
| **Narrative Coherence** | Count of significant events (trust collapses, classifications, cascades) per seed. |

### Hand Strength

| Term | Definition |
|------|-----------|
| **Strong** | Equity > 66% vs random hand. Preflop: AA, KK, QQ, JJ, AKs, AKo, AQs. |
| **Medium** | Equity 33–66%. Preflop: TT–77, suited broadways, suited connectors, suited aces. |
| **Weak** | Equity < 33%. Everything else (~80% of starting hands). |
| **_fast_bucket** | Deterministic rank-class bucketing using treys evaluator (no Monte Carlo). Used at showdown. |

---

*End of Phase 1 Report.*
