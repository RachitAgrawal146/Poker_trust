# COMPILE_REPORT.md — arXiv source-bundle verification

**Manuscript:** *Trust Dynamics in Multi-Agent Strategic Interaction: A
Simulation Study of Bayesian Reputation Systems in 8-Player Limit Texas
Hold'em*
**Target:** arXiv, primary category **cs.GT**
**Source used:** branch `origin/claude/focused-thompson-1gTAE`,
`paper_resources/manuscript/main.tex` (the version that contains the borrowed
Figure 1 the task instructs me to remove; confirmed as the canonical/updated
LaTeX). The current working branch's `main.tex` is a divergent edit with a
different lead figure and **no** Figure 1, so it was **not** used — see
`BUNDLE_MANIFEST.md`.

## Toolchain

| | |
|---|---|
| Engine | **pdflatex** — pdfTeX 3.141592653-2.6-1.40.25 (TeX Live 2023/Debian) |
| Why pdflatex | preamble uses `mathptmx` + `helvet` (Times/Helvetica), `T1`/`utf8`; **no** `fontspec`/`unicode-math`, so XeLaTeX/LuaLaTeX not required |
| Bibliography | **BibTeX + natbib** (`\bibliographystyle{plainnat}`, `\bibliography{references}`), **frozen** to `main.bbl` (17 entries) |
| Shell-escape | **not needed** — no `minted`, `\write18`, `svg`, `epstopdf`; compiled with `-no-shell-escape` |
| Engines absent on host | `xelatex`, `biber`, `latexmk` — **not required** for this document |

## Bibliography freeze (Step C)

`pdflatex → bibtex → pdflatex → pdflatex` was run once with `references.bib`
present to generate `main.bbl`. `main.bbl` (3,981 bytes) is then shipped **in
place of** `references.bib`, so arXiv's AutoTeX never needs to run BibTeX. Not
biblatex/biber — the more fragile path — so no biber caveat applies.

## Compile passes

### Step C/F freeze build (with `references.bib`, in a clean dir)
| Step | Command | Exit |
|---|---|---|
| 1 | `pdflatex -interaction=nonstopmode -no-shell-escape main.tex` | 0 |
| 2 | `bibtex main` | 0 — read `plainnat.bst`, `references.bib`, wrote `main.bbl` |
| 3 | `pdflatex … main.tex` | 0 |
| 4 | `pdflatex … main.tex` | 0 |

### Step F — clean compile, **bundle contents only** (no `.bib`, no bibtex)
Fresh directory containing exactly `main.tex`, `main.bbl`, `tables/`,
`figures/` — what arXiv actually sees.
| Pass | Exit | Output |
|---|---|---|
| 1 | 0 | |
| 2 | 0 | |
| 3 | 0 | `Output written on main.pdf (13 pages, 979088 bytes)` |

The frozen `main.bbl` resolved all 17 citations with no `.bib` present. ✅

### Step H — fresh-extract self-contained build
Tarball extracted into a brand-new empty directory and compiled from scratch
(`pdflatex ×3`, no bibtex):
| Pass | Exit |
|---|---|
| 1 | 0 |
| 2 | 0 |
| 3 | 0 — `Output written on main.pdf (13 pages, 979088 bytes)` |

**Step H result: ✅ PASS** — byte-identical 13-page PDF (979,088 bytes) from the
tarball alone. The bundle is self-contained.

## Warnings (all benign; none block arXiv)

| Warning | Count | Disposition |
|---|---|---|
| `Reference 'fig:pd' on page 2 undefined` | 1 | **Expected.** This is the removed Figure 1 (Step D). It renders as "Figure&nbsp;??" in the prose at line 420. **Author action — see `TODO.md`.** Not fixed here (would require rewording). |
| `There were undefined references` | 1 | Roll-up of the single `fig:pd` warning above. |
| `Overfull/Underfull \hbox/\vbox` | 8 | Cosmetic micro-typography only; present in the author's original two-column layout. No content impact. |

No hard errors (`!`), no `Fatal error`, no missing-file warnings.

## Output

| | |
|---|---|
| Pages | **13** (was 13 with Figure 1; the removed figure shared a column page, so page count is unchanged) |
| PDF | `paper.pdf` — 979,088 bytes |
| Figures rendered | 6 (all PNG, all found) |
| Figure numbering | auto-renumbered 1–6 after Figure 1 removal (verified via `.aux`) |

## Bundle size

| | |
|---|---|
| Tarball `arxiv_submission.tar.gz` | **879,292 bytes (≈ 0.86 MB)** |
| Uncompressed bundle | ≈ 1.1 MB |
| arXiv limit | 50 MB — **well within** (1.7 % of limit) |
| Largest assets | `14_nash_convergence_compare.png` 215 KB · `03_economic_inversion.png` 194 KB · `10_param_drift_unbounded_aggressive.png` 165 KB |

## arXiv-compatibility summary (Step E)

| Check | Result |
|---|---|
| shell-escape packages (`minted`, `\write18`) | none — OK |
| absolute / `../` paths | fixed → all in-bundle relative (`figures/`, `tables/`) |
| figure formats | all PNG (pdflatex-native); no EPS |
| multiple top-level `.tex` | only `main.tex` has `\documentclass`; tables are `\input` children → no `00README.json` needed |
| filenames | all lowercase ASCII, no spaces, no case collisions |
| total size vs 50 MB | 0.86 MB — OK |

**Verdict: the bundle compiles offline, with no shell-escape, from a fresh
extract, on the first try.**
