# REFINEMENT_REPORT.md — final pre-upload pass on the TMLR submission

**Input:** `tmlr_submission/` (snapshot preserved untouched at
`tmlr_submission_pre_refinement/`)
**Output:** refined `tmlr_submission/` + `tmlr_build/tmlr_anonymous_final.pdf` (the
upload candidate; the superseded pre-refinement PDF is retained in git history)
**Scope kept:** 6 mechanical edits, all asserted-unique and logged below; title and
abstract verified **byte-identical** to the snapshot; no sentence written or reworded.

---

## Step 1 — Citation redundancies (4 fixed, name now renders exactly once)

| # | File:line | Before | After | Renders |
|---|---|---|---|---|
| 1a | `main.tex:247–248` | `conducted by Resnick \& Zeckhauser`⏎`\citep{resnick2002trust}` | `conducted by \citet{resnick2002trust}` | "conducted by Resnick and Zeckhauser (2002)" |
| 1b | `main.tex:357–358` | `this included Billings et al.'s Loki and Poki bots`⏎`\citep{billings1998opponent}` | `this included \citeauthor{billings1998opponent}'s Loki and Poki bots`⏎`\citeyearpar{billings1998opponent}` | "Billings et al.'s Loki and Poki bots (1998)" |
| 1c | `main.tex:358–359` | `formalized by Southey`⏎`et al.\ \citep{southey2005bayes}` | `formalized by`⏎`\citet{southey2005bayes}` | "formalized by Southey et al. (2005)" |
| 1d | `main.tex:360–361` | `followed by Ganzfried and Sandholm's \citep{ganzfried2015safe}`⏎`further generalization` | `followed by \citeauthor{ganzfried2015safe}'s \citeyearpar{ganzfried2015safe}`⏎`further generalization` | "Ganzfried and Sandholm's (2015) further generalization" |

Each was verified in the compiled PDF text: **every author name appears exactly
once** in its sentence (Step 5.5 below).

### FLAGGED — not changed (author's call)

- **§2.4 Park et al. (the borderline named in the brief):** renders
  *"…and Park et al.'s study on generative agents (Park et al., 2023), suggest…"*
  — name doubled. Fix would be the same `\citeauthor`+`\citeyearpar` pattern as 1b/1d;
  left untouched per instructions.
- **Residual scan:** all 22 bibliography surnames were scanned in the PDF text for
  the pattern *surname … (same-surname, year)*. **The Park instance above is the
  only doubled citation in the entire paper.** No unlisted instances exist (the
  plain parenthetical cites — e.g. "(Resnick and Zeckhauser, 2002; Bolton et al.,
  2004)" — are not doubled: the prose there does not name the authors).

## Step 2 — Back-matter conventions

| File:line | Before | After |
|---|---|---|
| `main.tex:1496` | `\section*{Sources}` + blank line before `\paragraph*{Competing interests.}` | heading removed — "Competing interests" and "Data and materials availability" now sit as `\paragraph*`s directly after the Broader Impact Statement |

Both paragraphs' text byte-identical except the Step-4b URL change. No
Acknowledgments section added (camera-ready only, per
`DEANONYMIZATION_CHECKLIST.md`).

## Step 3 — AWAITING-AUTHOR-APPROVAL (prepared, NOT applied)

```diff
- \paragraph*{Competing interests.} The author declares no competing
+ \paragraph*{Competing interests.} The author(s) declare no competing
  interests.
```

Rationale: "The author" (singular) weakly signals team size under double-blind.
The author has not yet approved this one-word change, so the submitted text is
unchanged. Say the word and it's a one-line edit.

## Step 4 — TODO-marker gate

- **Broader Impact (`broader_impact.txt`):** the statement was already inserted in
  the previous pass. Verified this pass: the in-source text is **byte-identical to
  the uploaded file** after normalizing exactly one encoding difference — the
  straight quotes around `"trust farming"` are set as LaTeX ``…'' (typography
  only; zero word changes). Marker count in source and PDF: **0**.
- **Repo link (`mirror_url.txt`):**

  | | |
  |---|---|
  | Before | `…and analysis scripts are available in an anonymized repository; the link will be`⏎`restored in the camera-ready version.` |
  | After | `…and analysis scripts are available at`⏎`\url{https://anonymous.4open.science/r/trust-sim-anonymous}`⏎`(anonymized repository for review).` |

  Provenance note: `mirror_url.txt` was not supplied as a file; the URL was taken
  from the brief's own SETUP line (author-specified). The URL string contains none
  of the identity strings. **Operational caveat: confirm the mirror is live and
  scrubbed (repo name, README, commit authors) before clicking upload.**

## Step 5 — Validation gate results

| Gate | Requirement | Result |
|---|---|---|
| 5.1 Fresh-dir build (`pdflatex ×3`, frozen `.bbl`, no shell-escape) | 0 errors, 0 undefined | ✅ 0 / 0 — `main.pdf, 20 pages, 1,427,143 bytes` |
| 5.2 Anonymity grep, **source + PDF text**, 12 strings: `Rachit, Agrawal, agrawal, Sahyadri, RachitAgrawal146, sahyadrischool.org, Poker_trust, poker_trust, poker-trust, Arpit, Bansal, Polygence` | all 0 | ✅ **0 matches for every string in both** (mirror URL itself verified clean) |
| 5.3 `[TODO-` in PDF text | 0 | ✅ 0 |
| 5.4 Visual-diff sanity | pages 19±1; 6 figures, 5 tables, Box 1–2; title+abstract byte-identical | ✅ 20 pages; Figures 1–6 ✓, Tables 1–5 ✓ (Table 1 = Hold'em primer … Table 5 = TMA), Box 1 ✓ Box 2 ✓; title ✅ byte-identical, abstract ✅ byte-identical to `tmlr_submission_pre_refinement/` |
| 5.5 Citation render | 4 fixed names exactly once | ✅ all four confirmed in PDF text (windows quoted in Step 1); only remaining double = flagged Park |

Diff-vs-snapshot audit: the source differs from `tmlr_submission_pre_refinement/`
in exactly the 6 logged edits (3 unified-diff hunks; edits 1b–1d share one hunk,
Step 2 + 4b share one). Machine-readable log: `tmlr_build/refinement_log.json`.

---

## Final status

# ✅ UPLOAD-READY

Upload `tmlr_build/tmlr_anonymous_final.pdf` to OpenReview. Two author reminders,
neither a gate failure: (1) confirm the anonymous mirror resolves before
submitting; (2) the Step-3 "author(s)" diff and the Park citation flag are open
one-liners if you want them.
