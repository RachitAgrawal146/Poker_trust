# BUNDLE_MANIFEST.md — what's in the arXiv source bundle, and why

**Tarball:** `arxiv_submission.tar.gz` · **Engine:** pdflatex · **Bib:** frozen `main.bbl`

## Source provenance (corrected)

This bundle is built from the **exact source of your final `main5_updated_1.pdf`**
— the version with **paraphrased prose**, **whitespace removed**, and the
**economic-inversion figure moved up**. Proof: that source compiles to a PDF
whose md5 is identical to the file you uploaded
(`e0818443ccaafb0612904ebcd129b3c4`).

That source is **not** a committed git branch. The `focused-thompson` branch
(used in the first attempt) still carries the **un-paraphrased draft prose** and
the **extra whitespace** — the mismatch you pointed out. The correct file was the
working copy produced earlier this session,
`build2/paper_resources/manuscript/main.tex`. A line-diff of the bundle against
that file shows **only** the removed Figure 1 float — no other content change.

The paraphrasing is fully baked in: **0** remaining `\W{...}` draft-text wrappers
(only the now-unused `\definecolor{draftnew}` / `\newcommand{\W}` definitions
linger harmlessly in the preamble).

## Included files (the bundle)

| File | Purpose |
|---|---|
| `main.tex` | top-level document (the only file with `\documentclass`) |
| `main.bbl` | frozen bibliography (BibTeX → from `references.bib`); ships so arXiv needs no `.bib` |
| `tables/per_archetype_p31.tex` | `\input` — booktabs table, self-contained |
| `tables/behavioral_shift_p1_p31.tex` | `\input` — booktabs table |
| `tables/tma_by_archetype.tex` | `\input` — booktabs table |
| `figures/05_trust_vs_stack.png` | Figure 1 (after renumber) |
| `figures/07_phase2_bounded_vs_unbounded_aggressive.png` | Figure 2 |
| `figures/03_economic_inversion.png` | Figure 3 |
| `figures/14_nash_convergence_compare.png` | Figure 4 |
| `figures/10_param_drift_unbounded_aggressive.png` | Figure 5 |
| `figures/06_tma_by_archetype.png` | Figure 6 |

All 6 figures are PNG, total ≈ 0.95 MB. Figure order (economic-inversion before
nash/param-drift) matches your `main5_updated_1.pdf`.

## Removed content (the only permitted content change)

| Item | Action | Reason |
|---|---|---|
| `00_game_of_trust.png` | excluded | borrowed third-party image (Nicky Case, *Evolution of Trust*); arXiv disallows |
| its `\begin{figure}[H]…\end{figure}` float incl. `\caption` + `\label{fig:pd}` | deleted from `main.tex` | removes the float for the borrowed image |

Prose untouched. The body still has `Figure~\ref{fig:pd}` (main.tex:420) →
renders "??"; left for the author (`TODO.md`). Remaining figures auto-renumber
to **1–6**.

## Path/filename fixes (mechanical only)

| Location | Before | After |
|---|---|---|
| `\graphicspath` | `{{../figures/}{./figures/}{./}}` | `{{figures/}{./}}` |
| `\input{../tables/per_archetype_p31.tex}` | `../tables/` | `tables/` |
| `\input{../tables/behavioral_shift_p1_p31.tex}` | `../tables/` | `tables/` |
| `\input{../tables/tma_by_archetype.tex}` | `../tables/` | `tables/` |

No renames: all source names are lowercase ASCII, no spaces, no case collisions.

## Excluded files (and why)

| File / class | Reason |
|---|---|
| `references.bib` | superseded by frozen `main.bbl` (kept in `bib_source/` for re-freezing, not shipped) |
| `00_game_of_trust.png` | borrowed Figure 1 |
| unused figures (`01*`, `02*`, `04*`, `07…unbounded` non-aggressive, `08`–`13*`, `archetypes/*`) | not referenced by `\includegraphics` (the `\archentry` macro is text-only) |
| `tables/headline_ladder.tex`, `tables/economic_inversion.tex` | not `\input` by `main.tex` |
| build artifacts (`.aux .log .out .blg .toc …`), compiled PDF, `.docx`, `data/`, `notes/`, `interesting_hands/` | not part of the manuscript source |

## Final bundle tree

```
arxiv_submission.tar.gz
├── main.tex
├── main.bbl
├── tables/
│   ├── per_archetype_p31.tex
│   ├── behavioral_shift_p1_p31.tex
│   └── tma_by_archetype.tex
└── figures/
    ├── 03_economic_inversion.png
    ├── 05_trust_vs_stack.png
    ├── 06_tma_by_archetype.png
    ├── 07_phase2_bounded_vs_unbounded_aggressive.png
    ├── 10_param_drift_unbounded_aggressive.png
    └── 14_nash_convergence_compare.png
```
