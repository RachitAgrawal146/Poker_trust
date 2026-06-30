# TODO_handwrite.md — author hand-edit punch list

The mechanical pass (`CHANGELOG.md`) is done. Everything below needs **your
words** or **your decision** — none of it could be done mechanically without
authoring scientific content, which the JEI AI policy forbids me from doing.

Every spot that needs new words has a **bracketed marker in
`JEI_manuscript_WORKING.docx`** so you can `Ctrl-F` to it:

| Marker | Meaning |
|---|---|
| `[TODO-KEYWORDS]` `[TODO-OVERVIEW]` `[TODO-HYPOTHESIS]` `[TODO-INTRO-CLOSING]` | empty/missing required element — write it |
| `[TODO-LIST]` | a forbidden list to rewrite as prose |
| `[TODO-BOX]` | a hand-transcript box to rebuild as a figure/table or cut |
| `[TODO-XREF]` | a section cross-reference that JEI numbering dropped |
| `[FIG1-REMOVED]` | a sentence that referred to the deleted Figure 1 |
| `[#]` | a figure/table/equation number to fill once you finalize the set |

Work top to bottom; Part 1 are submission blockers.

---

## PART 1 — SUBMISSION BLOCKERS (JEI returns the manuscript without these)

**1 · Senior (adult) author — MISSING.** (fix-list item 1) The title page lists
only **Rachit Agrawal**. JEI requires a senior/adult author listed **last**, and
that adult must submit through Editorial Manager. → Add your mentor/PI with a
real affiliation; do not submit from a student account.

**2 · Figure + table count is 9; limit is 8.** (items 2, 34) I removed the
borrowed Figure 1 (Nicky Case screenshot), so you are down from 10 to **9**
(6 figures + 3 tables). You must drop **one more**, and remember the two
hand boxes (item 16) and two Methods tables (item 36) are *not* counted yet.
See the inventory in **Part 4**.

**3 · Title is 134 characters; limit is 110.** (item 3) Current:
> "Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation Study of
> Bayesian Reputation Systems in 8-Player Limit Texas Hold'em"

→ Cut ~24 characters. A compliant option (96 ch) you may adapt:
*"Trust Dynamics in Multi-Agent Strategic Interaction: A Bayesian Reputation
Study in Limit Hold'em."* (Wording is yours.)

---

## PART 2 — FILL THE PLACEHOLDERS (each has a marker in the docx)

**6 · KEYWORDS** — `[TODO-KEYWORDS]`, ¶8. Supply **3–5 keywords, each a single
standalone word** (no phrases). Drawn from your own text, you might pick from:
*trust, reputation, poker, Bayesian, agents, simulation.*

**7 · OVERVIEW** — `[TODO-OVERVIEW]`, ¶9. A 2–3 sentence plain-language blurb
(the website summary).

**8 · Hypothesis in the Summary** — `[TODO-HYPOTHESIS]`, ¶12. Add one explicit
*"We hypothesized…"* sentence. Frame it about the **science** (whether
observation-based reputation rewards exploitation), not about the model
"working" (item 11).

**10/11 · Closing Introduction paragraph** — `[TODO-INTRO-CLOSING]`, ¶25. JEI
requires the final Intro paragraph to state (a) the hypothesis, (b) the major
results (the −0.752 → −0.094 ladder), and (c) 1–2 key takeaways. The Intro
currently ends on the question *"…does the cost of being trusting depend on the
trust system or on the agents inside it?"* — add the closing paragraph after it.

**13 · Bulleted list → prose** — `[TODO-LIST]`, ¶21–24. JEI forbids lists in the
main text. The "four lines of previous research" (lead-in ¶20) are currently
four list items — rewrite as a running paragraph **in your own words**:
1. (¶21) "The experimental economic literature on reputation systems in the
   Internet age: … the cost of transparency."
2. (¶22) "Computational studies on cooperation in repeated games — including the
   Prisoner's Dilemma to Axelrod's tournaments."
3. (¶23) "Bayesians use in modeling poker opponents — the inference mechanism we
   adopted."
4. (¶24) "The still-open question of whether large language models can reason
   strategically, or only mimic strategy."

**16 · Hand-transcript boxes** — `[TODO-BOX]`, ¶36 (Box 1) and ¶53 (Box 2).
Each was a multi-line action table that can't sit in JEI body text. The lead-in
sentences are kept:
- ¶35: *"The mechanism was also visible in a single representative hand…"* → Box 1
- ¶52: *"The mechanism underlying these values was best shown in a single hand.
  Box 2 reproduced Phase 3.1 hand #146: Wall, holding K♥ Q♥…"* → Box 2

→ For each: rebuild as a **Word figure/table at the end** (counts toward the
8-item limit — see Part 4) **or cut it** and fold the key line into the prose.

**17 · Cross-references `[#]`** — fill the number once your figure/table set is
final. Equation refs were already resolved (now read "Equation 2/3/…"). The
**9 remaining `[#]`** are:

| ¶ | Context |
|---|---|
| 32 | "…illustrative hands. **Table [#]** previews the endpoint…" |
| 34 | "…personality-only role-play (**Figure [#]**, left, Phase 3)…" |
| 46 | "…relative to Phases 1 and 2 (**Table [#]** reports per-archetype VPIP…)" |
| 50 | "…The right panel of **Figure [#]** (introduced earlier)…" |
| 50 | "…economic ordering was in **Table [#]**, shown at the start…" |
| 96 | "…the eight types — are given in **Table [#]**." |
| 112 | "…that of Sentinel (see **Table [#]**)…" |
| 123 | "…is described in turn; **Table [#]** gives the numerical policy…" |
| 127 | "…canonical parameters (see **Table [#]**)…" |

**17 (section refs) · `[TODO-XREF]`** — ¶87 and ¶88 referred to a numbered
*Section* ("…we will revisit this in Section [#]…", "…its definition is deferred
to Section [#]…"). JEI manuscripts have no section numbers. → Reword to a named
pointer ("…later in the Materials & Methods…") or delete the cross-reference.

**(Figure-1 fallout) · `[FIG1-REMOVED]`** — ¶27, inside the Prisoner's-Dilemma
background sentence. It read "…Figure [#] illustrates these four possible
outcomes." With Figure 1 gone, rewrite the clause to describe the four PD
payoffs in words, or delete the dependent clause.

---

## PART 3 — PROSE DECISIONS (no marker — review and revise in place)

**4 · Affiliation** "Independent research, 2025–2026" (¶3) → replace with a real
institution (your school: Department/School, City, State, Country).
**5 · "Student Authors" line** "Rachit Agrawal, High School" (¶6) → confirm
school level; the student must also be a first author.

**12 · Background-merge seams (Introduction).** The former Background subsections
(2.1–2.4) are now consecutive paragraphs ¶26–30 with no subheadings; the joins
may read abruptly. Add a transition sentence at each seam:
- ¶26 → ¶27 seam: *"…conducted by Resnick…"* **|** *"Second, there is a
  substantial amount of computational research concerning cooperation…"*
- ¶28 → ¶29 seam: *"…Nowak developed his five rules…"* **|** *"Third, there is
  Bayesian opponent modeling in poker. Initially this included Billings et
  al.'s Loki…"*
- ¶29 → ¶30 seam: *"…the inference mechanism we adopted."* **|** *"Finally, we
  treat this last point as it relates to two of our phases…"*

**19 · Discussion-subsection seams.** The former §5.1–5.4 are concatenated
(¶55–78), no subheadings. Smooth these joins:
- ¶59 → ¶60: *"…why this trap is so stable."* **|** *"The next three phases of
  the experiment narrow the space of possible explanations…"*
- ¶63 → ¶64: *"…trap behavior is a robust property…"* **|** *"The Phase 3.1
  result is consistent with an interpretation in which agent reasoning…"*
- ¶67 → ¶68: *"…meta-cognitive rather than informational…"* **|** *"These
  mechanisms suggest hypotheses for real-world reputation systems…"*
- ¶71 → ¶72: *"…the paper's central qualitative result…"* **|** *"Three clusters
  of limitations remain after the revisions above."*

**20 · Conclusion folded into Discussion.** JEI has no separate Conclusion. Your
former §6 now ends the Discussion at ¶76 (*"We have presented a controlled
simulation study…"*). Confirm it reads as a concluding paragraph that briefly
summarizes results and impact (¶78, *"Why should anyone care outside of
cards?…"*, currently closes it).

**24 · Methods passive voice (remaining).** Six sentences were already inverted
to passive (see CHANGELOG item 24). The rest of Materials & Methods (¶79–135)
is still mostly active voice ("We use…", "We construct…", "We characterize…").
JEI wants **passive voice in Methods only**. → Convert the remaining
"We <verb>…" sentences (e.g. "We use 8-player fixed-limit…" → "An 8-player
fixed-limit game was used…"). This is a large, meaning-preserving but
authorial sweep, so it is left to you.

**31 · 16 footnote definitions were removed.** JEI uses no footnotes. For each,
decide: (a) fold the definition into the sentence as a clause, or (b) drop it
(standard scientific terms need no definition). **Any definition taken from an
external source must be paraphrased.** Removed definitions:
bluff / value bet / fold equity; side pot; TEI; CS; OA; NS; walkover; hand rank;
3-bet / 4-bet; L₁ distance; VPIP; PFR; AF; SU; continuation bet (c-bet); tell.

**32 · Reference DOIs/URLs.** JEI requires an `https://` link for any reference
with a DOI/weblink. The source had none. → Look up and append the DOI URL for
each of the 12 references.

**44 · Length.** JEI's 10-page limit covers Introduction → end of Materials &
Methods. The current main text is **≈8,580 words** (Intro 1,650 / Results 1,575
/ Discussion 2,605 / Methods 2,565) which at the required Arial 11 / 1.5
spacing is well over 10 pages (rough estimate **~18–20 text pages** before
figures, tables, and references — render to confirm). → Substantial trimming is
required; this is content work only you can do.

### `[VERIFY]` proofreading flags (quick author confirmations)
- **9** — Summary opens with rhetorical questions ("What if being trustworthy
  cost you something?"). JEI summaries are declarative — keep or reword.
- **14** — Introduction present tense: general truths ("Trust is…") may stay
  present, but any "what we did/found" must be past.
- **15 (residual)** — 27 Results reporting verbs were converted to past tense.
  **7** were intentionally left and are yours to confirm: ¶32 "frames" (paper
  roadmap), ¶35 "calls every street" and ¶38 "reads its posterior" (general
  archetype behavior), and the four verbs in the Box 2 hand replay (¶52:
  "calls… reads… wins 32 chips… makes a river bet") — historical present. Convert
  to past if you want strict JEI past tense, or keep as deliberate present.
- **18** — Italic Phase 1…Phase 3.1 subheaders in Results were kept (allowed) —
  confirm you want them.
- **21** — Scan Discussion for causal overstatement (data *support*, not *prove*).
- **22** — Confirm Limitations (¶72–75) don't dominate the Discussion.
- **28** — Confirm the eight archetype descriptions (Methods) read as prose, not
  a disguised list.
- **30** — Add software/version specifics (hand evaluator, NumPy, Anthropic SDK
  version) — the simulation analogue of "company + catalog number."
- **33** — Skim references for MLA-8 title-case consistency.
- **35** — Confirm each figure caption has: title, what's shown, methods,
  statistics/values, and the seed count (n = 5); verify the bold-title boundary.
- **42** — 21 sets of double quotes are scare-quotes on your own terms (allowed);
  confirm none are verbatim external quotations (JEI forbids direct quotes).

---

## PART 4 — FIGURE + TABLE INVENTORY (must end at ≤ 8)

Currently **9** (over by 1), before re-adding any boxes/Methods tables:

| # | Item | Keep? |
|---|---|---|
| Fig 1 | Trust vs. final stack (LLM phases) | |
| Fig 2 | Bounded vs. unbounded hill-climbing per seed | |
| Fig 3 | Economic ordering inversion P3 → P3.1 | |
| Fig 4 | Population dispersal in parameter space | |
| Fig 5 | Per-archetype preflop bluff-rate drift | |
| Fig 6 | Trust Manipulation Awareness per archetype | |
| Table 1 | Phase 3.1 economic outcomes by archetype | |
| Table 2 | Behavioral fingerprints, P1 vs P3.1 | |
| Table 3 | Trust Manipulation Awareness per archetype | |
| (Box 1) | Hand #67 transcript — *not counted yet* (item 16) | |
| (Box 2) | Hand #146 transcript — *not counted yet* (item 16) | |
| (Methods) | Policy-bounds table — *not rebuilt* (item 36) | |
| (Methods) | Limit-Hold'em primer table — *not rebuilt* (item 36) | |

→ Decide the final ≤ 8. Note Fig 6 and Table 3 both present TMA — merging them
is one easy way to get under the limit. Re-number figures/tables and fill every
`[#]` (Part 2, item 17) once the set is locked.
