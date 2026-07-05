# JEI Fix List — items you must edit by hand

This document lists everything that requires changing your **words** or supplying
**missing content**, which the formatting pass could not (and must not) do for you.
The companion file `JEI_formatted_manuscript.docx` already has the mechanical
formatting applied (Arial 11, 1.5 spacing, 1″ margins, continuous line numbers,
JEI section order, instruction blocks removed, figures/tables at the end,
references renumbered to MLA 8). Every item below is a prose- or content-level
decision that is yours to make.

> **Read this first — prose provenance.** Your manuscript text was converted
> mechanically from the LaTeX source into the JEI template. Conversion can
> introduce subtle artifacts (spacing around former math, dropped/[]-marked
> cross-references). **Proofread the body against your original** for
> character-exactness before submitting. Items flagged `[VERIFY]` are the
> most likely spots.

---

## A. SUBMISSION BLOCKERS (JEI will return the manuscript without these)

1. **Senior (adult) author — MISSING.** The title page lists only one author
   (Rachit Agrawal). JEI **requires** a senior/adult author, listed **last**,
   and that adult (not the student) must submit through Editorial Manager.
   → Add your mentor/PI as the senior author with a valid affiliation. Do not
   submit from a student account.

2. **Figure + table count over the limit.** JEI allows **8 figures + tables
   combined**. The manuscript currently has **7 figures + 3 tables = 10**, and
   that is *before* re-adding the two hand-transcript boxes (Box 1, Box 2) and
   the two Methods tables (policy-bounds table, limit-Hold'em primer) that were
   not carried over. → Decide which ≤8 to keep; merge or cut the rest. (See §G.)

---

## B. TITLE PAGE

3. **Title exceeds 110 characters** (currently **134**):
   "Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation Study of
   Bayesian Reputation Systems in 8-Player Limit Texas Hold'em".
   → Shorten to ≤110 characters. (Not done for you — wording change.)

4. **Affiliation = "Independent research".** JEI does not accept "unaffiliated"
   / "mentor" / general-industry affiliations. → Replace with a real
   institution (e.g., your school: Department/School, City, State, Country).

5. **Student Authors line** reads "Rachit Agrawal, High School" as a placeholder.
   → Confirm school level and that this matches the author list (student must
   also be a first author).

6. **KEYWORDS — MISSING.** A "KEYWORDS:" heading is present but empty.
   → Supply **3–5 keywords, each a single standalone word** (no phrases).
   Candidate single words you might choose from your own text: *trust,
   reputation, poker, Bayesian, agents, simulation.*

7. **OVERVIEW — MISSING.** An "OVERVIEW:" heading is present but empty.
   → Supply a 2–3 sentence plain-language blurb (used as the website summary).

---

## C. SUMMARY

8. **No explicit hypothesis.** JEI requires a "**We hypothesized…**" sentence in
   the Summary. The current summary (your narrative abstract, 170 words, one
   paragraph, no citations — all compliant) has none. → Add a "We
   hypothesized…" sentence.

9. `[VERIFY]` The Summary opens with rhetorical questions ("What if being
   trustworthy cost you something?"). JEI summaries are narrative and
   declarative; consider whether the rhetorical framing is appropriate. (No
   change made — stylistic, your call.)

---

## D. INTRODUCTION

10. **Closing-paragraph requirements missing.** JEI requires the final
    Introduction paragraph to state (a) the hypothesis ("We hypothesized…"),
    (b) the major results, and (c) 1–2 key takeaways. The current Introduction
    ends on a transition sentence ("This study could not have been possible
    without…") with none of these. → Add the closing paragraph.

11. **Hypothesis must be about the *science*, not the model.** Per JEI's
    ML/simulation guidance, frame the hypothesis around the strategic-trust
    dynamics (e.g., whether observation-based reputation rewards exploitation),
    **not** "our simulation works." → Phrase accordingly when you add item 10/8.

12. **Background was a separate section; it is now merged into the
    Introduction, and its subsection headings (2.1–2.4) were removed** (JEI
    Introductions are narrative with **no subheadings**). The merge may read
    abruptly at the former subsection seams. → Add transition sentences between
    the merged paragraphs. (Connective wording is a prose change — not done.)

13. **Bulleted list in the main text.** The "four lines of previous research"
    appears as a bulleted list. JEI forbids bulleted/numbered lists in the main
    text (Summary→Methods). → Rewrite as prose. (Left as a list + flagged; not
    converted.)

14. `[VERIFY]` Present tense. The Introduction uses present tense for general
    claims ("Trust is…"). General truths can stay present, but statements about
    what *you did/found* must be past tense. → Review.

---

## E. RESULTS

15. **Present tense throughout.** Results are written in present tense
    ("Phase 1 **produces** rtp = −0.752…", "Phase 2 **generates**…"). JEI
    requires **past tense** in Results (e.g., "Phase 1 produced…"). → Convert
    all Results verbs to past tense. (Not done — wording.)

16. **Hand-transcript boxes (Box 1, Box 2) removed from the body.** Each is a
    multi-line action table that cannot sit in the JEI main text. They appear
    as bracketed placeholders. → Either rebuild them as a Figure/Table at the
    end (counts toward the 8-item limit) or cut them. Their surrounding
    sentences ("The mechanism is also visible in a single representative
    hand…") remain in the Results prose.

17. **Cross-references show as "Figure [#]" / "Table [#]" / "Equation [#]".**
    The figure/table/equation numbers could not be auto-resolved after
    reordering. → Replace each `[#]` with the correct number once you finalize
    which figures/tables you keep.

18. `[VERIFY]` Italic subsection headers (Phase 1…Phase 3.1) were **kept** —
    these are allowed in Results. Confirm you want them.

---

## F. DISCUSSION

19. **Subsection headings (5.1–5.4) removed.** JEI Discussions are narrative
    with **no subheadings**. The four subsections were concatenated; add
    transition sentences at the seams. (Not done — wording.)

20. **Conclusion (§6) folded into the Discussion.** JEI has no separate
    Conclusion section; its content now ends the Discussion. → Review that it
    reads as a concluding paragraph, per JEI ("Conclude with a paragraph that
    briefly summarizes results and impact").

21. `[VERIFY]` Overclaiming. No literal "prove/proves" was found (good). Still
    review for causal overstatement; JEI: data *support*, not *prove*.

22. `[VERIFY]` Limitations are present (former §5.4) but should not dominate the
    Discussion. Confirm balance.

---

## G. MATERIALS & METHODS

23. **Section order.** Per JEI, Materials & Methods is placed **after**
    Discussion (done). Unusual for a CS paper but required — confirm you accept.

24. **Active voice → passive voice.** JEI expects **passive voice in Materials
    & Methods only** (active everywhere else). Your Methods are in active voice
    ("We use 8-player fixed-limit…", "We construct eight archetypes…"). →
    Convert Methods sentences to passive (e.g., "Eight archetypes were
    constructed…"). (Not done — wording.)

25. **Equations replaced with placeholders.** Five display equations (Pearson
    correlation; Bayesian posterior update; between-hand decay; trust score;
    and the Bayes-rule definition) appear as
    "[Equation — re-enter with Word's equation editor…]". JEI requires
    equations entered with Word's equation/Insert-Symbol tools, **not** pasted.
    → Re-enter each equation natively. (Originals are in your LaTeX source.)

26. **Pasted/Unicode math symbols.** Inline symbols were rendered as text
    (rtp, ε, λ, δ, σ, ≈, ±, ×, ≤, ≥, Σ, →, ∈, |, log2, superscripts/subscripts
    like Phase 2^*). → Re-enter all of these via Word's **InsertSymbol** /
    equation editor so Editorial Manager can read them.

27. **§2.5 "Ideas in mathematics" moved from Background to Methods.** This
    math-primer subsection now opens Methods. → Confirm placement and add a
    transition if needed.

28. `[VERIFY]` The eight archetype descriptions (Oracle…Judge) read as a
    run of short definitional paragraphs. Ensure they read as prose, not a
    disguised list.

29. **Code citation.** A "Code availability" note citing the GitHub repo
    (https://github.com/RachitAgrawal146/Poker_trust) was added in Methods, and
    the repo is also cited in the Appendix. JEI does **not** accept Google
    Drive links (none present). → Confirm this is how you want code cited
    (repo citation vs. full code appendix).

30. `[VERIFY]` Software/version specificity. Seeds (42, 137, 256, 512, 1024)
    and the model (Claude Haiku 4.5) are stated. Library/version details
    (e.g., the poker hand evaluator, NumPy, the Anthropic SDK version) are not
    given precisely — the simulation analogue of JEI's "company + catalog
    number" rule. → Add versions where vague.

---

## H. FOOTNOTES (JEI does not use footnotes)

31. **16 footnote definitions were removed from the body** (JEI manuscripts do
    not use footnotes). These are mostly poker-term/metric definitions. Decide
    for each whether to (a) integrate the definition into the sentence as a
    clause, or (b) drop it (scientific terms/acronyms need no definition under
    JEI). **Definitions taken from external sources must be paraphrased.** The
    removed definitions were:
    1. bluff / value bet / fold equity
    2. side pot (all-in mechanics)
    3. TEI (Trust Exploitation Index)
    4. CS (Contextual Sensitivity)
    5. OA (Opponent Adaptation)
    6. NS (Non-Stationarity)
    7. walkover / uncontested pot
    8. hand rank (7-card equity tables)
    9. 3-bet / 4-bet
    10. L1 distance
    11. VPIP (voluntarily put in pot)
    12. PFR (preflop raise rate)
    13. AF (aggression factor)
    14. SU (Strategic Unpredictability)
    15. continuation bet (c-bet)
    16. tell

---

## I. REFERENCES

32. **DOIs / URLs missing.** JEI requires "https://" links for any reference
    with a DOI or weblink. The source `.bib` had no DOIs, so none could be
    added (fabricating them is not allowed). → Look up and append the DOI URL
    for each of the 12 references. (Formatting is otherwise MLA 8: numbered by
    citation order, "first author et al." for 3+ authors, journal names
    italicized, no hanging indent — all applied.)

33. `[VERIFY]` MLA 8 title capitalization. Titles were carried over as in the
    source; MLA uses title case. → Skim for consistency.

---

## J. FIGURES & TABLES (at the end of the document)

34. **Figure 1 is a borrowed screenshot.** Figure 1 is a screenshot of Nicky
    Case's "Evolution of Trust" interactive — **not your original work**. JEI
    requires copyright approval for any borrowed image, or replace it with an
    original figure. → Obtain permission or replace/remove. (Likely the easiest
    single cut toward the 8-item limit.)

35. **Figure captions.** Captions were carried over and split into a bold title
    + un-bold body. Confirm each caption contains: title, what is shown,
    methods, statistical tests/values, and **replicate/seed counts** (n = 5
    seeds). Add any missing element. The bold/un-bold split is approximate —
    `[VERIFY]` the title boundary on each.

36. **Tables built as Word tables (good):** Table 1 (Phase 3.1 economic
    outcomes), Table 2 (behavioral fingerprints P1 vs P3.1), Table 3 (TMA).
    The **policy-bounds table** and the **limit-Hold'em primer table** from
    your Methods/Background were **not** rebuilt. → If you keep them, create
    them with Word's InsertTable (not as images), counting toward the 8-item
    limit.

37. Multi-panel figures must be a single file (your trust-vs-stack and
    bounded-vs-unbounded figures are already single combined images — OK).

---

## K. GLOBAL PROSE-POLICY SCAN (report only)

38. **First-person singular:** none found ("we/our" used throughout) — OK.
39. **Present tense (Summary/Intro/Results/Discussion):** present-tense
    reporting found mainly in Results (see item 15) — convert to past.
40. **Active voice in Materials & Methods:** present throughout — convert to
    passive (item 24).
41. **Lists in main text:** the Background bullet list (item 13).
42. **Direct quotations:** 21 sets of double quotes were found; these are
    *scare quotes* on your own terms ("good", "baseline", "lookup tables",
    "load bearing", etc.), which are allowed. → Scan to confirm none are
    verbatim external quotations; JEI forbids direct quotations even when
    cited, and external definitions must be paraphrased.
43. **Pasted/Unicode symbols:** see item 26 — re-enter via InsertSymbol.

---

## L. LENGTH

44. **10-page limit** (Introduction → end of Materials & Methods). Confirm the
    final length after you re-enter equations, integrate footnote definitions,
    and cut figures/tables. The source manuscript ran ~13 journal pages in its
    two-column form, so expect to trim. (1–1.5 pages over is acceptable at
    initial submission.)
