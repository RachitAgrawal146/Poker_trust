# Paper Resources

Curated assets for the Polygence research paper *"The Trust Trap: When
Reputation Systems Reward Exploitation in Multi-Agent Strategic
Interaction."* Everything in this folder is paper-ready: figures are
publication-quality PNGs, tables are CSV + LaTeX, and notes are draft
sections that can be slotted into `paper.md` or `paper/paper.tex`.

## Quick navigation

```
paper_resources/
├── README.md                         (you are here — index of assets)
├── figures/                          (publication-ready PNGs, 180 dpi)
│   ├── 01_four_tier_ladder.png       Headline: 4-tier r ladder
│   ├── 02_per_seed_ladder.png        Per-seed dot plot showing variance
│   ├── 03_economic_inversion.png     Wall 8 → 1, Oracle 3 → 8
│   ├── 04_behavioral_shift.png       VPIP/PFR/AF P1 vs P3.1
│   ├── 05_trust_vs_stack.png         Pooled scatter, P3 vs P3.1
│   ├── 06_tma_by_archetype.png       Trust-farming by archetype
│   ├── 07_phase2_bounded_vs_unbounded.png  (added once unbounded run completes)
│   ├── 08_stack_trajectories_p2_unbounded.png  (added once data arrives)
│   └── 09_param_drift_unbounded.png  (added once data arrives)
├── tables/                           (LaTeX `tabular` snippets)
│   ├── headline_ladder.tex
│   ├── per_archetype_p31.tex
│   ├── behavioral_shift_p1_p31.tex
│   ├── tma_by_archetype.tex
│   └── economic_inversion.tex
├── data/                             (CSVs — the source data behind every table)
│   ├── headline_ladder.csv
│   ├── per_archetype_p31.csv
│   ├── behavioral_shift_p1_p31.csv
│   ├── tma_by_archetype.csv
│   ├── economic_inversion.csv
│   ├── per_seed_stacks_p3.csv
│   └── per_seed_stacks_p31.csv
├── interesting_hands/                (curated hand transcripts for the paper)
│   └── (populated once Phase 2 unbounded sqlite is available)
└── notes/                            (paper-section drafts not yet in paper.md)
    ├── societal_implications.md      Real-world parallels (eBay, AI alignment, etc.)
    └── future_work_expanded.md       Detailed roadmap (Phase 4, multi-LLM, etc.)
```

## Headline result (the figure to lead with)

`figures/01_four_tier_ladder.png` — bar chart of mean trust-profit r
across the four agent architectures:

```
Phase 1 (frozen rules)              r = -0.752 ± 0.073
Phase 2 (hill-climbing)             r = -0.637 ± 0.125
Phase 3 (LLM personality role-play) r = -0.510 ± 0.268
Phase 3.1 (LLM + reasoning)         r = -0.094 ± 0.301   ← trap broken
```

The Phase 3 → Phase 3.1 step (Δr = +0.416) is **larger than all three
prior phase transitions combined**. Two of five Phase 3.1 seeds show
*positive* r, meaning trusted agents made more money than distrusted
ones — a complete inversion of the trap.

## How to regenerate everything

From the repo root:

```bash
# (1) Static figures (six PNGs, ~5 sec) — works without any SQLite
python3 analysis/make_paper_figures.py

# (2) Static tables (CSVs + LaTeX, ~1 sec) — works without any SQLite
python3 analysis/make_paper_tables.py

# (3) Phase 2 unbounded comparison (figures 07 + 10, scorecard, writeup)
python3 analysis/phase2_unbounded_compare.py \
        --db runs_phase2_unbounded.sqlite

# (4) Per-hand trajectory figures (08 + 09)
python3 analysis/make_trajectory_figures.py \
        --db runs_phase2_unbounded.sqlite --tag phase2_unbounded

# (5) Curated interesting hands per seed
python3 analysis/curate_interesting_hands.py \
        --db runs_phase2_unbounded.sqlite
```

Steps (1) and (2) work entirely from the JSON dumps at the repo root
(`phase3_stats.json`, `phase31_stats.json`) and the canonical
scorecards under `reports/`, so they re-run anywhere with no
dependencies on the heavy SQLite databases. Steps (3)-(5) require
the unbounded SQLite (~12 MB), which lives in this repo's working tree
after the simulation runs but is gitignored (LFS-tracked).

## Mapping to paper sections

| Asset | Paper.md section |
|---|---|
| `figures/01_four_tier_ladder.png`     | §1.3 Contributions, §5.8 Phase 3.1 results |
| `figures/02_per_seed_ladder.png`      | §5.8 Phase 3.1, §6.5 Limitations |
| `figures/03_economic_inversion.png`   | §5.8 Phase 3.1 |
| `figures/04_behavioral_shift.png`     | §5.7 Phase 3, §5.8 Phase 3.1 |
| `figures/05_trust_vs_stack.png`       | §5.2 Phase 1, §5.8 Phase 3.1 |
| `figures/06_tma_by_archetype.png`     | §5.8 Phase 3.1 (TMA discussion) |
| `figures/07_phase2_bounded_vs_unbounded.png` | (new) §5.5 Phase 2 |
| `tables/headline_ladder.tex`          | §1 / §5 (lead table) |
| `tables/per_archetype_p31.tex`        | §5.8 |
| `tables/behavioral_shift_p1_p31.tex`  | §5.7, §5.8 |
| `tables/tma_by_archetype.tex`         | §5.8 |
| `tables/economic_inversion.tex`       | §5.8 |
| `notes/societal_implications.md`      | (extends §7.2 Implications) |
| `notes/future_work_expanded.md`       | (extends §7.3 Future Work) |

## Provenance

All numerical values trace back to one of three sources:

1. **`phase3_stats.json`** — per-seed JSON dumped from
   `runs_phase3_long.sqlite` via `extract_phase3_stats.py`.
2. **`phase31_stats.json`** — same, for Phase 3.1.
3. **`reports/phase31_long_scorecard.txt`** — the canonical scorecard
   tying together P1, P2, P3, and P3.1 headline numbers.

Phase 1 and Phase 2 (bounded) detailed numbers live in the lean
`runs_phase{1,2}_*.sqlite` databases on the user's Windows machine and
are not on the server. The headline summaries are reproduced verbatim
from the scorecards.

Phase 2 unbounded is a new run produced this session; `runs_phase2_unbounded.sqlite`
is generated by `python3 phase2/adaptive/run_adaptive.py --unbounded`.
