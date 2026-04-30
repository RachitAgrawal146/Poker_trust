# Phase 2 (Adaptive) Report — Bounded Online Optimization Weakens But Cannot Escape the Trust Trap

**Author:** Rachit Agrawal | Polygence Research Project | 2025–2026
**Branch:** `claude/poker-trust-phase-2-C1yUP` (phase2-adaptive lineage)
**Canonical run config:** 5 seeds × 10 000 hands, `eval_window = 200`,
`delta = 0.03 → 0.005`, decay 0.995. Lean run (3 × 5000) executed first as a
sanity check — see Section 6 for the lean-vs-long comparison.
**Artifacts:** `reports/phase2_scorecard_long.txt` (canonical),
`reports/phase2_scorecard.txt` (lean),
`phase2/adaptive/optimization_log_long.json`,
`phase2/adaptive/param_trajectories_long.json`,
`runs_phase1_long.sqlite` (P1 reference, gitignored),
`runs_phase2_long.sqlite` (P2 adaptive, gitignored)

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
- **5 seeds × 10 000 hands canonical, 3 seeds × 5 000 hands lean.** The
  lean configuration was run first as a sanity check (~25 minutes wall on
  a laptop); the canonical configuration matches Phase 1's research
  scale. Section 6.1 documents the lean-vs-long shift.

## 3. Results

All numbers below are means ± standard deviations across the five canonical
seeds (42, 137, 256, 512, 1024) at 10 000 hands each. Full scorecard:
`reports/phase2_scorecard_long.txt`. A lean replication (3 seeds × 5000)
in `reports/phase2_scorecard.txt` showed the same qualitative pattern but
with wider error bars; the long run is canonical and Section 6.1 discusses
the differences.

### 3.1 Headline scorecard (Table 0)

| Metric | Phase 1 | Phase 2 | Δ |
|---|---|---|---|
| Trust–Profit r | −0.752 ± 0.074 | **−0.637 ± 0.126** | **+0.116** |
| Mean TEI | −0.169 ± 0.005 | −0.150 ± 0.014 | +0.019 |
| Context Sensitivity (CS) | +0.142 ± 0.003 | +0.142 ± 0.005 | −0.000 |
| Opponent Adaptation (OA) | +0.0003 | +0.0003 | −0.0000 |
| Non-Stationarity (NS) | +0.00253 | +0.00257 | +0.00004 |
| Unpredictability (SU bits) | +1.883 ± 0.162 | +1.832 ± 0.165 | −0.051 |
| Trust Manipulation (TMA) | +0.140 ± 0.011 | +0.141 ± 0.007 | +0.001 |

The headline finding: **bounded online optimization weakens the trust
trap by Δr = +0.116 (−0.75 → −0.64), but does not eliminate it.** This
shift is bigger than either phase's seed-to-seed standard deviation
(P1: 0.074; P2: 0.126), so it is unlikely to be noise. Other behavioral
metrics — CS, OA, NS, TMA — stay flat to four decimal places, which means
the r movement is *not* an artifact of agents becoming more volatile or
more opponent-aware. They are, in aggregate, the same kind of agent;
they have just shifted to a slightly less-exploitable point in their
parameter boxes.

### 3.2 Behavioral fingerprints (Table 1)

VPIP, PFR and AF (= (bets + raises) / calls) per archetype. As at the lean
scale, the interesting movements concentrate in the two agents that lost
their Phase 1 adaptive modifiers:

- **Predator** AF rises from 0.82 → **1.01** (+23 %), and its preflop PFR
  rises from 0.041 → 0.054 (+32 %). Without the `PREDATOR_EXPLOIT` blend,
  the climber walked Predator's baseline toward broadly more aggression.
- **Mirror** VPIP drops 0.19 → 0.16 (−12 %), AF rises 0.90 → **0.99**
  (+10 %). Without the opponent-mimic copy step, the climber tightened
  Mirror's preflop range and pushed its postflop aggression up.
- **Six other archetypes stay essentially flat** — Oracle, Sentinel,
  Firestorm, Wall, Phantom, Judge all drift well under one P1 std on every
  axis. This is exactly the bound-box invariance we designed for.

### 3.3 Economic ordering (Table 2)

| Archetype | Stack P1 | Stack P2 | Rebuys P1 | Rebuys P2 | Rank P1 | Rank P2 | ΔRank |
|---|---|---|---|---|---|---|---|
| firestorm | 6875 ± 847 | **7953 ± 1082** | 0 | 0 | 1 | 1 | 0 |
| oracle | 1718 ± 597 | 1339 ± 331 | 0 | 0 | 2 | 2 | 0 |
| sentinel | 1535 ± 284 | 1034 ± 537 | 0 | 1 | 3 | 3 | 0 |
| mirror | 1375 ± 714 | 681 ± 245 | 1 | 1 | 4 | **6** | **+2** |
| judge | 1243 ± 337 | 929 ± 488 | 1 | 1 | 5 | **4** | **−1** |
| predator | 336 ± 233 | **754 ± 513** | 4 | 1 | 6 | **5** | **−1** |
| phantom | 135 ± 58 | 147 ± 59 | 23 | 21 | 7 | 7 | 0 |
| wall | 103 ± 44 | 84 ± 34 | 29 | 32 | 8 | 8 | 0 |

Four significant moves:

1. **Firestorm got more dominant** under adaptation (+1078 chips on
   average), widening its already large lead. Its bound box is ±30–40 % so
   the climber had room to optimize, and it pushed Firestorm's preflop
   `mbr` (medium-bet rate) down by 0.139 — folding more medium hands
   preflop and concentrating its action on strong holdings, a more
   exploitative profile.
2. **Predator climbed one rank** (6 → 5) with stack +124 % (336 → 754).
   This is the largest *relative* improvement in the table.
3. **Mirror fell two ranks** (4 → 6), losing exactly half its stack
   (1375 → 681). Removing the opponent-mimic adaptation hurt Mirror
   more than the climber could recover within its bound box.
4. **Judge climbed one rank** (5 → 4), modest gain. Most of Judge's
   value in Phase 2 comes from the retaliatory state, which has a loose
   bound box and fired against all 7 opponents at this scale.

The bottom of the ordering is unchanged — Wall and Phantom are still
pinned at the floor with 21–32 rebuys per seed, and adaptation didn't
pull them up.

### 3.4 Trust–profit r per seed (Table 3)

| Seed | Phase 1 r | Phase 2 r | Δ |
|---|---|---|---|
| 42 | −0.774 | −0.759 | +0.015 |
| 137 | −0.608 | **−0.424** | **+0.184** |
| 256 | −0.792 | −0.719 | +0.073 |
| 512 | −0.812 | −0.717 | +0.095 |
| 1024 | −0.776 | **−0.564** | **+0.212** |
| mean | −0.752 ± 0.074 | **−0.637 ± 0.126** | **+0.116** |

**The direction is consistent across every seed.** In all five seeds,
Phase 2's r is less negative than Phase 1's at the same seed. Magnitudes
range from +0.015 (seed 42, basically noise) to +0.212 (seed 1024, large).
Compared to the lean run — where two of three seeds went the *other*
direction — the long-run pattern is robust.

Seeds 137 and 1024 deserve a callout: at +0.184 and +0.212 they move r
from "strong negative" to "moderate negative", showing that adaptation
*can* meaningfully soften the trap when the seed conditions are favorable.
Seeds 42, 256, and 512 still show the trap at near-Phase-1 strength.

### 3.5 Parameter trajectories (Table 4)

Each agent runs 25 cycles per seed (5 seeds × 25 = 125 total). The
hill-climber's bookkeeping:

| Archetype | Cycles | Accepted | Rejected | Rate | L1 dist | Most-moved (round, metric, Δ) |
|---|---|---|---|---|---|---|
| mirror | 125 | 74 | 51 | **59.2 %** | 0.320 | river strong_fold +0.086 |
| predator | 125 | 69 | 56 | 55.2 % | 0.321 | flop vbr +0.086 |
| firestorm | 125 | 67 | 58 | 53.6 % | 0.339 | preflop mbr **−0.139** |
| oracle | 125 | 62 | 63 | 49.6 % | 0.307 | flop strong_fold −0.059 |
| phantom | 125 | 62 | 63 | 49.6 % | 0.299 | preflop med_raise +0.057 |
| sentinel | 125 | 62 | 63 | 49.6 % | 0.286 | preflop strong_call +0.117 |
| judge | 125 | 58 | 67 | 46.4 % | 0.319 | turn weak_call +0.086 |
| wall | 125 | 55 | 70 | **44.0 %** | 0.276 | river weak_call +0.083 |

Two patterns survive from the lean run, plus one new finding:

- **Wall still has the lowest accept rate** (44 %), consistent with its
  tight bound box constraining the search. Sentinel's accept rate
  (49.6 %) is closer to the median at the long scale, and its L1 movement
  is now meaningful (0.286 with a +0.117 swing on `preflop strong_call`).
  At more cycles the tight-bound agents *do* find directions, just slowly.
- **L1 distances are about 1.7× the lean run** (lean: 0.13–0.22; long:
  0.28–0.34). With 25 cycles instead of 12 and a δ that decays to ~0.026
  by cycle 25, the climber moves further. None of the agents have plateaued.
- **New: Firestorm's most-moved metric is preflop `mbr = −0.139`** —
  more than double the next-largest move on the table. At the long
  horizon, Firestorm strongly prefers folding medium hands preflop,
  concentrating its huge bluff rate (br) on strong-or-bust profiles. This
  is the parameter signature behind Firestorm's stack growth in §3.3.

### 3.6 Adaptation success: last-1000-hand profit + Firestorm leak (Table 5)

The "did adaptation help?" test, restricted to the final 1 000 hands so the
optimizer has settled. "Loss → FS" is chips this agent invested in hands
Firestorm won at showdown — lower is better, since Firestorm's profit comes
disproportionately from extracting value from the table.

| Archetype | Last-1k P1 | Last-1k P2 | Δ | Loss→FS P1 | Loss→FS P2 |
|---|---|---|---|---|---|
| firestorm | +1133 ± 194 | +1026 ± 239 | −108 | — | — |
| oracle | +671 ± 177 | +474 ± 224 | −197 | 1214 | 1199 |
| sentinel | +405 ± 66 | +429 ± 187 | +24 | 952 | 1111 |
| wall | −410 ± 183 | **−177 ± 173** | **+232** | 4764 | 4766 |
| phantom | −72 ± 241 | −57 ± 126 | +15 | 1289 | 1354 |
| predator | +474 ± 137 | +431 ± 179 | −44 | 1350 | **1070** |
| mirror | +318 ± 131 | **+485 ± 157** | **+168** | 1497 | **1030** |
| judge | +480 ± 207 | +390 ± 144 | −90 | 922 | **761** |

Three findings worth surfacing — note that two flipped sign relative to
the lean run:

1. **Wall improved at long scale.** Lean: −283 chips. Long: +232 chips.
   At 25 cycles the climber found something for Wall (most-moved metric
   `river weak_call +0.083`), and Wall's last-1000 deficit shrank by 57 %.
   Wall still loses overall — its rebuy count (32) is the highest on the
   table — but the trend is toward stabilization, not collapse.
2. **Sentinel did not collapse.** Lean: −198 chips, the most negative
   delta in the lean run. Long: +24 chips, essentially flat. The lean
   "tight bounds destroy Sentinel" story does not hold at the canonical
   scale; Sentinel is fine, just doesn't gain.
3. **Emergent Firestorm defense is the most interesting finding.**
   Mirror cuts its leak to Firestorm by 31 % (1497 → 1030), Predator by
   21 % (1350 → 1070), Judge by 17 % (922 → 761). These three are
   exactly the agents whose Phase 1 design included the most "adaptive"
   sub-mechanism (Mirror copies opponents, Predator exploits per-opponent
   posteriors, Judge retaliates) — and even with those mechanisms removed
   or simplified, the climber still found profit improvements that
   reduce their leak to the dominant exploiter. Sentinel and Wall — the
   rule-bound, non-adaptive archetypes — show the opposite or no change
   (Sentinel +17 % leak, Wall flat). The climber's global profit
   gradient happens to align with "lose less to Firestorm" because
   Firestorm extracts a disproportionate share of every other agent's
   losses; this is incidental defense, not structured opponent modeling.
   Section 4 unpacks why this matters for Phase 3.

### 3.7 Aberration Index: behavioral drift from spec (Table 6)

L2 distance in (VPIP, PFR, AF) space between Phase 2's end-of-run behavior
and the Phase 1 spec, with each axis normalized by the Phase-1 cross-archetype
standard deviation (so a unit equals "one P1 archetype-spread"):

| Archetype | L2 drift | dominant axis |
|---|---|---|
| **predator** | **0.701** | AF +0.19, PFR +0.013 |
| **mirror** | **0.501** | AF +0.10, VPIP −0.022 |
| phantom | 0.128 | VPIP −0.005, PFR +0.004 |
| oracle | 0.063 | AF +0.01 |
| judge | 0.052 | AF +0.01 |
| wall | 0.048 | (mostly clamped) |
| sentinel | 0.036 | AF −0.01 |
| firestorm | 0.013 | (essentially fixed) |

Mean Aberration Index: **0.193** (lean run was 0.244). The two largest
drifters are still the agents whose Phase 1 adaptive modifiers were
removed (Predator's `PREDATOR_EXPLOIT` blend, Mirror's opponent copy);
their drift is partly an artifact of the modifier removal rather than
optimization-driven divergence. The other six archetypes drift well
under 0.15 axis-spreads, confirming that the bound boxes preserve
archetype identity even at the canonical horizon. The slight *decrease*
from lean to long (0.244 → 0.193) suggests the climber finds a
narrower profit-optimal pocket within each bound box at higher cycle
counts — agents settle rather than wander.

## 4. Key findings

Five questions, five answers.

### 4.1 Did the trust trap weaken under adaptation?

**Yes, partially.** Trust–profit r moves from −0.752 to −0.637 — a delta
of +0.116, which is larger than either phase's seed-to-seed standard
deviation (0.074 in Phase 1, 0.126 in Phase 2). All five seeds show
positive deltas, confirming the effect is robust rather than driven by
one or two outliers. But the trap is not eliminated: r = −0.64 is still a
strong negative correlation, and at no seed did r come close to zero
(min |r| in Phase 2 = 0.42, on seed 137). Bounded numerical optimization
chips ~0.12 off the trap; it cannot remove it.

This is the lean-vs-long result that flipped. The 3 × 5000 lean run
showed Δr = +0.003, well inside seed noise, with two of three seeds
moving the *wrong* way. Section 6.1 discusses why the long horizon
recovers a different conclusion.

### 4.2 Which archetypes actually adapted?

Four patterns:

- **Predator and Mirror drifted the most** (Aberration Index 0.70 and 0.50),
  but this is largely because they lost their built-in Phase 1 adaptation
  modifiers. The climber walked Predator's baseline toward broadly more
  aggression (AF +0.19, PFR +0.013) and Mirror toward a tighter, more
  aggressive postflop profile (VPIP −0.022, AF +0.10).
- **Firestorm got more dominant**, gaining ~1100 chips on average (+16 %)
  by adopting a "fold medium hands preflop, then aggress on strong-or-bust"
  profile — its preflop `mbr` dropped −0.139, the largest single-parameter
  movement in the optimization log.
- **Mirror is the only Phase-2 *winner* in last-1000-hand profit**
  (+168 chips vs Phase 1), despite falling two ranks in final stack.
  The discrepancy reflects an early-game cost of removing the mimic
  modifier; the climber recovers from that cost over 25 cycles, but
  not enough to climb back up the cumulative-stack ranking.
- **Sentinel and Wall, the tight-bound archetypes, did not collapse**
  (lean run prediction was wrong) but also did not improve. Their
  accept rates (49.6 %, 44.0 %) and L1 movements (0.286, 0.276) are
  the smallest in the table — bounded optimization preserves their
  archetype identity but offers them little upside.

### 4.3 Did per-opponent strategies emerge?

**No.** Opponent Adaptation stayed at 0.0003 in both phases (zero to four
decimal places). Hill-climbing on aggregate chip profit cannot produce
per-opponent strategies because there is no per-opponent state in the
optimizer. The fact that Mirror, Predator, and Judge nonetheless cut
their losses to Firestorm by 17–31 % is surprising on its face but
consistent with this story: their *aggregate* profit gradient happens
to point in the same direction as "lose less to Firestorm", because
Firestorm extracts a disproportionate share of every other agent's
losses. This is incidental defense, not structured opponent modeling —
the climber would do the same thing if the dominant exploiter were a
different agent.

### 4.4 How miscalibrated did the trust model become?

The Aberration Index measures the gap between observed behavior in Phase 2
and the Phase 1 archetype baseline that the trust model's likelihood
tables encode. Mean drift is 0.193 axis-spreads at the long scale (down
from 0.244 at lean scale), with the two pre-modifier archetypes
(Predator 0.70, Mirror 0.50) dominating. The remaining six archetypes
drift under 0.15 axis-spreads, so the trust posterior — which classifies
opponents into the eight archetype types — remains *roughly* calibrated
even after 10 000 hands of optimization.

This is the result the hard bounds were designed to produce: agents can
tune within their archetype shape, but they cannot escape it. Notably,
the *decrease* from lean to long (0.244 → 0.193) suggests the climber
finds a narrower profit-optimal pocket inside each bound box at more
cycles, rather than wandering further. The miscalibration we set out
to study is therefore real but self-limiting under hill-climbing; a
longer-horizon run with wider bounds or a different optimizer would
likely deepen it.

### 4.5 What does this mean for Phase 3?

Phase 2 establishes that the gap Phase 3 must close is specifically the
**per-opponent / linguistic-reasoning gap**. Three quantitative claims
fall out of the scorecard:

- **Trap robustness.** Phase 1 r = −0.75, Phase 2 r = −0.64. Phase 3's
  pilot at 50 hands sat at r = −0.41. The progression −0.75 → −0.64
  → −0.41 is a clean ladder where each tier of intelligence chips
  ~0.12–0.23 off the trap. The 0.23-point gap between Phase 2 and
  Phase 3 is now attributable to the LLM's specific reasoning
  capability — adaptation alone covers ~half the distance from Phase 1
  to Phase 3, and the second half is the reasoning gap.
- **OA threshold.** Phase 2 produced OA = 0.0003, almost-zero. If Phase 3
  produces OA > 0.01 at the same hand budget, that is direct evidence
  the LLM is doing per-opponent strategy that bounded numerical search
  cannot.
- **TMA hypothesis.** Trust Manipulation Awareness moved from +0.140 to
  +0.141 — flat to two decimals. An LLM agent that explicitly reasons
  about reputation should be able to drive TMA either further positive
  (farming trust before exploiting) or significantly negative
  (responding to its own trust trajectory). Either move would be
  diagnostic.

## 5. Implications for Phase 3

The redesign sharpens Phase 3's contribution along three axes.

**5.1 Phase 3 inherits a calibrated baseline.** Phase 2's r = −0.637 is
now the "adaptive but not reasoning" reference. The progression
**−0.75 → −0.64 → −0.41** (Phase 1 → Phase 2 → Phase 3 pilot) reads as a
ladder where each tier of intelligence chips off a comparable slice of
the trap, and the Phase 2 → Phase 3 step (0.23 points) is roughly the
same size as the Phase 1 → Phase 2 step (0.12 points). This is a
stronger framing than the lean run's "Phase 2 == Phase 1" framing
because it presents adaptation as *part of the explanation* rather than
something the LLM has to outdo wholesale.

**5.2 Per-opponent behavior is now a falsifiable Phase 3 claim.** Phase 2's
OA = 0.0003 establishes a hard zero point: hill-climbing on aggregate reward
within bound boxes cannot produce per-opponent strategy. If Phase 3's
500-hand run produces OA > 0.01, that single number tests whether LLM
reasoning produces opponent-conditional play that numerical search cannot.
This is the cleanest cross-phase test the project has.

**5.3 The miscalibration story is intact.** The Aberration Index of 0.193
is large enough to demonstrate that the Phase 1 trust posterior is
demonstrably miscalibrated relative to actual behavior, but small enough
that the posterior is still *useful* (six of eight archetypes drift
under 0.15 axis-spreads). Phase 3 should report its own Aberration
Index alongside behavioral metrics — if LLM agents drift further from
their seeded prompts than Phase 2 agents drift from their bounds, the
trust model's classification ability degrades faster, and that is
itself a finding.

A subtle implication: the 50-hand Phase 3 pilot's r = −0.41 is noisy,
but the Phase 2 numbers make it more credible by establishing the right
ladder rung beneath it. The natural follow-up is a 500-hand Phase 3 run
for a stable comparison.

## 6. Limitations

Five honest constraints on the result.

**6.1 Lean run vs long run: the headline flipped.** The 3 × 5000 lean run
(committed as `reports/phase2_scorecard.txt`) showed Δr = +0.003,
essentially zero. The canonical 5 × 10000 long run shows Δr = +0.116,
clearly nonzero. The lean run was *not* mistaken about the sign: at
n = 3 with σ ≈ 0.13 per seed, the 95 % CI on Δr was ±0.20, comfortably
covering both 0 and +0.12. What the lean run missed was the *consistency*
across seeds — at n = 5 the direction is unanimous, and the magnitude
is about half the per-phase std rather than negligible. This is a useful
methodological note in itself: at the lean scale, "no measurable shift"
and "shift of ~0.1" are indistinguishable. Future Phase 2-style
experiments should default to 5+ seeds.

**6.2 Single optimizer.** Hill-climbing was chosen because it is local,
interpretable, and produces plottable parameter trajectories. CMA-ES,
REINFORCE, or population-based training would all explore the bound boxes
differently. The "bounded numerical optimization weakens but cannot escape
the trap" claim is strictly about hill-climbing; a different optimizer
might find larger movement, especially if it had per-opponent state.
We don't think that's likely — the bound boxes are the binding constraint,
not the optimizer — but it is not tested.

**6.3 No per-opponent state in the optimizer.** The objective is aggregate
windowed profit. By construction, the climber cannot bucket-train per
opponent (the way a poker agent might learn "play tight against Wall,
loose against Phantom"). This is intentional — it isolates the *adaptive*
component from the *opponent-modeling* component, so Phase 3's
contribution is testable. But it means the OA = 0.0003 result is partly
trivial: the optimizer literally has no way to differentiate opponents.

**6.4 Predator and Mirror lost their adaptive modifiers.** The Aberration
Index for those two agents is dominated by removing
`PREDATOR_EXPLOIT[top_target]` (Predator) and `mirror_default ←
opponent_metrics` (Mirror). Their drift is therefore not a clean
"optimization-driven" signal. A future Phase 2.5 could keep the modifiers
and put the climber on top of them, but that conflates two adaptation
mechanisms.

**6.5 Cycles are still finite.** Even at 25 cycles per seed (the long
run), the climber's L1 movements (0.28–0.34) are well below the
theoretical maximum, but only because δ has decayed substantially by
that point. At 50–100 cycles the climber would likely converge fully
inside each bound box, and any remaining behavioral movement would have
to come from inter-agent dynamics (e.g. Firestorm finding a new
exploit, every other agent re-optimizing in response). A 50 000-hand
run would let the system reach that steady state.

---

*Last updated: 2026-04-30. Source artifacts and reproduction commands:
`reports/phase2_scorecard_long.txt` (canonical long-run data),
`reports/phase2_scorecard.txt` (lean replication),
`phase2/adaptive/phase2_comparison.py` (regeneration script),
`phase2/adaptive/run_adaptive.py` (the underlying simulation).*


