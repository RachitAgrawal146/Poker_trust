# Phase 2 Redesign — Plan & Status

**Audience:** Arpit
**Branch:** `phase2-adaptive`
**Status:** stages 1–4 implemented, canonical run (3 seeds × 5000 hands) executed, comparison + writeup pending

---

## TL;DR

We are replacing the imitation-based Phase 2 (ML models trained on
Phase 1 hand traces) with **bounded online hill-climbing**. Each agent
starts from its Phase 1 archetype spec and tunes its own parameters
within an archetype-shaped bound box every 200 hands, maximizing
windowed chip profit. The trust model stays Phase-1-static, so agents
exploit a *miscalibrated* reputation system — a feature, not a bug.

**Headline preliminary result (3 seeds × 5000 hands):**
trust–profit Pearson r is **unchanged** between Phase 1 (−0.77) and
Phase 2 (−0.77). Adaptive optimization within archetype bounds does
not weaken the trust–profit anticorrelation. This is the cleanest
motivation we could ask for Phase 3 (LLM reasoning).

---

## 1. Why we changed Phase 2

The original Phase 2 trained tabular and neural ML models on Phase 1
hand traces and dropped them in as policies. Result: r = −0.825,
behavioral metrics ≈ Phase 1. By construction — supervised imitation
of Phase 1 reproduces Phase 1.

That made Phase 2 a sanity check, not a finding. The three-phase
narrative wasn't supported: Phase 3 (LLM) appeared to be a step over
Phase 1, with Phase 2 a less-effective sibling.

The redesign reframes each phase as testing a different *kind of
intelligence* against the same trust trap:

| Phase | Mechanism | Question |
|---|---|---|
| 1 | Frozen archetype specs | Does fixed strategy cause the trap? |
| 2 | **Online parameter optimization within bounds** | Can numerical search escape the trap? |
| 3 | LLM symbolic / linguistic reasoning | Can qualitative reasoning succeed where numerical search fails? |

The original Phase 2 code lives untouched at
`phase2/_imitation_archive/` — preserved on-tree so the paper can
cite both approaches.

---

## 2. The four design decisions

These are the choices that shape the result. Each is locked in the
current implementation; if you want to revisit any of them, flag it
before the comparison and report stages.

### 2a. Bounded online hill-climbing (not REINFORCE / CMA-ES)

Every 200 hands the climber alternates between baseline (measure
profit on current params) and trial (perturb one (round, metric) by
±δ, measure profit). Accept if better, revert otherwise. δ starts
at 0.03 and decays geometrically with a floor at 0.005.

Why hill-climbing over policy gradient: the paper's question is
"what does *adaptive but not-reasoning* look like?" — local search
is exactly that, and the param trajectories are interpretable
(plottable). REINFORCE collapses fast toward Nash-ish play and
erodes archetypes.

### 2b. Hard bounds, not soft regularizers

Each archetype gets a (lo, hi) box per (round, metric). Wall's
`br` ∈ [0.00, 0.05]; Sentinel's `vbr` ∈ [0.85, 1.00]; Firestorm's
`br` ∈ [0.40, 0.95]. Bounds are derived from the Phase 1 starting
value plus a personality-appropriate margin (±10 % tight, ±25 %
moderate, ±35 % loose).

Identity-locked metrics (Wall.br, Wall.strong_raise, Wall.med_raise,
Sentinel.br) are clamped near zero so the *shape* of the archetype
survives optimization.

### 2c. Uniform profit objective (not per-archetype reward functions)

All eight agents maximize plain windowed chip profit. We don't give
Sentinel a risk-adjusted objective or Phantom a deception-success
objective — the bounds *already* shape the search space, and per-
archetype objectives would muddy attribution ("did results differ
because of adaptation, or because the objective changed?").

### 2d. Trust model stays Phase-1-static

`trust/bayesian_model.py` imports the original `ARCHETYPE_PARAMS` /
`HONESTY_SCORES` tables. As agents adapt, their behavior drifts but
the trust posterior keeps using the original likelihoods. This means
agents are exploiting a *miscalibrated* reputation system — which
maps onto a real-world insight: a person's reputation lags their
behavior. Stage 5's analysis quantifies how miscalibrated it gets.

---

## 3. File layout

```
phase2/
├── _imitation_archive/         # Old ML Phase 2, preserved untouched
│   ├── README.md               # Pointer + reason for archive
│   ├── ml/                     # Trained tabular/neural models
│   ├── run_ml_sim.py
│   ├── phase2_report.md        # Original imitation results
│   └── requirements_ml.txt
└── adaptive/                   # New Phase 2
    ├── __init__.py
    ├── bounds.py               # ARCHETYPE_BOUNDS dict (Stage 1)
    ├── adaptive_agent.py       # AdaptiveAgent + AdaptiveJudge (Stage 2)
    ├── hill_climber.py         # HillClimber optimizer (Stage 3)
    ├── run_adaptive.py         # 3-seed × 5000-hand runner (Stage 4)
    ├── param_trajectories.json # written by runner
    ├── optimization_log.json   # written by runner
    ├── phase2_comparison.py    # PENDING (Stage 5)
    └── phase2_report.md        # PENDING (Stage 6)
```

Phase 1 code is **untouched**. The runner imports Phase 1's `engine/`,
`trust/`, `data/sqlite_logger.py`, and `agents/base_agent.py`
verbatim. Schema is identical, so `analyze_runs.py`, `deep_analysis.py`,
and `compute_metrics.py` work on the Phase 2 SQLite without
modification.

---

## 4. Implementation status

Commits on branch `phase2-adaptive`:

| Hash      | Stage | What it adds |
|-----------|-------|--------------|
| `2fc4b24` | 0     | Archive `phase2/ml/` → `_imitation_archive/` |
| `0060d5f` | 1     | `bounds.py` — per-archetype `(lo, hi)` per (round, metric) |
| `952dc29` | 2     | `AdaptiveAgent`, `AdaptiveJudge` (mutable params, `record_snapshot`) |
| `c1b85fe` | 3     | `HillClimber` (baseline / trial cycle, log, decay) |
| `a342ec0` | 4     | `run_adaptive.py` (3-seed runner; smoke 30h OK) |

Canonical run executed:

```
python3 phase2/adaptive/run_adaptive.py --hands 5000 --seeds 42,137,256
```

- Wall time: ~25 minutes
- LLM calls: 0 (Phase 1 engine, no LLM in this phase)
- Chip conservation: **OK on all 3 seeds**
- Each agent: 12 hill-climb cycles per seed (≈4 accept + 6 reject + 2
  on-boundary, varies)
- Judge triggered on 6/7 opponents (seed 42), 7/7 (seed 137), 6/7
  (seed 256) — much more saturated than Phase 1 because adapted
  agents drove their bluff rates higher

Reference Phase 1 run executed at the same scale (3 seeds × 5000
hands) for the comparison: `runs_phase1_ref.sqlite`.

---

## 5. Preliminary results (full scorecard pending Stage 5)

The two big questions and what we see so far:

### Q1: Did the trust–profit anticorrelation weaken?

**No.** Mean across 3 seeds:

| Phase | Seed 42 | Seed 137 | Seed 256 | Mean |
|---|---|---|---|---|
| 1 (frozen) | −0.838 | −0.825 | −0.654 | **−0.773** |
| 2 (adaptive) | −0.878 | −0.858 | −0.573 | **−0.769** |

Within seed-to-seed variation. The trap is **structurally robust** to
bounded numerical optimization. This is the strongest possible
motivation for Phase 3.

### Q2: Did the economic ordering change?

Largely no, but Firestorm got *more* dominant under adaptation.

| Archetype | Phase 1 final stack (seed 42) | Phase 2 final stack (seed 42) |
|---|---|---|
| oracle    | 1409 | 887 |
| sentinel  | 1065 | 739 |
| firestorm | 2925 | **3606** |
| wall      |   57 |   69 |
| phantom   |   34 |  105 |
| predator  |  243 |  400 |
| mirror    |  757 |  376 |
| judge     |  310 |  618 |

(Seed-42 numbers; the Stage 5 scorecard will average across all 3
seeds and add std.) Firestorm climbed; Mirror dropped; Wall stayed
nailed to the floor (rebuy count: 12 → 13). Adaptation didn't save
the most-trusted agents — Wall keeps losing despite tuning.

### Other behavioral dimensions

Stage 5 will compute Phase 1 vs Phase 2 for: Context Sensitivity,
Opponent Adaptation, Non-Stationarity, Strategic Unpredictability,
Trust Manipulation Awareness — using the existing
`compute_metrics.py` functions on both DBs. Predictions:

- **NS rises** by construction — params change, action distribution
  changes. Likely 0.05+ vs Phase 1's 0.002.
- **OA stays near zero** — hill-climbing on aggregate reward can't
  produce per-opponent strategies. This is the result that motivates
  Phase 3.
- **CS, SU, TMA** — uncertain; will report.

---

## 6. What this means for Phase 3

The redesign **sharpens Phase 3's contribution**:

- Phase 3's question becomes precise: *can symbolic reasoning
  produce the opponent-conditional behavior (OA > 0) that bounded
  numerical optimization cannot?* If Phase 2's OA ≈ 0 and Phase 3's
  OA > 0.01, that's the headline number of the paper.
- Phase 3's "trust manipulation" claim becomes testable. An LLM
  agent claiming to "reason about reputation" is more convincing if
  Phase 2 (with optimization power but no reasoning) fails at
  reputation management. We can compare TMA across phases as a
  direct test.
- The just-pushed Phase 3 50-hand pilot (`reports/phase3_scorecard.txt`,
  branch `claude/run-phase3-poker-nGwB5`) showed Phase 3 r = −0.41.
  With Phase 2 r = −0.77, the gap **−0.77 → −0.41** is now
  attributable to LLM reasoning specifically, not to "having any
  adaptive mechanism at all."

The 50-hand Phase 3 r is noisy — the natural follow-up is a
500-hand Phase 3 run for a stable comparison.

---

## 7. Open questions / decisions for you

Each of these is a fork in the road. Default in parens is what's in
the code; tell me if you want a different choice and I'll re-run.

1. **Bound widths** (locked). Currently ±10 % tight / ±25 %
   moderate / ±35 % loose. If results show Wall is just oscillating
   at its boundaries, we should widen Wall's box; if Firestorm
   converged to a single point, we widen Firestorm's box and re-run.
2. **`eval_window = 200`** (locked). 200-hand baseline + 200-hand
   trial = 400 hands per cycle. With 5000 hands that's ~12 cycles
   per agent. If we want more cycles, lower to 100 and re-run.
3. **`delta = 0.03` initial, decay 0.995** (locked). With 12 cycles
   delta only decays from 0.03 → 0.028 — basically constant. That's
   intentional at this hand count. If we extend to 20k hands, the
   decay schedule should be revisited.
4. **3 seeds × 5000 hands** (run). Spec said "lean run." Phase 1's
   canonical research run is 5 seeds × 10000 hands. If we want to
   match, the cost is roughly 4× the current ~25 min ≈ ~1.5 hr.
5. **No per-opponent adaptation by design** (intentional). This is
   *the* limitation that makes Phase 3 necessary. If you want to
   relax it (let the climber bucket-train per opponent), that's a
   separate research direction (Phase 2.5?).

---

## 8. What's next

Stage 5 (`phase2/adaptive/phase2_comparison.py`) — generate six
tables comparing Phase 1 and Phase 2 across:

1. Behavioral fingerprints (VPIP / PFR / AF per archetype)
2. Final stacks + economic ordering
3. Trust–profit r (already computed, see §5)
4. Parameter trajectories (which params moved, which were rejected)
5. Adaptation success (per-archetype profit improvement)
6. Trust-model miscalibration (gap between posterior classification
   and adapted behavior)

Stage 6 (`phase2/adaptive/phase2_report.md`) — paper-style writeup
of the comparison, with the §5 headline number front and center.

Both stages then commit + push to `phase2-adaptive`. Estimated 1–2
hours.

---

*Last updated: 2026-04-25 16:55 UTC. Run artifacts: `runs_phase2_adaptive.sqlite`, `runs_phase1_ref.sqlite`, `phase2/adaptive/param_trajectories.json`, `phase2/adaptive/optimization_log.json`.*
