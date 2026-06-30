# COMPLIANCE_REPORT.md — JEI v7 (2025) checklist re-run

**Manuscript:** `JEI_manuscript_WORKING.docx`
**Pass type:** mechanical compliance only (no scientific content authored)
**Schema validation:** ✅ PASSED (OOXML well-formed; all injected math validates)
**Mechanical edits logged:** 71 (see `CHANGELOG.md`)
**Author hand-edits still required:** see `TODO_handwrite.md`

Legend: **DONE** = applied mechanically · **PARTIAL** = mechanical part done,
authorial part flagged · **TODO-AUTHOR** = needs your words/decision (placeholder
or flag left) · **N/A** = already compliant, no action.

---

## 1 · Formatting integrity (template conformance) — ✅ ALL PASS

| Requirement | Spec | In file | Status |
|---|---|---|---|
| Font | Arial 11 pt | `rFonts=Arial`, `sz=22`; only Arial in body runs | ✅ |
| Line spacing | 1.5 | `w:line=360, lineRule=auto` | ✅ |
| Margins | 1″ all sides | `top/right/bottom/left = 1440` | ✅ |
| Page size | US Letter | `12240 × 15840` | ✅ |
| Line numbers | continuous, by 1 | `lnNumType countBy=1 restart=continuous` | ✅ |
| Section order | Summary→Intro→Results→Discussion→Methods→Refs→Figs→Tables→Appendix | present in that order | ✅ |
| Methods placement | after Discussion | confirmed (¶79, after Discussion ¶54–78) | ✅ |
| Equations | native, not pasted images | 5 display + 1 inline OMML; 0 placeholders left | ✅ |
| Leaked LaTeX | none | 0 backslash tokens, 0 `^`/math-`_`, 0 `[Equation]` | ✅ |

> **Note:** I could not render the file to a paginated PDF in this environment
> (LibreOffice is non-functional here), so page-count figures below are
> word-count estimates — open in Word to confirm exact pagination.

---

## 2 · The 44-item checklist

### A. Submission blockers
| # | Item | Status | Note |
|---|---|---|---|
| 1 | Senior (adult) author | **TODO-AUTHOR** | none on title page; must be added & submit |
| 2 | Figure+table ≤ 8 | **PARTIAL** | removed borrowed Fig 1 → **10 → 9**; still **1 over** |

### B. Title page
| # | Item | Status | Note |
|---|---|---|---|
| 3 | Title ≤ 110 char | **TODO-AUTHOR** | currently **134**; option given in TODO |
| 4 | Real affiliation | **TODO-AUTHOR** | "Independent research" not accepted |
| 5 | Student-author line | **TODO-AUTHOR** | confirm "High School" placeholder |
| 6 | KEYWORDS (3–5 single words) | **DONE / TODO-AUTHOR** | `[TODO-KEYWORDS]` ¶8; candidate words listed |
| 7 | OVERVIEW blurb | **DONE / TODO-AUTHOR** | `[TODO-OVERVIEW]` ¶9 |

### C. Summary
| # | Item | Status | Note |
|---|---|---|---|
| 8 | "We hypothesized…" sentence | **DONE / TODO-AUTHOR** | `[TODO-HYPOTHESIS]` ¶12 |
| 9 | `[VERIFY]` rhetorical questions | **TODO-AUTHOR** | stylistic |

### D. Introduction
| # | Item | Status | Note |
|---|---|---|---|
| 10 | Closing paragraph (hyp+results+takeaways) | **DONE / TODO-AUTHOR** | `[TODO-INTRO-CLOSING]` ¶25 |
| 11 | Hypothesis about science, not model | **TODO-AUTHOR** | guidance in TODO |
| 12 | Background-merge seam transitions | **TODO-AUTHOR** | 3 seams quoted in TODO |
| 13 | Bulleted list → prose | **DONE / TODO-AUTHOR** | `[TODO-LIST]` ¶21–24; 4 items quoted |
| 14 | `[VERIFY]` Intro present tense | **TODO-AUTHOR** | general truths may stay present |

### E. Results
| # | Item | Status | Note |
|---|---|---|---|
| 15 | Past tense throughout | **DONE / TODO-AUTHOR** | **27** reporting verbs converted to past; **7** left as historical-present (Box 2 hand narration ¶52) or meta/general-truth (¶32 "frames", ¶35 "calls", ¶38 "reads") — author stylistic call |
| 16 | Hand boxes (Box 1, Box 2) | **DONE / TODO-AUTHOR** | `[TODO-BOX]` ¶36, ¶53; rebuild as fig/table or cut |
| 17 | Cross-refs `[#]` | **PARTIAL** | equations resolved (Eq 2–5); 9 fig/table `[#]` + 2 section `[TODO-XREF]` left |
| 18 | `[VERIFY]` italic Phase subheaders | **N/A** | kept (allowed); confirm |

### F. Discussion
| # | Item | Status | Note |
|---|---|---|---|
| 19 | Subsection-seam transitions | **TODO-AUTHOR** | 4 seams quoted in TODO |
| 20 | Conclusion folded in | **TODO-AUTHOR** | review ¶76/¶78 read as conclusion |
| 21 | `[VERIFY]` no overclaiming | **TODO-AUTHOR** | "support" not "prove" |
| 22 | `[VERIFY]` limitations balance | **TODO-AUTHOR** | ¶72–75 |

### G. Materials & Methods
| # | Item | Status | Note |
|---|---|---|---|
| 23 | Methods after Discussion | **DONE** | confirmed |
| 24 | Active → passive voice | **PARTIAL** | 6 sentences inverted; rest is an authorial sweep |
| 25 | Equations entered natively | **DONE** | 5 display + 1 inline OMML |
| 26 | Pasted/Unicode symbols re-entered | **DONE** | rₜₚ, Phase 2*, Δ, ♠♥♦♣, L₁, log₂, x̄/ȳ, Tᵪᵣᵢₜ, xᵢ/yᵢ, $-escapes |
| 27 | Math primer moved to Methods | **DONE** | structural; confirm placement |
| 28 | `[VERIFY]` archetypes read as prose | **TODO-AUTHOR** | |
| 29 | Code citation (GitHub, no Drive) | **N/A / TODO-AUTHOR** | repo cited; confirm method |
| 30 | `[VERIFY]` software versions | **TODO-AUTHOR** | add library versions |

### H. Footnotes
| # | Item | Status | Note |
|---|---|---|---|
| 31 | 16 footnotes removed | **DONE / TODO-AUTHOR** | removed; integrate-or-drop each (list in TODO) |

### I. References
| # | Item | Status | Note |
|---|---|---|---|
| 32 | DOIs / `https://` links | **TODO-AUTHOR** | none in source; cannot fabricate |
| 33 | `[VERIFY]` MLA-8 title case | **TODO-AUTHOR** | |

### J. Figures & tables
| # | Item | Status | Note |
|---|---|---|---|
| 34 | Borrowed Figure 1 removed | **DONE** | image+caption deleted; Figs 2–7 → 1–6; in-text ref flagged |
| 35 | `[VERIFY]` caption completeness | **TODO-AUTHOR** | title/shown/methods/stats/seeds |
| 36 | Tables as Word tables | **DONE / TODO-AUTHOR** | 3 native tables present; 2 Methods tables not rebuilt |
| 37 | Multi-panel single file | **N/A** | already single combined images |

### K. Global prose-policy scan
| # | Item | Status | Note |
|---|---|---|---|
| 38 | First-person singular | **N/A** | none ("we/our" only) |
| 39 | Present-tense reporting | **DONE / TODO-AUTHOR** | Results converted (item 15); 7 historical-present verbs flagged |
| 40 | Active voice in Methods | **PARTIAL** | see item 24 |
| 41 | Lists in main text | **DONE / TODO-AUTHOR** | flagged (item 13) |
| 42 | Direct quotations | **TODO-AUTHOR** | 21 scare-quote sets — confirm none verbatim |
| 43 | Pasted/Unicode symbols | **DONE** | see item 26 |

### L. Length
| # | Item | Status | Note |
|---|---|---|---|
| 44 | 10-page limit (Intro→Methods) | **TODO-AUTHOR** | **over** — see §4 |

---

## 3 · Figure + table count

| | Count | Limit | Status |
|---|---|---|---|
| Figures | 6 (Fig 1–6) | — | |
| Tables | 3 (Table 1–3) | — | |
| **Combined** | **9** | **8** | ❌ **1 over** |

Removing the borrowed Figure 1 brought this from 10 to 9. One more must go;
Box 1/Box 2 and the two un-rebuilt Methods tables are **not** in this count yet.
Easiest single cut: merge Fig 6 and Table 3 (both are TMA-per-archetype). See
`TODO_handwrite.md` Part 4.

## 4 · Page length vs the 10-page limit

Rendering to exact pages was not possible here (no working renderer), so this is
a **word-count estimate**:

| Section | Words |
|---|---|
| Summary | 184 |
| Introduction | 1,653 |
| Results | 1,575 |
| Discussion | 2,605 |
| Materials & Methods | 2,566 |
| **Main text (Intro→Methods, the limited span)** | **≈ 8,580** |
| References + figures + tables + appendix | 681 |
| **Whole document** | **≈ 9,300** |

At the mandated Arial 11 / 1.5 spacing / 1″ margins, ≈8,580 words of main text is
roughly **18–20 text pages** — well over the 10-page limit (the source ran ~13
two-column journal pages, so the single-column JEI reflow is expected to be
longer). **Substantial trimming is required**, and that is content work reserved
for the author. ❌ over limit.

---

## 5 · Additional findings (beyond the 44-item list)

- **Acknowledgments section absent.** JEI's mandatory order includes an
  *Acknowledgments* section between Materials & Methods and References; the
  manuscript goes straight from Methods to References. → Add a brief
  Acknowledgments section (or confirm intentional omission). *Not auto-added —
  it is authored content.*
- **Stray leaked list directive removed.** A bold list item reading `sep2pt`
  (a `\setlist{itemsep=2pt}`-type remnant) sat between the list lead-in and the
  first item; deleted as mechanical cleanup (logged).
- **Infinitive over-conversion caught & reverted.** The past-tense map had
  turned "what to **do**" into "what to **did**" (¶48); reverted, since "do"
  there is an infinitive, not a Results verb.

---

## 6 · Bottom line

Mechanical compliance is **complete and schema-valid**: template formatting,
native equations, symbol rendering, tense in Results, the six passive-voice
Methods edits, figure renumbering, and every required placeholder are in place,
with all 71 changes logged. **The manuscript is not yet submission-ready** — it
remains blocked on author-only work: a senior author, the title length, the
≤8 figure/table cut, the ~2× length overage, and the prose/decision items in
`TODO_handwrite.md`. None of those were touched, by policy.
