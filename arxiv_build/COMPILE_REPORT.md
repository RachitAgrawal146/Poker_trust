# COMPILE_REPORT.md — arXiv source-bundle verification

**Manuscript:** *Trust Dynamics in Multi-Agent Strategic Interaction: A
Simulation Study of Bayesian Reputation Systems in 8-Player Limit Texas
Hold'em*
**Target:** arXiv, primary category **cs.GT**

## Source used

Built from the **exact LaTeX that produced your final `main5_updated_1.pdf`**
(paraphrased prose, whitespace trimmed, figures rearranged). Verified by hash:
the source's compiled PDF md5 equals the uploaded
`main5_updated_1.pdf` (`e0818443ccaafb0612904ebcd129b3c4`). A line-diff against
that source shows only the removed Figure 1 float and the one author-approved
prose fix below.

## Author-approved edits in this revision

| Edit | Where | Detail |
|---|---|---|
| Removed borrowed Figure 1 | float deleted | `00_game_of_trust.png` (Nicky Case *Evolution of Trust*) + its `\caption`/`\label{fig:pd}` |
| **Fixed the dangling reference** | `main.tex` line ~419 | deleted the broken clause `Figure~\ref{fig:pd} illustrates these four possible outcomes using the framing of Nicky Case's \textit{Evolution of Trust} interactive:` and capitalized the next word. Now reads: *"…neither receives any reward. Mutual cooperation provides a reward of +2…"* |

The second edit was made on your explicit instruction. **No "Figure ??" remains,
and there are no undefined-reference warnings.**

## Toolchain

| | |
|---|---|
| Engine | **pdflatex** — pdfTeX 3.141592653-2.6-1.40.25 (TeX Live 2023/Debian) |
| Why pdflatex | `mathptmx` + `helvet`, `T1`/`utf8`; no `fontspec`/`unicode-math` |
| Bibliography | **BibTeX + natbib** (`plainnat`), **frozen** to `main.bbl` (3,981 bytes, 17 entries) |
| Shell-escape | not needed — no `minted`/`\write18`/`svg`; compiled `-no-shell-escape` |

## Compile passes

### Freeze build (Step C, with `references.bib`, clean dir)
`pdflatex → bibtex (exit 0) → pdflatex → pdflatex` — all exit 0.

### Step F — clean compile, **bundle contents only** (no `.bib`, no bibtex)
| Pass | Exit | Output |
|---|---|---|
| 1–3 | 0 | `Output written on main.pdf (12 pages, 978121 bytes)` |

Frozen `main.bbl` resolved all 17 citations with no `.bib` present. ✅

### Step H — fresh-extract self-contained build
Tarball extracted into a brand-new empty directory, `pdflatex ×3`, no bibtex:
| Pass | Exit |
|---|---|
| 1–3 | 0 — `Output written on main.pdf (12 pages, 978121 bytes)` |

**Step H result: ✅ PASS** — byte-identical 12-page PDF from the tarball alone.

## Warnings

| Warning | Count | Disposition |
|---|---|---|
| Undefined references | **0** | ✅ the `fig:pd` dangling reference is fixed — clean |
| Missing files | **0** | all 6 figures + 3 tables + `.bbl` resolve |
| `Overfull/Underfull \hbox/\vbox` | 7 | cosmetic only; from the two-column layout |

**No hard errors, no `Fatal error`, no undefined references, no missing files.**

## Output

| | |
|---|---|
| Pages | **12** |
| PDF | `paper.pdf` — 978,121 bytes |
| Figures | 6, numbered 1–6: (1) trust-vs-stack, (2) bounded-vs-unbounded, (3) economic-inversion, (4) nash dispersal, (5) param-drift, (6) TMA — economic-inversion precedes nash/param-drift, matching your PDF |

## Bundle size

| | |
|---|---|
| Tarball `arxiv_submission.tar.gz` | **879,244 bytes (≈ 0.86 MB)** |
| Uncompressed | ≈ 1.1 MB |
| arXiv limit | 50 MB — well within |

## arXiv-compatibility (Step E)

| Check | Result |
|---|---|
| shell-escape (`minted`, `\write18`) | none — OK |
| absolute / `../` paths | fixed → in-bundle relative |
| figure formats | all PNG; no EPS |
| multiple top-level `.tex` | only `main.tex` has `\documentclass` → no `00README.json` needed |
| filenames | lowercase ASCII, no spaces, no collisions |
| size vs 50 MB | 0.86 MB — OK |

**Verdict: the bundle compiles offline, no shell-escape, from a fresh extract,
with zero errors and zero undefined-reference warnings. Ready to upload.**
