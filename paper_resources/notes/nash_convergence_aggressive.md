# Nash Convergence Test (aggressive)

> Aggressive unbounded hill-climbing: 5 seeds × 10,000 hands.
> Each agent independently maximizes its own profit.
> Cluster spread = mean pairwise L1 between 8 agents in 36-dim params.

## Headline

Mean convergence index across 5 seeds: **1.324**.
**NO CONVERGENCE** — agents preserved their archetype diversity.

## Per-seed results

| seed | initial spread | final spread | convergence index | mean drift | max drift |
|---|---|---|---|---|---|
| 42 | 5.821 | 7.518 | 1.291 | 3.380 | 4.148 |
| 137 | 5.821 | 8.139 | 1.398 | 3.612 | 4.862 |
| 256 | 5.821 | 7.556 | 1.298 | 3.238 | 3.928 |
| 512 | 5.821 | 7.736 | 1.329 | 3.245 | 3.997 |
| 1024 | 5.821 | 7.602 | 1.306 | 3.512 | 4.269 |

## Interpretation guide

- **Convergence index ≈ 1.0** — agents barely moved relative to each other.
- **Convergence index < 0.5** — agents merged into a tight cluster (Nash basin).
- **Convergence index < 0.1** — virtually identical strategies.

- **Drift > 5.0** — agent meaningfully migrated from its starting archetype.
- **Drift < 1.0** — agent stayed near its starting profile.

## Figures

- `paper_resources/figures/11_nash_convergence_spread_aggressive.png`
- `paper_resources/figures/12_nash_convergence_drift_aggressive.png`
