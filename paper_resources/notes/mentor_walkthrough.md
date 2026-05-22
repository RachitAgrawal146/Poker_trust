# 30-Minute Walkthrough Script for Arpit

> Written 2026-05-04. Walks Arpit through (a) the unbounded Phase 2
> sub-experiment he proposed at the 2026-04-30 meeting, and (b) the
> final data-collection deliverables for the Polygence paper.
>
> Total target time: **30 minutes** (5 min × 6 beats).
> If running short, the must-show items are flagged with ★.

---

## Beat 0 — Tabs to keep open (60 sec setup before he joins)

Open these in this order; you'll click through them top-to-bottom:

1. ★ `paper_resources/figures/14_nash_convergence_compare.png` — weak vs aggressive
2. ★ `paper_resources/figures/13_nash_convergence_pca_aggressive.png` — 2D PCA
3. `paper_resources/notes/phase2_unbounded_writeup_aggressive.md` — backing prose
4. ★ `paper_resources/figures/01b_five_tier_ladder_with_unbounded.png` — five-tier
5. ★ `paper_resources/interesting_hands/EVOLUTION_STORY.md` — narrative arc
6. `paper_resources/interesting_hands/p3_story.txt` (search "HAND #67") — the trap
7. `paper_resources/interesting_hands/p31_story.txt` (search "HAND #146") — inversion
8. `paper_resources/README.md` — contents index
9. `reports/phase2_unbounded_scorecard_aggressive.txt` — backup numbers

---

## Beat 1 — Lead with the answer to his question (5 min) ★

**Open:** `figures/14_nash_convergence_compare.png`

**Say:**

> "You asked at last meeting whether unbounded agents would converge
> to a Nash-equilibrium-like Oracle profile if they were all just
> trying to maximize economic return. I ran two experiments to find
> out — a default-strength hill-climber and an aggressive one — and
> the answer is **no, decisively**, in both cases.
>
> Each panel shows the same metric: the average L1 distance between
> all 8 agents in the 36-dimensional parameter space, plotted over
> 10,000 hands. If they were converging to Nash, this should drop
> toward zero. In both runs, the **opposite** happens. With the
> default optimizer they barely move (the line is flat). With the
> aggressive optimizer — 4× more cycles, 5× larger steps — they
> actually **diverge**, with cluster spread growing 30%."

**Pre-empt the obvious follow-up:** "Did the optimizer have enough
budget?" → "Yes, that's exactly why I ran the aggressive version.
Each agent gets 100 perturbation cycles vs the default 25; total
parameter drift is 11× larger. Agents *are* moving substantially —
they're just moving apart, not together."

---

## Beat 2 — Why no convergence (5 min)

**Open:** `notes/phase2_unbounded_writeup_aggressive.md` and scroll to
"Why no convergence to Nash?".

**Say:**

> "Three reasons, in order of importance:
>
> **First, the trust posterior is non-stationary inside each agent's
> optimization loop.** The trust model has lambda = 0.95 decay, so
> when Sentinel changes its strategy, opponents take ~70 hands to
> reflect that in their posteriors. Sentinel's hill-climber only
> evaluates 50-hand windows, so its accept-reject decisions are
> contaminated by opponents reacting to *stale beliefs*.
>
> **Second, all 8 agents are climbing simultaneously.** Sentinel's
> optimal response to Phantom-on-hand-100 differs from
> Phantom-on-hand-200, because Phantom is also drifting. The
> stationary-objective assumption hill-climbing relies on is
> violated.
>
> **Third, coordinate descent in 36 dimensions is fundamentally
> slow.** Even at 100 cycles, each (round, metric) slot is touched
> only ~3 times. Joint moves like 'raise more AND bluff more
> proportionally' can't be discovered by axis-aligned search."

**Pivot to the strengthening:**

> "The really nice thing about this result is it *strengthens* the
> paper's central argument. Phase 1 said the trust trap exists.
> Phase 2 bounded said adaptation softens but doesn't break it.
> *Both* unbounded experiments now say: this isn't a parameter-space
> limitation, and it's not an optimizer-budget limitation — the
> reputation system itself is the binding constraint."

---

## Beat 3 — The five-tier ladder (5 min) ★

**Open:** `figures/01b_five_tier_ladder_with_unbounded.png`

**Say:**

> "Updated headline figure. Phase 2 unbounded sits at r = -0.609,
> essentially identical to Phase 2 bounded (-0.637). Removing the
> personality bounds *does not* break the trap. The variance is
> three times higher (sigma = 0.221 vs 0.125) — some seeds
> dramatically softer (-0.354), others deeper (-0.887) — but the
> mean trap depth is unchanged.
>
> Notice the gap between Phase 2* and Phase 3.1. That's a delta of
> +0.515 — larger than all four prior phase transitions combined.
> The only intervention that meaningfully changes the dynamic is
> *qualitative reasoning* (Phase 3.1's CoT + memory + adaptive
> notes), not *quantitative optimization* at any tested scale."

If Arpit asks about the per-seed variance: open
`reports/phase2_unbounded_scorecard_aggressive.txt`. The TABLE A in
that file shows the full per-seed delta column.

---

## Beat 4 — Cross-phase inversion in two hands (5 min) ★

**Open:** `interesting_hands/EVOLUTION_STORY.md`

**Say:**

> "I curated story hands across all 5 phases — 38 total transcripts,
> all extracted from the canonical SQLites by a single phase-agnostic
> script. The arc tells a four-act story. The two most important
> hands are P3 #67 and P3.1 #146 — let me show you both."

**Open** `p3_story.txt`, search for **`HAND #67`**.

**Say:**

> "Phase 3 — LLM agents with personality specs but no reasoning
> scaffolding. Watch the LLM playing Wall: it calls a 4-bet pot
> preflop with **two-five offsuit** — total trash. Then calls flop,
> calls turn, calls river. Loses 35 chips to Firestorm's pair of
> jacks. This is the trap in microcosm: the LLM is mechanically
> following its 'calling station' personality with zero situational
> awareness. It would have folded at **any** real poker strategy
> level."

**Open** `p31_story.txt`, search for **`HAND #146`**.

**Say:**

> "Now Phase 3.1 — same LLM, same poker engine, same trust model,
> same archetype. Wall has K-Q hearts. Firestorm raises preflop;
> Wall calls. Firestorm c-bets flop and turn; Wall calls. Then
> Firestorm **checks** the river — that's a tell. The reasoning-
> scaffolded Wall picks up on it and **bets** the river. Firestorm
> calls with eight-queen suited. **Wall wins 32 chips.**
>
> This is precisely the kind of move canonical Wall would never
> make. The reasoning scaffolding lets Wall exploit Firestorm's
> exposed weakness while the trust system still classifies Wall as
> a passive caller. **47 total actions across two phases tells the
> entire project arc.**"

If Arpit asks "but is this a cherry-picked hand?" → "It's the
*highest-pot* P3.1 hand where Wall raised and won — selected by
SQL fingerprint, not by hand-curation. The selection criterion is
identical for all 5 phases. The fact that the criterion returns
*nothing* on the 'Wall pays off Firestorm' query in P3.1 is itself
a finding."

---

## Beat 5 — Data collection inventory (5 min)

**Open:** `paper_resources/README.md`

**Say:**

> "Everything for the paper lives under `paper_resources/`. Eleven
> figures at publication quality, eight CSVs of source data, five
> LaTeX-formatted tables paste-ready for Overleaf, four prose drafts
> for the discussion sections, and the cross-phase narrative
> document.
>
> Everything is **regeneratable** with one command:
> `bash analysis/make_all_paper_resources.sh`. The static figures
> (the ones that don't need the heavy SQLites) come from JSON
> dumps at the repo root. The unbounded-specific figures and the
> story hands are scripted off the new SQLite I generated this
> session.
>
> If we want to change a number — say, fix a typo in the headline
> ladder — it's a one-line edit in `analysis/make_paper_figures.py`
> and a re-run. No manual figure editing."

If Arpit wants to see a specific item:

| He says | Open |
|---|---|
| "show me the headline" | `figures/01_four_tier_ladder.png` |
| "the trap inversion" | `figures/03_economic_inversion.png` |
| "the trust farming numbers" | `figures/06_tma_by_archetype.png` |
| "the LaTeX table" | `tables/headline_ladder.tex` |
| "the prose draft" | `notes/phase2_unbounded_writeup_aggressive.md` |
| "where do these numbers come from" | `data/headline_ladder.csv` |

---

## Beat 6 — What's next + open the door (5 min)

**Say:**

> "Paper finalization is the immediate next step — I have the
> Markdown source ready and a Pandoc-converted LaTeX file for
> Overleaf. The new content from this session — Phase 2 unbounded,
> the convergence falsification, the cross-phase narrative — needs
> to be slotted into Sections 5.5, 6.3, and an appendix.
>
> Beyond that, the three Phase 4 directions captured in
> `paper_resources/notes/future_work_expanded.md`:
>
> 1. **n = 20 seed replication** of Phase 3.1 — tightens the 95% CI
>    on r from [-0.36, +0.18] to something we can talk about with
>    confidence. ~$60 of API spend.
>
> 2. **Multi-LLM tournament** — Sentinel as Sonnet, Firestorm as
>    GPT-4, Wall as a smaller open model. Tests whether the trap
>    survives agent diversity, not just model capability.
>
> 3. **No-limit Hold'em** — limit constrains aggression; in
>    no-limit, Firestorm could shove all-in. The trap may be
>    substantially deeper or shallower.
>
> Before any of those, I'd value your input on (a) is the current
> result tight enough to publish, and (b) which Phase 4 direction
> would be the strongest follow-up."

---

## FAQ — likely Arpit questions and prepared answers

**Q: "Why aggressive HC instead of CMA-ES or REINFORCE?"**

A: Engineering effort vs evidence quality. The aggressive HC takes
~90 min of CPU and required no new dependencies. CMA-ES would have
taken a day to integrate properly and would only sharpen — not
change — the conclusion. The three structural reasons (non-
stationary trust, multi-agent simultaneity, coupled-coordinate
gradient) apply to any local optimizer. Phase 4 could try CMA-ES
as a robustness check.

**Q: "Couldn't the agents converge if you ran it longer?"**

A: Possibly, but the per-seed variance suggests not. With aggressive
HC after 10,000 hands, two seeds converged toward Firestorm-like
strategies (deeper trap), two diverged (different local optima),
one stayed put. Different seeds, different trajectories — there's
no shared attractor for the search to find.

**Q: "What if the trust model itself were adaptive?"**

A: Phase 3.1's effect is exactly that — but inside the agent's
*reasoning*, not the system's posterior. The agent uses per-opponent
memory and adaptive notes to *reason as if* the trust model were
adapting. The system's likelihood tables remain Phase 1's (static)
throughout. A Phase 4 design with an adaptive system-side trust
posterior is a separate, interesting experiment but not what we
ran here.

**Q: "Can I see one of the per-seed P3.1 inversions?"**

A: Yes — open `reports/phase31_long_scorecard.txt`. Seeds 512 and
1024 have positive r (trap inverted: trusted agents made *more*
money than distrusted ones). For a hand-level example from those
seeds, run:
```
python3 analysis/extract_story_hands.py \
    --db runs_phase31_long.sqlite --phase P3.1-seed1024 --seed 1024
```

**Q: "How do I reproduce all of this?"**

A: From the repo root:
```
bash analysis/make_all_paper_resources.sh
```
That's the canonical regeneration command. It auto-detects whether
the unbounded SQLite is present and skips the dependent steps if
not. Static figures + tables run unconditionally.

---

## After the meeting — capture his feedback

Open a quick note `paper_resources/notes/mentor_meeting_2026-05-XX.md`
and jot down:

- Did he agree the unbounded result is publishable as-is?
- Which Phase 4 direction did he push toward?
- Any methodology critiques you didn't anticipate?
- Did he suggest specific framings for Sections 5.5 / 6.3?

The pattern that worked at past meetings: capture the questions you
*couldn't* answer in real time. Those become the Phase 4 work items.
