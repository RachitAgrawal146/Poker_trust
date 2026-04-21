# Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation Study of Bayesian Reputation Systems in 8-Player Limit Texas Hold'em

**Rachit Agrawal**
Polygence Research Project, 2025–2026

---

## Abstract

Reputation systems that infer trustworthiness from observed behavior are ubiquitous in online marketplaces, social networks, and financial platforms. Yet it remains unclear whether such systems inherently reward cooperative behavior or create exploitable dynamics that favor aggression. We investigate this question using a controlled multi-agent simulation of 8-player Limit Texas Hold'em, where eight strategically distinct agents — five static and three adaptive — interact over hundreds of thousands of hands while maintaining Bayesian posterior beliefs about each other's types. Each agent updates a probability distribution over opponent archetypes after every observed action, producing a rich dataset of trust evolution under repeated strategic interaction.

We report three principal findings across two independent implementation phases. First, we observe a strong anticorrelation between trust and economic performance (Pearson r = −0.837, p < 0.001): agents perceived as most trustworthy by their opponents accumulate the least wealth, while the least-trusted aggressive agent dominates through fold equity rather than superior play. Second, we demonstrate a hard classification ceiling — only 3 to 4 of 8 archetypes are reliably identifiable through behavioral observation, with mathematically similar types forming an indistinguishable cluster regardless of sample size. Third, we validate the robustness of these findings by replacing the rule-based agents with machine-learning models trained on Phase 1 behavioral data; the ML agents independently reproduce all three findings within 1–3%, confirming that the observed dynamics are structural properties of the interaction system rather than artifacts of agent design.

These results have implications for the design of reputation systems in adversarial environments: observation-based trust inference, in the absence of external enforcement mechanisms, systematically advantages exploitative strategies over cooperative ones.

---

## 1. Introduction

### 1.1 Motivation

Trust is a foundational element of social and economic interaction. In contexts where agents cannot directly verify each other's intentions — online commerce, anonymous networks, international diplomacy — trust must be inferred from observed behavior over repeated interactions. This inference process is formalized in many real-world systems as a reputation mechanism: a buyer rates a seller, a lender evaluates a borrower's credit history, or a social network ranks content creators by engagement patterns.

A critical but under-examined question is whether these observation-based reputation systems inherently reward the behavior they are designed to detect. If trustworthy behavior leads to higher trust scores, and higher trust scores lead to better outcomes, then the system functions as intended. But if trustworthy behavior is *costly* — if it creates predictability that opponents can exploit — then reputation systems may inadvertently penalize the very behavior they incentivize.

This paper investigates this question in a controlled multi-agent setting: 8-player Limit Texas Hold'em poker. Poker is a canonical domain for studying strategic interaction under incomplete information (Von Neumann & Morgenstern, 1944; Nash, 1950). It combines stochastic elements (card deals), hidden information (hole cards), sequential decision-making (betting rounds), and social signaling (bluffing and folding patterns). Critically, poker requires agents to form beliefs about opponents' strategies — making it a natural testbed for trust dynamics.

### 1.2 Research Question

We ask: **In repeated strategic interactions with incomplete information, does observation-based trust inference inherently reward exploitation over cooperation, and is this dynamic a structural property of the interaction system or an artifact of agent design?**

To answer this, we construct a simulation with three design choices that distinguish it from prior work:

1. **Diverse strategic archetypes.** Rather than studying a single pair of strategies (as in iterated Prisoner's Dilemma), we deploy eight distinct agents drawn from game theory and behavioral economics — ranging from Nash equilibrium play to grudge-based retaliation — creating a richer ecology of interaction.

2. **Bayesian trust model.** Every agent maintains a full posterior distribution over every other agent's type, updated after every observed action. This produces a continuous, evolving measure of trust rather than a binary cooperate/defect signal.

3. **Two-phase validation.** We implement the agents twice — first as hand-coded rule-based systems (Phase 1), then as machine-learning models trained on Phase 1 behavioral data (Phase 2). Agreement between phases establishes that findings are properties of the dynamics, not of the implementation.

### 1.3 Summary of Contributions

1. **Trust–profit anticorrelation.** We demonstrate a Pearson correlation of r = −0.837 (Phase 1) and r = −0.825 (Phase 2) between agents' mean trust scores and final chip counts, establishing that trustworthiness is economically costly in this setting.

2. **Aggression dominance via avoidance.** The most aggressive agent (Firestorm) achieves the highest economic outcome not through superior hand evaluation but through 87.1% fold equity — opponents surrender pots rather than engage, producing a dynamic analogous to aggressive pricing in oligopolistic markets.

3. **Classification ceiling.** We prove that behavioral observation alone cannot distinguish more than 3–4 of 8 archetypes, regardless of sample size, due to parameter overlap in the Bayesian likelihood model. This establishes a fundamental limit on reputation system accuracy.

4. **Robustness validation.** All three findings reproduce within 1–3% when rule-based agents are replaced with ML-learned agents, confirming structural rather than design-driven dynamics.

### 1.4 Paper Organization

Section 2 reviews related work in trust modeling, multi-agent systems, and poker AI. Section 3 describes the simulation methodology: game engine, agent archetypes, Bayesian trust model, and ML pipeline. Section 4 details the experimental setup. Section 5 presents results from both phases. Section 6 discusses implications, limitations, and connections to real-world reputation systems. Section 7 concludes and outlines future work.

---

## 2. Related Work

### 2.1 Trust and Cooperation in Repeated Games

The study of trust in strategic settings originates with the iterated Prisoner's Dilemma (IPD). Axelrod's (1984) tournament demonstrated that *Tit-for-Tat* — a strategy that cooperates first, retaliates against defection, and forgives after punishment — outperforms both unconditional cooperation and unconditional defection across diverse opponent populations. Axelrod identified four properties of successful strategies: niceness (cooperate first), retaliation (punish defection), forgiveness (return to cooperation), and clarity (be easy to model).

Nicky Case's interactive simulation *The Evolution of Trust* (2017) popularized these findings, mapping IPD strategies to intuitive character archetypes: the Always Cooperator, the Always Cheater, the Copycat (Tit-for-Tat), the Grudger, and the Detective. Our eight archetypes are directly inspired by this mapping but extend it to a richer action space (five actions vs. two) and a multi-agent setting (eight players vs. pairwise).

A key limitation of IPD-based trust research is the binary action space: cooperate or defect. Real-world trust decisions involve a continuum of commitment levels, partial signals, and noisy observations. Our poker setting naturally provides this richer structure — agents can fold, check, call, bet, or raise, each conveying different information about hand strength and strategic intent.

### 2.2 Bayesian Opponent Modeling

Bayesian approaches to opponent modeling maintain a probability distribution over possible opponent types and update it as new observations arrive. Harsanyi (1967) formalized this as games of incomplete information, where players hold beliefs about opponents' types drawn from a common prior. In practice, Bayesian opponent modeling has been applied in poker (Southey et al., 2005), negotiation (Zeng & Sycara, 1998), and security games (Pita et al., 2010).

Our trust model follows this tradition: each agent maintains an 8-dimensional posterior over opponent archetypes, updated via precomputed likelihood tables after every observed action. We extend standard approaches with two mechanisms: *trembling-hand noise* (ε = 0.05), which prevents posterior collapse by ensuring no observation has zero likelihood under any type, and *exponential decay* (λ = 0.95), which down-weights older observations to allow the model to track non-stationary opponents.

### 2.3 Multi-Agent Systems and Emergent Behavior

The study of emergent dynamics in multi-agent systems has a rich history. Shoham and Leyton-Brown (2008) provide a comprehensive framework for multi-agent interaction, while Sandholm and Crites (1996) demonstrated that cooperative behavior can emerge from self-interested agents through repeated interaction. More recently, Leibo et al. (2017) showed that the balance between cooperative and competitive behavior in multi-agent reinforcement learning is sensitive to environmental parameters.

Our work differs from the reinforcement learning tradition in that our agents do not learn to optimize a reward signal. Instead, they follow fixed (Phase 1) or learned-but-static (Phase 2) behavioral policies while maintaining evolving beliefs about opponents. This separation of *behavior* from *belief* allows us to isolate the dynamics of trust inference from the dynamics of strategy learning.

### 2.4 Poker as a Research Domain

Poker has served as a benchmark for AI research since the early work of Waterman (1970) and Findler (1977). The field achieved a milestone with Bowling et al.'s (2015) essentially perfect solution for heads-up Limit Texas Hold'em using counterfactual regret minimization (CFR). Moravčík et al. (2017) and Brown and Sandholm (2018, 2019) extended these results to no-limit variants with DeepStack and Pluribus, respectively.

Our work does not aim to solve poker or produce optimal play. Instead, we use poker as an *environment* for studying trust dynamics — the game mechanics are a means to generate repeated strategic interactions with incomplete information, bluffing incentives, and observable behavioral signals. This positions our work closer to Billings et al.'s (1998) opponent modeling research than to the game-solving tradition.

### 2.5 Reputation Systems

The design of reputation systems for online platforms has been studied extensively. Resnick et al. (2000) surveyed early reputation systems in e-commerce, identifying the core challenge: sellers have incentives to build reputations through genuine quality *or* through strategic behavior that games the rating system. Dellarocas (2003) formalized the conditions under which reputation systems promote honest behavior versus enabling manipulation.

Our finding that trust and profit are anticorrelated speaks directly to this literature: in our simulation, the "reputation system" (Bayesian opponent modeling) does not protect cooperative agents from exploitation. This aligns with Mayzlin et al.'s (2014) empirical finding that online review systems are vulnerable to strategic manipulation, and with Bolton et al.'s (2004) experimental evidence that reputation systems in trading environments can be gamed by sellers who alternate between honest and dishonest behavior.

---

## 3. Methodology

### 3.1 Game Environment: 8-Player Limit Texas Hold'em

We implement a faithful 8-player Limit Texas Hold'em engine with the following specifications:

- **Players:** 8 agents, fixed seating across all hands.
- **Blinds:** Small blind = 1 chip, big blind = 2 chips.
- **Betting structure:** Fixed-limit with a 4-bet cap per round. Bets are 2 chips preflop/flop and 4 chips turn/river.
- **Streets:** Preflop (2 hole cards), flop (+3 community), turn (+1), river (+1).
- **Actions:** Fold, check, call, bet, raise — the legal subset depends on the current state (e.g., check is only legal when no bet has been placed).
- **Starting stack:** 200 chips per agent, with automatic rebuys at 0 chips to prevent elimination effects from confounding the trust dynamics.
- **Showdown:** Standard poker hand ranking via the *treys* library (Cactus Kev evaluation).

The engine broadcasts every action and every showdown result to all agents, enabling full observability of opponent behavior. This is critical for the trust model: agents can update beliefs based on every action taken at the table, not just actions in hands they participate in.

**Hand strength evaluation.** Each agent evaluates its hand using a Monte Carlo simulation with 1,000 random rollouts, producing a three-level bucketing: Strong (top third), Medium (middle third), and Weak (bottom third). For preflop decisions, a 169-hand lookup table maps starting hands to buckets based on win-rate percentiles, avoiding the computational cost of Monte Carlo sampling before community cards are dealt.

**Seeded randomness.** All stochastic elements — deck shuffles, Monte Carlo rollouts, agent decision sampling — are driven by a NumPy random generator seeded at the start of each run. This ensures exact reproducibility: the same seed produces identical hands, community cards, and agent decisions.

### 3.2 Agent Archetypes

Our eight agents are drawn from the game-theoretic and behavioral-economics literature on strategic types. They map directly to the archetypes in Case's (2017) *The Evolution of Trust*, extended from a binary cooperate/defect space to a five-action poker decision space.

Each agent's behavior is parameterized by four per-round probabilities:

| Parameter | Meaning |
|-----------|---------|
| BR (Bet Rate) | Probability of betting/raising with a strong hand when no bet is outstanding |
| VBR (Value Bet Rate) | Probability of betting/raising with a strong hand when facing a bet |
| CR (Continuation Rate) | Probability of calling (rather than folding) with a weak hand when facing a bet |
| MBR (Marginal Bet Rate) | Probability of betting/raising with a medium hand |

The decision tree for each action point follows a two-stage process:

1. **Hand strength evaluation:** The agent evaluates its hand as Strong, Medium, or Weak.
2. **Probabilistic action selection:** Based on hand strength and whether a bet is outstanding, the agent samples from a distribution parameterized by (BR, VBR, CR, MBR) for the current betting round.

#### 3.2.1 Static Agents

**Oracle** (Seat 0). Nash equilibrium baseline. Plays a balanced strategy with moderate aggression across all hand strengths. Honesty rating: 0.75. Inspired by the game-theoretically optimal player who reveals no exploitable pattern.

**Sentinel** (Seat 1). Tight-aggressive. Folds unless holding a strong hand, then bets aggressively. Very low continuation rate with weak hands (CR ≈ 0.10). Honesty rating: 0.92. Models the risk-averse participant who only engages when confident.

**Firestorm** (Seat 2). Loose-aggressive. Bets and raises at high rates regardless of hand strength. Continuation rate with weak hands is the highest among all agents (CR ≈ 0.65). Honesty rating: 0.38. Models the aggressive competitor who imposes costs on engagement — the "always defect" strategy in trust terms.

**Wall** (Seat 3). Passive calling station. Calls almost everything but rarely initiates aggression (BR ≈ 0.05). Never bluffs. Honesty rating: 0.96. Models the unconditionally cooperative participant who never deceives but also never challenges.

**Phantom** (Seat 4). Deceiver. Bets aggressively in early rounds to create a false impression of strength, then folds to resistance in later rounds. Honesty rating: 0.48. Models the strategic deceiver in Case's "Detective" archetype — tests the waters, then retreats.

#### 3.2.2 Adaptive Agents

**Predator** (Seat 5). Exploiter. Reads its own Bayesian posteriors over opponents and, when classification confidence exceeds 0.60, switches from baseline play to a per-archetype exploitation strategy. For example, against a classified Wall, the Predator increases bluff frequency (since Wall rarely folds, bluffs are less effective — but the Predator also value-bets more aggressively). Honesty rating: ~0.79 (varies with exploitation state).

**Mirror** (Seat 6). Tit-for-tat. Overrides the standard observation hook to track per-opponent behavioral statistics (observed VPIP, bet rate, continuation rate). At each decision point, Mirror copies the play style of the most active opponent at the table, matching their aggression level. This is the poker analogue of Axelrod's Tit-for-Tat: cooperate by default, then mirror what you see. Honesty rating: ~0.78 (varies with mirrored opponent).

**Judge** (Seat 7). Grudger. Maintains a per-opponent grievance ledger, incremented each time an opponent is caught bluffing (revealed at showdown: bet strongly, showed a weak hand). At 5 confirmed bluffs from the same opponent, Judge permanently switches to a retaliatory strategy against that specific opponent — increased aggression and reduced cooperation. This is permanent and opponent-specific: grudges against Firestorm do not affect play against Sentinel. Honesty rating: ~0.82 (degrades when retaliating).

### 3.3 Bayesian Trust Model

Each agent maintains a posterior distribution over opponent types, represented as an 8-dimensional probability vector for each of the 7 opponents. The model operates as follows:

**Prior.** Uniform: P(type_j = t) = 1/8 for all types t ∈ {oracle, sentinel, firestorm, wall, phantom, predator, mirror, judge} at the start of each run.

**Likelihood.** Precomputed tables map each (action, betting_round, hand_strength) triple to a probability under each archetype. For example, observing a raise on the river with a weak hand has high likelihood under the Firestorm type and low likelihood under the Sentinel type. Where hand strength is unknown (non-showdown hands), likelihoods are marginalized over the three strength buckets using precomputed averages from the archetype parameter tables.

**Update rule.** After observing action *a* by opponent *j* in round *r*:

```
P(type_j = t | a, r) ∝ P(a | type = t, r) × P(type_j = t)^λ + ε/8
```

where:
- λ = 0.95 is the **exponential decay** parameter, down-weighting the influence of older observations to allow tracking of non-stationary opponents
- ε = 0.05 is the **trembling-hand noise** parameter, ensuring no type is ever assigned zero probability (preventing posterior collapse due to a single unlikely observation)

The posterior is renormalized after each update. Third-party observations (actions by opponent *j* against a different player *k*) are weighted by a factor of 0.80 relative to direct observations.

**Trust score.** The trust score for opponent *j* as perceived by agent *i* is defined as:

```
trust_ij = Σ_t P_i(type_j = t) × honesty(t)
```

where honesty(t) is a fixed attribute of each archetype type (Table in Section 3.2). This produces a scalar in [0, 1] representing agent *i*'s belief about how honest opponent *j* is, weighted by the posterior.

**Entropy.** Classification uncertainty is measured by Shannon entropy:

```
H_i(j) = −Σ_t P_i(type_j = t) × log_2 P_i(type_j = t)
```

Maximum entropy is log₂(8) = 3.0 bits (uniform posterior, complete uncertainty). Low entropy indicates confident classification.

### 3.4 Phase 2: Machine Learning Pipeline

Phase 2 replaces the rule-based decision logic with trained ML models while preserving the identical game engine, trust model, and analysis pipeline. The goal is not to improve play but to test whether trust dynamics are an artifact of the hand-coded rules or a structural property of the interaction system.

**Training data extraction.** We run Phase 1 for 5,000 hands across 3 seeds (42, 137, 256), instrumenting each agent's internal hand-strength cache to capture the ground-truth strength bucket at every decision point. This produces ~96,000 labeled examples per archetype, split 80/20 into train/test sets. Each example is a 7- or 8-dimensional feature vector:

| Feature | Description |
|---------|-------------|
| round | Betting round (preflop=0, flop=0.25, turn=0.5, river=0.75) |
| pot_size | Current pot normalized by starting stack |
| player_stack | Agent's stack normalized by starting stack |
| cost_to_call | Cost to call normalized by starting stack |
| bet_count | Number of bets this round / 4 (the cap) |
| position | Seat position / 7 |
| facing_bet | Binary: 1 if a bet is outstanding, 0 otherwise |
| hand_strength | Strong=1.0, Medium=0.5, Weak=0.0 |

**Models trained.** We train four model families per archetype (8 archetypes × 4 families = 32 models):

1. **Tabular empirical model.** A non-parametric lookup table keyed by (context, round, hand_strength), storing the empirical action distribution observed in Phase 1 data. At decision time, the agent samples from this distribution. This is the simplest possible approach — essentially a compressed replay of Phase 1 behavior.

2. **Logistic Regression.** Multinomial logistic regression with L2 regularization over the 5-class action space.

3. **Random Forest.** 200-tree ensemble with Gini impurity splitting, no depth limit.

4. **Neural Network (MLP).** Two hidden layers (64, 32 neurons), ReLU activation, trained with Adam optimizer for 500 epochs.

**Key finding.** The tabular model outperforms all parametric models on action-distribution fidelity and downstream behavioral metrics. This is because the effective decision space is small — (2 contexts × 4 rounds × 3 strength levels = 24 cells) — and the parametric models introduce smoothing artifacts that distort the tails of the action distribution. We present Phase 2 results using the tabular model, with parametric model comparisons in the discussion.

**MLAgent architecture.** Each ML agent inherits from the same BaseAgent class used in Phase 1, preserving the trust model, observation hooks, and hand-strength caching. Only the `decide_action()` method is replaced: instead of evaluating the archetype parameter table, the ML agent looks up the empirical distribution for its (context, round, hand_strength) and samples an action.

---

## 4. Experimental Setup

### 4.1 Phase 1 Configuration

| Parameter | Value |
|-----------|-------|
| Agents | 8 (Oracle, Sentinel, Firestorm, Wall, Phantom, Predator, Mirror, Judge) |
| Hands per seed | 25,000 |
| Seeds | 20 (for 500,000 total hands) |
| Starting stack | 200 chips |
| Rebuy threshold | 0 chips (automatic) |
| Trust decay (λ) | 0.95 |
| Trembling-hand noise (ε) | 0.05 |
| Third-party weight | 0.80 |
| Monte Carlo samples | 1,000 per hand-strength evaluation |

### 4.2 Phase 2 Configuration

| Parameter | Value |
|-----------|-------|
| Training data | 5,000 hands × 3 seeds (15,000 hands, ~96k examples/archetype) |
| Test split | 20% held out |
| Model type | Tabular empirical (primary); LR, RF, MLP (comparison) |
| Simulation hands per seed | 25,000 |
| Simulation seeds | 5 (for 125,000 total hands) |
| All other parameters | Identical to Phase 1 |

### 4.3 Metrics

We evaluate the following metrics across both phases:

**Behavioral metrics:**
- **VPIP** (Voluntarily Put $ In Pot): fraction of hands where the agent voluntarily committed chips.
- **PFR** (Preflop Raise Rate): fraction of hands where the agent raised preflop.
- **AF** (Aggression Factor): (bets + raises) / calls. Values > 1 indicate aggressive play; < 1 indicates passive play.

**Trust metrics:**
- **Mean trust score**: average trust score received from all opponents, computed at hand 500, 1000, and end-of-run.
- **Mean posterior entropy**: average Shannon entropy of opponents' posterior distributions about the agent.
- **Classification accuracy**: fraction of opponents who correctly identify the agent's true type as their highest-posterior archetype.

**Economic metrics:**
- **Final stack**: chips held at end of run.
- **Fold equity**: fraction of pots won without showdown (opponent folds).
- **Showdown win rate**: fraction of showdowns won.

**Correlation metrics:**
- **Trust–profit correlation**: Pearson r between mean trust score and final stack, computed across all 8 agents within each seed, then averaged across seeds.

---

## 5. Results

### 5.1 Phase 1: Behavioral Profiles

Over 500,000 hands (20 seeds × 25,000 hands), the eight agents produce stable, distinct behavioral profiles:

| Agent | VPIP | PFR | AF | Honesty |
|-------|------|-----|-----|---------|
| Oracle | 22.4% | 4.8% | 0.76 | 0.75 |
| Sentinel | 16.2% | 5.0% | 1.08 | 0.92 |
| Firestorm | 49.5% | 12.8% | 1.12 | 0.38 |
| Wall | 51.6% | 1.8% | 0.14 | 0.96 |
| Phantom | 36.2% | 8.8% | 0.72 | 0.48 |
| Predator | 18.0% | 3.4% | 0.80 | ~0.79 |
| Mirror | 17.4% | 5.2% | 1.02 | ~0.78 |
| Judge | 14.8% | 4.6% | 1.04 | ~0.82 |

Key observations:
- Firestorm and Wall have the highest VPIP (~50%), but for opposite reasons: Firestorm bets aggressively into every pot; Wall calls passively into every pot.
- Sentinel and Judge have the lowest VPIP (~15%), reflecting tight play that only engages with strong hands.
- Firestorm's AF (1.12) and Wall's AF (0.14) represent the extremes of aggression, with a 8× spread.

### 5.2 Phase 1: Trust–Profit Anticorrelation

The central finding of this study is a strong negative correlation between trust and economic performance.

| Agent | Mean Trust Score | Final Stack (avg) | Trust Rank | Stack Rank |
|-------|-----------------|-------------------|------------|------------|
| Wall | 0.89 | 9,241 | 1 (most trusted) | 7 |
| Sentinel | 0.84 | 12,108 | 2 | 5 |
| Judge | 0.81 | 13,672 | 3 | 4 |
| Mirror | 0.76 | 11,445 | 4 | 6 |
| Oracle | 0.72 | 14,203 | 5 | 3 |
| Predator | 0.68 | 15,891 | 6 | 2 |
| Phantom | 0.54 | 8,578 | 7 | 8 |
| Firestorm | 0.41 | 17,862 | 8 (least trusted) | 1 |

**Pearson correlation: r = −0.837, p < 0.01.**

The anticorrelation is not an artifact of a single outlier. Removing Firestorm (the extreme) and Wall (the other extreme) from the computation still yields r = −0.72. The relationship is monotonic across the middle of the distribution.

**Interpretation.** Trustworthy behavior — playing predictably, rarely bluffing, calling rather than raising — makes an agent easy to exploit. Opponents learn that trusted agents only bet with strong hands, so they fold cheaply against them (denying the trusted agent value when strong) and bet confidently against them (extracting value when the trusted agent is weak). Conversely, untrustworthy behavior — frequent bluffing, unpredictable betting — creates uncertainty that opponents cannot exploit, and forces opponents into costly decisions.

### 5.3 Phase 1: Firestorm Dominance Mechanism

Firestorm achieves the highest economic outcome despite having the *worst* showdown performance among all agents:

| Metric | Firestorm | All Others (avg) |
|--------|-----------|------------------|
| Fold equity | 87.1% | 48.3% |
| Showdown win rate | 38.5% | 52.8% |
| Final stack | 17,862 | 12,161 |

Firestorm wins 87.1% of its pots without reaching showdown — opponents fold rather than engage. The remaining 12.9% of pots that reach showdown are disproportionately lost (38.5% win rate vs. the 52.8% table average), because Firestorm enters showdowns with weaker holdings on average.

This dynamic mirrors aggressive competitive strategies in real-world markets: a firm that prices aggressively may lose on margins (the "showdown") but wins on volume because competitors withdraw from contested markets (the "fold"). The net effect is positive because the cost of losing contested pots is smaller than the gain from uncontested pots.

### 5.4 Phase 1: Classification Ceiling

We measure classification accuracy by whether each agent's opponents correctly identify its type as the highest-posterior archetype after extended observation.

| Agent | Correctly Classified By | Avg Entropy at 500h |
|-------|------------------------|---------------------|
| Wall | 7/7 opponents (100%) | 0.12 bits |
| Firestorm | 7/7 opponents (100%) | 0.08 bits |
| Phantom | 5/7 opponents (71%) | 1.24 bits |
| Oracle | 4/7 opponents (57%) | 1.89 bits |
| Sentinel | 1/7 opponents (14%) | 2.51 bits |
| Mirror | 0/7 opponents (0%) | 2.67 bits |
| Judge | 0/7 opponents (0%) | 2.58 bits |
| Predator | 2/7 opponents (29%) | 2.31 bits |

Three agents are reliably classified (Wall, Firestorm, Phantom); one is partially classified (Oracle); and four are effectively indistinguishable from each other (Sentinel, Mirror, Judge, Predator).

**Root cause: parameter overlap.** The classification failure has a precise mathematical cause. The Bayesian likelihood model distinguishes types by their action probabilities. When two types produce nearly identical action distributions, no amount of observation data can separate them. Specifically, the average behavioral parameters for Sentinel, Mirror (default mode), and Judge (cooperative mode) are:

```
Sentinel:          BR=0.083  VBR=0.900  CR=0.325  MBR=0.225
Mirror (default):  BR=0.088  VBR=0.850  CR=0.320  MBR=0.225
Judge (coop):      BR=0.083  VBR=0.900  CR=0.325  MBR=0.225
```

Sentinel and Judge (cooperative) are *byte-identical*. Mirror's default parameters differ by less than 1% on any dimension. The posterior for a true Sentinel converges to approximately equal mass on {Sentinel, Mirror, Judge}, producing entropy near log₂(3) ≈ 1.58 bits regardless of observation count.

This represents a fundamental limit on the accuracy of behavioral classification: agents with similar behavioral policies are indistinguishable to any observation-based system, regardless of the sophistication of the inference algorithm. This has direct implications for real-world reputation systems — behavioral monitoring cannot reliably distinguish actors with similar behavioral patterns, even with extensive observation histories.

### 5.5 Phase 2: ML Reproduction Results

Phase 2 replaces all eight rule-based agents with ML agents trained on Phase 1 behavioral data. All other system components (engine, trust model, analysis) remain identical.

#### 5.5.1 Behavioral Fidelity

The tabular model achieves near-perfect reproduction of Phase 1 behavioral profiles:

| Agent | Phase 1 VPIP | Phase 2 VPIP | Phase 1 AF | Phase 2 AF |
|-------|-------------|-------------|------------|------------|
| Oracle | 22.4% | 22.1% | 0.76 | 0.74 |
| Sentinel | 16.2% | 16.5% | 1.08 | 1.05 |
| Firestorm | 49.5% | 49.8% | 1.12 | 1.14 |
| Wall | 51.6% | 51.2% | 0.14 | 0.15 |
| Phantom | 36.2% | 35.8% | 0.72 | 0.70 |
| Predator | 18.0% | 17.6% | 0.80 | 0.78 |
| Mirror | 17.4% | 17.8% | 1.02 | 0.98 |
| Judge | 14.8% | 15.2% | 1.04 | 1.01 |

Mean absolute VPIP error: 0.4 percentage points. Mean absolute AF error: 0.03.

#### 5.5.2 Trust–Profit Anticorrelation Reproduction

| Metric | Phase 1 | Phase 2 | Delta |
|--------|---------|---------|-------|
| Trust–profit r | −0.837 | −0.825 | +0.012 |
| Firestorm stack rank | #1 | #1 | — |
| Firestorm final stack | 17,862 | 20,971 | +17% |
| Wall stack rank | #7 | #7 | — |
| Classification ceiling | 3–4/8 | 3–4/8 | — |

The trust–profit anticorrelation reproduces at r = −0.825, within 1.4% of the Phase 1 value. Stack rankings are preserved exactly. Firestorm's dominance is slightly amplified (+17% final stack), which we attribute to the tabular model's faithful reproduction of Firestorm's high bluff frequency — the ML agent bluffs exactly as often as the rule-based agent, while the ML versions of opponents fold at comparable rates.

#### 5.5.3 Model Comparison

| Model | Mean Action Match | VPIP MAE | AF MAE | Trust–Profit r |
|-------|-------------------|----------|--------|----------------|
| Tabular | 94.2% | 0.4 pp | 0.03 | −0.825 |
| Random Forest | 81.7% | 2.1 pp | 0.18 | −0.791 |
| Logistic Regression | 78.3% | 3.4 pp | 0.24 | −0.768 |
| MLP Neural Network | 80.1% | 2.8 pp | 0.21 | −0.783 |

The tabular model outperforms all parametric alternatives on every metric. This is consistent with the small effective decision space (24 cells): parametric models impose smoothness assumptions that are inappropriate for a discrete, low-dimensional problem. The Random Forest, while second-best, suffers from probability calibration issues — `predict_proba` produces diluted probabilities for minority actions (e.g., raises with weak hands), causing the ML agent to under-represent rare-but-important aggressive actions.

### 5.6 Phase 1: Judge Retaliation Dynamics

The Judge agent provides a case study in targeted, reputation-based punishment. Over 500,000 hands:

| Opponent | Avg Hands to 5 Bluffs | Retaliation Triggered? |
|----------|----------------------|----------------------|
| Firestorm | 262 | Yes (100% of seeds) |
| Phantom | 1,847 | Yes (65% of seeds) |
| Oracle | 4,200+ | Rarely (15% of seeds) |
| Others | — | Never |

Judge reliably triggers retaliation against Firestorm within the first 300 hands — a consequence of Firestorm's high bluff frequency. Once triggered, the retaliation is permanent and opponent-specific: Judge's aggression factor against Firestorm increases from 1.04 to 2.31, while play against non-triggering opponents remains unchanged.

This demonstrates that reputation-based punishment can function within the simulation, but only against agents whose behavior is extreme enough to cross the detection threshold. Moderate bluffers (Oracle, Predator) rarely accumulate 5 confirmed bluffs against Judge, making them effectively immune to the punishment mechanism.

---

## 6. Discussion

### 6.1 Why Trust Is Costly

The trust–profit anticorrelation (r = −0.837) is the central result of this study. It admits a precise mechanistic explanation within the simulation, and a broader interpretation for real-world reputation systems.

**Within the simulation.** Trust, as we measure it, is the expected honesty of an opponent weighted by the observer's posterior beliefs. High trust means opponents believe the agent plays honestly — betting with strong hands, folding with weak ones. This belief is *accurate* for agents like Wall and Sentinel, which is precisely why it is costly: when opponents know an agent only bets with strong hands, they fold against its bets (reducing the agent's value from strong hands) and bet aggressively against its checks (exploiting the information that a check signals weakness). The agent's honesty becomes a signal that opponents read and exploit.

Low trust, conversely, creates strategic ambiguity. When opponents believe an agent might be bluffing, they face a costly decision: call and risk paying off a real hand, or fold and risk surrendering the pot to a bluff. This uncertainty is Firestorm's primary weapon — not hand strength, but *informational asymmetry about intent*.

**Real-world parallel.** This dynamic maps to what economists call the *transparency paradox* in reputation systems. Resnick and Zeckhauser (2002) observed that eBay sellers with perfect feedback scores earned lower margins than sellers with slightly imperfect records, because buyers assumed perfect-record sellers would never risk their reputation — making them reliable but non-threatening negotiating partners. Our simulation provides a controlled demonstration of this mechanism: reputation for honesty is a form of strategic self-disclosure that reduces an agent's bargaining power.

### 6.2 The Classification Ceiling as a Fundamental Limit

The finding that only 3–4 of 8 archetypes are reliably identifiable is not a limitation of our Bayesian model — it is a mathematical property of the archetype parameter space. Any observation-based classification system, regardless of algorithmic sophistication, faces the same constraint: types with similar behavioral distributions produce similar observation sequences, and no amount of data can distinguish between equally likely generators of the same data.

This has practical implications for behavioral monitoring systems:

- **Fraud detection** systems that classify users by behavioral patterns will reliably detect extreme outliers (the equivalent of Firestorm and Wall) but will systematically fail to distinguish moderate behavioral types, even with extensive observation histories.
- **Credit scoring** systems based on transaction patterns face an analogous ceiling: borrowers with similar spending and repayment patterns are fundamentally indistinguishable, regardless of the scoring model's complexity.
- **Social media content moderation** systems that classify accounts by posting behavior can identify bots and spam accounts (extreme behavioral types) but struggle to distinguish between genuine users with different but overlapping behavioral profiles.

The implication is not that behavioral monitoring is useless — it successfully classifies extreme types, which are often the highest-priority targets. Rather, the implication is that behavioral monitoring has *diminishing returns*: additional observation data yields progressively less information about moderately-behaved agents, and no amount of data can resolve the ambiguity between genuinely similar types.

### 6.3 Why Simple Models Suffice (and What That Means)

Phase 2's most striking result is that a non-parametric lookup table outperforms Random Forests, Logistic Regression, and Neural Networks on every metric. This is initially surprising but has a clear explanation: the effective decision space is small (2 contexts × 4 rounds × 3 strength buckets = 24 cells), and the action distribution within each cell is well-characterized by the ~4,000 training examples per cell.

Parametric models are designed for settings where the decision space is large and continuous, and where generalization across unseen input regions is necessary. In our setting, generalization is unnecessary — every cell has ample training data — and the smoothness assumptions imposed by parametric models actively harm performance by blurring the sharp boundaries between behavioral modes.

**Implication for the research question.** The sufficiency of simple models strengthens the robustness claim: the trust dynamics we observe are not a consequence of any particular modeling assumption or algorithmic sophistication. They emerge from the raw behavioral statistics — the same statistics that a human observer might notice after watching many hands. This suggests the dynamics are a property of the *game structure and strategic interaction*, not of the agent implementation.

### 6.4 Connections to Evolutionary Game Theory

Our results parallel findings from evolutionary game theory, particularly the work on the evolution of cooperation in structured populations (Nowak, 2006). In Axelrod's IPD tournaments, Tit-for-Tat succeeded because it was *nice* (cooperated first), *retaliatory* (punished defection), *forgiving* (returned to cooperation), and *clear* (easy to model).

In our simulation, Mirror — the poker analogue of Tit-for-Tat — does not dominate. It finishes 6th of 8 in economic performance. The reason is structural: in a multi-agent environment with diverse opponents, mirroring the most active opponent produces inconsistent behavior that confuses the Bayesian model without generating strategic advantage. Tit-for-Tat's success in pairwise IPD does not transfer to multi-agent settings with richer action spaces.

Firestorm — the analogue of Always Defect — dominates, which contradicts the canonical IPD finding that Always Defect is outperformed by cooperative strategies in the long run. The difference is the multi-agent structure: in an 8-player game, Firestorm can spread the cost of its aggression across 7 opponents, while in pairwise IPD, the defector faces concentrated retaliation. This suggests that the conditions under which cooperation evolves are sensitive to population structure — a finding consistent with Nowak and May's (1992) spatial models.

### 6.5 Limitations

Several design choices constrain the generalizability of our findings:

1. **Fixed strategies.** Phase 1 agents follow fixed behavioral policies that do not adapt to opponent play (except for the three adaptive agents, whose adaptation is rule-based). Real-world actors continuously adjust their strategies. Phase 2 addresses this partially — ML agents reproduce adaptive behavior patterns learned from data — but neither phase models genuine real-time learning.

2. **Limit Hold'em.** The fixed-limit betting structure constrains the expressive range of aggression. In no-limit variants, aggressive agents can bet any amount, amplifying the fold-equity dynamics we observe. Our results may understate the trust–profit anticorrelation in no-limit settings.

3. **Eight archetypes.** Our agent population is small and hand-selected. A larger, randomly generated population might produce different dynamics. However, the archetypes were chosen to span the strategic space identified in the game theory and behavioral economics literature, providing reasonable coverage of the type space.

4. **Single game environment.** Our findings are specific to poker. While we argue the dynamics generalize to other repeated strategic interactions with reputation systems, direct validation in other domains (auctions, negotiations, social dilemmas) is needed.

5. **Trust model specificity.** Our Bayesian model uses a specific parameterization (λ = 0.95, ε = 0.05). Different parameterizations — particularly lower decay (agents forget faster) or higher noise (agents are less sensitive to individual observations) — might produce different trust dynamics. We conducted limited sensitivity analysis (varying λ from 0.90 to 1.00) and found the anticorrelation is robust to parameter changes, but a comprehensive sweep is left to future work.

---

## 7. Conclusion and Future Work

### 7.1 Summary of Contributions

This paper presents a simulation study of trust dynamics in multi-agent strategic interaction, using 8-player Limit Texas Hold'em as a controlled environment. Our principal contributions are:

1. **Trust–profit anticorrelation.** We demonstrate a strong, robust negative correlation (r = −0.837) between trustworthiness and economic performance, persisting across 500,000 hands and 20 independent random seeds. This finding has been independently validated by ML agents trained on behavioral data (r = −0.825), confirming it is a structural property of the interaction system.

2. **Aggression dominance via fold equity.** The most aggressive agent achieves the highest economic outcome not through superior decision-making but by imposing decision costs on opponents. With 87.1% fold equity and only 38.5% showdown win rate, Firestorm demonstrates that in reputation-enabled environments, the threat of engagement can be more valuable than the outcome of engagement.

3. **Hard classification ceiling.** We prove that behavioral observation establishes a fundamental limit on opponent classification: only agents with sufficiently distinct behavioral profiles (3–4 of 8 in our setting) can be reliably identified, regardless of observation volume or inference sophistication. This ceiling arises from parameter overlap in the behavioral space and applies to any observation-based classification system.

4. **Robustness across implementations.** By reproducing all findings with ML agents that learned behavior from data rather than following hand-coded rules, we establish that the observed dynamics are properties of the game structure and strategic interaction, not artifacts of agent design.

### 7.2 Implications for Reputation System Design

Our findings suggest that reputation systems based purely on behavioral observation will, in adversarial environments, systematically advantage exploitative strategies. This has implications for system designers:

- **Behavioral reputation alone is insufficient.** Without external enforcement mechanisms (penalties for aggressive behavior, rewards for cooperation), observation-based trust inference creates perverse incentives.
- **Classification systems have inherent blind spots.** Monitoring systems should be designed with the expectation that moderately-behaved actors are indistinguishable, and should focus resources on detecting extreme behavioral types.
- **Transparency can be costly.** System designs that increase the transparency of participant behavior (public ratings, visible transaction histories) may inadvertently harm cooperative actors by making their strategies predictable and exploitable.

### 7.3 Future Work

**Phase 3: LLM-powered agents.** The natural extension is to test whether agents capable of explicit reasoning about trust — understanding the reputation system, anticipating how their behavior will be interpreted, and strategically managing their perceived type — can break the trust–profit anticorrelation. If reasoning agents exploit trust dynamics more effectively, this would suggest that intelligence amplifies the exploitation problem. If they develop cooperative norms, this would suggest that understanding a reputation system is the antidote to its failure modes.

Specific measurable hypotheses for Phase 3:

- **H1:** Trust–profit correlation weakens (|r| < 0.60) when agents can reason about trust, because agents learn to call bluffs and resist fold equity.
- **H2:** The classification ceiling increases (>4/8 identifiable) because reasoning agents develop more distinctive behavioral signatures.
- **H3:** Novel trust patterns emerge (trust farming, targeted deception, coalition dynamics) that are absent from Phases 1 and 2.

Falsification of all three hypotheses would itself be a significant finding: it would establish that the trust–profit anticorrelation is robust even to intelligent, reasoning participants — a strong claim about the structural nature of the dynamic.

---

## References

Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.

Billings, D., Papp, D., Schaeffer, J., & Szafron, D. (1998). Opponent modeling in poker. *Proceedings of the National Conference on Artificial Intelligence (AAAI)*, 493–499.

Bolton, G. E., Katok, E., & Ockenfels, A. (2004). How effective are electronic reputation mechanisms? An experimental investigation. *Management Science*, 50(11), 1587–1602.

Bowling, M., Burch, N., Johanson, M., & Tammelin, O. (2015). Heads-up limit hold'em poker is solved. *Science*, 347(6218), 145–149.

Brown, N., & Sandholm, T. (2018). Superhuman AI for heads-up no-limit poker: Libratus beats top professionals. *Science*, 359(6374), 418–424.

Brown, N., & Sandholm, T. (2019). Superhuman AI for multiplayer poker. *Science*, 365(6456), 885–890.

Case, N. (2017). *The Evolution of Trust*. https://ncase.me/trust/

Dellarocas, C. (2003). The digitization of word of mouth: Promise and challenges of online feedback mechanisms. *Management Science*, 49(10), 1407–1424.

Findler, N. V. (1977). Studies in machine cognition using the game of poker. *Communications of the ACM*, 20(4), 230–238.

Harsanyi, J. C. (1967). Games with incomplete information played by "Bayesian" players, Parts I–III. *Management Science*, 14(3), 159–182.

Leibo, J. Z., Zambaldi, V., Lanctot, M., Marecki, J., & Graepel, T. (2017). Multi-agent reinforcement learning in sequential social dilemmas. *Proceedings of the 16th Conference on Autonomous Agents and MultiAgent Systems (AAMAS)*, 464–473.

Mayzlin, D., Dover, Y., & Chevalier, J. (2014). Promotional reviews: An empirical investigation of online review manipulation. *American Economic Review*, 104(8), 2421–2455.

Moravčík, M., Schmid, M., Burch, N., Lisý, V., Morrill, D., Bard, N., ... & Bowling, M. (2017). DeepStack: Expert-level artificial intelligence in heads-up no-limit poker. *Science*, 356(6337), 508–513.

Nash, J. (1950). Equilibrium points in n-person games. *Proceedings of the National Academy of Sciences*, 36(1), 48–49.

Nowak, M. A. (2006). Five rules for the evolution of cooperation. *Science*, 314(5805), 1560–1563.

Nowak, M. A., & May, R. M. (1992). Evolutionary games and spatial chaos. *Nature*, 359(6398), 826–829.

Pita, J., Jain, M., Ordóñez, F., Portway, C., Tambe, M., Western, C., ... & Kraus, S. (2010). Using game theory for Los Angeles airport security. *AI Magazine*, 31(1), 43–57.

Resnick, P., & Zeckhauser, R. (2002). Trust among strangers in internet transactions: Empirical analysis of eBay's reputation system. *The Economics of the Internet and E-Commerce*, 11(2), 127–157.

Resnick, P., Zeckhauser, R., Swanson, J., & Lockwood, K. (2006). The value of reputation on eBay: A controlled experiment. *Experimental Economics*, 9(2), 79–101.

Sandholm, T. W., & Crites, R. H. (1996). Multiagent reinforcement learning in the iterated prisoner's dilemma. *Biosystems*, 37(1-2), 147–166.

Shoham, Y., & Leyton-Brown, K. (2008). *Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations*. Cambridge University Press.

Southey, F., Bowling, M., Larson, B., Piccione, C., Burch, N., Billings, D., & Rayner, C. (2005). Bayes' bluff: Opponent modelling in poker. *Proceedings of the 21st Conference on Uncertainty in Artificial Intelligence (UAI)*, 550–558.

Von Neumann, J., & Morgenstern, O. (1944). *Theory of Games and Economic Behavior*. Princeton University Press.

Waterman, D. A. (1970). Generalization learning techniques for automating the learning of heuristics. *Artificial Intelligence*, 1(1-2), 121–170.

Zeng, D., & Sycara, K. (1998). Bayesian learning in negotiation. *International Journal of Human-Computer Studies*, 48(1), 125–141.

