# DEANONYMIZATION_CHECKLIST.md — camera-ready restoration list

Everything removed or neutralized for double-blind review, with the **verbatim
original text** to restore on acceptance. Work through this top-to-bottom after
the accept decision; every item lives in `tmlr_submission/main.tex` unless
noted.

## 0 · Switch the style-file mode

Replace `\usepackage{tmlr}` with `\usepackage[accepted]{tmlr}` and define, per
the template:

```latex
\def\month{MM}  % 2-digit month of publication
\def\year{YYYY} % 4-digit year
\def\openreview{\url{https://openreview.net/forum?id=XXXX}} % your forum link
```

(For a later arXiv/preprint posting of the accepted paper, use
`\usepackage[preprint]{tmlr}` instead.)

## 1 · Author block

Current: `\author{Anonymous authors\\Paper under double-blind review}`.
Restore with the TMLR author macros (`\name`, `\email`, `\addr`):

```latex
\author{\name Rachit Agrawal \email rachit.agrawal@sahyadrischool.org \\
      \addr Independent research, 2025--2026}
```

Original title-block lines (from the arXiv source, for reference):

```latex
\textbf{Rachit Agrawal}\textsuperscript{1}
\textsuperscript{1}Independent research, 2025--2026.
Correspondence: rachit.agrawal@sahyadrischool.org
```

## 2 · Author contributions paragraph

Removed from the `Sources` section. Restore **verbatim** (TMLR places it as an
unnumbered subsubsection after the Broader Impact Statement — either form is
accepted):

```latex
\paragraph*{Author contributions.} R.A.\ conceived the study,
implemented the simulation, performed the analysis, and wrote the
manuscript.
```

## 3 · Repository link (Data and materials availability)

Current (anonymized):

> The full simulation codebase, SQLite databases, figures, tables,
> and analysis scripts are available in an anonymized repository; the link will be
> restored in the camera-ready version.

Restore the original ending:

```latex
… are available at
\url{https://github.com/RachitAgrawal146/Poker_trust}.
```

(If you created an anonymized mirror during review — see TODO.md — also retire
or redirect that mirror.)

## 4 · Not removed (nothing to restore)

- Title, abstract, all body prose, math, tables, boxes, figures — untouched.
- "Competing interests" paragraph — kept in the review copy (not identifying).
- Supplementary-materials list — kept (repo-relative paths only).
- The bibliography contains no self-citation, so none was neutralized.

## 5 · Final camera-ready sweep

After restoring items 1–3, grep the source and the compiled PDF once more —
this time the *expected* counts are: `Rachit`/`Agrawal` in the author block and
repo URL only, `sahyadrischool.org` in the author block only. Also add
Acknowledgments only now (TMLR: "Only add this information once your submission
is accepted and deanonymized").
