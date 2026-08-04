# FINAL_PASS_REPORT.md — ToG final pass, 2026-08-04

Supersedes the gate numbers in `CLOSEOUT_REPORT.md` (2026-07-19), which
described the pre-n=20, 17-reference state. That report is kept as the
record of the July port; everything below is what changed since, and the
numbers here are the current ones.

> **Read the second-round section at the bottom first.** A referee
> pre-flight after this section was written found four content defects and
> forced one more relocation, so the upload-set and float numbers below are
> one revision stale. Current numbers live under "Referee pre-flight pass
> (second round)".

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


---

# Referee pre-flight pass, 2026-08-04 (second round)

An external pre-flight caught four content defects the first pass missed,
two of them inside figures. All are fixed; the gates below were re-run
from scratch afterwards.

## Blocking defects

**B1 — Fig. 2 contradicted its own data.** `03_economic_inversion.png`
carried the title "Economic Ordering Inversion: Wall Goes 8 → 1, Oracle
3 → 8" and a footer claiming Wall reached rank 1 with zero rebuys. The
plotted lines, the LaTeX caption and Table I all showed the n=20 result
(Wall 8→6 on 0.6 rebuys, Mirror first, Firestorm last). The plot had been
regenerated from the twenty-seed data; the annotation strings were
hardcoded from the five-seed temperature-1.0 run and were never touched.

**B2 — Supplementary Fig. S1 had the same defect.**
`06_tma_by_archetype.png` claimed "six of eight farm" and named Wall and
Sentinel the heaviest farmers. The bars show seven of eight positive with
Judge (+0.304) and Predator (+0.280) heaviest and Wall/Sentinel the
*lightest* positive.

Both are now **derived from the plotted arrays** rather than written by
hand, so the class of bug cannot recur: the titles and footers are
f-strings over `RANK_P3`/`RANK_P31`/`TMA_P31`/`_N20AGG`. The TMA figure's
x-limits were also fixed at `[-0.5, 0.95]` — sized for the five-seed run
whose TMA reached +0.73 — and now track the data.

**B3 — §V-C claimed all three scaffolds are required** and attributed the
evidence to "the supplementary validation suite", which does not exist in
any bundle. §IV-F, Limitations and the Conclusion all correctly say only
the no-CoT arm ran. The paragraph now says what the other three say.

**B4 — SU threshold.** "crossing the >1.5 threshold for the first time
across all phases" contradicted §IV-D, where SU is 1.88 in Phases 1–2
before falling to 1.19 in Phase 3. Now: "recovering past 1.5 for the
first time in the LLM phases (Phases 1–2 sat at 1.88)."

**B5 — prior-venue trace in the source.** `main.tex` lines 1–3 said the
document was "mechanically ported from the verified TMLR source". Invisible
in the PDF but present in the upload zip, where it tells an editor the
paper had a prior venue. Removed, along with the equivalent header in
`supplementary.tex`. Grep for `TMLR`/`tmlr`/`under review`/`PORT_TRIM`
across source and both PDFs: 0.

## Same-pass corrections

| Item | Fix |
|---|---|
| "The four agents are all lookup tables" (Phase 1) | → "All eight agents"; "four" had leaked in from the "four agent architectures" heading |
| "At the beginning of each **hand**, each player has a chip count of 200" | → per-run buy-in with stacks carrying across hands; as written it contradicted rebuys and the varying final stacks |
| "four lines of previous research" with four bullets | Background has five subsections; the missing one (reputation as a formal object) is now its own bullet, and the later "all four lines" callback is corrected |
| "Bayesians use in modeling poker opponents" | → "Bayesian opponent modelling in poker" |
| "byte-identical" Sentinel/Judge (5 places) vs Table S2's *different* bound boxes | Scoped to the four summary statistics the likelihood model reads; Table S2's caption now states that the boxes differ while those four are byte-identical at (0.083, 0.900, 0.325, 0.225) — verified against `archetype_params.ARCHETYPE_AVERAGES`. The cross-check a referee would run now resolves in the paper's favour |
| Fig. 2 caption's "~9 rebuys per seed" in a Phase 3→3.1 comparison | The number is right (Phase 3 Wall = 9.40, recomputed from `phase3_stats.json`) but read as carried over from the Phase 1 sentence in §IV-A. Both the caption and the body now name the phase |
| "Anthropic Haiku 4.5" | → "Claude Haiku 4.5", matching the other two mentions |
| Supplementary Fig. S2 never cited | One parenthetical added in §IV-C |
| Abstract 288 words vs IEEE's ~250 | **Manuscript abstract unchanged** — see below |

## Abstract: deliberately not edited

The reviewer is right that 288 words exceeds IEEE's ~250 guidance and that
the ScholarOne field can object. The manuscript abstract was still left
alone, because it is the hedged technical abstract the author canonized on
2026-07-19, recorded in `CLAUDE.md` as "use it verbatim in every future
regeneration or new port of any submission variant". Silently rewriting it
would override a standing author decision to satisfy a soft guideline.

Instead, `tog_build/abstract_scholarone.txt` holds a **246-word** version
for the portal field only — same ladder, same SDs, same bootstrap
interval, same capability-vs-power caveat, same hedge, nothing added. If
the portal accepts 288 words, paste the manuscript abstract and ignore the
file.

## Page gate, again

The corrections added net text and pushed main back to 11 pages. Reclaimed
by tightening the added prose and by one further relocation: the
behavioral-fingerprint table (Phase 1 vs Phase 3.1 VPIP/PFR/AF) moves to
Supplementary **Table S4**, with both in-text references repointed. Main
now carries Table I (per-archetype economics) and Figs. 1–2.

## Gates after the second pass

| Gate | Result |
|---|---|
| Main page count | 10 / 10 including references |
| Supplementary | 5 pages |
| Build | main 0 errors, 0 undefined; supplementary 0 errors; 0 overfull >20pt |
| References | 34 |
| Anonymity + prior-venue grep — 16 strings × (3 source files + both PDFs) | all 0 |
| Stale-string grep — 10 strings × both PDFs (`Goes 8`, `six of eight`, `validation suite`, `across all phases`, `The four agents`, …) | all 0 |
| S-pointer resolution | all 15 `Supplementary …~S<n>` strings resolve; Table S4 and Figs. S3–S4 verified against `supplementary.aux` |
| Standalone bundle | `tog_main_source.zip` → 10 pages under `TEXINPUTS=.: BSTINPUTS=.:` |
| Regression | canonical 15pp/49 refs, arXiv 13pp, TMLR 21pp — all 0 undefined |

Upload zip is now 10 files (the behavioral table left with the relocation).

## Still open, author-side

- The `anonymous.4open.science` link cannot be checked from here (the host
  blocks automated access). Open it in a private window and confirm both
  that it renders and that its expiry is set past the review horizon.
- Cover letter / response-to-reviewers is author-supplied.
