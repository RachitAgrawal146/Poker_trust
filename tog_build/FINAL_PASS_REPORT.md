# FINAL_PASS_REPORT.md — ToG final pass, 2026-08-04

Supersedes the gate numbers in `CLOSEOUT_REPORT.md` (2026-07-19), which
described the pre-n=20, 17-reference state. That report is kept as the
record of the July port; everything below is what changed since, and the
numbers here are the current ones.

## What forced a new pass

Three things landed after the July closeout:

1. The **n=20 temperature-0 Phase 3.1 replication** (workflow run
   30788234686) replaced the five-seed exploration as the canonical
   Phase 3.1 dataset, moving the headline from $r_{tp} = -0.094$ to
   $+0.062$ and reordering every per-archetype exhibit.
2. The **bibliography roughly doubled** (17 → 34 rendered entries).
3. A **partial scaffold ablation** (no-cot arm, n=5) was run and needed
   reporting.

(1) and (2) each broke a gate: (1) left the ToG tables contradicting
their own figure captions, and (2) pushed the main document to 11 pages.

## Blocking defect found and fixed

`tog_submission/tables/per_archetype_p31.tex` and
`behavioral_shift_p1_p31.tex` still held the retired **five-seed**
numbers while the figure caption immediately above them stated the
twenty-seed result. As shipped, the PDF asserted both "Wall rank 1 with
zero rebuys" (table) and "Wall rises to rank 6 with 0.6 rebuys, Mirror
finishes first" (caption) on the same page.

The same staleness was present in `arxiv_build/bundle/tables/` and
`tmlr_submission/tables/`; all three were resynced from
`paper_resources/tables/`, which is generated from
`paper_resources/data/phase31_n20_stats.json`.

A related generator bug was fixed upstream: `analysis/make_paper_tables.py`
captioned the behavioral-shift table "Phase 3.1 columns from the original
five-seed exploration" even though line 526 of `make_paper_figures.py`
overrides `BEHAVIORAL["P3.1"]` with the n=20 aggregates. The caption now
states the actual provenance of each column block.

## Page gate: 11 → 10

Page 11 held nothing but references, so the overflow was the expanded
bibliography, not body growth. Reclaimed by structural relocation plus one
style correction — **no prose was cut**:

| # | Change | Effect |
|---|---|---|
| F1 | §II-E "Ideas in mathematics used throughout" (the Pearson / Bayes primer, with Eqs. 1–2) → Supplementary **Section S1**, replaced in main by a 6-line summary that names both tools, defines $r_{tp}$, and points to S1 | ~0.4 column |
| F2 | Fig. "Bounded versus unbounded hill-climbing per seed" → Supplementary **Fig. S3** | ~0.25 column |
| F3 | Fig. "The 8-agent population becomes dispersed in parameter space" → Supplementary **Fig. S4** | ~0.25 column |
| F4 | 31 periodical and conference titles in `references.bib` abbreviated to IEEE house style (`Proceedings of the National Conference on Artificial Intelligence` → `Proc. Nat. Conf. Artif. Intell.`, `Advances in Neural Information Processing Systems` → `Adv. Neural Inf. Process. Syst.`, etc.) | ~4 lines |

F4 is a conformance fix, not a squeeze: IEEE reference style abbreviates
venue titles, and the pre-pass bibliography did not. It is scoped to
`tog_submission/references.bib`; the arXiv and TMLR bundles keep full
venue names, which their styles want.

F2 and F3 follow the July port's own precedent for relocation (R2): both
figures were never `\ref`'d from the main text. That gap is now closed in
the other direction — each relocated figure gained an explicit
"Supplementary Fig. S3/S4" pointer in the sentence it supports, and
`Fig.~\ref{fig:economic-inversion}`, previously an orphan float, is now
cited in the Phase 3.1 results prose. **Every float in the main document
is referenced from the text.**

Rejected alternatives, with why: narrowing all figures to
`0.80\linewidth` still left a reference on page 11 (float placement
absorbed the gain); `\setlength{\bibsep}{0pt}` changed nothing (natbib's
separation was already zero under IEEEtran); dropping references would
have undone the expansion this pass exists to ship.

## Supplementary restructuring

The supplement was flat (floats, then two starred back-matter headings).
It now opens with two numbered sections so the main text can point into
it by number:

- **S1 Mathematical preliminaries** — the relocated primer, verbatim apart
  from `\rtp` → `$r_{tp}$` (the macro is main-only) and a closing sentence
  redirecting to the main text for the study-specific posterior mechanics.
- **S2 Additional tables, figures, and hand transcripts** — everything the
  July port relocated, unchanged.
- Broader Impact Statement and Supplementary Materials stay unnumbered.

Float numbering verified against `supplementary.aux`: Table S1 primer,
Table S2 bounds, Table S3 TMA, Fig. S1 TMA bars, Fig. S2 param drift,
Fig. S3 bounded-vs-unbounded, Fig. S4 dispersion. All eleven
`Supplementary …~S<n>` strings in the main PDF resolve to the right float.

## Gate results (clean-room build, pdflatex ×3 + bibtex/IEEEtranN)

| Gate | Result |
|---|---|
| Main page count | ✅ **10 / 10** including references |
| Supplementary | 5 pages (outside the limit per ToG policy) |
| Build | ✅ main 0 errors, 0 undefined; supplementary 0 errors |
| Overfull boxes > 20pt | ✅ 0 |
| References rendered | ✅ 34 (was 17) |
| Anonymity grep — 12 strings × (3 source files + both PDFs) | ✅ all 0 |
| `TODO-` markers in both PDFs | ✅ 0 / 0 |
| n=20 tables render | ✅ Table I leads with `mirror 0.748 280`, ends `firestorm 0.449 196`; Table II Phase 3.1 columns match `phase31_n20_stats.json` |
| Headline numbers | ✅ `+0.062` ×6, `±0.073` ×3 |
| Index Terms / competing-interests line | ✅ both render unchanged |
| Standalone source bundle | ✅ `tog_main_source.zip` compiles to 10 pages with `TEXINPUTS=.:` and `BSTINPUTS=.:` — i.e. using only files inside the zip |

## Upload set changes

`tog_main_source.zip` is now 11 files (was 15). Rebuilt from `main.tex`'s
actual dependencies, so the three figures and one table that moved to the
supplement are no longer shipped in the main bundle:

- dropped: `figures/07_phase2_bounded_vs_unbounded_aggressive.png`,
  `figures/14_nash_convergence_compare.png`,
  `figures/10_param_drift_unbounded_aggressive.png`,
  `tables/tma_by_archetype.tex`
- unchanged: `main.tex`, `main.bbl`, `references.bib`, `IEEEtran.cls`,
  `IEEEtranN.bst`, `figures/05_trust_vs_stack.png`,
  `figures/03_economic_inversion.png`,
  `tables/per_archetype_p31.tex`, `tables/behavioral_shift_p1_p31.tex`

`title_page.docx` is untouched and still the only identified artifact —
the ResearchExchange slot map in `UPLOAD_MANIFEST.md` is otherwise
unchanged, except that the post-upload proof check should now confirm
**10 pages and 34 references**.

## Known gap, not addressed here

`arxiv_build/bundle/` and `tmlr_submission/` received the n=20 tables and
the content updates, but their bibliographies are still at **12 rendered
entries** — the reference expansion reached the canonical manuscript
(`paper_resources/manuscript/`, 47 cite keys / 49 bib entries) and this
ToG port only. The arXiv bundle additionally ships a frozen `main.bbl`
with no `references.bib`, so expanding it means replaying the
citation-bearing prose the same way it was replayed into ToG. Left for a
deliberate decision rather than done silently, since it touches two
frozen, separately verified bundles for venues that may not be used.
