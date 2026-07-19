# PORT_TRIM_REPORT.md — TMLR → IEEE Transactions on Games port

**Input:** `tmlr_submission/` (untouched; verified anonymized, compile-clean)
**Output:** `tog_submission/` (IEEEtran source) + `tog_build/tog_anonymous.pdf` (main,
**10 pages including references**) + `tog_build/supplementary.pdf` (2 pages, excluded
from the limit).
**Method:** structural relocation only. No sentence written, reworded, or deleted.
`approved_cuts.md` does not exist → Step 4 skipped. The 10-page gate was reached
without prose cuts → Step 5 (TRIM_MAP) not triggered.

---

## Step 1 — Template port (all changes logged)

| # | Change | Before → After | Note |
|---|---|---|---|
| E1 | Document class | `\documentclass[10pt]{article}` + `\usepackage{tmlr}` → `\documentclass[journal]{IEEEtran}` | Official IEEEtran.cls from TeX Live (`texlive-publishers`), not a hand-written lookalike |
| E2 | Caption packages removed | `caption`/`subcaption` + global `\captionsetup` block → removed | The caption package is officially unsupported with IEEEtran; the class styles captions itself |
| E8/E8b | Per-float `\captionsetup{font={small,sf}}` (bounds table, primer table) → removed | Same reason as E2 | |
| E3 | tcolorbox preamble | moved verbatim to `supplementary.tex` | Both story-hand boxes relocated (Step 2) |
| E4 | Citations | `\bibliographystyle{plainnat}` (authoryear via tmlr.sty) → `\usepackage[numbers,compress]{natbib}` + `\bibliographystyle{IEEEtranN}` | Numeric IEEE style; bibliography regenerated from `references.bib` (frozen TMLR `main.bbl` discarded, new `main.bbl` shipped) |
| E5 | Author block | `Anonymous authors\\Paper under double-blind review` → `Anonymous authors` | ToG double-anonymous (mandatory since Jan 2025); no `\markboth` set, so no identifying running heads |
| E6 | Index Terms | inserted `[TODO-INDEX-TERMS: author to pick 4–6 — candidates from his own text: trust, reputation, poker, Bayesian, agents, simulation, multi-agent]` inside `IEEEkeywords` | Author decision — see TODO.md |
| E12a | Billings possessive citation | `\citeyearpar{billings1998opponent}` → `\citep{billings1998opponent}` | Forced by numeric style (`\citeyearpar` would print a bare year with no bracket); renders "Billings et al.'s Loki and Poki bots [6]" — name exactly once |
| E12b | Ganzfried possessive citation | `\citeyearpar{ganzfried2015safe}` → `\citep{ganzfried2015safe}` | Same; renders "Ganzfried and Sandholm's [8] further generalization" |
| E13 | Broader Impact heading | `\subsubsection*{...}` → `\section*{Broader Impact Statement}` | KEEP-in-main default (see TODO.md); IEEE has no subsubsection back-matter convention |

Title: byte-identical to input ✓. Abstract body: byte-identical to input ✓
(both verified programmatically against `tmlr_submission/main.tex`).
`tmlr.sty` / `tmlr.bst` removed from the port copy.

### Citation render verification (from the built PDF)

| Citation | Renders as | Name count |
|---|---|---|
| Resnick & Zeckhauser (`\citet`) | "conducted by Resnick and Zeckhauser [1]" | once ✓ |
| Billings (`\citeauthor`+`\citep`) | "Billings et al.'s Loki and Poki bots [6]" | once ✓ |
| Southey (`\citet`) | "formalized by Southey et al. [7]" | once ✓ |
| Ganzfried (`\citeauthor`+`\citep`) | "Ganzfried and Sandholm's [8] further generalization" | once ✓ |
| **Park (flagged in TMLR pass)** | "Park et al.'s study on generative agents [12]" | once ✓ — **the doubling self-resolves under numeric style**; no text change was needed |

## Step 2 — Structural relocations (all verbatim; page math in Step 3)

| # | Float | Destination | In-text reference updates |
|---|---|---|---|
| R1 | Table 1 — fixed-limit Hold'em primer | Supplementary **Table S1** | none needed — the primer is never `\ref`'d in prose (verified). Rationale: ToG's audience is games researchers; a poker primer is ideal supplementary content |
| R2 | Figure 6 — TMA per archetype bars | Supplementary **Figure S1** | none needed — never `\ref`'d; its numbers are fully duplicated by the TMA table (now Table IV) in the main text. Float spec `[tb]`→`[!ht]` in the supplement (logged; single-page supp layout) |
| R3 | Box 1 — Phase 3 hand #67 transcript | Supplementary **Box S1** | 1 rename: "Box~1 reproduces hand \#67" → "Supplementary Box~S1 reproduces hand \#67" |
| R4 | Box 2 — Phase 3.1 hand #146 transcript | Supplementary **Box S2** | 3 renames: "Box~2 reproduces Phase 3.1 hand \#146" / "reproduced in Box~2" / "hand in Box~2 is a miniature" → same with "Supplementary Box~S2" |
| R5 | Supplementary-materials pointer list | end of `supplementary.tex` | heading `\subsection*` → `\section*` (structure only); list content byte-identical, repo-relative, anonymized |

Box titles inside the supplement: "Box~1.\quad" → "Supplementary Box~S1.\quad"
and "Box~2.\quad" → "Supplementary Box~S2.\quad" (the only text changed in the
moved blocks). Remaining main-text floats auto-renumber via `\ref`:
Tables II–V → I–IV, Figures 1–5 unchanged (Figure 6 was last). Zero stray
"Box 1"/"Box 2" strings remain in the main PDF (grep-verified).

### Reflow fixes (allowed category: float sizing / table widths)

| Fix | Before → After | Why |
|---|---|---|
| `tables/per_archetype_p31.tex` | `table*` + `\small` → single-column `table` + `\footnotesize` + `tabcolsep=3pt` | Content is ~3.5 in wide; a two-column span wasted a full column band in IEEE layout (pure reflow artifact of the port). Fits `\columnwidth` with zero overfull |
| `tables/behavioral_shift_p1_p31.tex` | same conversion | same |
| Overfull hboxes | 2 paragraph overfulls of 1.8 pt / 1.6 pt — **noted, not fixed** | Both pre-existing prose paragraphs; < 2 pt is invisible and fixing would require rewording, which is out of scope |

The bounds table (`tab:bounds-comprehensive`, genuinely full-width `tabularx`)
stays `table*`; results Tables, Figures 1–5 not relocated, per instructions.

## Step 3 — Page-count math

| Build | State | Pages |
|---|---|---|
| input | TMLR single-column format | 20 |
| M0 | IEEEtran two-column port, nothing relocated | **12** |
| M1 | − primer table | 11 |
| M2 | − Figure 6 | 11 (slack created, no page boundary crossed) |
| M3 | − Boxes 1–2, − pointer list | 11 |
| final | + the two table\*→table reflow fixes | **10 ✓ PASS** |

(M1/M2 measured with the box environments erroring in place — box *content*
still typeset, so counts are directionally exact; M3 and final are clean
0-error builds.) Final build: `pdflatex → bibtex (IEEEtranN) → pdflatex ×2`,
`-no-shell-escape`: **0 errors, 0 undefined references/citations.**
Supplementary: **2 pages, 0 errors** (single-column IEEEtran; format
unconstrained since supplementary is outside the page limit).

## Step 4 — skipped (`approved_cuts.md` does not exist). No `[TODO-SEAM]` markers.
## Step 5 — not triggered (gate passed structurally). No TRIM_MAP.md.

## Step 6 — Validation gate

| Gate | Result |
|---|---|
| Fresh build | ✅ 0 errors, 0 undefined (main and supplementary) |
| Anonymity grep — 12 strings × (source + main PDF + supplementary PDF) | ✅ **0 matches everywhere**; mirror URL present ×1 and clean |
| `[TODO-` | ✅ main: exactly 1 = `[TODO-INDEX-TERMS...]` (author must resolve before upload); supplementary: 0 |
| Title + abstract | ✅ byte-identical to input |
| Relocated floats | ✅ Table S1, Fig. S1, Boxes S1–S2 all render in supplement; all 4 in-text S-references resolve; no float referenced-but-missing |
| Main floats | ✅ Figures 1–5, Tables I–IV render; bounds table full-width intact |
| Citation renders | ✅ all five verified (table above) |
| Page limit | ✅ 10/10 including references |

---

## Final status

# READY (pending INDEX-TERMS)

Author items are in `TODO.md`. The only marker in the main PDF is the
Index-Terms placeholder; it must be replaced with 4–6 chosen terms before
OpenReview/ScholarOne upload.
