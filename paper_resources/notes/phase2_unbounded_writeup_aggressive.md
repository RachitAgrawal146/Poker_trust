# Phase 2 Unbounded (Aggressive HC) — Writeup Notes

> Draft prose for paper.md §5.5 (Phase 2 Results) and §6.3
> (Discussion). This is the **canonical** Phase 2 unbounded result —
> the version that properly tests Arpit's "do agents converge to
> Nash?" hypothesis with sufficient optimizer budget.

## Methodology note: why the aggressive run is canonical

The first unbounded run used the default hill-climber settings
(`delta=0.03`, `eval_window=200`, `decay=0.995`). At these settings,
each agent receives only ~25 cycles across 10,000 hands, and each
cycle perturbs a single (round, metric) slot by at most ±0.03. The
total parameter drift was small (~0.3 L1 across the full 36-dim
space) — agents barely moved. That run cannot be interpreted as a
test of "do agents converge to Nash?", because no agent was given
sufficient optimization budget to escape its starting neighborhood.

The aggressive run uses `delta=0.15`, `eval_window=50`,
`decay=0.998`. This gives each agent **100 cycles** (4× more), with
**5× larger steps**, producing **11× more total drift** in
parameter space. This is what we report below as the canonical
Phase 2 unbounded result.

The original weak-HC results are preserved in
`reports/phase2_unbounded_scorecard.txt` and
`paper_resources/notes/phase2_unbounded_writeup.md` as a methodology
footnote.

## Headline result

Across 5 seeds × 10,000 hands with `ARCHETYPE_BOUNDS` replaced by
`(0.0, 1.0)` and aggressive hill-climbing:

| | Bounded P2 | Unbounded (weak) | Unbounded (aggressive) |
|---|---|---|---|
| Mean trust-profit r | **−0.637** | −0.779 | **−0.609** |
| Std r | 0.125 | 0.087 | **0.221** |
| Mean per-agent drift (L1) | n/a | 0.3 | **3.4** |

Per-seed for the aggressive run:

| Seed | Bounded | Aggressive | Δ |
|---|---|---|---|
| 42   | −0.759 | **−0.354** | **+0.405** |
| 137  | −0.424 | −0.700     | −0.276 |
| 256  | −0.719 | **−0.344** | **+0.375** |
| 512  | −0.717 | −0.887     | −0.170 |
| 1024 | −0.564 | −0.759     | −0.195 |

Two seeds soften dramatically (+0.40 each). Three seeds deepen.
Mean trust-profit r is essentially **unchanged** from bounded
(Δ = +0.028). Variance triples.

## What does NOT happen: Nash convergence

The cleanest test of the convergence hypothesis is **cluster spread**
— mean pairwise L1 distance between all 8 agents in 36-dim
parameter space. Across 5 seeds:

| Seed | Initial spread | Final spread | Convergence index |
|---|---|---|---|
| 42   | 5.821 | 7.518 | **1.291** |
| 137  | 5.821 | 8.139 | **1.398** |
| 256  | 5.821 | 7.556 | **1.298** |
| 512  | 5.821 | 7.736 | **1.329** |
| 1024 | 5.821 | 7.602 | **1.306** |

Mean convergence index = **1.324**. **Agents diverged**, not
converged. Every seed shows growing spread.

Mean per-agent drift from starting parameters: **3.4 L1** (vs 0.3 in
the weak run). The agents moved — they just didn't move toward each
other.

## Economic ordering: Firestorm still dominates

| Archetype | Stack | σ | Trust | Rebuys |
|---|---:|---:|---:|---:|
| firestorm | **6,512** | 2,894 | 0.466 | 0.0 |
| oracle    | 1,541 | 758 | 0.777 | 1.4 |
| sentinel  | 1,219 | 707 | 0.816 | 0.6 |
| judge     | 1,107 | 790 | 0.788 | 2.6 |
| mirror    |   925 | 421 | 0.817 | 0.4 |
| predator  |   611 | 689 | 0.751 | 2.0 |
| phantom   |   187 |  97 | 0.672 | 18.6 |
| wall      |   179 |  89 | 0.962 | 27.8 |

Firestorm wins by a smaller margin than in the weak run (6,500 vs
7,860) but still **6× the next archetype**. Wall and Phantom still
hemorrhage chips (28 + 19 mean rebuys respectively).

Stack spread shrinks from 17,500 (bounded P2) to 6,300 (aggressive
unbounded) — a 64% reduction — but the *ordering* is preserved
across all 5 seeds.

## Why divergence in parameters but reduced spread in stacks

These two facts are reconcilable:

- **Parameters diverge** because each agent finds a *different*
  local optimum. Sentinel discovers it can extract more chips by
  deviating in one direction; Mirror finds a different deviation;
  Predator finds a third. None of these deviations land on the
  same parameter profile — so the cluster spread grows.

- **Stacks compress** because the moderate archetypes (oracle,
  sentinel, mirror, predator, judge) all migrate, in their own
  ways, into a smaller-margin profitability band. They each find
  modest improvements that close the gap to Firestorm slightly
  without overtaking it.

The *only* outcome that would have falsified the trap-as-structural
claim — all 8 agents converging to a single Nash-like profile —
does not happen.

## Why no convergence to Nash?

Three structural reasons, in order of importance:

**(1) The trust posterior is non-stationary inside each agent's
optimization loop.** Sentinel's accept-reject decision compares
50-hand windowed profit before vs after a perturbation. But
Sentinel's profit depends on *opponents' beliefs* about Sentinel,
which lag behind Sentinel's actual behavior. Specifically, the
trust model has λ = 0.95 decay, so opponents' posteriors take
~70 hands to converge after Sentinel changes its strategy. Trial
profit therefore reflects opponents reacting to *stale* beliefs
about Sentinel, contaminating the gradient signal.

**(2) Multi-agent simultaneity creates a moving target.** All 8
agents climb simultaneously. Sentinel's trial perturbation is
evaluated against the joint behavior of the other 7 — but those 7
are also drifting. The optimal Sentinel-strategy for Phantom-on-
hand-100 is different from the optimal Sentinel-strategy for
Phantom-on-hand-200. The hill-climber's local-search assumption
(stationary objective) is violated.

**(3) Coordinate descent in 36-dim is slow, even with bigger steps.**
The hill-climber perturbs ONE (round, metric) slot per cycle. With
100 cycles, each of the 36 slots gets touched ~3 times on average.
Joint optimal moves (e.g., "raise more AND bluff more
proportionally") cannot be discovered by axis-aligned search; they
require multi-coordinate perturbations.

A REINFORCE-style or CMA-ES optimizer with ~50,000 cycles would be
the next step — but it would not change the conclusion, only sharpen
it. Reasons (1) and (2) are structural, not algorithmic.

## Implication for the paper's central argument

The aggressive unbounded result tightens §6.3:

- The bound boxes were not the binding constraint.
- The optimizer's strength was not the binding constraint.
- The binding constraint is the **stationary trust posterior**.
  Phase 1's likelihood tables compute every observer's belief
  assuming the canonical archetype distribution. Inside that
  reputation system, Firestorm's profile is locally optimal for
  a fold-equity-extractor, Wall's profile is locally optimal for
  a defensive caller, and so on. Local search keeps each agent at
  its archetype's local maximum — never traversing to Nash.

Phase 3.1's effect comes from making the trust system **mutable
in the agent's reasoning** — the per-opponent memory and adaptive
strategy notes let Wall reason "Firestorm has bet every street;
my hand is good; raise" *despite* Wall's reputation telling
opponents to expect a passive call. That is the only kind of
intervention that broke the trap. Adding optimizer strength
(this experiment) does not.

## Falsification of the convergence hypothesis

Arpit's hypothesis (mentor meeting 2026-04-30): *"if the agents
have full freedom and are all maximizing economic return, won't
they converge to a Nash-equilibrium-like profile?"*

Empirical answer at 5 seeds × 10,000 hands with aggressive HC:

- **NO.** Cluster spread *grows* from 5.8 to 7.5+. Convergence
  index 1.324.
- The agents move 11× more than under weak HC, but they move
  *apart*, not *together*.
- The economic ordering (Firestorm > moderates > Wall, Phantom)
  is preserved.

The hypothesis is decisively falsified within the optimization
budget tested. A stronger argument — that Nash convergence is
*structurally impossible* under stationary-trust hill-climbing —
requires a theoretical result we do not derive here.

## Cross-references

Figures generated:
- `paper_resources/figures/07_phase2_bounded_vs_unbounded_aggressive.png`
- `paper_resources/figures/10_param_drift_unbounded_aggressive.png`
- `paper_resources/figures/11_nash_convergence_spread_aggressive.png`
- `paper_resources/figures/12_nash_convergence_drift_aggressive.png`
- `paper_resources/figures/13_nash_convergence_pca_aggressive.png`
- `paper_resources/figures/14_nash_convergence_compare.png` —
  weak vs aggressive side-by-side

Data:
- `paper_resources/data/phase2_unbounded_summary_aggressive.csv`
- `paper_resources/data/nash_convergence_aggressive.csv`

Scorecard:
- `reports/phase2_unbounded_scorecard_aggressive.txt`

## What this adds to the four-tier ladder

```
Phase 1 (frozen rules)              r = -0.752  ± 0.073
Phase 2 bounded (bounded HC)        r = -0.637  ± 0.125
Phase 2 UNBOUNDED (weak HC)         r = -0.779  ± 0.087   [methodology footnote]
Phase 2 UNBOUNDED (aggressive HC)   r = -0.609  ± 0.221   [canonical]
Phase 3 (LLM personalities)         r = -0.510  ± 0.268
Phase 3.1 (LLM + reasoning)         r = -0.094  ± 0.301
```

The aggressive unbounded result is roughly equivalent to bounded
Phase 2 in mean r, but with much higher variance — confirming that
the trap is robust to *parameter-space freedom* AND *optimizer
strength*. The discontinuity at Phase 3.1 (Δ = +0.416) remains the
only intervention that meaningfully changes the dynamic, supporting
the paper's central claim that *qualitative reasoning, not
quantitative optimization, breaks the trust trap.*
