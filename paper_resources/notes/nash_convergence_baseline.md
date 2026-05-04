# Nash Convergence Test (baseline)

> Aggressive unbounded hill-climbing: 5 seeds × 10,000 hands.
> Each agent independently maximizes its own profit.
> Cluster spread = mean pairwise L1 between 8 agents in 36-dim params.

## Headline

Mean convergence index across 5 seeds: **1.016**.
**NO CONVERGENCE** — agents preserved their archetype diversity.

## Per-seed results

| seed | initial spread | final spread | convergence index | mean drift | max drift |
|---|---|---|---|---|---|
| 42 | 5.821 | 5.922 | 1.017 | 0.321 | 0.415 |
| 137 | 5.821 | 5.968 | 1.025 | 0.281 | 0.399 |
| 256 | 5.821 | 5.905 | 1.014 | 0.271 | 0.459 |
| 512 | 5.821 | 5.918 | 1.017 | 0.276 | 0.423 |
| 1024 | 5.821 | 5.852 | 1.005 | 0.278 | 0.427 |

## Interpretation guide

- **Convergence index ≈ 1.0** — agents barely moved relative to each other.
- **Convergence index < 0.5** — agents merged into a tight cluster (Nash basin).
- **Convergence index < 0.1** — virtually identical strategies.

- **Drift > 5.0** — agent meaningfully migrated from its starting archetype.
- **Drift < 1.0** — agent stayed near its starting profile.

## Figures

- `paper_resources/figures/11_nash_convergence_spread_baseline.png`
- `paper_resources/figures/12_nash_convergence_drift_baseline.png`
