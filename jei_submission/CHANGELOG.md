# CHANGELOG — JEI mechanical-compliance pass

Working copy: `JEI_manuscript_WORKING.docx` (derived from the committed `JEI_formatted_manuscript.docx`). Every change below is **mechanical** — formatting, tense/voice surface morphology, symbol rendering, figure renumbering, or an inserted **placeholder** that carries no scientific meaning. No sentence meaning was authored, rephrased for content, summarized, or invented. Each entry is grouped by its `JEI_fix_list.md` item and shows the text *before* → *after*.

> **Paragraph numbers** are 0-indexed body-paragraph positions *at the time of the edit*. Two structural edits (Figure-1 caption removal, one stray list item) shifted later indices by ±1; the before→after text — not the index — is the authoritative locator.

## Change tally by fix-list item

| Fix-list item | Edits |
|---|---|
| Item 6 — KEYWORDS (empty heading → placeholder) | 1 |
| Item 7 — OVERVIEW (empty heading → placeholder) | 1 |
| Item 8 — Summary hypothesis (missing → placeholder) | 1 |
| Items 10/11 — Introduction closing paragraph (missing → placeholder) | 1 |
| Item 13 — Bulleted list in main text (flagged, not converted) | 1 |
| Items 15/39 — Results converted to past tense | 27 |
| Item 16 — Hand-transcript boxes (flagged → placeholder) | 2 |
| Item 17 — Equation cross-references resolved | 3 |
| Item 17 — Section cross-references (unresolvable → flagged) | 2 |
| Items 24/40 — Materials & Methods: active → passive voice | 6 |
| Items 26/43 — Pasted/leaked LaTeX symbols → proper glyphs | 17 |
| Items 26/43 — Sub/superscripts re-entered as real runs | 1 |
| Item 34 — Figure 1 (borrowed screenshot) removed | 1 |
| Item 34 — Figure 1 (borrowed screenshot) removed | 1 |
| Item 34 — Figures renumbered after removal | 6 |
| **Item 25 — 5 display equations + 1 inline equation re-entered natively** | 6 (see note below) |
| **Total logged mechanical edits** | **71** |

## Item 6 — KEYWORDS (empty heading → placeholder)

- **¶8**
  - before: KEYWORDS:...
  - after:  ...+ [TODO-KEYWORDS: author to supply 3–5 single standalone words — see TODO_handwrite.md item 6]

## Item 7 — OVERVIEW (empty heading → placeholder)

- **¶9**
  - before: OVERVIEW:...
  - after:  ...+ [TODO-OVERVIEW: author to supply 2–3 sentence blurb — see TODO_handwrite.md item 7]

## Item 8 — Summary hypothesis (missing → placeholder)

- **¶12**
  - before: What if being trustworthy cost you something? Repu...
  - after:  ...+ [TODO-HYPOTHESIS: author to add a “We hypothesized…” sentence — see TODO item 8]

## Items 10/11 — Introduction closing paragraph (missing → placeholder)

- **¶26**
  - before: Together, these define our core question: does the...
  - after:  ...+ [TODO-INTRO-CLOSING: author to add a closing paragraph stating the hypothesis (“We hypothesized…”), major results, and 1–2 takeaways — see TODO items 8/10/11]

## Item 13 — Bulleted list in main text (flagged, not converted)

- **¶22**
  - before: The experimental economic literature on reputation...
  - after:  ...+ [TODO-LIST: this bulleted list must become running prose in the author’s words — JEI forbids lists in the main text; see TODO item 13]

## Items 15/39 — Results converted to past tense

- **¶33** — _verbs: augments, establishes, is, replaces_
  - before: We present results in order of agent capability: Phase 1 (frozen rule-based agents) establishes the baseline trap; Phase 2 (bounded hill-climbing) tests whether numerical adaptation can soften it; Phase 2^* (unbounded hill-climbing) tests whether the bounds were the binding constraint; Phase 3 (LLM…
  - after:  We present results in order of agent capability: Phase 1 (frozen rule-based agents) established the baseline trap; Phase 2 (bounded hill-climbing) tests whether numerical adaptation can soften it; Phase 2^* (unbounded hill-climbing) tests whether the bounds were the binding constraint; Phase 3 (LLM…
- **¶35** — _verbs: are, dissolves, has, is, persists, produces, recurs_
  - before: Phase 1 produces rtp = -0.752 across the five canonical seeds, with per-seed values {-0.774, -0.608, -0.792, -0.812, -0.776}. Wall (the most-trusted archetype, honesty 0.96) has the smallest mean stack and approximately 9.4 rebuys per seed. Firestorm (the least-trusted, honesty 0.38) has the larges…
  - after:  Phase 1 produced rtp = -0.752 across the five canonical seeds, with per-seed values {-0.774, -0.608, -0.792, -0.812, -0.776}. Wall (the most-trusted archetype, honesty 0.96) had the smallest mean stack and approximately 9.4 rebuys per seed. Firestorm (the least-trusted, honesty 0.38) had the larges…
- **¶36** — _verbs: is, reproduces_
  - before: The mechanism is also visible in a single representative hand. (Firestorm happens to hold a genuine hand here rather than running a bluff; the hand directly illustrates Wall's calling-station leak.) Box 1 reproduces hand #67 from seed 42: Wall is dealt 2♠ 5♣ (hand rank 6,749, the worst hand at the …
  - after:  The mechanism was also visible in a single representative hand. (Firestorm happens to hold a genuine hand here rather than running a bluff; the hand directly illustrates Wall's calling-station leak.) Box 1 reproduced hand #67 from seed 42: Wall was dealt 2♠ 5♣ (hand rank 6,749, the worst hand at th…
- **¶39** — _verbs: are, blends, classifies, have, is, saturates_
  - before: The Predator archetype, which reads its posterior to choose exploitation targets, reliably classifies only 2 of 7 opponents above the prespecified 0.60 confidence threshold after 1,000 hands—Wall (p ≈ 1.0) and Firestorm (p ≈ 0.82)—with Phantom only occasionally crossing the threshold (p ≈ 0.60 in s…
  - after:  The Predator archetype, which reads its posterior to choose exploitation targets, reliably classified only 2 of 7 opponents above the prespecified 0.60 confidence threshold after 1,000 hands—Wall (p ≈ 1.0) and Firestorm (p ≈ 0.82)—with Phantom only occasionally crossing the threshold (p ≈ 0.60 in s…
- **¶41** — _verbs: agrees, are, does, generates, have, is, optimises_
  - before: Phase 2 generates rtp = -0.637 ± 0.125 with per-seed values {-0.759, -0.424, -0.719, -0.717, -0.564}. The direction of movement from Phase 1 (Δrtp = +0.116) agrees across all five seeds (directional movements of +0.015, +0.184, +0.073, +0.095, +0.212). The Opponent Adaptation metric also remains co…
  - after:  Phase 2 generated rtp = -0.637 ± 0.125 with per-seed values {-0.759, -0.424, -0.719, -0.717, -0.564}. The direction of movement from Phase 1 (Δrtp = +0.116) agreed across all five seeds (directional movements of +0.015, +0.184, +0.073, +0.095, +0.212). The Opponent Adaptation metric also remains co…
- **¶43** — _verbs: is, persists, yields_
  - before: Phase 2^* yields rtp = -0.609 ± 0.221 with per-seed values {-0.354, -0.700, -0.344, -0.887, -0.759}. The mean increase in rtp from Phase 2 is +0.028, well within the standard deviation associated with the seed-to-seed variation. With respect to movement in parameter space, the mean per-agent L₁ dri…
  - after:  Phase 2^* yielded rtp = -0.609 ± 0.221 with per-seed values {-0.354, -0.700, -0.344, -0.887, -0.759}. The mean increase in rtp from Phase 2 was +0.028, well within the standard deviation associated with the seed-to-seed variation. With respect to movement in parameter space, the mean per-agent L₁ d…
- **¶44** — _verbs: are, becomes, expands, is_
  - before: The explanation for why this occurs becomes apparent on examining the dispersal in cluster-spread space. The averaged pairwise L₁ distance between all eight agents in 36-dimensional parameter space expands from an initial 5.82 to ≥ 7.5 on every seed; the mean of the final-to-initial cluster-spread …
  - after:  The explanation for why this occurs became apparent on examining the dispersal in cluster-spread space. The averaged pairwise L₁ distance between all eight agents in 36-dimensional parameter space expanded from an initial 5.82 to ≥ 7.5 on every seed; the mean of the final-to-initial cluster-spread …
- **¶45** — _verbs: does, elaborate, incurs_
  - before: Firestorm's mean stack continues to remain 6× that of the next closest archetype; Wall still incurs 28 rebuys per seed. The economic ordering does not change. We credit the lack of convergence to three structural causes that we expect would survive any specific optimizer choice—non-stationary feedb…
  - after:  Firestorm's mean stack continues to remain 6× that of the next closest archetype; Wall still incurred 28 rebuys per seed. The economic ordering did not change. We credit the lack of convergence to three structural causes that we expect would survive any specific optimizer choice—non-stationary feed…
- **¶47** — _verbs: are, collapses, generates, is_
  - before: Phase 3 generates rtp = -0.510 ± 0.268 with per-seed values {-0.884, -0.525, -0.171, -0.712, -0.259}. This is a change from Phase 2 (Δrtp = +0.127) of similar magnitude to the Phase 1 → Phase 2 step. The variance of rtp among seeds is roughly double that of Phase 2 (0.268 vs. 0.125). Only two of si…
  - after:  Phase 3 generated rtp = -0.510 ± 0.268 with per-seed values {-0.884, -0.525, -0.171, -0.712, -0.259}. This was a change from Phase 2 (Δrtp = +0.127) of similar magnitude to the Phase 1 → Phase 2 step. The variance of rtp among seeds was roughly double that of Phase 2 (0.268 vs. 0.125). Only two of …
- **¶48** — _verbs: become, collapse, do, inform, is | CORRECTION: infinitive "do" in "what to do" preserved (auto-map over-converted to "did"; reverted)._
  - before: Specifications describing personality characteristics inform an LLM what to do, but not how to reason about doing so. Absent supporting information about reasoning, the LLMs in our sample collapse onto a more generic, stereotyped canonical interpretation of each archetype, and thus become more clas…
  - after:  Specifications describing personality characteristics informed an LLM what to do, but not how to reason about doing so. Absent supporting information about reasoning, the LLMs in our sample collapsed onto a more generic, stereotyped canonical interpretation of each archetype, and thus became more c…
- **¶50** — _verbs: cannot, do, generate, generates, has, indicate, is_
  - before: Phase 3.1 generates rtp = -0.094 ± 0.301 with per-seed values {-0.289, -0.338, -0.327, +0.047, +0.435}. The directional shift from Phase 3 (Δrtp = +0.416) is larger than that of any previous phase, but the small number of samples per seed (n = 5) and the short 150-hand horizon create significant un…
  - after:  Phase 3.1 generated rtp = -0.094 ± 0.301 with per-seed values {-0.289, -0.338, -0.327, +0.047, +0.435}. The directional shift from Phase 3 (Δrtp = +0.416) was larger than that of any previous phase, but the small number of samples per seed (n = 5) and the short 150-hand horizon create significant u…
- **¶51** — _verbs: is_
  - before: Wall's mean stack rises from 100–200 chips in Phases 1–3 to 280 in Phase 3.1; rebuy count drops from 9.4 per seed to zero, consistent with the rank-order claim above. The right panel of Figure [#] (introduced earlier) shows the trust–stack scatter under Phase 3.1: the negative slope visible in the …
  - after:  Wall's mean stack rises from 100–200 chips in Phases 1–3 to 280 in Phase 3.1; rebuy count drops from 9.4 per seed to zero, consistent with the rank-order claim above. The right panel of Figure [#] (introduced earlier) shows the trust–stack scatter under Phase 3.1: the negative slope visible in the …
- **¶52** — _verbs: are, warrants_
  - before: Four of six secondary metric targets are met in Phase 3.1 (vs. two of six in Phase 3). Strategic Unpredictability rises from 1.19 to 1.55 bits, crossing the >1.5 threshold for the first time across all phases. Trust Manipulation Awareness rises from +0.164 to +0.242, with six of eight archetypes sh…
  - after:  Four of six secondary metric targets were met in Phase 3.1 (vs. two of six in Phase 3). Strategic Unpredictability rises from 1.19 to 1.55 bits, crossing the >1.5 threshold for the first time across all phases. Trust Manipulation Awareness rises from +0.164 to +0.242, with six of eight archetypes s…
- **¶53** — _verbs: does, is, reproduces_
  - before: The mechanism underlying these values is best shown in a single hand. Box 2 reproduces Phase 3.1 hand #146: Wall, holding K♥ Q♥ (rank 872), calls a flop continuation bet and a turn barrel from Firestorm, reads Firestorm's river check as a tell, places a value bet on the river, and wins 32 chips. Ca…
  - after:  The mechanism underlying these values was best shown in a single hand. Box 2 reproduced Phase 3.1 hand #146: Wall, holding K♥ Q♥ (rank 872), calls a flop continuation bet and a turn barrel from Firestorm, reads Firestorm's river check as a tell, places a value bet on the river, and wins 32 chips. C…
- **¶34** — _residual reporting verb → past (context-verified)_
  - before: Firestorm wins,
  - after:  Firestorm won,
- **¶34** — _residual reporting verb → past (context-verified)_
  - before: it wins because
  - after:  it won because
- **¶40** — _residual reporting verb → past (context-verified)_
  - before: remains constant
  - after:  remained constant
- **¶44** — _residual reporting verb → past (context-verified)_
  - before: continues to remain
  - after:  continued to remain
- **¶46** — _residual reporting verb → past (context-verified)_
  - before: drops from 0.14
  - after:  dropped from 0.14
- **¶46** — _residual reporting verb → past (context-verified)_
  - before: falls from 1.88
  - after:  fell from 1.88
- **¶49** — _residual reporting verb → past (context-verified)_
  - before: spans roughly
  - after:  spanned roughly
- **¶49** — _residual reporting verb → past (context-verified)_
  - before: corresponds to comple
  - after:  corresponded to comple
- **¶50** — _residual reporting verb → past (context-verified)_
  - before: rises from 100
  - after:  rose from 100
- **¶50** — _residual reporting verb → past (context-verified)_
  - before: drops from 9.4
  - after:  dropped from 9.4
- **¶50** — _residual reporting verb → past (context-verified)_
  - before: shows the trust
  - after:  showed the trust
- **¶51** — _residual reporting verb → past (context-verified)_
  - before: rises from 1.19
  - after:  rose from 1.19
- **¶51** — _residual reporting verb → past (context-verified)_
  - before: rises from +0.1
  - after:  rose from +0.1

## Item 16 — Hand-transcript boxes (flagged → placeholder)

- **¶37**
  - before: [Hand-transcript box — relocate to Figures/Tables per JEI; see JEI_fix_list.md]
  - after:  [TODO-BOX: author to rebuild this hand transcript as a Figure or Table at the end (counts toward the 8-item limit) or cut it — see TODO item 16]
- **¶54**
  - before: [Hand-transcript box — relocate to Figures/Tables per JEI; see JEI_fix_list.md]
  - after:  [TODO-BOX: author to rebuild this hand transcript as a Figure or Table at the end (counts toward the 8-item limit) or cut it — see TODO item 16]

## Item 17 — Equation cross-references resolved

- **¶88**
  - before: Each agent maintains a categorical posterior distribution over the 8 archetypes for each other player at the table. They update their beliefs with Equation [#] on every action they observe. In Section [#], we will revisit this belief-updating mechanism (including the noise floor and hand-forgetting…
  - after:  Each agent maintains a categorical posterior distribution over the 8 archetypes for each other player at the table. They update their beliefs with Equation 2 on every action they observe. In Section [#], we will revisit this belief-updating mechanism (including the noise floor and hand-forgetting) …
- **¶97**
  - before: The eight archetypes (cooperative vs. exploitative; static vs. adaptable; based on opponent vs. based on action type) span the axes identified by Game Theory and Behavioral Economics as “load bearing.” The policies for each agent are tables of probability distributions over actions per round given …
  - after:  The eight archetypes (cooperative vs. exploitative; static vs. adaptable; based on opponent vs. based on action type) span the axes identified by Game Theory and Behavioral Economics as “load bearing.” The policies for each agent are tables of probability distributions over actions per round given …
- **¶109**
  - before: where L(a| t, r) is a precomputed likelihood that a type-t agent emits action a in round r, T is the set of eight archetypes, and ε = 0.05 is a noise floor preventing any type from being fully eliminated. We characterize Equation [#] as Bayes-flavoured but not strictly Bayesian. The noise floor is …
  - after:  where L(a| t, r) is a precomputed likelihood that a type-t agent emits action a in round r, T is the set of eight archetypes, and ε = 0.05 is a noise floor preventing any type from being fully eliminated. We characterize Equation 3 as Bayes-flavoured but not strictly Bayesian. The noise floor is en…

## Item 17 — Section cross-references (unresolvable → flagged)

- **¶88**
  - before: Each agent maintains a categorical posterior distribution over the 8 archetypes for each other player at the table. They update their beliefs with Equation 2 on every action they observe. In Section [#], we will revisit this belief-updating mechanism (including the noise floor and hand-forgetting) …
  - after:  Each agent maintains a categorical posterior distribution over the 8 archetypes for each other player at the table. They update their beliefs with Equation 2 on every action they observe. In [TODO-XREF: section number removed per JEI; author to rephrase — see TODO], we will revisit this belief-upda…
- **¶89**
  - before: A third concept—the honesty score h(t) that converts a probability distribution over archetypes into a scalar trust score—is specific enough to our setup that its definition is deferred to Section [#].
  - after:  A third concept—the honesty score h(t) that converts a probability distribution over archetypes into a scalar trust score—is specific enough to our setup that its definition is deferred to [TODO-XREF: section number removed per JEI; author to rephrase — see TODO].

## Items 24/40 — Materials & Methods: active → passive voice

JEI asks for passive voice in Materials & Methods only. These six sentences were converted **without changing meaning** (subject/verb inversion only). The remaining active-voice Methods sentences require authorial rewording and are left to the author (see TODO item 24).

| ¶ | Before | After |
|---|---|---|
| 82 | Two quantitative tools recur in every part of the analysis, and we introduce them once here so the rest of the paper can use them without further build-up. | Two quantitative tools recur in every part of the analysis, and they are introduced once here so that the rest of the paper can use them without further build-up. |
| 89 | A third concept—the honesty score h(t) that converts a probability distribution over archetypes into a scalar trust score—is specific enough to our setup that we defer its definition to Section [#]. | A third concept—the honesty score h(t) that converts a probability distribution over archetypes into a scalar trust score—is specific enough to our setup that its definition is deferred to Section [#]. |
| 95 | The overall game setting remains constant for all phases of this study. We will utilize a fixed-limit version of eight player Texas Hold'em, where the small blind is 1, the large blind is 2, the small bet (2) can be mad… | The overall game setting remains constant for all phases of this study. A fixed-limit version was utilized of eight player Texas Hold'em, where the small blind is 1, the large blind is 2, the small bet (2) can be made p… |
| 119 | We also present six auxiliary measures, including the index of exploitation of trust (TEI), sensitivity to context (CS), adaptation by the opponent (OA), non-stationarity (NS), unpredictability in strategy (SU), and awa… | Six auxiliary measures are also presented, including the index of exploitation of trust (TEI), sensitivity to context (CS), adaptation by the opponent (OA), non-stationarity (NS), unpredictability in strategy (SU), and … |
| 121 | These six auxiliary metrics were selected post-hoc rather than pre-registered. We report the metrics above descriptively, with no inferential tests; an individual value should therefore be interpreted as indicative rath… | These six auxiliary metrics were selected post-hoc rather than pre-registered. The metrics above are reported descriptively, with no inferential tests; an individual value should therefore be interpreted as indicative r… |
| 124 | The phases share every component described above and differ only in how each agent turns the current game state into an action. We describe each in turn; Table [#] gives the numerical policy that each phase starts from. | The phases share every component described above and differ only in how each agent turns the current game state into an action. Each is described in turn; Table [#] gives the numerical policy that each phase starts from. |

## Items 26/43 — Pasted/leaked LaTeX symbols → proper glyphs

- **¶36**
  - before: The mechanism is also visible in a single representative hand. (Firestorm happens to hold a genuine hand here rather than running a bluff; the hand directly illustrates Wall's calling-station leak.) Box 1 reproduces hand #67 from seed 42: Wall is dealt 2\spadesuit 5\clubsuit (hand rank 6,749, the w…
  - after:  The mechanism is also visible in a single representative hand. (Firestorm happens to hold a genuine hand here rather than running a bluff; the hand directly illustrates Wall's calling-station leak.) Box 1 reproduces hand #67 from seed 42: Wall is dealt 2♠ 5♣ (hand rank 6,749, the worst hand at the …
- **¶39**
  - before: The Predator archetype, which reads its posterior to choose exploitation targets, reliably classifies only 2 of 7 opponents above the prespecified 0.60 confidence threshold after 1,000 hands—Wall (p ≈ 1.0) and Firestorm (p ≈ 0.82)—with Phantom only occasionally crossing the threshold (p ≈ 0.60 in s…
  - after:  The Predator archetype, which reads its posterior to choose exploitation targets, reliably classifies only 2 of 7 opponents above the prespecified 0.60 confidence threshold after 1,000 hands—Wall (p ≈ 1.0) and Firestorm (p ≈ 0.82)—with Phantom only occasionally crossing the threshold (p ≈ 0.60 in s…
- **¶41**
  - before: Phase 2 generates rtp = -0.637 ± 0.125 with per-seed values {-0.759, -0.424, -0.719, -0.717, -0.564}. The direction of movement from Phase 1 (\Deltartp = +0.116) agrees across all five seeds (directional movements of +0.015, +0.184, +0.073, +0.095, +0.212). The Opponent Adaptation metric also remai…
  - after:  Phase 2 generates rtp = -0.637 ± 0.125 with per-seed values {-0.759, -0.424, -0.719, -0.717, -0.564}. The direction of movement from Phase 1 (Δrtp = +0.116) agrees across all five seeds (directional movements of +0.015, +0.184, +0.073, +0.095, +0.212). The Opponent Adaptation metric also remains co…
- **¶43**
  - before: Phase 2^* yields rtp = -0.609 ± 0.221 with per-seed values {-0.354, -0.700, -0.344, -0.887, -0.759}. The mean increase in rtp from Phase 2 is +0.028, well within the standard deviation associated with the seed-to-seed variation. With respect to movement in parameter space, the mean per-agent L_1 dr…
  - after:  Phase 2^* yields rtp = -0.609 ± 0.221 with per-seed values {-0.354, -0.700, -0.344, -0.887, -0.759}. The mean increase in rtp from Phase 2 is +0.028, well within the standard deviation associated with the seed-to-seed variation. With respect to movement in parameter space, the mean per-agent L₁ dri…
- **¶44**
  - before: The explanation for why this occurs becomes apparent on examining the dispersal in cluster-spread space. The averaged pairwise L_1 distance between all eight agents in 36-dimensional parameter space expands from an initial 5.82 to ≥ 7.5 on every seed; the mean of the final-to-initial cluster-spread…
  - after:  The explanation for why this occurs becomes apparent on examining the dispersal in cluster-spread space. The averaged pairwise L₁ distance between all eight agents in 36-dimensional parameter space expands from an initial 5.82 to ≥ 7.5 on every seed; the mean of the final-to-initial cluster-spread …
- **¶47**
  - before: Phase 3 generates rtp = -0.510 ± 0.268 with per-seed values {-0.884, -0.525, -0.171, -0.712, -0.259}. This is a change from Phase 2 (\Deltartp = +0.127) of similar magnitude to the Phase 1 → Phase 2 step. The variance of rtp among seeds is roughly double that of Phase 2 (0.268 vs. 0.125). Only two …
  - after:  Phase 3 generates rtp = -0.510 ± 0.268 with per-seed values {-0.884, -0.525, -0.171, -0.712, -0.259}. This is a change from Phase 2 (Δrtp = +0.127) of similar magnitude to the Phase 1 → Phase 2 step. The variance of rtp among seeds is roughly double that of Phase 2 (0.268 vs. 0.125). Only two of si…
- **¶50**
  - before: Phase 3.1 generates rtp = -0.094 ± 0.301 with per-seed values {-0.289, -0.338, -0.327, +0.047, +0.435}. The directional shift from Phase 3 (\Deltartp = +0.416) is larger than that of any previous phase, but the small number of samples per seed (n = 5) and the short 150-hand horizon create significa…
  - after:  Phase 3.1 generates rtp = -0.094 ± 0.301 with per-seed values {-0.289, -0.338, -0.327, +0.047, +0.435}. The directional shift from Phase 3 (Δrtp = +0.416) is larger than that of any previous phase, but the small number of samples per seed (n = 5) and the short 150-hand horizon create significant un…
- **¶53**
  - before: The mechanism underlying these values is best shown in a single hand. Box 2 reproduces Phase 3.1 hand #146: Wall, holding K\heartsuit Q\heartsuit (rank 872), calls a flop continuation bet and a turn barrel from Firestorm, reads Firestorm's river check as a tell, places a value bet on the river, and…
  - after:  The mechanism underlying these values is best shown in a single hand. Box 2 reproduces Phase 3.1 hand #146: Wall, holding K♥ Q♥ (rank 872), calls a flop continuation bet and a turn barrel from Firestorm, reads Firestorm's river check as a tell, places a value bet on the river, and wins 32 chips. Ca…
- **¶77**
  - before: We have presented a controlled simulation study of trust dynamics in 8-player Limit Texas Hold'em. Across four agent architectures, the Pearson correlation between agent trust score and final stack falls along the ladder -0.752 → -0.637 → -0.510 → -0.094, with each step accompanied by a confidence …
  - after:  We have presented a controlled simulation study of trust dynamics in 8-player Limit Texas Hold'em. Across four agent architectures, the Pearson correlation between agent trust score and final stack falls along the ladder -0.752 → -0.637 → -0.510 → -0.094, with each step accompanied by a confidence …
- **¶160**
  - before: Figure 5. The 8-agent population becomes dispersed in ⏎ parameter space. Averaged pairwise L_1 distance between all ⏎ eight agents in a 36-dimensional parameter space over ⏎ 10,000 hands of unbounded hill-climbing. (Left) ⏎ With weak HC (δ = 0.03), agents barely move. ⏎ (Right) Aggressive HC (δ = 0…
  - after:  Figure 5. The 8-agent population becomes dispersed in ⏎ parameter space. Averaged pairwise L₁ distance between all ⏎ eight agents in a 36-dimensional parameter space over ⏎ 10,000 hands of unbounded hill-climbing. (Left) ⏎ With weak HC (δ = 0.03), agents barely move. ⏎ (Right) Aggressive HC (δ = 0.…
- **¶162**
  - before: Figure 6. Per-archetype preflop bluff-rate drift under ⏎ aggressive unbounded hill-climbing. Each panel is one archetype ⏎ and each translucent line is one of the five seeds. Every ⏎ archetype's bluff rate wanders substantially over the run, yet the ⏎ panels do not converge on a common profile (the…
  - after:  Figure 6. Per-archetype preflop bluff-rate drift under ⏎ aggressive unbounded hill-climbing. Each panel is one archetype ⏎ and each translucent line is one of the five seeds. Every ⏎ archetype's bluff rate wanders substantially over the run, yet the ⏎ panels do not converge on a common profile (the…
- **¶74** — _\$ escape restored; T_crit set as subscript_
  - before: …\60 in API spend… T_crit = 2.776…
  - after:  …$60 in API spend… T<sub>crit</sub> = 2.776…
- **¶78** — _\$ escape restored_
  - before: …estimated cost \60 in API spend…
  - after:  …estimated cost $60 in API spend…
- **¶83** — _\bar restored as combining macron (x̄, ȳ); x_i,y_i set as subscripts_
  - before: …paired observations (x_i, y_i) with sample means \barx and \bary…
  - after:  …paired observations (x̄… subscript i …) with sample means x̄ and ȳ…
- **¶115** — _two \$ escapes restored_
  - before: …43 943 LLM calls, \33.10)… 11 953 calls, \17)…
  - after:  …43 943 LLM calls, $33.10)… 11 953 calls, $17)…
- **¶122** — _T_crit subscript; \binom rendered as native inline equation_
  - before: …T_crit = 2.776… from at most \binom2n-1n = 126 possible combinations…
  - after:  …T<sub>crit</sub> = 2.776… from at most [inline OMML binomial (2n−1 over n)] = 126…
- **¶21** — _leaked list-spacing directive (itemsep/\sep 2pt) that survived conversion as a stray numbered-list item_
  - before: sep2pt  (stray bold list item between the list lead-in and the first real item)
  - after:  (removed)

## Items 26/43 — Sub/superscripts re-entered as real runs

- **¶(global)**
  - before: (rtp/^* occurrences)
  - after:  23 paragraphs reformatted

## Item 34 — Figure 1 (borrowed screenshot) removed

- **¶152**
  - before:  / Figure 1. The Prisoner's Dilemma, as a g
  - after:  (removed)

## Item 34 — Figure 1 (borrowed screenshot) removed

- **¶28**
  - before: Second, there is a substantial amount of computational research concerning cooperation in repeated games. Prior to discussing cooperation, it is necessary to discuss the Prisoner's Dilemma as it is widely recognized as the paradigmatic example of the conflict between cooperation and exploitation. E…
  - after:  Second, there is a substantial amount of computational research concerning cooperation in repeated games. Prior to discussing cooperation, it is necessary to discuss the Prisoner's Dilemma as it is widely recognized as the paradigmatic example of the conflict between cooperation and exploitation. E…

## Item 34 — Figures renumbered after removal

- **¶154**
  - before: Figure 2. Trust versus final s
  - after:  Figure 1. Trust versus final s
- **¶156**
  - before: Figure 3. Bounded versus unbou
  - after:  Figure 2. Bounded versus unbou
- **¶158**
  - before: Figure 4. Economic ordering in
  - after:  Figure 3. Economic ordering in
- **¶160**
  - before: Figure 5. The 8-agent populati
  - after:  Figure 4. The 8-agent populati
- **¶162**
  - before: Figure 6. Per-archetype preflo
  - after:  Figure 5. Per-archetype preflo
- **¶164**
  - before: Figure 7. Trust Manipulation A
  - after:  Figure 6. Trust Manipulation A

## Item 25 — Display & inline equations re-entered as native OOXML math

Five "[Equation — re-enter…]" placeholders were replaced with native Word (OMML) equation objects generated from the original LaTeX, numbered (1)–(5) in document order, right-aligned with a centered equation body and a right-flush number (the JEI/standard convention). A sixth, inline, equation (the binomial coefficient in the Methods CI paragraph) was also re-entered natively. **0 equation placeholders remain.**

| # | Equation | Type | Source |
|---|---|---|---|
| (1) | Pearson correlation coefficient | display | `eq1.tex` |
| (2) | Bayes’ rule (definition) | display | `eq2.tex` |
| (3) | Categorical posterior update | display | `eq3.tex` |
| (4) | Between-hand trust decay | display | `eq4.tex` |
| (5) | Trust / honesty score | display | `eq5.tex` |
| inline | Binomial coefficient C(2n−1, n) | inline | from `\binom{2n-1}{n}` |

All six pass OOXML schema validation (element ordering for `m:dPr`, `m:rPr`, `m:naryPr`, `m:fPr` corrected to the CT_* sequence Word requires).

---

## Integrity corrections made during this pass

- **¶48 (Results):** the safe past-tense map over-converted the infinitive in "inform an LLM what to **do**" to "what to **did**". Reverted to "what to do" (the verb "do" there is an infinitive, not a finite Results verb). The finite verbs in the same sentence ("inform→informed", "collapse→collapsed") were kept.
- Noun/verb-ambiguous words (e.g. *causes, tests, reports, frames, calls, wins, reads, shows, makes, remains, spans*) were **excluded** from the automatic tense map to avoid mis-converting nouns; "three structural **causes**" was verified intact.
- The per-seed value sets written in braces — e.g. `{-0.774, -0.608, …}` — are legitimate set notation, **not** leaked LaTeX, and were left untouched.

---

# Pass 2 — final mechanical formatting pass (`JEI_manuscript_FINAL.docx`)

Working copy: `JEI_manuscript_FINAL.docx` (copied from `JEI_manuscript_WORKING.docx`, which is left untouched). Same rules as pass 1: every change below is mechanical — cross-reference numbers, verb form/voice only, or flag-only location markers. No scientific content was authored; no placeholder was filled. **32 edits this pass; 103 total across both passes.**

| Group | Edits |
|---|---|
| Item 17 — Figure/table cross-references resolved (5) | 5 |
| Items 17/36 — References to the never-carried-over policy-bounds table → flagged (4) | 4 |
| Items 15/39 — Results past tense, finished (9) | 9 |
| Items 24/40 — Methods active → passive, finished (11) | 11 |
| Items 24/40 — Methods mid-sentence tense parallel (1) | 1 |
| Mentor item — [TODO-DISCUSSION-LOOP] location markers (2, flag-only) | 2 |

## Item 17 — Figure/table cross-references resolved (5)

- **¶32** — _appositive names the target: "the final per-archetype economic ordering under Phase 3.1" = Table 1 caption_
  - before: Table [#] previews the endpoint
  - after:  Table 1 previews the endpoint
- **¶34** — _Figure 1 caption: "Trust versus final stack in the LLM phases. (Left) Phase 3 …"_
  - before: (Figure [#], left, Phase 3)
  - after:  (Figure 1, left, Phase 3)
- **¶46** — _Table 2 caption: "Behavioral fingerprints … VPIP = …; PFR = …"_
  - before: (Table [#] reports per-archetype VPIP
  - after:  (Table 2 reports per-archetype VPIP
- **¶50** — _same trust–stack scatter figure; right panel = Phase 3.1 per Figure 1 caption_
  - before: Figure [#] (introduced earlier)
  - after:  Figure 1 (introduced earlier)
- **¶50** — _"shown at the start of this section" = the Table 1 reference resolved at the Results opening_
  - before: in Table [#], shown at the start
  - after:  in Table 1, shown at the start

## Items 17/36 — References to the never-carried-over policy-bounds table → flagged (4)

- **¶96** — _target is the per-archetype policy-bounds table (LaTeX tab:bounds-comprehensive), absent from this docx_
  - before: are given in Table [#].
  - after:  are given in Table [TODO-XREF-TABLE: policy-bounds table was not carried into this document — rebuild it (counts toward the 8-item limit) or reword; see TODO item 36].
- **¶112** — _target is the per-archetype policy-bounds table (LaTeX tab:bounds-comprehensive), absent from this docx_
  - before: (see Table [#])
  - after:  (see Table [TODO-XREF-TABLE: policy-bounds table was not carried into this document — rebuild it (counts toward the 8-item limit) or reword; see TODO item 36])
- **¶123** — _target is the per-archetype policy-bounds table (LaTeX tab:bounds-comprehensive), absent from this docx_
  - before: Table [#] gives the numerical policy
  - after:  Table [TODO-XREF-TABLE: policy-bounds table was not carried into this document — rebuild it (counts toward the 8-item limit) or reword; see TODO item 36] gives the numerical policy
- **¶127** — _target is the per-archetype policy-bounds table (LaTeX tab:bounds-comprehensive), absent from this docx_
  - before: (see Table [#])
  - after:  (see Table [TODO-XREF-TABLE: policy-bounds table was not carried into this document — rebuild it (counts toward the 8-item limit) or reword; see TODO item 36])

## Items 15/39 — Results past tense, finished (9)

- **¶32** — _finishes the parallel list whose other verbs (established/replaced/augmented) were converted in pass 1; can→could is sequence-of-tenses_
  - before: tests whether numerical adaptation can soften it
  - after:  tested whether numerical adaptation could soften it
- **¶32** — _same parallel list_
  - before: tests whether the bounds were the binding constraint
  - after:  tested whether the bounds were the binding constraint
- **¶35** — _specific hand #67 narration; lead-in already past_
  - before: and calls every street of a 3-bet pot
  - after:  and called every street of a 3-bet pot
- **¶46** — _reported finding_
  - before: three of the metrics move backward
  - after:  three of the metrics moved backward
- **¶52** — _specific hand #146 narration_
  - before: calls a flop continuation bet
  - after:  called a flop continuation bet
- **¶52** — _specific hand #146 narration_
  - before: reads Firestorm
  - after:  read Firestorm
- **¶52** — _specific hand #146 narration_
  - before: places a value bet on the river
  - after:  placed a value bet on the river
- **¶52** — _specific hand #146 narration_
  - before: and wins 32 chips
  - after:  and won 32 chips
- **¶52** — _observed fact about the recorded Phase 1–3 datasets_
  - before: Canonical Wall never makes a river bet
  - after:  Canonical Wall never made a river bet

## Items 24/40 — Methods active → passive, finished (11)

- **¶84** — _subject/verb inversion, part 1 of sentence_
  - before: We use r between
  - after:  r between
- **¶84** — _part 2 of same sentence_
  - before: its final stack to measure how
  - after:  its final stack is used to measure how
- **¶84** — _de-agentified relative clause_
  - before: a value we call 
  - after:  a value called 
- **¶87** — _clean inversion inside the TODO-XREF sentence_
  - before: we will revisit this belief-updating mechanism (including the noise floor and hand-forgetting) in detail.
  - after:  this belief-updating mechanism (including the noise floor and hand-forgetting) will be revisited in detail.
- **¶92** — _clean inversion_
  - before: First we describe the common environment
  - after:  First the common environment is described
- **¶108** — _clean inversion_
  - before: We characterize Equation 3 as
  - after:  Equation 3 is characterized as
- **¶112** — _two clean inversions_
  - before: here we have chosen this simple form, and we report results under this definition throughout
  - after:  here this simple form has been chosen, and results are reported under this definition throughout
- **¶112** — _dummy-subject passive_
  - before: in our limitations section we note that
  - after:  in our limitations section it is noted that
- **¶114** — _clean inversion_
  - before: We discuss this issue explicitly in the discussion section
  - after:  This issue is discussed explicitly in the discussion section
- **¶119** — _de-agentified relative clause_
  - before: (which we call 
  - after:  (which is called 
- **¶127** — _clean inversion of embedded question_
  - before: can we achieve escape from the trap using
  - after:  can escape from the trap be achieved using

## Items 24/40 — Methods mid-sentence tense parallel (1)

- **¶114** — _finishes the mid-sentence parallel: the second clause already reads "and all phases used the same eight archetypes"_
  - before: All four phases use the same five random seeds
  - after:  All four phases used the same five random seeds

## Mentor item — [TODO-DISCUSSION-LOOP] location markers (2, flag-only)

- **¶55** — _location marker only; opening Discussion paragraph is the hypothesis-verdict slot_
  - before: The title to this research has been intentionally unsettling…
  - after:  …+ [TODO-DISCUSSION-LOOP: mentor guidance — restate the Introduction hypothesis here at the top of the Discussion and state whether the results supported it (author’s words; see TODO_handwrite.md)]
- **¶76** — _location marker only; concluding "We have presented…" paragraph_
  - before: We have presented a controlled simulation study of trust dyn…
  - after:  …+ [TODO-DISCUSSION-LOOP: mentor guidance — close the loop here: return to the stated hypothesis and give its final verdict alongside the ladder summary (author’s words; see TODO_handwrite.md)]

## Deliberately NOT changed in pass 2

- **¶32 "frames / reports / previews", ¶46 "Table 2 reports"** — document-navigation meta-text about the paper/table itself; conventionally present tense.
- **¶38 "which reads its posterior"** — general description of the Predator mechanism (a design truth), allowed in present.
- **¶85 "the action a we just observed", ¶92 "we close with a detailed description"** — the only two remaining first-person constructions in Methods; neither has a clean word-preserving passive, so they are left to the author (TODO item 24).
- **¶76 "falls along the ladder" (Discussion)** — Discussion tense was never part of the mechanical scope; flagged as a [VERIFY] item since the author will edit this paragraph anyway for the hypothesis loop-closer.
- **Title, subject terms, and all game-theory/poker framing** — untouched everywhere (see the Subject-integrity check in COMPLIANCE_REPORT.md).
