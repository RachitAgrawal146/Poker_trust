# Phase 2 — Bounded Online Optimization

Phase 2 keeps Phase 1's eight rule-based archetypes and adds a per-cycle
hill-climber that lets each agent tune its own decision parameters
within an archetype-shaped bound box. Everything else — engine, trust
model, analysis pipeline — is reused unchanged. The headline result is
that bounded optimization softens the trust–profit anticorrelation
from r = −0.752 to r = −0.637 (Δr = +0.116) without closing it.

A sub-experiment, **Phase 2\* unbounded**, replaces the bound boxes with
the full unit hypercube and turns up the optimizer step size to test
whether economically-motivated agents converge to a Nash-like profile.
They do not — cluster spread grows from 5.82 to 7.5+ on every seed.

> The earlier ML-imitation Phase 2 (which reproduced Phase 1 by
> construction by training tabular and neural models on Phase 1 hand
> traces) was superseded by this adaptive redesign and removed from the
> tree in May 2026. See `docs/CHANGELOG.md` for the original Phase 2
> milestone and the redesign rationale.

## Contents

| File / Dir | Purpose |
|------------|---------|
| `adaptive/` | Canonical Phase 2 — bounded online hill-climbing |
| `adaptive/adaptive_agent.py` | `AdaptiveAgent` + `AdaptiveJudge` wrappers |
| `adaptive/bounds.py` | Per-archetype parameter bound boxes + `make_unbounded_bounds()` helper |
| `adaptive/hill_climber.py` | Per-cycle perturb-and-accept optimizer |
| `adaptive/run_adaptive.py` | Simulation runner (`--unbounded` toggles Phase 2\*) |
| `adaptive/phase2_comparison.py` | Phase 1 vs Phase 2 cross-phase metrics |
| `adaptive/phase2_report.md` | Full Phase 2 writeup |
| `adaptive/PHASE2_REDESIGN_PLAN.md` | Pre-work design brief (historical) |
| `adaptive/param_trajectories*.json` | Per-agent parameter history per cycle |
| `adaptive/optimization_log*.json` | Per-cycle accept/reject log |

## Quick start

```bash
# Phase 2 bounded (canonical, 5 seeds × 10 000 hands)
python phase2/adaptive/run_adaptive.py --hands 10000 --seeds 42,137,256,512,1024 \
    --db runs_phase2_long.sqlite

# Phase 2* unbounded (aggressive HC — the Nash-falsification run)
python phase2/adaptive/run_adaptive.py --hands 10000 --seeds 42,137,256,512,1024 \
    --db runs_phase2_unbounded_aggressive.sqlite \
    --unbounded --hc-delta 0.15 --hc-eval-window 50

# Phase 1 vs Phase 2 comparison report
python -m phase2.adaptive.phase2_comparison --p1-db runs_phase1_long.sqlite \
    --p2-db runs_phase2_long.sqlite > reports/phase2_scorecard_long.txt
```

## Relation to Phase 1

Phase 2 **imports** Phase 1's building blocks without modifying them:

- `engine.table.Table` — same game loop
- `agents/<archetype>.py` — wrapped by `AdaptiveAgent`, original
  decision logic intact
- `trust.bayesian_model` — same Phase 1 likelihood tables
  (intentionally stationary across all numerical phases)
- `data.sqlite_logger.SQLiteLogger` — same schema

The Phase 1 trust posterior is deliberately *not* refit per Phase 2.
The adapting agents are exploiting a stale reputation system; that is
the experiment.
