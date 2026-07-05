# TODO.md — author-only items for the TMLR submission

The port and anonymization are done and verified (see PORT_REPORT.md). These
three items need your writing or your judgment — nothing here was drafted for
you.

## 1 · Broader Impact Statement — ✅ DONE

Your three-paragraph statement (supplied 2026-07) was inserted **verbatim**
into `\subsubsection*{Broader Impact Statement}`, replacing the
`[TODO-BROADER-IMPACT]` marker (only mechanical change: straight double quotes
around "trust farming" became LaTeX ``…'' quotes). The rebuilt
`tmlr_anonymous.pdf` is now **20 pages**, compiles with zero errors/undefined
references, and the identity grep is still all-zero.

## 2 · Decide: anonymized mirror vs. placeholder sentence  *(recommended: mirror)*

The data-availability paragraph currently ends with the neutral sentence
"…available in an anonymized repository; the link will be restored in the
camera-ready version." Reviewers therefore cannot inspect the code.

Option A — keep the placeholder sentence (zero effort, weaker reproducibility
story during review).
Option B — create an actual anonymized mirror (e.g., https://anonymous.4open.science
) pointing at a scrubbed copy of the repo, and substitute that URL for the
placeholder sentence. If you do this, scrub the mirror itself: repo name,
README, commit authors, `CLAUDE.md`, and the `paper_resources/` notes all
currently carry your name — an anonymized export (not a fork) is the safe route.

## 3 · Visual review of the single-column reflow  *(10 minutes with the PDF)*

Nothing broke in the build, but three spots changed shape the most going from
two columns to one — eyeball them in `tmlr_anonymous.pdf`:

- **Boxes 1 and 2** (the hand transcripts, pp. ~8 and ~11): now full text
  width. They render cleanly but read wider and flatter than the original
  column-width boxes. If you dislike the look, say so — the box style can be
  narrowed mechanically; do not accept a redesign from anyone else's pen.
- **The two wide tables** (limit-Hold'em primer; per-archetype policy bounds):
  formerly full-page-width `table*` spanning two columns, now ordinary
  full-width tables. Check row spacing and that no column looks cramped.
- **Citations changed style** (template-forced): numeric "(1)" became
  author–year "(Axelrod, 1984)" throughout. Skim for any sentence where the
  author–year form reads oddly against your prose (e.g., where the citation
  was used as a noun). Flag them; do not let anyone rewrite the sentences for
  you.

## Submission mechanics reminder

TMLR submits through OpenReview (https://openreview.net). Upload the PDF
(`tmlr_anonymous.pdf`); keep `tmlr_submission/` as the exact source that built
it. The submitted version must keep `\usepackage{tmlr}` with no options —
the `[accepted]` switch and all de-anonymization steps live in
`DEANONYMIZATION_CHECKLIST.md` for later.
