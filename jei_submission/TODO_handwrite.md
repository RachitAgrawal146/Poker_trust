# TODO_handwrite.md — author hand-edit punch list (after pass 2)

Two mechanical passes are complete (`CHANGELOG.md` has all 103 logged edits).
`JEI_manuscript_FINAL.docx` is now mechanically finished: all resolvable
cross-references are filled in, Results tense and Methods voice conversions are
done except where your words are required, and every remaining gap is a
`Ctrl-F`-able bracketed marker. Everything below needs **your words or your
decision** — none of it could be done without authoring scientific content,
which the JEI AI policy forbids.

| Marker in the docx | Count | Meaning |
|---|---|---|
| `[TODO-KEYWORDS]` `[TODO-OVERVIEW]` `[TODO-HYPOTHESIS]` `[TODO-INTRO-CLOSING]` | 4 | required element missing — write it |
| `[TODO-DISCUSSION-LOOP]` | 2 | **new (mentor guidance)** — where the Discussion must return to the hypothesis |
| `[TODO-LIST]` | 1 | forbidden bulleted list to rewrite as prose |
| `[TODO-BOX]` | 2 | hand-transcript boxes — rebuild as end figure/table or cut |
| `[TODO-XREF]` | 2 | section cross-refs whose numbering JEI removed — reword |
| `[TODO-XREF-TABLE]` | 4 | refs to the **policy-bounds table that is not in this docx** — rebuild it or reword |
| `[FIG1-REMOVED]` | 1 | sentence that referred to the deleted PD figure |

Work top to bottom; Part 1 items are submission blockers.

---

## PART 1 — SUBMISSION BLOCKERS

**1 · Senior (adult) author — MISSING.** (fix-list item 1) Title page lists only
Rachit Agrawal. JEI requires a senior/adult author listed **last**, and that
adult must submit through Editorial Manager.

**2 · Figure + table count is 9; limit is 8.** (items 2, 34, 36) Currently
6 figures + 3 tables. You must cut/merge at least one — and the two hand
boxes (item 16) and the policy-bounds table (item 36, now referenced by four
`[TODO-XREF-TABLE]` markers) would **add** to the count if rebuilt. Inventory in
Part 4. Easiest single move: merge Figure 6 and Table 3 (both are TMA-per-archetype).

**3 · Title is 134 characters; limit is 110.** (item 3) Shorten by ~24
characters — wording is yours. *(Do not soften the subject: the title's
game-theory/poker framing is accurate and should survive the trim.)*

---

## PART 2 — THE HYPOTHESIS SPINE (mentor guidance: make the paper hypothesis-central)

These four markers form one thread — write them as a set so they agree:

**8 · `[TODO-HYPOTHESIS]` (Summary, ¶12).** One explicit *"We hypothesized…"*
sentence. Frame it around the strategic-trust science (e.g., whether
observation-based reputation rewards exploitation) — **not** "our simulation
works" (item 11).

**10/11 · `[TODO-INTRO-CLOSING]` (end of Introduction, ¶25).** Closing paragraph
stating (a) the hypothesis, (b) the major results (the −0.752 → −0.094 ladder),
(c) 1–2 takeaways.

**NEW · `[TODO-DISCUSSION-LOOP]` ×2 (Discussion).** Close the loop on the
hypothesis:
- **¶55 (Discussion opening paragraph** — "The title to this research has been
  intentionally unsettling…"**):** restate the Introduction hypothesis and state
  plainly whether the results supported it.
- **¶76 (concluding paragraph** — "We have presented a controlled simulation
  study…"**):** the final verdict on the hypothesis alongside the ladder summary.

Location markers only — the sentences are yours. While editing ¶76, also decide
the tense of "the Pearson correlation … **falls** along the ladder" (see
`[VERIFY]` list below).

---

## PART 3 — FILL THE REMAINING PLACEHOLDERS

**6 · `[TODO-KEYWORDS]` (¶8).** 3–5 keywords, each a single standalone word.
Candidates from your own text: *trust, reputation, poker, Bayesian, agents,
simulation.*

**7 · `[TODO-OVERVIEW]` (¶9).** 2–3 sentence plain-language blurb (website summary).

**13 · `[TODO-LIST]` (¶20–24).** The "four lines of previous research" bulleted
list must become running prose in your words (JEI forbids main-text lists).

**16 · `[TODO-BOX]` ×2 (¶36, ¶53).** Hand-transcript boxes (hand #67, hand #146):
rebuild each as a Word figure/table at the end (counts toward the 8-item limit)
or cut it and fold the key line into the prose.

**17 · `[TODO-XREF]` ×2 (¶87, ¶88).** Former "Section N" cross-refs; JEI has no
section numbers. Reword to a named pointer ("later in the Materials & Methods")
or delete the clause.

**36 · `[TODO-XREF-TABLE]` ×4 (¶96, ¶112, ¶123, ¶127).** All four point at the
**per-archetype policy-bounds table**, which was never carried into this
document. Decide once: (a) rebuild it as a Word table at the end — it then takes
a number, counts toward the 8-item limit, and you replace all four markers with
"Table N"; or (b) reword the four sentences to not cite a table. This is the
single highest-leverage remaining decision because it interacts with blocker 2.

**(Figure-1 fallout) · `[FIG1-REMOVED]` (¶27).** The Prisoner's-Dilemma sentence
that referenced the removed borrowed figure — rewrite the clause to describe the
four PD payoffs in words, or delete it.

**Resolved for you in pass 2 (no action):** the five formerly-broken
figure/table numbers now read **Table 1** (×2, ¶32/¶50), **Figure 1** (×2,
¶34/¶50), **Table 2** (¶46). ⚠️ If you add, cut, or merge any figure/table while
fixing blocker 2, **re-check these five numbers** — they are correct only for
the current 6-figure/3-table set.

---

## PART 4 — FIGURE + TABLE INVENTORY (must end at ≤ 8)

Currently **9** (over by 1), before re-adding any boxes or the bounds table:

| # | Item | Notes |
|---|---|---|
| Fig 1 | Trust vs. final stack (LLM phases) | referenced ¶34, ¶50 |
| Fig 2 | Bounded vs. unbounded hill-climbing per seed | |
| Fig 3 | Economic ordering inversion P3 → P3.1 | |
| Fig 4 | Population dispersal in parameter space | |
| Fig 5 | Per-archetype preflop bluff-rate drift | |
| Fig 6 | TMA per archetype | overlaps Table 3 |
| Table 1 | Phase 3.1 economic outcomes | referenced ¶32, ¶50 |
| Table 2 | Behavioral fingerprints P1 vs P3.1 | referenced ¶46 |
| Table 3 | TMA per archetype | overlaps Fig 6 |
| (Box 1, Box 2) | hand transcripts — not counted yet (item 16) | |
| (bounds table) | not rebuilt — 4 markers point at it (item 36) | |
| (primer table) | limit-Hold'em primer — not rebuilt (item 36) | |

---

## PART 5 — PROSE DECISIONS (no marker — review in place)

**4 · Affiliation** "Independent research, 2025–2026" (¶3) → JEI requires a real
institution (your school: Department/School, City, State, Country).
**5 · "Student Authors" line** (¶6) → confirm school level; student must be a
first author.

**12 · Background-merge seams (Introduction, ¶26–30).** Three joins need your
transition sentences (seam quotes in the pass-1 version of this file):
¶26→¶27 (Resnick → "Second, there is…"), ¶28→¶29 (Nowak → "Third, there is
Bayesian opponent modeling…"), ¶29→¶30 ("…we adopted." → "Finally…").

**19 · Discussion-subsection seams (¶55–78).** Four joins: ¶59→¶60, ¶63→¶64,
¶67→¶68, ¶71→¶72.

**20 · Conclusion folded into Discussion.** Confirm ¶76–78 read as a conclusion
(you will already be editing ¶76 for the loop-closer).

**24 · Methods voice — 2 sentences remain.** Pass 2 converted every cleanly
invertible first-person sentence (18 total across both passes). Two have no
word-preserving passive and need your rewording:
- ¶85: "…a likelihood P(a|t) that a type-t opponent would have taken the action
  a **we just observed**…"
- ¶92: "…the metrics; **we close with** a detailed description of the four agent
  implementations, one per phase."
Also note the Methods still contains agentless present-tense system description
("Every agent uses a hill climber…") — JEI convention is past+passive for what
you did, but present for how the system works is defensible; your call.

**31 · 16 removed footnote definitions.** Integrate as clauses or drop
(paraphrase anything externally sourced): bluff/value bet/fold equity; side pot;
TEI; CS; OA; NS; walkover; hand rank; 3-bet/4-bet; L₁ distance; VPIP; PFR; AF;
SU; continuation bet; tell.

**32 · Reference DOIs.** Look up and append the `https://doi.org/...` link for
each of the 12 references (none existed in the source; none were fabricated).

**44 · Length.** Main text ≈ 8,600 words ≈ 18–20 pages at Arial 11 / 1.5 — the
JEI limit is 10 pages (Intro → end of Methods). Substantial trimming required;
content work only you can do.

### `[VERIFY]` proofreading flags
- **9** — Summary opens with rhetorical questions; JEI summaries are declarative.
- **14** — Intro present tense: general truths fine; "what we did/found" must be past.
- **15 (residual)** — deliberately left present: ¶32 "frames/reports/previews"
  and ¶46 "Table 2 reports" (document-navigation meta-text), ¶38 "reads its
  posterior" (mechanism description). Convert only if you want strict past
  throughout. **New:** ¶76 "the Pearson correlation … **falls** along the
  ladder" (Discussion) — decide while writing the loop-closer there.
- **18** — italic Phase 1…3.1 subheaders in Results kept (allowed).
- **21** — Discussion: data *support*, never *prove*.
- **22** — Limitations (¶72–75) shouldn't dominate the Discussion.
- **28** — archetype descriptions (Methods) must read as prose, not a disguised list.
- **30** — add software/library versions (hand evaluator, NumPy, Anthropic SDK).
- **33** — MLA-8 title-case consistency across references.
- **35** — every figure caption: title, what's shown, methods, stats, n = 5 seeds.
- **42** — 21 scare-quote pairs are your own terms (allowed); confirm none are
  verbatim external quotations.
