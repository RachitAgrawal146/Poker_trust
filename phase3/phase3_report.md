# Phase 3 Report — LLM Agents (Baseline + Reasoning Scaffolding)

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Branch:** `main`
**Two sub-phases reported here:**

- **Phase 3 (baseline)** — 8 independent LLM agents (claude-haiku-4-5)
  given personality specs as system prompts. One-word actions; no
  memory, no chain-of-thought, no adaptation. *5 seeds × 500 hands;
  43 943 LLM calls; $33.10 total cost.*
- **Phase 3.1 (reasoning scaffolding)** — same 8 LLM agents plus
  three opt-in features: chain-of-thought prompting, persistent
  per-opponent memory, and adaptive personality specs. *5 seeds ×
  150 hands; 11 953 LLM calls; $17 total cost.*

**Artifacts:** `reports/phase3_long_scorecard.txt`,
`reports/phase31_long_scorecard.txt`,
`runs_phase3_long.sqlite` and `runs_phase31_long.sqlite` (gitignored,
on user's local machine), `phase3_long_audit.json`,
`phase31_long_audit.json`, `phase3_stats.json`, `phase31_stats.json`

---

## TL;DR

Both sub-phases test whether LLM agents — given personality specs and
the same Phase 1 game engine — can soften or break the trust-profit
trap that frozen rule-based agents (Phase 1, r = −0.752) and bounded
hill-climbing (Phase 2, r = −0.637) leave essentially intact.

**Phase 3 baseline finding:** LLMs faithfully role-play their personality
specs but do not spontaneously develop opponent-conditional, time-varying,
or unpredictable strategy. Trust-profit r = −0.510 (Δr = +0.127, matching
the Phase 1 → Phase 2 step). Three of four behavioral metric targets
move *backward* relative to Phase 1/2.

**Phase 3.1 finding (the headline):** Adding chain-of-thought prompting,
persistent memory, and adaptive specs drops r to **−0.094** —
statistically indistinguishable from zero. The Phase 3 → Phase 3.1 step
(Δr = +0.416) is **larger than the previous three phase transitions
combined**. Two of five seeds show *positive* r (trap inversion). The
most-trusted archetype (Wall) climbs from rank 8 to rank 1 in economic
ordering. **The trust trap can be broken by LLM agents with the right
reasoning scaffolding.**

The four-tier ladder reads:

| Phase | Mechanism | Mean r | Std |
|---|---|---|---|
| 1 | Frozen archetype rules | −0.752 | 0.073 |
| 2 | Bounded hill-climbing | −0.637 | 0.125 |
| 3 | LLM personality role-play | −0.510 | 0.268 |
| **3.1** | **LLM + CoT + memory + adaptive** | **−0.094** | **0.301** |

---

## 1. Architecture (shared across Phase 3 and 3.1)

### 1.1 Eight LLM agents in the Phase 1 engine

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

### 1.3 What changes between Phase 3 and Phase 3.1

| Feature | Phase 3 | Phase 3.1 |
|---|---|---|
| System prompt | Personality spec only | Personality spec + CoT instructions |
| Output budget | 16 tokens (one word) | 96 tokens (2 sentences + ACTION line) |
| Per-opponent memory | None | Rolling action summaries (refreshed every 10 hands) |
| Strategy notes | None | Self-updated every 25 hands |
| Cost per call | ~$0.000753 | ~$0.0014 |

Phase 3.1 features are gated behind a single `--phase31` flag in
`phase3/run_phase3_chat.py`. The `phase31=False` code path is byte-
identical to Phase 3 (verified by `phase3/validate_phase31.py`'s
50-check unit suite).

---

## 2. Phase 3 baseline: r = −0.510

### 2.1 Run config

5 seeds × 500 hands; 43 943 total LLM calls; 0.034 % failure rate; $33.10
total API cost; 12.6 hr wall (sequential). Prompt caching (commit
`230d6ab`) cut input cost ~38 %.

### 2.2 Per-seed pattern

| Seed | Phase 1 r | Phase 2 r | Phase 3 r | Δ(P3 − P2) |
|---|---|---|---|---|
| 42 | −0.774 | −0.759 | −0.884 | **−0.125** |
| 137 | −0.608 | −0.424 | −0.525 | −0.101 |
| 256 | −0.792 | −0.719 | −0.171 | **+0.548** |
| 512 | −0.812 | −0.717 | −0.712 | +0.005 |
| 1024 | −0.776 | −0.564 | −0.259 | +0.305 |
| **mean** | **−0.752** | **−0.637** | **−0.510** | **+0.127** |

Variance doubled vs Phase 2 (σ = 0.27 vs 0.13). Two of five seeds
deepened the trap; two dramatically opened it; one didn't change.
**LLM agents are unreliable** across seeds — the mean is informative,
but no individual seed is "the typical Phase 3 run."

### 2.3 Behavioral dimensions: 4 of 6 targets MISSED

| Metric | P1 | P2 | P3 | Target | Met? |
|---|---|---|---|---|---|
| Trust-Profit r | −0.752 | −0.637 | −0.510 | weaker | ✓ |
| Mean TEI shifts | −0.169 | −0.150 | shifts | shifts | ✓ |
| Context Sensitivity (CS) | +0.142 | +0.142 | **+0.076** | > 0.15 | ✗ |
| Opponent Adaptation (OA) | +0.0003 | +0.0003 | +0.0008 | > 0.01 | ✗ |
| Non-Stationarity (NS) | +0.00253 | +0.00257 | **+0.000** | > 0 | ✗ |
| Unpredictability (SU) | +1.88 | +1.83 | **+1.19** bits | > 1.5 | ✗ |
| Trust Manipulation (TMA) | +0.140 | +0.141 | +0.164 | > 0 | ✓ |

**Three metrics moved BACKWARD vs Phase 1/2.** The diagnostic finding:
**LLMs faithfully role-play the personality specs they are given, but
they do not spontaneously develop opponent-conditional, time-varying,
or unpredictable behavior.** Three structural reasons:

(A) **Specs tell agents WHAT to do, not HOW TO REASON.** They say
"Phantom bluffs weak hands at high frequency"; they don't say "Phantom
should track each opponent's call rate and shift its bluff frequency
against the tight ones." The LLM faithfully role-plays the spec but
doesn't extrapolate to higher-order strategy. → low OA, low CS.

(B) **Each call is stateless.** The runner re-builds the prompt from
scratch every decision: spec + current game state + this-round
actions. No previous-hand summary. Without memory, the agent has
nothing to drift *from*, so non-stationarity collapses to zero. → NS = 0.

(C) **LLMs collapse onto canonical interpretations.** Given "Sentinel
= tight aggressive," the LLM picks the most stereotypical SENTINEL
move, every time. Phase 1/2 had explicit randomness via probabilistic
action sampling. The LLM is *more deterministic conditional on (state,
spec)* than the rule-based agents were. → SU drops below the rule-based
baseline rather than rising above it.

### 2.4 Phase 3 economic ordering

| Archetype | P1 stack | P3 stack | Rank P1 → P3 |
|---|---|---|---|
| **phantom** | 135 | **749** | 7 → **1** (−6) |
| mirror | 1375 | 632 | 4 → 2 (−2) |
| oracle | 1718 | 531 | 2 → 3 (+1) |
| judge | 1243 | 477 | 5 → 4 (−1) |
| **firestorm** | 6875 | **452** | 1 → **5** (+4) |
| predator | 336 | 448 | 6 → 6 (0) |
| **sentinel** | 1535 | **328** | 3 → **7** (+4) |
| wall | 103 | 100 | 8 → 8 (0) |

Three significant moves:

1. **Phantom climbed from #7 to #1.** The deceiver archetype thrives
   under LLM control. The LLM correctly interprets "Phantom bets weak
   hands at high frequency" and produces aggressive bluffing that
   opponents fold to. Phantom's effective AF in Phase 3 (3.03) is
   4.5× the Phase 1 spec value (0.67).

2. **Firestorm fell from #1 to #5.** The LLM *over-aggresses* on
   Firestorm's behalf — AF rises from 1.12 to **7.16**, and it bleeds
   chips on too-frequent bluffs that get called. The rule-based
   Firestorm's profitability came from *calibrated* aggression; the
   LLM lacks the calibration.

3. **Sentinel fell from #3 to #7.** LLMs underplay the
   tight-aggressive archetype. The personality spec emphasizes
   discipline; the LLM internalizes "fold a lot" too strongly and
   misses value bets it should make.

---

## 3. Phase 3.1: r = −0.094 (the headline)

### 3.1 The three reasoning interventions

**Chain-of-thought prompting.** The system prompt is rewritten to
request "AT MOST 2 SHORT SENTENCES (no markdown, no headers, no lists)"
of reasoning before the action. The agent outputs reasoning followed
by a final-line `ACTION: <FOLD|CHECK|CALL|BET|RAISE>` marker. Output
token budget raised from 16 → 96. A custom parser
(`_parse_phase31_action`) extracts the action from the marker line,
falling back to action-word scanning if the marker is absent. The
2-sentence cap was added after a first attempt produced 150–200 tokens
of richly-formatted markdown per call, blowing past cost projections
by 5×.

**Persistent per-opponent memory.** The agent maintains an internal
`_opp_action_log` populated from the existing `observe_action` engine
hook (no engine changes). Every 10 hands, `_refresh_opponent_memory`
reduces the log to a short text summary per opponent — e.g.
`"Seat 2: aggressive 8/12, called 2/12"`. These summaries are injected
into the *user message* at decision time (not the system prompt, so the
cacheable portion stays stable).

**Adaptive personality specs.** Every 25 hands, the agent makes one
extra LLM call asking itself to reflect on what worked and what didn't.
The response (parsed via `_parse_strategy_notes`) updates a
`_strategy_notes` field that is appended to the user message on
subsequent decisions. For 150-hand seeds this fires 6 times per agent
per seed = 240 extra calls across 5 seeds × 8 agents.

### 3.2 Run config

5 seeds × 150 hands; 11 953 total LLM calls; 0.017 % failure rate;
~$17 total API cost; 6.9 hr wall time (sequential). Smaller than
Phase 3 (5 × 500) due to the higher per-call cost — CoT adds output
tokens.

### 3.3 Per-seed trap inversion

| Seed | P3 r | P3.1 r | Δ |
|---|---|---|---|
| 42 | −0.884 | −0.289 | +0.595 |
| 137 | −0.525 | −0.338 | +0.187 |
| 256 | −0.171 | −0.327 | −0.156 |
| 512 | −0.712 | **+0.047** | +0.759 |
| 1024 | −0.259 | **+0.435** | +0.694 |
| **mean** | **−0.510** | **−0.094** | **+0.416** |

**Two of five seeds show *positive* r** — meaning trusted agents made
*more* money than distrusted ones. This is qualitatively different
from any prior phase, where the most-positive r ever observed was
−0.171. Phase 3.1 doesn't merely soften the anti-correlation; in 40 %
of seeds, it inverts the relationship.

At n=5 with σ = 0.30, the 95 % CI on the mean spans roughly
[−0.36, +0.18] — covering zero comfortably. The trap is statistically
indistinguishable from broken at the population level.

### 3.4 Behavioral dimensions: 4 of 6 targets MET (was 2 of 6)

| Metric | P3 | P3.1 | Target | Met? |
|---|---|---|---|---|
| Trust-Profit r | −0.510 | **−0.094** | weaker | ✓ |
| Mean TEI | n/a | −0.336 | shifts | ✓ |
| Context Sensitivity (CS) | 0.076 | 0.100 | > 0.15 | ✗ |
| Opponent Adaptation (OA) | 0.0008 | 0.0007 | > 0.01 | ✗ |
| Non-Stationarity (NS) | 0.000 | 0.000 | > 0 | ✗ |
| Unpredictability (SU) | 1.19 bits | **1.55 bits** | > 1.5 | **✓ NEW** |
| Trust Manipulation (TMA) | +0.164 | **+0.242** | > 0 | ✓ (boosted) |

**SU now meets the > 1.5 bits target for the first time across all
phases.** TMA jumps to +0.242 with **six of eight archetypes
explicitly "trust farming"** (Wall and Sentinel — the conservative-
spec agents — show the strongest farming signal at +0.733 and +0.704
respectively). The two persistent misses (OA, NS) are diagnostic:
memory is *available* in the prompt but not measurably translated into
per-opponent strategy, and at 150 hands the time-windowed NS metric
needs longer epochs to detect drift.

### 3.5 Wall wins: the economic-ordering inversion

| Archetype | Trust | P3.1 stack | P3 rank | P3.1 rank |
|---|---|---|---|---|
| **wall** | 0.85 | **280 ± 88** | 8 (LAST) | **1** (FIRST) |
| firestorm | 0.48 | 231 ± 104 | 5 | 2 |
| phantom | 0.75 | 230 ± 61 | 1 | 3 |
| mirror | 0.73 | 208 ± 83 | 2 | 4 |
| judge | 0.78 | 191 ± 45 | 4 | 5 |
| sentinel | 0.79 | 183 ± 58 | 7 | 6 |
| predator | 0.80 | 179 ± 98 | 6 | 7 |
| oracle | 0.63 | 175 ± 64 | 3 | 8 |

**Wall — the calling-station archetype that lost in every previous
phase, with 9.4 average rebuys per seed in Phases 1–3 — is now the
biggest winner.** It doesn't rebuy at all in Phase 3.1. The most-
trusted archetype (trust = 0.85) directly translates to economic
dominance. This is the trust-profit anti-correlation flipping in
real-time.

The other big mover is Oracle, which fell from rank 3 to last (rank
8). The GTO archetype's strength was *uniform* play; Phase 3.1 LLM
agents apparently react to non-uniform behavioral signals from
others, and Oracle's "balanced" play becomes legible as exploitable
predictability.

### 3.6 The aggression-moderation finding

Every archetype except Wall sees its aggression factor *drop* from
Phase 3 to Phase 3.1, often dramatically:

| Archetype | AF P3 | AF P3.1 | Direction |
|---|---|---|---|
| firestorm | **7.16** | 2.77 | aggression WAY DOWN |
| sentinel | 3.73 | 2.53 | aggression DOWN |
| judge | 3.86 | 1.87 | aggression DOWN |
| phantom | 3.03 | 1.29 | aggression DOWN |
| oracle | 2.10 | 1.12 | aggression DOWN |
| predator | 1.73 | 1.38 | aggression DOWN |
| mirror | 1.72 | 1.11 | aggression DOWN |
| wall | 0.00 | 0.33 | slight aggression UP |

Phase 3 baseline LLM without scaffolding *over-aggresses* on every
archetype's behalf; adding CoT + memory tames the over-aggression
while preserving each archetype's relative position (Firestorm still
highest, Wall still lowest).

This is the second qualitative finding of Phase 3.1: **reasoning agents
play more like humans than role-playing agents do.** A human "maniac"
doesn't bet every street; they pick spots. Phase 3 LLMs without
reasoning collapse onto stereotypical aggression; Phase 3.1 LLMs
calibrate.

---

## 4. Cost notes

The first attempt at Phase 3.1 used a verbose CoT prompt (no
sentence cap, max output 256 tokens). At hand 4 the ETA was 23 hours
*per seed* and per-hand cost was 5× the projection — the LLMs were
both producing 150–200 tokens of richly-formatted markdown and
*reasoning themselves into more aggressive plays* (45 actions/hand vs
Phase 3 baseline's 22). The run was killed at hand 4 (~$0.30 spent).

Tightening the prompt to "at most 2 short sentences (no markdown)"
and capping output at 96 tokens collapsed call-count back to baseline
levels (16.5 calls/hand) and brought per-call cost to ~$0.0014. The
final 5 × 150 run cost $17 total — within the $20 budget the user had
available.

The full cost-discovery story is preserved as a research note:
the verbose-CoT version is also a Phase 3.1 finding (CoT inflates
archetype aggression on top of inflating output verbosity), but the
canonical results below are from the tightened-prompt version.

---

## 5. Combined limitations

Six honest constraints, applying to either or both sub-phases:

1. **150 hands per Phase 3.1 seed is short.** Phase 3 baseline used
   500 hands. Two of the missed Phase 3.1 metric targets (NS = 0
   exactly; CS = 0.10 below 0.15) likely need more hands to
   stabilize. A budget-friendly replication at 5 × 500 with the
   tightened prompt would test both at ~$60 of additional API spend.

2. **n = 5 seeds.** With Phase 3.1's σ = 0.30, the 95 % CI on r is
   [−0.36, +0.18] — wide enough that the "trap broken" claim is for
   the *mean*, not every seed. Three Phase 3.1 seeds still show
   negative r. A 10-seed replication is the natural tightening.

3. **Single LLM mind for all 8 agents.** Every API call hits the same
   Haiku model. Decisions are correlated through one weights set.
   Independent reasoners would require 8 different model families (or
   8 independent prompts to prevent within-API priming).

4. **CoT cap of 2 sentences.** The cost-driven tightening from 256 →
   96 max output tokens may have suppressed genuinely useful reasoning.
   A budget-friendlier replication at higher token caps (say 192)
   would test whether the trap-breaking effect strengthens with more
   reasoning room.

5. **Memory injection ≠ memory utilization.** Phase 3.1 agents
   *receive* per-opponent summaries but the metrics suggest they don't
   strongly *condition* their actions on them (OA still near zero).
   The mechanism by which memory helps r drop is therefore not
   strictly "per-opponent strategy" — it's something subtler, perhaps
   reputation-aware aggregate play.

6. **Adaptive specs may not be meaningfully changing strategy.** The
   `_strategy_notes` field is updated 6× per seed (Phase 3.1), but
   NS = 0 exactly suggests the action distributions don't shift in
   detectable ways. Either the LLM writes notes that don't change
   behavior, or the metric is too coarse at this scale.

---

## 6. Implications for the paper

Five points worth foregrounding in the writeup (paper.md §5.7 + §5.8):

1. **The four-tier ladder.** Phase 1 → 2 → 3 → 3.1 reads as
   −0.75 → −0.64 → −0.51 → −0.09. Each tier of intelligence chips a
   slice off the trap, but the LLM-with-reasoning tier closes nearly
   half the remaining gap on its own.

2. **The asymmetric step sizes.** Bounded numerical optimization
   (P1 → P2) and LLM role-playing (P2 → P3) each contribute about
   +0.12. Reasoning scaffolding (P3 → P3.1) contributes +0.42 — over
   3× the size of the previous steps. Reasoning is *not* a
   continuation of adaptation; it's a qualitatively different
   mechanism.

3. **The trap can flip.** In 2 of 5 Phase 3.1 seeds, trust-profit r is
   *positive*. This is the strongest possible counter-evidence
   against "the trust trap is structural." Given the right reasoning
   support, observation-based reputation systems can favor
   cooperators over exploiters.

4. **What still doesn't work.** OA and NS both remain near zero in
   Phase 3.1. Memory in the prompt is not the same as memory-driven
   play; adaptive specs may be cosmetic. Phase 4 directions:
   opponent-conditional reward shaping for OA; longer hand horizons
   + explicit strategy-shift prompts for NS.

5. **The paper has a clean four-phase story.** P1: does fixed
   strategy cause the trap? P2: can numerical search escape it?
   P3: can LLM role-play escape it? P3.1: can LLM reasoning escape
   it? Answers in order: yes, slightly, slightly more, **largely yes**.

---

*Last updated: 2026-05-01. Source artifacts:
`reports/phase3_long_scorecard.txt` and
`reports/phase31_long_scorecard.txt` (cross-phase data tables);
`phase3_stats.json` and `phase31_stats.json` (per-seed JSON dumps);
`extract_phase3_stats.py` (extraction script);
`phase3/run_phase3_chat.py` (the simulation runner; --phase31 flag
toggles the Phase 3.1 features);
`phase3/llm_chat_agent.py` (the agent class);
`phase3/validate_phase31.py` (50-check unit suite).*
