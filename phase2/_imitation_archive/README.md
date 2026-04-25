# Phase 2 Imitation Archive

This directory holds the original Phase 2 implementation: ML models trained on
Phase 1 hand traces (supervised imitation of the rule-based archetype agents).

It has been **superseded** by `phase2/adaptive/`, which redesigns Phase 2 around
*online adaptive optimization* rather than imitation. The motivation: imitation
models reproduced Phase 1 dynamics by construction, so they couldn't answer the
research question Phase 2 was meant to test ("can a non-LLM learner escape the
trust-profit anticorrelation?").

The code here is preserved untouched so the paper can reference the original
approach and its result. Nothing in here is run by the canonical Phase 2 CLI.

Layout:

- `ml/` — training data, feature engineering, and trained tabular/neural models
- `run_ml_sim.py` — runner that swapped trained ML policies into the engine
- `requirements_ml.txt` — pinned ML dependencies
- `phase2_report.md` — original imitation-Phase-2 results writeup
