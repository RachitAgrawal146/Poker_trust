# Paper Resources

Materials for writing the Polygence research paper externally
(Overleaf). The paper itself is **not** in this repo — only the
assets needed to write it: publication-ready figures, LaTeX table
snippets, CSV data, curated hand transcripts, and topical writeups.

The headline argument the paper has to defend is a **five-tier
ladder** of trust–profit Pearson r across agent architectures:

```
Phase 1 (frozen rule-based)              r = -0.752 ± 0.073
Phase 2 (bounded hill-climbing)          r = -0.637 ± 0.125
Phase 2* (unbounded HC, aggressive)      r = -0.609 ± 0.221   ← Nash falsification
Phase 3 (LLM personality role-play)      r = -0.510 ± 0.268
Phase 3.1 (LLM + CoT + memory + adaptive) r = -0.094 ± 0.301  ← trap broken
```

(A weak-HC unbounded variant at r = −0.779 is preserved as a
methodology footnote — see `notes/phase2_unbounded_writeup.md`.)

## Folder layout

```
paper_resources/
├── README.md                         (you are here — index of assets)
├── figures/                          (publication-ready PNGs, 180 dpi)
├── tables/                           (LaTeX `tabular` snippets)
├── data/                             (CSV source data behind every table)
├── interesting_hands/                (curated hand transcripts per phase)
└── notes/                            (topical writeups — methodology, discussion, future work)
```

## Figures (20 PNGs)

Headline / cross-phase:

| File | Use for |
|---|---|
| `01_four_tier_ladder.png` | Headline 4-tier r ladder (backward compatible) |
| `01b_five_tier_ladder_with_unbounded.png` | **Five-tier ladder including Phase 2\*** (preferred) |
| `02_per_seed_ladder.png` | Per-seed dot plot showing variance growth across phases |
| `03_economic_inversion.png` | Wall 8→1, Oracle 3→8: most-trusted wins in P3.1 |
| `04_behavioral_shift.png` | VPIP/PFR/AF shifts P1 vs P3.1 |
| `05_trust_vs_stack.png` | Pooled trust-vs-stack scatter |
| `06_tma_by_archetype.png` | Trust Manipulation Awareness per archetype |

Phase 2 unbounded sub-experiment:

| File | Use for |
|---|---|
| `07_phase2_bounded_vs_unbounded.png` | Per-seed r delta + economic ordering (weak HC) |
| `07_phase2_bounded_vs_unbounded_aggressive.png` | Same, aggressive HC (canonical) |
| `08_stack_trajectories_phase2_unbounded.png` | Firestorm runs away while Wall hemorrhages |
| `09_trust_evolution_phase2_unbounded.png` | Per-archetype trust over 10 000 hands |
| `10_param_drift_unbounded.png` | Preflop bluff-rate drift (weak HC — agents barely move) |
| `10_param_drift_unbounded_aggressive.png` | Aggressive HC — 11× more drift |

Nash convergence test (per Arpit's 2026-04-30 question):

| File | Use for |
|---|---|
| `11_nash_convergence_spread_baseline.png` | Weak HC: cluster spread per seed |
| `11_nash_convergence_spread_aggressive.png` | Aggressive HC: cluster spread grows on every seed |
| `12_nash_convergence_drift_baseline.png` | Per-agent L1 drift, weak HC |
| `12_nash_convergence_drift_aggressive.png` | Per-agent L1 drift, aggressive HC |
| `13_nash_convergence_pca_baseline.png` | 2D PCA trajectory, weak HC |
| `13_nash_convergence_pca_aggressive.png` | 2D PCA trajectory, aggressive HC |
| `14_nash_convergence_compare.png` | Weak vs aggressive side-by-side (use this one figure) |

## Tables (5 LaTeX snippets)

Drop-in `tabular` blocks for `\input{}` in Overleaf:

- `headline_ladder.tex` — the five-tier r table
- `per_archetype_p31.tex` — Phase 3.1 per-archetype stack / trust / rebuys
- `behavioral_shift_p1_p31.tex` — VPIP/PFR/AF Phase 1 vs Phase 3.1
- `tma_by_archetype.tex` — Trust Manipulation Awareness per archetype
- `economic_inversion.tex` — Wall 8→1 economic-ordering shift table

## Data (13 CSVs)

Every figure and table traces back to one of these CSVs. Open in
Excel / Python / a Polygence reviewer's spreadsheet if asked for raw
numbers.

| File | Backs |
|---|---|
| `headline_ladder.csv` | `headline_ladder.tex`, figures 01 / 01b / 02 |
| `per_archetype_p31.csv` | `per_archetype_p31.tex`, figure 06 |
| `behavioral_shift_p1_p31.csv` | `behavioral_shift_p1_p31.tex`, figure 04 |
| `tma_by_archetype.csv` | `tma_by_archetype.tex`, figure 06 |
| `economic_inversion.csv` | `economic_inversion.tex`, figure 03 |
| `per_seed_stacks_p3.csv` | Per-seed stacks for Phase 3 |
| `per_seed_stacks_p31.csv` | Per-seed stacks for Phase 3.1 |
| `phase2_unbounded_summary.csv` | Phase 2\* weak HC summary |
| `phase2_unbounded_summary_aggressive.csv` | Phase 2\* aggressive HC summary (canonical) |
| `r_bootstrap_ci.csv` | Per-phase mean-r t-interval + bootstrap CI, per-seed Fisher-z CI (from `analysis/bootstrap_ci.py`) |
| `nash_convergence_baseline.csv` | Cluster spread + drift, weak HC |
| `nash_convergence_aggressive.csv` | Cluster spread + drift, aggressive HC |
| `unbounded_archetype_drift.csv` | L1-distance-to-canonical for each agent |

## Interesting hands (one transcript file per phase)

`EVOLUTION_STORY.md` is the narrative arc: an 8-slot story-hand
catalogue (A1.1 walkover, A1.2 Wall pays off Firestorm, etc.) plus
the slot-to-paper-section mapping. The per-phase story files
contain the actual transcripts:

- `p1_story.txt` — Phase 1 (8 slots × 5 seeds = up to 40 hands)
- `p2-bounded_story.txt` — Phase 2 bounded HC
- `p2-unbounded_story.txt` — Phase 2\* unbounded
- `p3_story.txt` — Phase 3 LLM (hand #67 = "the trap": Wall calls down with 2♠5♣)
- `p31_story.txt` — Phase 3.1 LLM + reasoning (hand #146 = "the inversion": Wall value-bets Firestorm with K♥Q♥)

`_highlights.txt` plus `phase2_unbounded_seed_*.txt` are the raw
biggest-pot dumps per seed (useful as a backup if a specific story
hand isn't compelling enough for the paper).

The **two "money quote" hands** for talks and paper figures:
- **P3 hand #67** — Wall (2♠5♣, rank 6749) calls a 4-bet pot all the way down, loses 35 chips to Firestorm's J♥J♦. Pure trap.
- **P3.1 hand #146** — Wall (K♥Q♥, rank 872) calls Firestorm's flop + turn bets, bets the river when Firestorm checks, gets called by Q-high. Wall wins 32 chips from Firestorm. Trap inverted.

## Notes (topical writeups, draft material)

These are **draft prose** the user can selectively quote, paraphrase,
or use as fact-check references when writing the paper externally.
Each note covers one self-contained topic.

| File | Topic |
|---|---|
| `phase2_unbounded_writeup_aggressive.md` | **Canonical** Phase 2\* writeup — methodology, results, Nash falsification |
| `phase2_unbounded_writeup.md` | Weak-HC variant — preserved as methodology footnote |
| `nash_convergence_aggressive.md` | Cluster-spread numbers + interpretation guide |
| `nash_convergence_baseline.md` | Same for the weak run (reference only) |
| `unbounded_archetype_drift.md` | L1 distance to canonical archetype: agents stay closest to themselves on every seed |
| `societal_implications.md` | Real-world parallels (eBay, AI alignment, HFT) — extends §7.2 |
| `future_work_expanded.md` | Detailed Phase 4 roadmap (n=20 replication, multi-LLM, no-limit) — extends §7.3 |
| `mentor_walkthrough.md` | 30-min script for the next Arpit meeting (6 beats × 5 min) |
| `methods_disclosures.md` | Methods-section checklist (LLM temperature disclosure, CI derivation, engine side-pot change) |

## Suggested paper outline (where to use each asset)

Each row is a likely paper section and the assets that support it.
Use as a checklist when writing in Overleaf; nothing here is binding.

| Likely section | Lead figure | Tables | Notes |
|---|---|---|---|
| Abstract / §1 Contributions | `01b_five_tier_ladder_with_unbounded.png` | `headline_ladder.tex` | — |
| §3 Methodology (Phase 2\*) | — | — | `phase2_unbounded_writeup_aggressive.md` |
| §5 Phase 1 results | `05_trust_vs_stack.png` | — | — |
| §5 Phase 2 (bounded + unbounded) | `07_*_aggressive.png`, `10_*_aggressive.png` | — | `phase2_unbounded_writeup_aggressive.md`, `unbounded_archetype_drift.md` |
| §5 Phase 3 results | `04_behavioral_shift.png`, P3 #67 transcript | `behavioral_shift_p1_p31.tex` | — |
| §5 Phase 3.1 results | `03_economic_inversion.png`, P3.1 #146 transcript | `per_archetype_p31.tex`, `tma_by_archetype.tex`, `economic_inversion.tex` | — |
| §6 Discussion (Nash falsification) | `14_nash_convergence_compare.png` | — | `nash_convergence_aggressive.md` |
| §7 Implications | — | — | `societal_implications.md` |
| §7 Future work | — | — | `future_work_expanded.md` |

## Regenerating the assets

All scripts live in `analysis/`. The master rebuild script is
`analysis/make_all_paper_resources.sh`. Individual steps:

```bash
# (1) Static figures + tables (no SQLite needed; ~5 sec)
python3 analysis/make_paper_figures.py
python3 analysis/make_paper_tables.py

# (2) Phase 2 unbounded comparison (figures 07 + 10, writeup, scorecard)
python3 analysis/phase2_unbounded_compare.py \
        --db runs_phase2_unbounded_aggressive.sqlite --tag aggressive

# (3) Nash convergence figures + CSV (11 + 12 + 13)
python3 analysis/nash_convergence.py \
        --trajectories phase2/adaptive/param_trajectories_unbounded_aggressive.json \
        --tag aggressive
python3 analysis/nash_convergence_compare.py    # produces figure 14

# (4) Per-hand trajectory figures (08 + 09)
python3 analysis/make_trajectory_figures.py \
        --db runs_phase2_unbounded.sqlite --tag phase2_unbounded

# (5) Story-hand transcripts per phase (one command per SQLite)
python3 analysis/extract_story_hands.py --db <phase>.sqlite --phase <tag>
```

Steps (1) work entirely from JSON dumps at the repo root and
canonical scorecards under `reports/`. Steps (2)–(5) require the
corresponding SQLite (LFS-tracked on the user's Windows machine).

## Provenance

All numerical values trace back to one of these sources:

1. `phase3_stats.json` / `phase31_stats.json` — per-seed JSON dumped
   from `runs_phase3_long.sqlite` / `runs_phase31_long.sqlite` via
   `extract_phase3_stats.py`.
2. `reports/phase31_long_scorecard.txt` — canonical cross-phase
   scorecard (P1, P2, P3, P3.1).
3. `reports/phase2_unbounded_scorecard_aggressive.txt` — canonical
   Phase 2\* unbounded scorecard.
4. Per-archetype L1 drift, cluster spreads, and convergence indices
   come from `phase2/adaptive/param_trajectories_unbounded_aggressive.json`.

Phase 1 and Phase 2 (bounded) detailed numbers live in the
`runs_phase{1,2}_*.sqlite` databases on the user's Windows machine
(LFS-tracked, gitignored on the server). The headline summaries are
reproduced verbatim from the scorecards under `reports/`.
