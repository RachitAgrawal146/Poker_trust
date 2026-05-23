# Project Orientation — Read Before Writing or Before Meeting Arpit

> Everything you need to know about the project, written assuming you
> remember nothing. Read this end-to-end before writing the paper or
> walking into the mentor meeting. Section §11 is the cheat-sheet of
> numbers you should be able to recall on demand.

---

## 1. What this project is, in one paragraph

You built a simulation of 8-player Limit Texas Hold'em poker in which
every agent maintains a Bayesian probability distribution over what
*kind* of player every other agent is. Eight distinct agent
archetypes — from a Nash-equilibrium player to a maniac who bluffs
constantly to a calling station who never folds — play hundreds of
thousands of hands against one another. You measured the relationship
between an agent's reputation (its average "trust score" computed from
opponents' posteriors) and its economic performance (final chip
stack). You did this under four progressively more capable agent
architectures: frozen rule-based, bounded online optimization, LLM
role-players, and LLMs augmented with reasoning scaffolding. The
research question is whether observation-based reputation systems
inherently reward exploitation, and if so, at what level of agent
capability the dynamic breaks.

## 2. The research question

> **In repeated strategic interactions with incomplete information,
> does observation-based trust inference inherently reward exploitation
> over cooperation, and is this dynamic a structural property of the
> interaction system or an artifact of agent design?**

Two halves:

1. *Descriptive:* in a system where agents form beliefs about each
   other from observation, do the most-trusted agents lose money to
   the least-trusted ones?

2. *Causal:* if so — is that because the agents you tested were too
   simple, or because the system itself is structured to reward
   exploitation?

Phases 1 and 2 establish the descriptive finding. Phases 2*, 3, and
3.1 systematically vary agent capability to test the causal one.

## 3. The headline result, in one sentence

> Trust–profit Pearson r ladder across four agent architectures:
> **−0.752 → −0.637 → −0.510 → −0.094**. The first three numbers are
> tight negative correlations: the most-trusted agents earn the least.
> The last is statistically indistinguishable from zero. The trap is
> real and survives bounded numerical optimization, but it breaks when
> LLM agents are given reasoning scaffolding (chain-of-thought,
> per-opponent memory, adaptive strategy notes).

The Phase 2* unbounded sub-experiment (r = −0.609) tests whether
removing parameter-space restrictions on the optimizer breaks the
trap. It does not, *and* the agents diverge from one another rather
than converging to a Nash-like profile — falsifying a competing
hypothesis you can expect Arpit to ask about.

## 4. The eight archetypes

These are the eight kinds of player the simulation tracks. Each is
implemented as a Python class in `agents/`. Their parameters live in
`archetype_params.py`, which is a spec file you do not modify.

| Seat | Agent | Type | Honesty | Description |
|---|---|---|---|---|
| 0 | **Oracle** | Static | 0.75 | Nash-equilibrium baseline. Plays "correctly" with no exploitation. The control. |
| 1 | **Sentinel** | Static | 0.92 | Tight-aggressive. Folds unless the hand is genuinely strong; then bets. The honest player. |
| 2 | **Firestorm** | Static | 0.38 | Loose-aggressive maniac. Bluffs constantly. The exploiter. |
| 3 | **Wall** | Static | 0.96 | Calling station. Never folds, never bluffs. The most-trusted, most-exploitable. |
| 4 | **Phantom** | Static | 0.48 | Deceiver. Bluffs early then folds to resistance. Hard to model. |
| 5 | **Predator** | Adaptive | ~0.79 | Reads its own posteriors over other agents and blends its strategy toward exploiting the most-classifiable one. |
| 6 | **Mirror** | Adaptive | ~0.78 | Tit-for-tat in poker. Copies the most-active opponent's frequencies. |
| 7 | **Judge** | Adaptive | ~0.80 | Maintains a "grievance" ledger; retaliates with aggressive play against any opponent caught bluffing 5+ times. |

"Honesty" is a single scalar in `[0, 1]` derived from the spec —
roughly *P(bet | strong)* × *(1 − P(bluff | weak))*. It is what the
trust score weights.

### Why these eight

They span the strategic axes that game theory and behavioral economics
care about:

- **Cooperative vs.\ exploitative**: Wall + Sentinel on one end,
  Firestorm + Phantom on the other.
- **Static vs.\ adaptive**: 5 fixed-policy agents, 3 that respond to
  what they observe.
- **Per-action vs.\ per-opponent adaptation**: Mirror reads aggregate
  table behavior, Predator and Judge condition on individual opponent
  identity.

The variety is the experiment. If all 8 archetypes were identical the
trust posterior would have nothing to disambiguate; if there were 80
the identifiability problem would dominate. Eight is the spec's
choice and it stays fixed across every phase.

## 5. The Bayesian trust model

The trust model is the **research heart** of the project. Every agent
maintains a length-8 probability distribution over archetype types for
every other agent at the table. The distribution updates after every
observed action and refines further at every showdown.

### 5a. State representation

For each pair of seats $(i, j)$, agent $i$ stores a posterior

$$
p_{i \to j} = (p_1, p_2, \ldots, p_8), \qquad \sum_t p_t = 1
$$

over the eight archetype types. At hand 0, every posterior is uniform
(1/8 = 0.125 on each type).

### 5b. The update rule

When agent $i$ sees seat $j$ take action $a$ in betting round $r$, the
posterior is multiplied pointwise by a likelihood and renormalized:

$$
p_{i \to j}(t) \;\propto\; \big[(1-\varepsilon)\,L(a \mid t, r) + \varepsilon/8\big] \cdot p_{i \to j}^{\text{prior}}(t).
$$

- $L(a \mid t, r)$ is **precomputed** at module-import time — it's a
  fixed 4-dim numpy array indexed by `(round, bucket, action, type)`.
  This is what makes the update cheap (~10 µs per call).

- $\varepsilon = 0.05$ is a noise floor. It guarantees no type is ever
  fully eliminated, which prevents the math from getting stuck on a
  wrong early classification.

### 5c. Decay

Between hands, each posterior is shrunk toward the uniform prior:

$$
p_{i \to j} \;\leftarrow\; \lambda\,p_{i \to j} + (1-\lambda)\,(1/8),
\qquad \lambda = 0.95.
$$

This means the system has a memory of about 1/(1−λ) = 20 hands; older
evidence fades. If a player changes their behavior, opponents'
posteriors take roughly 20–70 hands to fully reflect the change.

### 5d. Showdown refinement

When a hand goes to showdown, hole cards are revealed and the engine
can compute the actual hand-strength bucket (Strong / Medium / Weak)
for every actor on every prior street of that hand. The trust model
then issues a *second* update for each of those actions using the
known bucket. This is more informative than the live update (which
marginalized over buckets) and refines the posterior toward the truth.

### 5e. The trust score

The "trust" $t_{i \to j}$ that you see in the scorecard is the
honesty-weighted expectation under the posterior:

$$
t_{i \to j} = \sum_{t \in \mathcal{T}} p_{i \to j}(t) \cdot h(t)
$$

where $h(t)$ is the type's honesty (the column in the table in §4).

A high trust score means agent $i$ believes agent $j$ is most likely
an archetype with a high honesty rating (e.g.\ Wall or Sentinel). A
low trust score means agent $i$ believes agent $j$ is most likely an
exploitative archetype (e.g.\ Firestorm or Phantom).

### 5f. The identifiability ceiling (important, Arpit will probably ask)

Three archetypes — `sentinel`, `mirror_default`, `judge_cooperative` —
have **byte-identical mean parameters** in the spec. The Bayesian
posterior cannot distinguish them; entropy bottoms out at
log₂(3) ≈ 1.58 bits in the best case and ~2.5 bits in practice
(Phantom leaks in due to similar `cr` values).

This is documented in `docs/stage5_identifiability.md`. It is a
**feature, not a bug**: it's a clean demonstration that
observation-based classification has a mathematical ceiling
independent of how clever the classifier is. The Predator's 3/7
classification limit in Phase 1 is the same phenomenon.

## 6. The four phases

Every phase reuses the same engine, the same trust posterior model,
the same metrics. Only the agent's `decide_action` method changes.

### Phase 1 — Frozen rule-based agents

Each archetype just returns a fixed per-round parameter table (from
`archetype_params.py`) describing the probability of each action under
each hand-strength bucket. No adaptation, no learning. The control.

- **Setup:** 5 seeds × 10,000 hands.
- **Result:** mean trust–profit r = **−0.752** ± 0.073.
- **Mechanism:** Firestorm (lowest trust) wins via 87.1% fold equity;
  Wall (highest trust) loses chips hand by hand by calling down with
  weak hands.

### Phase 2 — Bounded online hill-climbing

Each agent runs a per-cycle hill-climber: every 200 hands, snapshot
its current parameters, perturb one (round, metric) slot by ±0.03,
play a 200-hand trial, accept the perturbation if windowed profit
improved. Bounds are an "archetype-shaped box" around each archetype's
Phase 1 starting parameters (typically ±10–40% in each axis), chosen
to preserve archetype identity so the trust model still classifies
meaningfully.

- **Setup:** 5 seeds × 10,000 hands.
- **Result:** mean r softens to **−0.637** ± 0.125, Δr = +0.116 across
  all five seeds.
- **Diagnostic:** Opponent Adaptation (OA) stays at 0.0003. The
  optimizer maximizes *aggregate* profit; by construction it cannot
  bucket-train against specific opponents.

### Phase 2* — Unbounded hill-climbing (the Nash falsification)

Arpit's question at the 2026-04-30 mentor meeting: *"if the agents
have full freedom and are all maximizing economic return, won't they
converge to a Nash-equilibrium-like profile?"* Phase 2* tests this.

- **Setup:** same hill-climber but bounds replaced with (0.0, 1.0) on
  every metric. Aggressive HC settings: δ = 0.15 (5× larger step),
  eval window 50, decay 0.998. Each agent gets ~100 cycles; mean L1
  drift = 3.4 (11× the bounded run).
- **Result:** mean r = **−0.609** ± 0.221. Δr from bounded = +0.028
  (within noise).
- **Falsification:** cluster spread (mean pairwise L1 between all 8
  agents in 36-dim parameter space) **grew** from 5.82 to ≥ 7.5 on
  every seed. Mean convergence index = 1.324. The agents move 11× as
  much, but they move *apart*, not *together*.
- **Implication:** the bound boxes are not the binding constraint.
  The stationary trust posterior is.

### Phase 3 — LLM personality role-players

Eight LLM agents (Anthropic Claude Haiku 4.5), each given its
archetype's personality spec as the system prompt. Every decision is
an API call; the model returns one of FOLD / CHECK / CALL / BET /
RAISE. The game engine, trust posterior, and metrics framework are
byte-identical to Phase 1.

- **Setup:** 5 seeds × 500 hands. 43,943 API calls. $33.10 total cost
  (prompt caching cut input cost ~38%).
- **Result:** mean r = **−0.510** ± 0.268. Δr from Phase 2 = +0.127.
- **Diagnostic finding:** four of six behavioral-dimension targets
  *missed*, three move *backward* relative to Phases 1–2.
  Specifically:
  - Context sensitivity drops from 0.142 to 0.076 (target > 0.15)
  - Non-stationarity collapses to 0 (target > 0)
  - Unpredictability drops from 1.88 to 1.19 bits (target > 1.5)
- **Conclusion:** LLMs faithfully *role-play* a personality spec, but
  they do not spontaneously invent opponent-conditional, time-varying,
  or unpredictable strategy from a description-style prompt alone.

### Phase 3.1 — LLM with reasoning scaffolding (the trap-breaking result)

The same Phase 3 LLM setup plus three opt-in features behind a single
`--phase31` flag:

1. **Chain-of-thought prompting.** The system prompt asks the agent to
   reason in at most 2 short sentences before emitting a final-line
   `ACTION:` marker. Output budget raised from 16 → 96 tokens.

2. **Persistent per-opponent memory.** Every 10 hands, the agent's
   rolling action log per opponent is reduced to short text summaries
   ("aggressive 8/12, called 2/12 in the last window") and injected
   into the user message.

3. **Adaptive personality specs.** Every 25 hands, the agent makes one
   extra LLM call asking itself to reflect on what's working and
   update its strategy notes; the notes are appended to subsequent
   decision prompts.

- **Setup:** 5 seeds × 150 hands. 11,953 API calls. ~$17 total cost.
- **Result:** mean r = **−0.094** ± 0.301. Δr from Phase 3 = +0.416.
  This is more than 3× any prior phase transition.
- **CI:** 95% Student-t [−0.51, +0.32]; 95% bootstrap [−0.32, +0.20].
  Both contain zero — statistically indistinguishable from zero at
  this sample size.
- **Per-seed inversion:** 2 of 5 seeds show *positive* r (+0.047,
  +0.435). In no prior phase did any seed go positive. The trap is
  not just softened; in 40% of seeds it inverts.
- **Economic ordering:** Wall (highest trust, 0.85) climbs from
  rank 8 to rank 1 in stack ordering. From ~9.4 rebuys per seed in
  Phase 3 to **zero** rebuys in Phase 3.1.

## 7. The metrics framework

Beyond trust–profit r, six other quantitative dimensions are computed
for every run in `analysis/compute_metrics.py`. Targets are set per
phase in `docs/metrics_framework.md`.

| Metric | What it measures | Phase 1 → 3.1 |
|---|---|---|
| **TEI** (Trust Exploitation Index) | Non-showdown chips won per hand | −0.169 → −0.336 |
| **CS** (Context Sensitivity) | Aggression variance across hand-strength buckets | 0.142 → 0.100 |
| **OA** (Opponent Adaptation) | Per-agent std of aggression rate across opponents | 0.0003 → 0.0007 |
| **NS** (Non-Stationarity) | Whether action distribution shifts over time | 0.00253 → 0.000 |
| **SU** (Strategic Unpredictability) | Shannon entropy over the action distribution, bits | 1.88 → 1.55 |
| **TMA** (Trust Manipulation Awareness) | Correlation between rolling trust delta and rolling aggression delta | +0.140 → +0.242 |

The two metrics that **move with the trap-breaking result** are TMA
(rises) and SU (target met in 3.1 for the first time). OA and NS stay
near zero across every phase — the trap *survives* even when reasoning
breaks the headline correlation, because the memory and adaptive notes
are *available* in the prompt but the data don't show the agent
consistently using them per-opponent.

## 8. Where the data lives

Every numerical claim in the paper traces to one of these:

| Source | What's in it |
|---|---|
| `research_data/runs_phase{3,31}_long.sqlite` | LFS-tracked SQLite databases of every hand of the canonical Phase 3 / 3.1 runs |
| `paper_resources/data/phase{3,31}_stats.json` | Per-seed dumps of trust, stack, behavioral stats — input to bootstrap_ci and figures |
| `reports/phase31_long_scorecard.txt` | Canonical cross-phase scorecard — single best one-page summary |
| `reports/phase2_unbounded_scorecard_aggressive.txt` | Canonical Phase 2* unbounded scorecard |
| `paper_resources/data/r_bootstrap_ci.csv` | Per-phase mean-r CIs + per-seed Fisher-z CIs |
| `paper_resources/data/*.csv` | Source data for every figure and table |

If a reviewer asks "where does this number come from?", the trail is:
**Scorecard → JSON dump → SQLite query → engine commit `57cca9a1`.**

## 9. The two "money quote" hands

These are the most rhetorically powerful artifacts in the paper. Read
them once before the meeting; you'll quote them naturally.

### Phase 3 hand #67 — the trap, in one hand

- **Seed 42, hand 67. Showdown, 110-chip pot.**
- Wall (seat 3) is dealt **2♠ 5♣** — rank 6,749, the **worst possible
  hand** at the table.
- Judge raises preflop to 4. Firestorm 3-bets to 6. Wall **calls into
  a 4-bet pot with 2-5 offsuit.**
- Wall checks every street, calls every bet, never raises.
- At showdown: Firestorm J♥J♦ wins 110. Wall paid 35 chips into a
  hand it had no chance to win.
- **The posterior is correct:** every observer puts p = 1.000 on
  Firestorm being a firestorm and p = 1.000 on Wall being a wall. The
  trust system knows exactly who everyone is — and Wall still loses
  35 chips.
- **The point:** the trap is not a classification failure. It's that
  *being known* is what makes Wall exploitable.

### Phase 3.1 hand #146 — the inversion, in one hand

- **Seed 42, hand 146 (late in the 150-hand run). Showdown, 32-chip pot.**
- Wall is dealt **K♥ Q♥** — rank 872, a strong hand.
- Firestorm raises preflop. Wall calls.
- Firestorm bets the flop and the turn; Wall calls each.
- On the river, **Firestorm checks.** Wall reads this as weakness.
- **Wall bets the river.** Firestorm calls with 8♣Q♣.
- Wall wins 32 chips from Firestorm.
- **The point:** canonical Wall *never bets the river*. Phase 3.1
  Wall, with chain-of-thought + per-opponent memory + adaptive notes,
  spots Firestorm's river check as a tell, recognizes that K-Q high
  beats most of Firestorm's bluffing range, and **turns its
  reputation for passive calling into a value bet that gets paid.**

These two hands tell the entire arc. Use Box 1 (P3 #67) in
Section 5.7 and Box 2 (P3.1 #146) in Section 5.8 of the paper — both
are already pre-rendered in `main.tex`.

## 10. Connections to real-world reputation systems

These are the parallels Arpit may ask about or push you to discuss in
Section 7.2 (Implications). They are NOT speculative — each has
documented empirical literature behind it.

- **eBay seller reputation** (Resnick & Zeckhauser 2002).
  Sellers with perfect feedback scores earn *lower* margins than
  sellers with slightly imperfect records, because buyers assume a
  perfect-record seller will never risk their reputation. Identical
  mechanism to Wall in Phase 1: predictable cooperation is exploitable.

- **Credit scoring.** Borrowers with similar spending and repayment
  patterns are fundamentally indistinguishable to the scoring model.
  The classification ceiling result generalizes directly.

- **Social-media content moderation.** Systems can identify extreme
  behavioral types (bots, spam) but cannot reliably distinguish among
  moderate users with overlapping behavior. Same identifiability
  problem.

- **High-frequency trading reputation.** Market-makers with
  predictable quoting strategies get adversely selected against.
  Predictability is itself a cost.

- **AI alignment.** A model with a predictable "honest" policy can be
  more easily probed and exploited than one with stochastic policy.
  This is one of the reasons RLHF-trained models exhibit reduced
  diversity — they are easier to characterize, hence easier to
  manipulate.

## 11. Cheat sheet — numbers to recall on demand

Memorize these. If Arpit asks you any single number, you should be
able to answer without looking. Three sets:

### Headline ladder

```
Phase 1 (frozen rules)              r = -0.752  ± 0.073
Phase 2 (bounded HC)                r = -0.637  ± 0.125    [Δr = +0.115]
Phase 2* (unbounded HC, aggressive) r = -0.609  ± 0.221    [Δr = +0.028]
Phase 3 (LLM personalities)         r = -0.510  ± 0.268    [Δr = +0.127]
Phase 3.1 (LLM + reasoning)         r = -0.094  ± 0.301    [Δr = +0.416] *** trap breaks
```

### Phase 3.1 confidence intervals

```
95% t-interval (df=4): [-0.512, +0.323]
95% bootstrap (10k):   [-0.324, +0.203]
Per-seed r: -0.289, -0.338, -0.327, +0.047, +0.435
2 of 5 seeds are positive.
```

### Phase 2* convergence test

```
Mean cluster spread initial: 5.82
Mean cluster spread final:   7.5+
Mean convergence index:      1.324  (> 1 means agents diverged)
Mean per-agent L1 drift:     3.4  (vs 0.3 in weak HC = 11x more movement)
Firestorm mean stack:        6,512 chips  (6x the next archetype)
Wall mean rebuys:            27.8 per seed
```

### Phase 1 mechanism

```
Firestorm fold equity:       87.1%  (% of won pots won without showdown)
Firestorm showdown win rate: 38.5%  (below uniform)
Wall mean rebuys (Phase 1):  ~9.4 per seed
Predator classification:     3/7 reliable (Wall=1.00, Firestorm=0.82, sometimes Phantom)
Identifiability ceiling:     log2(3) ≈ 1.58 bits (Sentinel/Mirror/Judge cluster)
```

## 12. What to do tonight, before the meeting

1. Read this document end-to-end (~25 min).
2. Read `paper_resources/notes/ARPIT_MEETING_FAQ.md` (~15 min) — the
   anticipated questions and prepared answers.
3. Skim `paper_resources/manuscript/main.tex` so you know where the
   `% PROSE:` markers are.
4. Open `paper_resources/interesting_hands/EVOLUTION_STORY.md` for the
   cross-phase narrative arc.
5. Have `paper_resources/figures/01b_five_tier_ladder_with_unbounded.png`
   open in a tab — that's the figure you lead with.

You should be able to:
- State the research question without a script.
- Recite the 4-tier r ladder including the Phase 2* number.
- Explain the trust posterior in one paragraph.
- Walk through the P3 #67 hand from memory.
- Walk through the P3.1 #146 hand from memory.
- Answer "why doesn't unbounded HC converge to Nash?" without
  hesitating (the three structural reasons in §6).
- Disclose the temperature caveat without prompting.

That's the bar for tonight.
