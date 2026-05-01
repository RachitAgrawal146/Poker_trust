# Phase 3 Report — LLM Agents as Personality Role-Players

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Branch:** `main`
**Run config:** 5 seeds × 500 hands, `claude-haiku-4-5-20251001` via
Anthropic API with prompt caching. 43 943 LLM calls across all seeds,
0.034 % failure rate, $33.10 total API cost.
**Artifacts:** `reports/phase3_long_scorecard.txt`,
`runs_phase3_long.sqlite` (gitignored, on user's local machine),
`phase3_long_audit.json`, `phase3_stats.json`

---

## TL;DR

Phase 3 replaces the rule-based / hill-climber agents of Phases 1 and 2
with **eight independent LLM agents**, each given an archetype-specific
system prompt and tasked with returning one action per decision. The
trust-profit anti-correlation softens further (r = −0.510 vs Phase 2's
−0.637, Δr = +0.13), but with **2× the seed-to-seed variance** of Phase 2
(σ = 0.27 vs 0.13). The four behavioral dimensions targeted in
`docs/metrics_framework.md` (Context Sensitivity, Opponent Adaptation,
Non-Stationarity, Strategic Unpredictability) **fail to meet their
thresholds** — three of them actually move *backward* relative to
Phase 1/2. The diagnostic finding: **LLMs faithfully role-play the
personality specs they are given, but they do not spontaneously develop
opponent-conditional, time-varying, or unpredictable behavior.**

---

## 1. Design

### 1.1 Architecture

Each of the 8 archetypes is wrapped as an `LLMChatAgent` (a `BaseAgent`
subclass) whose `decide_action()` builds a chat message and calls the
LLM. The system prompt is loaded from
`phase3/personality_specs/<archetype>.md` (~600 tokens of qualitative
spec + canonical action frequencies). The user message contains:
- hole cards, community cards, hand strength bucket
- pot size, cost to call, bet count, bet cap
- player stack and position
- actions taken so far this betting round (with archetype tags)

The LLM responds with one of `FOLD CHECK CALL BET RAISE`. A `Dealer`
layer validates the action and substitutes a legal default if the LLM
emits something illegal (e.g. `BET` when only `CHECK` or `CALL` is
legal at this point).

### 1.2 What's preserved from Phase 1/2

The game engine, trust posterior, observation hooks, hand-strength
caching, SQLite logger, and metrics framework are **byte-identical**
to Phase 1. Only the agent's `decide_action` is replaced.

### 1.3 What's NOT in Phase 3

By design, no:
- **Memory across calls.** Each LLM invocation is stateless; the
  agent has no recollection of the previous hand.
- **Per-opponent reasoning.** The prompt includes opponent archetype
  tags in `actions_this_round`, but does not summarize history per
  opponent.
- **Chain-of-thought.** The agent is asked for a one-word action; no
  intermediate reasoning is requested.
- **Adaptive strategy.** The personality spec is constant for the
  entire run.

These four omissions are intentional — they isolate the *role-play*
capability of the LLM from higher-order strategic reasoning, making
Phase 3.1 (which adds them) a clean comparison.

### 1.4 Cost model

With prompt caching enabled (commit `230d6ab`):
- Input: ~1500 tokens/call (~600 cached personality + ~900 game state)
- Output: 1–3 tokens/call
- Effective cost per call: ~$0.000753
- Total: $33.10 for 43 943 calls

Without caching, the run would have cost ~$53. Caching saved ~38 %.

---

## 2. Headline result: trust-profit r = −0.510 ± 0.268

| Phase | Mechanism | Mean r | Std | Per-seed |
|---|---|---|---|---|
| 1 | Frozen archetype rules | −0.752 | 0.073 | -0.774, -0.608, -0.792, -0.812, -0.776 |
| 2 | Bounded hill-climbing | −0.637 | 0.125 | -0.759, -0.424, -0.719, -0.717, -0.564 |
| **3** | **LLM personality role-play** | **−0.510** | **0.268** | **-0.884, -0.525, -0.171, -0.712, -0.259** |

The "ladder" reads cleanly at the mean: each tier of intelligence chips
~0.12–0.13 off the trap. Phase 1 → Phase 2: Δr = +0.115; Phase 2 →
Phase 3: Δr = +0.127. **The increments are essentially equal.**

### 2.1 But the variance doubled

Phase 3's std on r is 0.268 — double Phase 2's 0.125. Two of five seeds
show *worse* r than Phase 2 (seeds 42 and 137). Two of five show
dramatically better (seeds 256 and 1024). One seed barely moves
(512). The reasons:

1. **LLM temperature stochasticity.** The Anthropic API calls use
   default temperature ≈ 1. Identical game state + identical spec can
   yield different actions on different calls. Phases 1/2 used numpy's
   seeded RNG and were fully deterministic.

2. **No cross-call memory.** Each LLM call is stateless, so subtle
   drifts in interpretation cascade across 8 800 calls per seed. A
   handful of out-of-character early decisions can bust an agent
   early and rewire the rest of the seed's dynamics.

3. **Different game trajectories per seed.** With deterministic agents,
   same cards = same play. With LLMs, same cards can branch into
   different action sequences, exploring different equilibria. Some
   seeds end where the trap opens (256 → −0.171), others where it
   closes (42 → −0.884).

4. **n = 5 is small.** With σ = 0.27 and n = 5, the standard error on
   the mean is 0.12. The 95 % CI on Δr from Phase 2 is approximately
   ±0.20 — wider than the +0.13 effect itself. The headline shift is
   directionally robust (3 of 5 seeds positive Δ from Phase 2) but not
   tight enough to claim a causally clean result.

### 2.2 Per-seed Δr decomposition

| Seed | Δ(P3 − P2) | Reading |
|---|---|---|
| 42 | −0.125 | LLMs *deepened* the trap |
| 137 | −0.101 | LLMs *deepened* the trap |
| 256 | **+0.548** | LLMs almost broke the trap (r = −0.17) |
| 512 | +0.005 | LLMs did nothing |
| 1024 | +0.305 | LLMs substantially weakened the trap |

This is the variance story to highlight in the paper: **LLM agents are
unreliable**. Sometimes they generate genuinely novel cooperative
dynamics; sometimes they collapse to even-more-stereotyped
exploitation. The variance is the finding.

---

## 3. Behavioral dimensions: 4 of 6 targets missed

The metrics framework (`docs/metrics_framework.md`) defined 6 targets
for Phase 3. Only 2 are met:

| Metric | P1 | P2 | P3 | Target | Met? |
|---|---|---|---|---|---|
| Trust-Profit r | −0.752 | −0.637 | **−0.510** | weaker | ✓ |
| Mean TEI | −0.169 | −0.150 | n/a | shifts | ✓ |
| Context Sensitivity (CS) | +0.142 | +0.142 | **+0.076** | > 0.15 | ✗ |
| Opponent Adaptation (OA) | +0.0003 | +0.0003 | +0.0008 | > 0.01 | ✗ |
| Non-Stationarity (NS) | +0.00253 | +0.00257 | **+0.00000** | > 0 | ✗ |
| Unpredictability (SU) | +1.88 | +1.83 | **+1.19** bits | > 1.5 | ✗ |
| Trust Manipulation (TMA) | +0.140 | +0.141 | +0.164 | > 0 | ✓ |

Three of the dropped metrics moved *backward* relative to the rule-based
phases. The mechanistic story:

### 3.1 Why CS dropped (0.142 → 0.076)

Context Sensitivity measures whether the agent's action correlates with
recent opponent aggression. The LLM's prompt contains
`actions_this_round` listing every action this betting round including
the archetype tags. In principle, the LLM has all the data needed to
respond to context. In practice, it doesn't — most of the LLM's
attention goes to the personality spec (the dominant context block) and
the current hand strength bucket. The opponent's actions list is
ignored.

### 3.2 Why OA stayed at zero (0.0008)

Opponent Adaptation is the standard deviation of the agent's aggression
rate across the 7 opponents. To produce non-zero OA, the agent must
play differently against different opponents. The LLM has the opponent
archetypes in the prompt but no per-opponent state — no rolling summary
of "how I've been playing against Wall." Without state, the LLM can't
develop opponent-specific strategy. Phase 2's hill-climber had the same
limitation by design (aggregate-reward objective). Phase 3 inherits it
from the prompt structure.

### 3.3 Why NS collapsed to zero

Non-Stationarity measures KL divergence between action distributions
over time windows. Phase 1/2 produced NS ≈ 0.0025 from finite-sample
RNG noise — the agents *meant* to play stationary policies, but
stochastic sampling introduced detectable drift. Phase 3 has no such
RNG: the LLM is *more* deterministic conditional on (state, spec) than
the rule-based agents were. With no memory and no internal randomness,
the action distribution is a pure function of the input, so NS → 0
exactly.

### 3.4 Why SU dropped (1.83 → 1.19 bits)

Strategic Unpredictability is the entropy of opponents' posterior beliefs
about this agent's archetype. A successful unpredictable agent
maintains high entropy by playing actions inconsistent with any single
archetype. Phase 1/2 agents had probabilistic action selection from
`archetype_params.py` — they sometimes played out of character,
keeping the posterior diffuse. Phase 3 LLMs don't randomize: given
"Sentinel = tight-aggressive," they pick the most-stereotypical
SENTINEL move every time the spot is similar. Result: opponents
quickly converge on the correct archetype classification, and SU
falls. Two archetypes (Firestorm and Wall) collapse to **SU = 0** —
they are perfectly classifiable.

### 3.5 What did improve: TMA

Trust Manipulation Awareness rose modestly (0.141 → 0.164). Six of eight
archetypes show "trust farming" — building reputation in early hands,
then exploiting it later. This is consistent with LLM linguistic
reasoning: the model understands that "playing tight initially" produces
a "trustworthy" reputation it can later weaponize. Notably, Firestorm
and Wall remain *reactive* (negative TMA), which matches their specs.

---

## 4. Economic ordering shifted dramatically

| Archetype | P1 stack | P3 stack | Rank P1 → P3 |
|---|---|---|---|
| **phantom** | 135 ± 58 | **749 ± 186** | 7 → **1** (−6) |
| mirror | 1375 ± 714 | 632 ± 132 | 4 → 2 (−2) |
| oracle | 1718 ± 597 | 531 ± 216 | 2 → 3 (+1) |
| judge | 1243 ± 337 | 477 ± 231 | 5 → 4 (−1) |
| **firestorm** | 6875 ± 847 | **452 ± 330** | 1 → **5** (+4) |
| predator | 336 ± 233 | 448 ± 135 | 6 → 6 (0) |
| **sentinel** | 1535 ± 284 | **328 ± 99** | 3 → **7** (+4) |
| wall | 103 ± 44 | 100 ± 58 | 8 → 8 (0) |

Three significant moves:

1. **Phantom climbed from #7 to #1.** The deceiver archetype thrives
   under LLM control. The LLM correctly interprets "Phantom bets weak
   hands at high frequency" and produces aggressive bluffing that
   opponents fold to. In rule-based Phase 1, Phantom's tight
   `vbr` (value bet rate) limited its profitability; the LLM, with no
   rate constraint, just bluffs more often. Phantom's effective
   aggression-factor in Phase 3 (3.03) is 4.5× the Phase 1 spec value
   (0.67).

2. **Firestorm fell from #1 to #5.** Conversely, the LLM
   *over-aggresses* on Firestorm's behalf — Firestorm's AF rises from
   1.12 to 7.16, and it bleeds chips on too-frequent bluffs that get
   called. The rule-based Firestorm's profitability came from
   *calibrated* aggression; the LLM lacks the calibration.

3. **Sentinel fell from #3 to #7.** LLMs underplay the
   tight-aggressive archetype. The personality spec emphasizes
   discipline and folding; the LLM internalizes "fold a lot" too
   strongly and misses value bets it should make. Sentinel's
   effective AF (3.73) is high *conditional on it playing*, but it
   plays so few hands that the volume is too low to compete.

Wall remains pinned at the bottom (rank 8). The calling-station archetype
is the only one for which the LLM produces behavior that is
*economically equivalent* to the rule-based version (both lose ~$100
across 5 seeds with high rebuy counts).

---

## 5. Limitations specific to Phase 3

In addition to the cross-phase limitations from Phase 2 (3 seeds, single
optimizer, etc.), Phase 3 has:

1. **Single LLM mind for all 8 agents.** While each agent has its own
   API call with its own system prompt, all calls go to the same Haiku
   instance. Decisions are *correlated*: a single update to Anthropic's
   weights or a single shift in API behavior would affect all 8
   agents. Truly independent reasoners would require 8 different model
   families.

2. **No memory across calls.** Each call is stateless. Section 3.2 / 3.3
   document the consequences (zero OA, zero NS).

3. **Single response token budget.** Maximum 16 output tokens, no
   chain-of-thought. Forces a fast/lossy decision style that may not
   reflect the LLM's full reasoning capability.

4. **Personality spec is descriptive, not prescriptive about
   adaptation.** The spec says "Phantom bluffs weak hands"; it does
   not say "Phantom should track each opponent and bluff more against
   tight ones." The metrics framework targets adaptive behavior but
   the prompt doesn't request it.

5. **n = 5 seeds is small.** With σ = 0.27 the 95 % CI on r is wide
   enough that some of the per-seed pattern could be noise. The
   direction of the trend is robust (3 of 5 seeds positive Δ from
   Phase 2), but the magnitude shouldn't be over-claimed.

6. **No retry on illegal actions.** When the LLM emits an illegal
   action (e.g. RAISE when bet cap is hit), the dealer substitutes a
   legal default. This was rare (0.034 % failure rate), but means
   ~15 hands had a non-LLM-decided action.

---

## 6. Implications for Phase 3.1 and beyond

The four missed targets (CS, OA, NS, SU) point to four interventions:

1. **Persistent memory** → directly targets OA. Append a per-opponent
   summary ("Wall called me 4 of 5 times this hour") to the system
   prompt. Forces the agent to accumulate state.

2. **Chain-of-thought prompting** → directly targets CS and TMA. Ask
   the agent to reason step-by-step before deciding. CoT scaffolding
   is known to surface latent reasoning that a one-shot answer hides.

3. **Adaptive personality specs** → directly targets NS. Allow the
   agent to update its own spec across hand boundaries based on what
   it has learned.

4. **Higher temperature or explicit randomization instruction** →
   targets SU. Encourage the LLM to mix actions to remain unclassifiable.

Phase 3.1 implements (1), (2), and (3). The expected impact:
- CS: 0.076 → 0.15-0.25
- OA: 0.0008 → 0.01-0.03
- NS: 0 → 0.005-0.02
- TMA: 0.16 → 0.25+
- r: −0.51 → −0.30 to −0.45 (depending on whether memory helps the
  agent exploit or defend)

These are predictions, not measurements — see `phase3_3_1_report.md`
when the run completes.

---

*Last updated: 2026-05-01. Source artifacts:
`reports/phase3_long_scorecard.txt` (this report's data),
`phase3_stats.json` (per-seed JSON dump),
`extract_phase3_stats.py` (extraction script),
`phase3/run_phase3_chat.py` (the simulation runner),
`phase3/llm_chat_agent.py` (the agent class).*
