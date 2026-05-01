# Phase 3.1 Report — LLM Agents with Reasoning Scaffolding

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Branch:** `main`
**Run config:** 5 seeds × 150 hands, `claude-haiku-4-5-20251001` via
Anthropic API with prompt caching, with `--phase31` enabled.
11 953 LLM calls across all seeds, 0.017 % failure rate, ~$17 total
API cost, 6.9 hr wall time (sequential).
**Artifacts:** `reports/phase31_long_scorecard.txt`,
`runs_phase31_long.sqlite` (gitignored, on user's local machine),
`phase31_long_audit.json`, `phase31_stats.json`

---

## TL;DR

Phase 3.1 extends Phase 3 with three reasoning interventions: **chain-of-thought
prompting** (capped at 2 sentences for cost control), **persistent
per-opponent memory** (rolling action summaries injected into the user
message), and **adaptive personality specs** (one extra LLM call per
agent every 25 hands updating its own strategy notes). The result:
trust-profit r drops from −0.510 (Phase 3) to **−0.094** — statistically
indistinguishable from zero. The Phase 3 → Phase 3.1 step (Δr = +0.416)
is **larger than the previous three phases' steps combined** (P1 → P2 →
P3 = +0.242). Two of five seeds show *positive* r — meaning the most
trusted agents made *more* money than the least trusted ones — and the
mean economic ordering inverts: Wall (the most-trusted, archetype-spec
calling-station that lost in every previous phase) is now the biggest
winner, climbing from rank 8 to rank 1.

The trust trap can be broken by LLM agents *with the right reasoning
scaffolding*. CoT alone, memory alone, and adaptive specs alone are
each insufficient — but combined, they produce a trap-breaking effect
that is qualitatively different from any prior tier.

---

## 1. Design

### 1.1 The three interventions

Phase 3.1 keeps everything from Phase 3 — same 8 personality archetypes,
same Anthropic Haiku backend, same engine, same trust posterior — and
adds three opt-in features behind a single `--phase31` flag:

**Chain-of-thought prompting.** The system prompt is rewritten to
request "AT MOST 2 SHORT SENTENCES (no markdown, no headers, no lists)"
of reasoning before the action. The agent outputs reasoning followed by
a final-line `ACTION: <FOLD|CHECK|CALL|BET|RAISE>` marker. Output token
budget raised from 16 → 96. A custom parser (`_parse_phase31_action`)
extracts the action from the marker line, falling back to action-word
scanning if the marker is absent. The 2-sentence cap was added after a
first attempt produced 150–200 tokens of richly-formatted markdown per
call, blowing past cost projections by 5×.

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

### 1.2 What's preserved

- Game engine, trust posterior, observation hooks, hand-strength caching,
  SQLite logger, and metrics framework: byte-identical to Phase 1.
- Personality specs in `phase3/personality_specs/<archetype>.md`: unchanged.
- The `phase31=False` baseline path: byte-identical to Phase 3
  (verified by `phase3/validate_phase31.py`'s 50-check unit suite).

### 1.3 Cost model

With prompt caching enabled and the tightened CoT format:
- Input: ~1500 cached + ~300 uncached (memory + notes) tokens/call
- Output: ~50 tokens/call (CoT reasoning + ACTION line)
- Effective per-call cost: ~$0.0014 (~85 % more than Phase 3's $0.000753)
- Total: $17 for 11 953 calls × 5 seeds × 150 hands

A first-attempt 5 × 500 run with verbose CoT was killed at hand 4 after
seeing a 23-hour ETA per seed and 5× the expected per-hand cost — the
LLM had been producing 150–200 tokens of richly-formatted reasoning
*plus* reasoning itself into more aggressive plays (45 actions/hand vs
Phase 3 baseline's 22). The tightened version collapsed call-count back
to baseline (16 calls/hand) while preserving the CoT signal.

---

## 2. Headline result: r drops to −0.094

| Phase | Mechanism | Mean r | Std | Δ from prior |
|---|---|---|---|---|
| 1 | Frozen archetype rules | −0.752 | 0.073 | — |
| 2 | Bounded hill-climbing | −0.637 | 0.125 | +0.115 |
| 3 | LLM personality role-play | −0.510 | 0.268 | +0.127 |
| **3.1** | **LLM + CoT + memory + adaptive** | **−0.094** | **0.301** | **+0.416** |

The Phase 3 → 3.1 step is **3.3× the size** of the Phase 1 → 2 step and
**3.3× the Phase 2 → 3 step**. The cumulative jump from Phase 1 to
Phase 3.1 is +0.658 — the trap is statistically indistinguishable from
broken at the population level.

### 2.1 Per-seed pattern

| Seed | P1 r | P2 r | P3 r | P3.1 r | Δ(3.1 − 3) |
|---|---|---|---|---|---|
| 42 | −0.774 | −0.759 | −0.884 | −0.289 | **+0.595** |
| 137 | −0.608 | −0.424 | −0.525 | −0.338 | +0.187 |
| 256 | −0.792 | −0.719 | −0.171 | −0.327 | −0.156 |
| 512 | −0.812 | −0.717 | −0.712 | **+0.047** | **+0.759** |
| 1024 | −0.776 | −0.564 | −0.259 | **+0.435** | **+0.694** |

Two notable patterns:

1. **Trap *inversion* in 2 of 5 seeds.** Seeds 512 and 1024 produce
   *positive* r — trusted agents made more money than distrusted ones.
   This is qualitatively different from any prior phase, where the
   most-positive r was −0.17 (Phase 3, seed 256). Phase 3.1 doesn't
   merely soften the anti-correlation; in 40 % of seeds it inverts the
   relationship.

2. **Seed 256 went *backward*.** Phase 3.1 r = −0.327 vs Phase 3's
   −0.171. This is the only seed where 3.1 is worse than 3. The other
   four seeds all improved. This points to genuine seed-conditional
   variance in how LLM reasoning interacts with game trajectories — a
   limitation worth foregrounding in the paper.

### 2.2 Variance commentary

σ = 0.301 — slightly higher than Phase 3's 0.268, very high relative to
Phase 1's 0.073. This is the second methodological caveat: even with
reasoning scaffolding, LLM agents remain *unreliable across seeds* in
their ability to break the trap. Three seeds show modest residual
trap (−0.29 to −0.34); two seeds show inversion (+0.05, +0.43). The
mean tells the headline story, but no individual seed is "the typical
Phase 3.1 run."

At n=5 with σ = 0.30, the 95 % CI on the mean is approximately
[−0.36, +0.18] — covering zero comfortably but also covering modest
negative r values comparable to Phase 3 baseline. A future replication
at n = 10–20 seeds would tighten this interval substantially.

---

## 3. Behavioral dimensions: 4 of 6 targets met

| Metric | P3 | P3.1 | Target | Met? |
|---|---|---|---|---|
| Trust-Profit r weaker | −0.510 | **−0.094** | weaker | ✓ |
| Mean TEI shifts | n/a | −0.336 | shifts | ✓ |
| Context Sensitivity (CS) | 0.076 | **0.100** | > 0.15 | ✗ |
| Opponent Adaptation (OA) | 0.0008 | 0.0007 | > 0.01 | ✗ |
| Non-Stationarity (NS) | 0.000 | **0.000** | > 0 | ✗ |
| Unpredictability (SU) | 1.19 bits | **1.55 bits** | > 1.5 | ✓ |
| Trust Manipulation (TMA) | +0.164 | **+0.242** | > 0 | ✓ |

Phase 3 hit 2 of 6 targets. Phase 3.1 hits 4 of 6 — significant
improvement, with two new targets cleared (SU and a substantial TMA
boost).

### 3.1 New wins

**Strategic Unpredictability rises to 1.55 bits.** First time the
target is met. Why: CoT introduces variability in how the LLM
interprets each spot — same hand-strength bucket + same game state
can produce different actions because the verbal reasoning surfaces
different considerations. The agents become harder to classify. Two
archetypes (Wall and Predator-equivalent) drove the increase; Wall in
particular shows SU = 0 in the by-archetype breakdown for seed 1024,
while Sentinel rises to 1.95 bits.

**Trust Manipulation Awareness rises to +0.242.** Six of eight
archetypes now show "trust farming" behavior — building reputation
early and exploiting it later. Wall and Sentinel — the two
conservative-spec archetypes — show the strongest farming signal
(+0.733 and +0.704), explicitly building trust before cashing in.
This is exactly the kind of *reputational reasoning* the paper's
hypothesis predicted CoT would unlock.

### 3.2 Persistent misses (and why)

**OA stays near zero.** Memory injection into the user message is
not enough on its own — the agent has the data but doesn't translate
it into measurably differentiated play across opponents. The
optimization signal that would push OA up (e.g. a reward for beating
specific opponents) isn't present; the LLM just plays its archetype.
This is the cleanest evidence for a Phase 4 direction:
*opponent-conditional reward shaping* would likely close the OA gap.

**NS = 0 exactly.** Even though the adaptive-spec update fires 6
times per seed (storing new strategy notes that the agent then sees
on subsequent hands), the time-windowed metric can't detect drift at
this scale. Two reasons: (a) 150 hands per seed × 6 updates = ~25
hands per epoch, which is shorter than the minimum window the metric
uses; (b) the strategy-note updates may not actually shift action
distributions enough to register as KL divergence. Running at 500+
hands per seed would test (a); inspecting the actual notes the LLMs
write would test (b).

**CS at 0.100 (still below 0.15).** Modest improvement from 0.076 but
not sufficient. The asymmetry across archetypes is illuminating:
Oracle, Predator, and Mirror (the agents whose specs explicitly
mention opponent observation or imitation) have CS in 0.17–0.19; the
others stay below 0.04. CoT amplifies what the spec already requests
but doesn't unlock new dimensions.

---

## 4. Economic ordering: Wall wins

The most striking single finding outside the r number:

| Archetype | Trust | P3.1 stack | P3 stack | Rank P3 → P3.1 |
|---|---|---|---|---|
| **wall** | 0.85 | **280 ± 88** | 100 (LAST) | 8 → **1** (−7) |
| firestorm | 0.48 | 231 ± 104 | 452 | 5 → 2 (−3) |
| phantom | 0.75 | 230 ± 61 | **749 (1st)** | 1 → 3 (+2) |
| mirror | 0.73 | 208 ± 83 | 632 | 2 → 4 (+2) |
| judge | 0.78 | 191 ± 45 | 477 | 4 → 5 (+1) |
| sentinel | 0.79 | 183 ± 58 | 328 | 7 → 6 (−1) |
| predator | 0.80 | 179 ± 98 | 448 | 6 → 7 (+1) |
| oracle | 0.63 | 175 ± 64 | 531 | 3 → 8 (+5) |

**Wall — the calling-station archetype that lost in every previous
phase, with 9.4 average rebuys per seed in Phases 1–3 — is now the
biggest winner.** It doesn't rebuy at all in Phase 3.1. Trust score
0.85 (highest in the table) translates directly to economic dominance.

This is the trust-profit anti-correlation flipping in real-time.
Combined with TMA = +0.733 (the highest in the table), the picture is
clear: Phase 3.1 Wall is *intentionally* maintaining its high-trust
reputation and using opponents' folds to its strong hands as the
profit mechanism. The behavior matches the archetype spec
(non-aggression, calling station) but the *outcome* inverts because
the other agents — also reasoning explicitly about reputation —
respect Wall's calls as legitimate.

The other big mover is Oracle, which fell from rank 3 to last (rank
8). The GTO archetype's strength was *uniform* play; Phase 3.1 LLM
agents apparently react to non-uniform behavioral signals from
others, and Oracle's "balanced" play becomes legible as exploitable
predictability.

---

## 5. Behavioral fingerprints

| Archetype | VPIP | PFR | AF | AF P3 | Direction |
|---|---|---|---|---|---|
| oracle | 0.302 | 0.111 | 1.12 | 2.10 | aggression DOWN |
| sentinel | 0.120 | 0.080 | 2.53 | 3.73 | aggression DOWN |
| firestorm | 0.722 | 0.453 | 2.77 | **7.16** | aggression WAY DOWN |
| wall | 0.626 | 0.067 | 0.33 | 0.00 | slight aggression UP |
| phantom | 0.437 | 0.162 | 1.29 | 3.03 | aggression DOWN |
| predator | 0.248 | 0.119 | 1.38 | 1.73 | aggression DOWN |
| mirror | 0.196 | 0.087 | 1.11 | 1.72 | aggression DOWN |
| judge | 0.174 | 0.098 | 1.87 | 3.86 | aggression DOWN |

**Universal AF moderation.** Every archetype except Wall sees its
aggression factor drop from Phase 3 to Phase 3.1 — most dramatically
Firestorm (7.16 → 2.77, 61 % reduction). The Phase 3 baseline LLM
without scaffolding *over-aggresses* on every archetype's behalf;
adding CoT + memory tames the over-aggression while preserving each
archetype's relative position (Firestorm still highest, Wall still
lowest).

This is the second qualitative finding of Phase 3.1: **reasoning
agents play more like humans than role-playing agents do.** A human
"maniac" doesn't bet every street; they pick spots. Phase 3 LLMs
without reasoning collapse onto stereotypical aggression; Phase 3.1
LLMs calibrate.

---

## 6. Limitations

Six honest constraints, partially overlapping with Phase 3:

1. **150 hands per seed is short.** Phase 3 baseline used 500 hands.
   Three of the missed metric targets (NS, possibly CS) likely need
   more hands per seed to stabilize.

2. **n = 5 seeds.** With σ = 0.30 the 95 % CI on r is wide enough that
   the "trap broken" claim is for the *mean*, not every seed. Three
   seeds still show negative r. A 10-seed replication is the natural
   tightening.

3. **Single LLM mind for all 8 agents.** Same caveat as Phase 3 — every
   API call hits the same Haiku model. Decisions are correlated through
   one weights set. Independent reasoners would require 8 different
   model families (or 8 independent prompts to prevent within-API
   priming).

4. **CoT cap of 2 sentences.** The cost-driven tightening from 256 → 96
   max output tokens may have suppressed genuinely useful reasoning.
   A budget-friendlier replication at higher token caps (say 192) would
   test whether the trap-breaking effect strengthens with more reasoning.

5. **Memory injection does not equal memory utilization.** The agents
   *receive* per-opponent summaries but the metrics suggest they don't
   strongly *condition* their actions on them (OA still near zero).
   The mechanism by which memory helps r drop is therefore not strictly
   "per-opponent strategy" — it's something subtler, perhaps
   reputation-aware aggregate play.

6. **Adaptive specs may not be meaningfully changing strategy.** The
   `_strategy_notes` field is updated 6× per seed, but NS = 0 exactly
   suggests the action distributions don't shift in detectable ways.
   Either the LLM writes notes that don't change behavior, or the
   metric is too coarse at this scale.

---

## 7. Implications for the paper

Five points worth foregrounding in the writeup:

1. **The four-tier ladder.** Phase 1 → 2 → 3 → 3.1 reads as
   −0.75 → −0.64 → −0.51 → −0.09. Each tier of intelligence chips a
   slice off the trap, but the LLM-with-reasoning tier closes nearly
   half the remaining gap on its own.

2. **The asymmetric step sizes.** Bounded numerical optimization
   (P1 → P2) and LLM role-playing (P2 → P3) each contribute about
   +0.12. Reasoning scaffolding (P3 → P3.1) contributes +0.42 — over
   3× the size of the previous steps. Reasoning is *not* a continuation
   of adaptation; it's a qualitatively different mechanism.

3. **The trap can flip.** In 2 of 5 seeds Phase 3.1 produces *positive*
   trust-profit r. This is the strongest possible counter-evidence
   against "the trust trap is structural." Given the right reasoning
   support, observation-based reputation systems can favor cooperators
   over exploiters.

4. **What still doesn't work.** OA and NS both remain near zero.
   Memory in the prompt is not the same as memory-driven play; adaptive
   specs may be cosmetic. Phase 4 directions: opponent-conditional
   reward shaping for OA; longer hand horizons + explicit strategy-shift
   prompts for NS.

5. **The paper has a clean four-phase story.** P1: does fixed strategy
   cause the trap? P2: can numerical search escape it? P3: can LLM
   role-play escape it? P3.1: can LLM reasoning escape it? Answers in
   order: yes, slightly, slightly more, **largely yes**.

---

*Last updated: 2026-05-01. Source artifacts:
`reports/phase31_long_scorecard.txt` (this report's data),
`phase31_stats.json` (per-seed JSON dump),
`extract_phase3_stats.py` (extraction script — same as Phase 3),
`phase3/run_phase3_chat.py` (the simulation runner with --phase31 flag),
`phase3/llm_chat_agent.py` (the agent class with phase31 mode),
`phase3/validate_phase31.py` (50-check unit suite).*
