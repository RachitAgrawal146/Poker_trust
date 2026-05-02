# reports/

Generated scorecards and audit dumps for every phase. The four canonical
reports below are the ones referenced in `paper.md`, `README.md`, and
each phase's `*_report.md`. Historical artifacts from earlier
iterations are preserved in `_legacy/`.

## Canonical reports

| File | Phase | Scope | Headline |
|---|---|---|---|
| `phase2_scorecard.txt` | 1 vs 2 | 3 seeds × 5000 hands (lean) | r drops -0.77 → -0.77 (within seed noise) |
| `phase2_scorecard_long.txt` | 1 vs 2 | 5 seeds × 10 000 hands | r drops -0.752 → -0.637 (Δ = +0.115) |
| `phase3_long_scorecard.txt` | 3 | 5 seeds × 500 hands | r = -0.510 (LLM role-play) |
| `phase31_long_scorecard.txt` | 1/2/3/3.1 | 5 seeds × 150 hands | **r = -0.094 (trap broken)** |

## How to regenerate

Phase 2 scorecards (run after Phase 1 + Phase 2 SQLite databases exist):

```
python phase2/adaptive/phase2_comparison.py \
  --phase1-db runs_phase1_long.sqlite \
  --phase2-db runs_phase2_long.sqlite \
  --trajectories phase2/adaptive/param_trajectories_long.json \
  --optlog phase2/adaptive/optimization_log_long.json \
  --output reports/phase2_scorecard_long.txt
```

Phase 3 / 3.1 scorecards:

```
# Per-seed JSON (small, no LFS issue)
python extract_phase3_stats.py --db runs_phase3_long.sqlite   --out phase3_stats.json
python extract_phase3_stats.py --db runs_phase31_long.sqlite  --out phase31_stats.json

# Six-dimension behavioral scorecard (Phase 1 baseline format)
PYTHONIOENCODING=utf-8 python compute_metrics.py --db runs_phase3_long.sqlite   > reports/phase3_long_scorecard.txt
PYTHONIOENCODING=utf-8 python compute_metrics.py --db runs_phase31_long.sqlite  > reports/phase31_long_scorecard.txt
```

## `_legacy/` — historical artifacts (do not cite in the paper)

These date from earlier iterations of the project (before the Phase 2
redesign and before Phase 3): the original Phase 1 deep-analysis dumps,
the ML-imitation Phase 2 reports, the 50-hand Phase 3 pilot, and the
"interesting hands" narrative tooling. Preserved for historical
reference; superseded by the canonical files above.

| File | Note |
|---|---|
| `analyze_v3.txt` | Phase 1 9-section standard report (5 seeds × 500k hands historical run) |
| `metrics_scorecard.txt` | Phase 1 6-dimension scorecard (historical baseline, r = -0.837) |
| `deep_analysis_v3_*.txt` | Phase 1 31-section deep analysis dumps |
| `comparison_final.txt` | Pre-redesign Phase 1 vs imitation-Phase 2 comparison |
| `ml_deep_analysis_final.txt` | Imitation-based Phase 2 (now in `phase2/_imitation_archive/`) |
| `phase3_scorecard.txt` | Phase 3 50-hand pilot scorecard (superseded by `phase3_long_scorecard.txt`) |
| `dealer_audit*.json` | Old Phase 3 dealer audit dumps |
| `interesting_hands.txt` / `interesting_hands_narrative.md` | Pre-Phase-3 hand-narrative tooling output |
