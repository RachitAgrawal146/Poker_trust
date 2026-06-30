# COMPILE_REPORT.md — arXiv source-bundle verification

**Manuscript:** *Trust Dynamics in Multi-Agent Strategic Interaction: A
Simulation Study of Bayesian Reputation Systems in 8-Player Limit Texas
Hold'em*
**Target:** arXiv, primary category **cs.GT**

## Source used (corrected)

The bundle is built from the **exact LaTeX that produced your final
`main5_updated_1.pdf`** — i.e. the version with the **paraphrased prose**, the
**whitespace trimmed**, and the **figures rearranged** (economic-inversion
figure moved up). This was verified by hash:

```
md5(main5_updated_1.pdf you uploaded) = e0818443ccaafb0612904ebcd129b3c4
md5(this source's compiled PDF)       = e0818443ccaafb0612904ebcd129b3c4   ← identical
```

That source is **not** any committed git branch — `focused-thompson` (the branch
I used in the previous attempt) still has the *un-paraphrased* draft prose and
the extra whitespace, which is exactly the mismatch you flagged. The correct
source was the working copy from earlier this session
(`build2/paper_resources/manuscript/main.tex`). The bundle is that file with
**only** the borrowed Figure 1 float removed plus path fixes — confirmed by a
line diff (the diff shows nothing but the removed float).

## Toolchain

| | |
|---|---|
| Engine | **pdflatex** — pdfTeX 3.141592653-2.6-1.40.25 (TeX Live 2023/Debian) |
| Why pdflatex | `mathptmx` + `helvet`, `T1`/`utf8`; no `fontspec`/`unicode-math` |
| Bibliography | **BibTeX + natbib** (`plainnat`), **frozen** to `main.bbl` (3,981 bytes, 17 entries) |
| Shell-escape | not needed — no `minted`/`\write18`/`svg`; compiled `-no-shell-escape` |

## Compile passes

### Freeze build (Step C, with `references.bib`, clean dir)
| Step | Exit |
|---|---|
| `pdflatex` | 0 |
| `bibtex main` | 0 (read `plainnat.bst`, `references.bib` → `main.bbl`) |
| `pdflatex` ×2 | 0, 0 |

### Step F — clean compile, **bundle contents only** (no `.bib`, no bibtex)
| Pass | Exit | Output |
|---|---|---|
| 1–3 | 0 | `Output written on main.pdf (12 pages, 978729 bytes)` |

Frozen `main.bbl` resolved all 17 citations with no `.bib` present. ✅

### Step H — fresh-extract self-contained build
Tarball extracted into a brand-new empty directory, `pdflatex ×3`, no bibtex:
| Pass | Exit |
|---|---|
| 1–3 | 0 — `Output written on main.pdf (12 pages, 978729 bytes)` |

**Step H result: ✅ PASS** — byte-identical 12-page PDF from the tarball alone.

## Warnings (benign; none block arXiv)

| Warning | Count | Disposition |
|---|---|---|
| `Reference 'fig:pd' undefined` (line 420) | 1 | **Expected** — the removed Figure 1. Renders as "Figure&nbsp;??" in the prose. **Author action — `TODO.md`.** |
| `There were undefined references` | 1 | roll-up of the above |
| `Overfull/Underfull \hbox/\vbox` | 7 | cosmetic only; from the author's two-column layout |

No hard errors, no `Fatal error`, no missing-file warnings.

## Output

| | |
|---|---|
| Pages | **12** (was 13 in the focused-thompson attempt; this is the paraphrased/trimmed layout, one figure shorter after the ncase removal) |
| PDF | `paper.pdf` — 978,729 bytes |
| Figures rendered | 6 (all PNG, all found) |
| Figure numbering | auto-renumbered 1–6 after Figure 1 removal: (1) trust-vs-stack, (2) bounded-vs-unbounded, (3) economic-inversion, (4) nash dispersal, (5) param-drift, (6) TMA — i.e. economic-inversion still precedes nash/param-drift, matching your PDF's order |

## Bundle size

| | |
|---|---|
| Tarball `arxiv_submission.tar.gz` | **879,298 bytes (≈ 0.86 MB)** |
| Uncompressed | ≈ 1.1 MB |
| arXiv limit | 50 MB — well within |
| Largest assets | `14_nash_convergence_compare.png` 215 KB · `03_economic_inversion.png` 194 KB · `10_param_drift_unbounded_aggressive.png` 165 KB |

## arXiv-compatibility (Step E)

| Check | Result |
|---|---|
| shell-escape (`minted`, `\write18`) | none — OK |
| absolute / `../` paths | fixed → in-bundle relative |
| figure formats | all PNG; no EPS |
| multiple top-level `.tex` | only `main.tex` has `\documentclass` → no `00README.json` needed |
| filenames | lowercase ASCII, no spaces, no collisions |
| size vs 50 MB | 0.86 MB — OK |

**Verdict: the corrected bundle (paraphrased final text, ncase figure removed)
compiles offline, no shell-escape, from a fresh extract, on the first try.**
