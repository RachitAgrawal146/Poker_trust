# UPLOAD_SET_REPORT.md — IEEE ResearchExchange upload set

Built from `tog_submission/` (closeout state behind `tog_anonymous_FINAL.pdf`);
the source directory was not modified — all work on copies.

## Step A — `tog_main_source.zip` (15 files, 1.27 MB uncompressed)

### Inclusions (with reason)

| File | Reason |
|---|---|
| `main.tex` | main document |
| `tables/per_archetype_p31.tex`, `tables/behavioral_shift_p1_p31.tex`, `tables/tma_by_archetype.tex` | the three `\input` children of `main.tex` (verified complete by grep) |
| `figures/05_trust_vs_stack.png`, `figures/07_phase2_bounded_vs_unbounded_aggressive.png`, `figures/03_economic_inversion.png`, `figures/14_nash_convergence_compare.png`, `figures/10_param_drift_unbounded_aggressive.png` | the five figures `\includegraphics`'d by the main document (Figures 1–5) |
| `main.bbl` | frozen bibliography — covers a portal compiler that does NOT run BibTeX |
| `references.bib` | covers a portal compiler that DOES run BibTeX |
| `IEEEtran.cls` | official class from TeX Live `texlive-publishers`, in case the portal's tree lacks it |
| `IEEEtranN.bst` | the natbib-compatible IEEE style **actually used** (`\bibliographystyle{IEEEtranN}`) — note: the brief said "IEEEtran.bst", but the document requires the N variant; shipping the file the source names |

### Exclusions (with reason)

| File | Reason |
|---|---|
| `supplementary.tex` | separate document; uploads as PDF in its own slot |
| `figures/06_tma_by_archetype.png` | referenced ONLY by the supplementary (Figure S1) |
| `tog_submission_...` snapshots, `tog_build/` reports/PDFs/logs | not part of the compile set |
| `.aux/.log/.synctex.gz`, editor backups, `.git` | junk — none present in the staging copy |

### Gate results

| Gate | Result |
|---|---|
| Standalone compile, **portal path** (fresh empty dir ← zip; `pdflatex → bibtex(references.bib+IEEEtranN.bst) → pdflatex ×2`, no shell-escape) | ✅ 10 pages, 0 errors, 0 undefined |
| Standalone compile, **frozen-bbl path** (pdflatex ×3 only, no BibTeX) | ✅ 10 pages, 0 errors, 0 undefined |
| Fresh build vs `tog_anonymous_FINAL.pdf` | ✅ **pdftotext byte-identical**, 10/10 pages — no diff |
| Index Terms present | ✅ |
| ±0.073 in abstract AND §IV-A | ✅ (2 hits, verified individually) |
| Anonymity grep — 12 strings × (every text file in the zip + fresh-build pdftotext) | ✅ **ALL 0** |

## Step B — `title_page.docx` (INTENTIONALLY IDENTIFIED — editors only)

`title_page_info.txt` was authored-supplied via chat: the author directed
**email-only correspondence at `agrawalrachit146@gmail.com`** (this overrides the
brief's hard-coded school address — logged as an author decision; no postal
address supplied, none invented) and no acknowledgments (`NONE` → section
omitted). `title_page_text.txt` is the author-requested copy of the same file.

| Field | Rendered value |
|---|---|
| Title | Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation Study of Bayesian Reputation Systems in 8-Player Limit Texas Hold'em (bold, centered — exact) |
| Author | Rachit Agrawal |
| Affiliation | Sahyadri School (KFI), Pune, India |
| Correspondence | agrawalrachit146@gmail.com |
| Acknowledgments | omitted (NONE) |

Verified: OOXML XSD validation PASSED; rendered via LibreOffice and visually
checked (one page, no page numbers, fields labeled).

**⚠️ Identity handling:** `title_page.docx`, `title_page_info.txt`, and
`title_page_text.txt` contain the author's identity BY DESIGN. Keep them out of
the Main Manuscript / Supplementary slots, and **exclude them from the
anonymous 4open.science mirror** if the mirror is synced from this repository.

## Step C — see `UPLOAD_MANIFEST.md` for the full slot map.
Cover letter: AUTHOR-SUPPLIED, pending — intentionally not generated.

---

# ✅ UPLOAD-SET READY

(Only outstanding portal item: the author's cover letter.)
