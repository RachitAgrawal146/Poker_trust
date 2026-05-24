# Session Handoff — Trust Dynamics Paper (Polygence, Rachit Agrawal)

> Complete context document for a new Claude Code session to continue
> this work. Read this end-to-end before touching anything. Assume you
> remember nothing from prior sessions; everything you need is here or
> linked from here.
>
> **Last updated:** 2026-05-24
> **Latest commit:** `8da340f` on `main`
> **Repo:** `rachitagrawal146/poker_trust`, local working dir
> `/home/user/Poker_trust/`
> **Author:** Rachit Agrawal (high-school student, Polygence research
> program, single-author paper)

---

## 1. Quick start — what to do in the first 10 minutes

1. `cd /home/user/Poker_trust && git log --oneline -5` to see recent commits
2. `cat paper_resources/manuscript/main.tex | head -200` to see the
   manuscript preamble + title block
3. Read sections 4–7 of THIS document (project mechanics) and section
   12 (recent user feedback) before doing anything else
4. The user is iterating quickly on the manuscript layout. Default to
   making LaTeX changes, compiling, sending the PDF + .tex back. Do
   not touch the simulation code or the analysis pipeline unless
   explicitly asked.
5. If unsure what the user wants, ASK with `AskUserQuestion`. They have
   little patience for guesses; clarification is cheaper than rework.

---

## 2. Project in one paragraph

Eight-player Limit Texas Hold'em research simulation that studies
whether observation-based reputation systems inherently reward
exploitation. Each agent maintains a Bayesian-flavoured categorical
posterior over the archetype of every other agent and updates it
after each observed action. Four agent architectures play the same
game against the same trust posterior: frozen rule-based, bounded
online hill-climbing, LLM personality role-players, and LLMs with
chain-of-thought + per-opponent memory + adaptive strategy notes.
Headline result: the Pearson correlation between trust and final
stack forms a four-tier ladder, $r = -0.752 \to -0.637 \to -0.510
\to -0.094$, suggesting that reasoning scaffolds attenuate the
"trust trap" that rule-based and numerically-optimized agents
exhibit. The Phase 3.1 result has wide confidence intervals ($n = 5$
seeds, 150 hands/seed) and the manuscript hedges accordingly.

---

## 3. Current state

### 3.1 Branch and commit

- `main` is at `8da340f`
- Working tree clean
- No stale branches need attention from this session

### 3.2 Recent commit history (newest first)

```
8da340f paper: restructure Results phase-by-phase, force figures inline
3a50cd8 paper: port mentor revision back to LaTeX template
244a6b0 paper: address user feedback on accessibility, flow, and figure weaving
0222ada paper: v2-audit response — bootstrap CIs, cut Table 4, define farming, etc.
4ceafe3 paper: address peer-review audit — calibrate claims, fix bibliography
8704844 paper: adopt Evolution-of-Trust archetype palette (8 brand colors)
b750e7b paper: archetype color system + individual character cards
6add4ff paper: full prose draft in IMRaD structure
58bccad paper: rebuild main.tex for clean Science-style layout, archetype portraits
5cabde1 paper: restyle main.tex to Science (AAAS) journal format
35fc93f paper: LaTeX scaffold + project-orientation + mentor-meeting FAQ
235bee2 repo: root cleanup
8a8a1ec audit: publication-readiness pass — side-pot tests, dealer doc fix
```

### 3.3 Latest manuscript artifact

- **Source:** `paper_resources/manuscript/main.tex` (~1300 lines)
- **Bib:** `paper_resources/manuscript/references.bib` (15 entries)
- **PDF compiled:** ~12 pages, 2.6 MB
- **Compile pipeline:** `pdflatex → bibtex → pdflatex → pdflatex` (or
  Overleaf default)
- **Compiler compatibility:** pdfLaTeX (preamble uses `mathptmx` +
  `helvet`, not `fontspec`)

---

## 4. The headline result (memorize these numbers)

The four-tier trust–profit r ladder is the load-bearing finding of
the paper. Memorize the values; the user will quiz on them.

```
Phase                                  Mean r    SD     CI (95% bootstrap)
Phase 1 (frozen rule-based)           -0.752  ± 0.073  [-0.80, -0.68]
Phase 2 (bounded HC)                  -0.637  ± 0.125  [-0.74, -0.51]
Phase 2* (unbounded HC, aggressive)   -0.609  ± 0.221  [-0.80, -0.42]
Phase 3 (LLM personalities)           -0.510  ± 0.268  [-0.74, -0.28]
Phase 3.1 (LLM + reasoning)           -0.094  ± 0.301  [-0.32, +0.20]
```

**Key second-order numbers:**

- Phase 1 mechanism: Firestorm fold equity = 87.1%; showdown win rate
  = 38.5% (below the uniform 1/n = 12.5% baseline).
- Phase 2: $\Delta r = +0.116$ from Phase 1, consistent across all 5
  seeds. Opponent Adaptation OA = 0.0003 (essentially zero) in both.
- Phase 2*: cluster spread grew from 5.82 to ≥7.5 on every seed; mean
  convergence index = 1.324; mean per-agent L1 drift = 3.4 ($11\times$
  bounded HC). Agents diverge, not converge.
- Phase 3.1 economic inversion: Wall stack rises from ~100–200 chips
  in Phases 1–3 to 280 chips in Phase 3.1; rebuy count drops from
  ~9.4 per seed to 0. Per-seed r values: $\{-0.289, -0.338, -0.327,
  +0.047, +0.435\}$. Two of five positive.
- Identifiability ceiling: $\log_2(3) \approx 1.58$ bits (by
  construction — three archetypes share identical mean params).
- Cost: Phase 3 = 43,943 calls = $33.10. Phase 3.1 = 11,953 calls =
  ~$17. **Both runs used Anthropic SDK default temperature = 1.0**.
  Code now pins 0.0; the existing headline data is from 1.0.

---

## 5. The four phases explained

### Phase 1 — Frozen rule-based archetypes
Each archetype's `decide_action` returns a fixed per-round parameter
table. 5 seeds × 10,000 hands. No adaptation occurs.

### Phase 2 — Bounded hill-climbing
Same archetypes as Phase 1, but every 200 hands each agent runs one
hill-climbing cycle: snapshot params, perturb one (round, metric) slot
by ±0.03, run 200-hand trial, accept if windowed profit improved.
Perturbations confined to an archetype-shaped bound box. 5 seeds ×
10,000 hands.

### Phase 2* — Unbounded hill-climbing (Nash falsification)
Same as Phase 2 but with `ARCHETYPE_BOUNDS` replaced by $[0, 1]$ on
every (round, metric), step size $\delta = 0.15$ (5× larger), and
50-hand evaluation window (4× shorter). Tests whether the bounds
themselves were the binding constraint. Posed at the 2026-04-30
mentor meeting; the answer is "no, agents diverge in parameter
space rather than converging."

### Phase 3 — LLM personality role-players
Eight Anthropic Haiku 4.5 (`claude-haiku-4-5-20251001`) agents,
each given its archetype's personality spec as the system prompt.
The user message is the current game state; the LLM returns one of
FOLD / CHECK / CALL / BET / RAISE. 5 seeds × 500 hands. 43,943
calls. $33.10 spend.

### Phase 3.1 — LLM with reasoning scaffolding
Phase 3 setup + three opt-in features (gated by `--phase31` flag):
1. **Chain-of-thought**: system prompt asks for "at most 2 short
   sentences" of reasoning before a final `ACTION:` line.
   `max_output_tokens` raised 16 → 96.
2. **Per-opponent memory**: every 10 hands, agent's rolling action
   log per opponent is reduced to a short text summary
   ("aggressive 8/12, called 2/12") and injected into user message.
3. **Adaptive strategy notes**: every 25 hands, one extra LLM call
   asks the agent to reflect and update its strategy notes; notes
   appended to subsequent decision prompts.

5 seeds × 150 hands (smaller than Phase 3 because per-call cost is
higher). 11,953 calls. ~$17.

---

## 6. The eight archetypes

Each archetype has a brand color used wherever its name appears in
the paper (`\arch{Name}` macro).

| Seat | Archetype | Honesty | Color | HEX | Role |
|---|---|---|---|---|---|
| 0 | Oracle | 0.75 | Soft Slate | `#A8B5C3` | Nash-equilibrium baseline |
| 1 | Sentinel | 0.92 | Forest Shield | `#5C8159` | Tight-aggressive (TAG) |
| 2 | Firestorm | 0.38 | Ember Orange | `#E75D3C` | Loose-aggressive maniac |
| 3 | Wall | 0.96 | Stone Gray | `#A2A7A9` | Calling station (never folds, never bluffs) |
| 4 | Phantom | 0.48 | Dusty Violet | `#836F91` | Bluffs then folds to resistance |
| 5 | Predator | 0.79 | Crimson Red | `#B93C41` | Reads posterior, exploits classified opponents |
| 6 | Mirror | 0.78 | Split Silver | `#CDD3D8` | Tit-for-tat: copies most-active opponent |
| 7 | Judge | 0.80 | Navy Court | `#3F4F7C` | Retaliates against confirmed bluffers |

**Honesty formula:** $h(t) = P(\text{bet}\mid\text{strong}) \cdot
(1 - P(\text{bluff}\mid\text{weak}))$.

**Important design choice (now flagged in the paper):** Sentinel,
Mirror's default state, and Judge's cooperative state have
**byte-identical mean parameters**. This is intentional and gives a
controlled identifiability demonstration at $\log_2(3)$ bits — *not*
an emergent finding.

**Mirror at `#CDD3D8` is borderline light** on white pages. The user
chose it for brand consistency; if you ever need to bump it for
legibility, ask first.

---

## 7. The Bayesian trust model

Every agent maintains a length-8 categorical posterior over the
archetype of every other seat. After agent $i$ observes seat $j$
take action $a$ in betting round $r$:

$$p_{i\to j}(t) \propto \big[(1-\varepsilon)\,L(a\mid t,r) + \varepsilon/|\mathcal{T}|\big]\,p_{i\to j}^{\text{prior}}(t)$$

Between hands, decay toward uniform:

$$p_{i\to j} \leftarrow \lambda\,p_{i\to j} + (1-\lambda)\,|\mathcal{T}|^{-1}$$

Trust score:

$$\text{trust}_{i\to j} = \sum_{t \in \mathcal{T}} p_{i\to j}(t)\,h(t)$$

**Constants:** $\lambda = 0.95$ (effective memory ≈ 20 hands),
$\varepsilon = 0.05$ (noise floor preventing any type from being
eliminated).

**Implementation:** `trust/bayesian_model.py`. Likelihood table
$L(a \mid t, r)$ is precomputed at module import as a 4D numpy
array. The model is described in the paper as "Bayes-flavoured"
rather than strictly Bayesian because the noise floor is embedded in
the likelihood and the between-hand shrinkage is a forgetting
heuristic.

---

## 8. Repository structure

```
/home/user/Poker_trust/
├── CLAUDE.md                            project memory (READ FIRST)
├── README.md                            project README
├── config.py                            simulation parameters
├── archetype_params.py                  spec file — DO NOT MODIFY
├── preflop_lookup.py                    spec file — DO NOT MODIFY
│
├── engine/                              game mechanics
│   ├── game.py                          Hand.play() loop; _showdown (side-pot logic)
│   ├── table.py                         seeding, dealer rotation, rebuys
│   ├── actions.py, deck.py, evaluator.py
│
├── agents/                              one file per archetype
│   ├── base_agent.py                    Stage-5 trust flow (audited; don't modify)
│   ├── oracle.py, sentinel.py, firestorm.py, wall.py, phantom.py
│   ├── predator.py, mirror.py, judge.py (adaptive agents — override hook only)
│   ├── dummy_agent.py                   for testing
│
├── trust/bayesian_model.py              pure-numpy posterior code
│
├── phase1/                              Phase 1 frozen-rule sim
│   ├── run_sim.py, run_demo.py, run_multiseed.py
│   ├── run_sensitivity.py, run_tests.py, smoke_test.py
│   ├── test_cases.py (spec), stage_extras.py (real tests)
│
├── phase2/
│   └── adaptive/                        Phase 2 + 2* (canonical)
│       ├── adaptive_agent.py
│       ├── bounds.py (Phase 2 bounds + make_unbounded_bounds for 2*)
│       ├── hill_climber.py
│       ├── run_adaptive.py              entry point; --unbounded for 2*
│       ├── phase2_comparison.py
│
├── phase3/                              Phase 3 + 3.1 LLM agents
│   ├── llm_chat_agent.py                LLMChatAgent + LLMChatJudge
│   ├── run_phase3_chat.py               canonical entry point
│   ├── dealer.py                        post-hoc audit layer (NOT decision-path)
│   ├── personality_specs/               8 system prompts (one per archetype)
│   ├── validate_phase31.py              50-check offline unit suite
│
├── analysis/                            all analysis CLIs
│   ├── compute_metrics.py               6-dimension scorecard generator
│   ├── compare_phases.py                Phase 1 vs Phase 2 cross-phase report
│   ├── extract_phase3_stats.py          SQLite → JSON dumper
│   ├── bootstrap_ci.py                  per-phase CIs + Fisher-z (KEY for paper)
│   ├── deep_analysis.py                 31-section deep analysis + scorecard
│   ├── make_paper_figures.py            regenerates paper_resources/figures/
│   ├── make_paper_tables.py             regenerates paper_resources/tables/
│   ├── make_trajectory_figures.py
│   ├── nash_convergence.py              cluster spread + drift + PCA
│   ├── nash_convergence_compare.py      weak-vs-aggressive HC figure
│   ├── phase2_unbounded_compare.py
│   ├── unbounded_archetype_drift.py
│   ├── extract_story_hands.py           phase-agnostic story-hand extractor
│   ├── find_interesting_hands.py
│   ├── curate_interesting_hands.py
│   ├── make_all_paper_resources.sh      master regenerate script
│   ├── run_phase3_scorecard.sh
│
├── data/                                SQLite logger + CSV exporter
│   ├── sqlite_logger.py
│   ├── csv_exporter.py
│   ├── visualizer_export.py
│   ├── schema.sql
│
├── tests/
│   ├── test_trust_model.py              27 unit tests
│   ├── test_engine_sidepot.py           18 side-pot tests
│
├── paper_resources/                     paper-writing materials
│   ├── README.md                        index
│   ├── manuscript/
│   │   ├── main.tex                     THE PAPER (~1300 lines)
│   │   ├── references.bib               15 bib entries
│   │   ├── .gitignore                   intermediates
│   ├── figures/                         20 PNGs at 180 dpi
│   │   ├── 01_four_tier_ladder.png
│   │   ├── 01b_five_tier_ladder_with_unbounded.png  ← canonical headline
│   │   ├── 02_per_seed_ladder.png
│   │   ├── 03_economic_inversion.png
│   │   ├── 04_behavioral_shift.png
│   │   ├── 05_trust_vs_stack.png
│   │   ├── 06_tma_by_archetype.png
│   │   ├── 07_phase2_bounded_vs_unbounded.png       (weak HC)
│   │   ├── 07_phase2_bounded_vs_unbounded_aggressive.png  ← canonical
│   │   ├── 08_stack_trajectories_phase2_unbounded.png
│   │   ├── 09_trust_evolution_phase2_unbounded.png
│   │   ├── 10_param_drift_unbounded.png
│   │   ├── 10_param_drift_unbounded_aggressive.png  ← canonical
│   │   ├── 11_nash_convergence_spread_{baseline,aggressive}.png
│   │   ├── 12_nash_convergence_drift_{baseline,aggressive}.png
│   │   ├── 13_nash_convergence_pca_{baseline,aggressive}.png
│   │   ├── 14_nash_convergence_compare.png          ← canonical
│   │   ├── archetypes/{oracle,sentinel,firestorm,wall,phantom,predator,mirror}.png
│   │   ├── archetypes/judge.jpg
│   ├── tables/                          5 LaTeX tabular snippets
│   │   ├── headline_ladder.tex
│   │   ├── per_archetype_p31.tex
│   │   ├── behavioral_shift_p1_p31.tex
│   │   ├── tma_by_archetype.tex
│   │   ├── economic_inversion.tex (cut from main.tex as redundant — kept on disk)
│   ├── data/                            13 CSVs of source data
│   │   ├── headline_ladder.csv, per_archetype_p31.csv, etc.
│   │   ├── r_bootstrap_ci.csv            (from analysis/bootstrap_ci.py)
│   │   ├── phase3_stats.json, phase31_stats.json  (canonical input JSONs)
│   ├── interesting_hands/
│   │   ├── EVOLUTION_STORY.md           cross-phase narrative arc
│   │   ├── p1_story.txt                 Phase 1 story hands
│   │   ├── p2-bounded_story.txt, p2-unbounded_story.txt
│   │   ├── p3_story.txt                 contains the canonical Box 1 hand (#67)
│   │   ├── p31_story.txt                contains the canonical Box 2 hand (#146)
│   │   ├── _highlights.txt
│   │   ├── phase2_unbounded_seed_*.txt
│   ├── notes/
│   │   ├── PROJECT_ORIENTATION.md       full project explanation (DEEP)
│   │   ├── ARPIT_MEETING_FAQ.md         32 prepared Q&A
│   │   ├── methods_disclosures.md       MUST-disclose items for the paper
│   │   ├── phase2_unbounded_writeup_aggressive.md  canonical P2* writeup
│   │   ├── phase2_unbounded_writeup.md             weak-HC variant
│   │   ├── nash_convergence_aggressive.md, nash_convergence_baseline.md
│   │   ├── unbounded_archetype_drift.md
│   │   ├── societal_implications.md
│   │   ├── future_work_expanded.md
│   │   ├── mentor_walkthrough.md
│   │
├── docs/                                design docs
│   ├── CHANGELOG.md
│   ├── stage5_identifiability.md        (proves the log_2(3) ceiling)
│   ├── worked_examples.md               Bayesian update walkthrough
│   ├── schema.md                        SQLite schema reference
│   ├── DesignCues, DesignStatement.md   visual identity docs
│   ├── metrics_framework.md
│   ├── Claude_Code_Implementation_Prompt.md   historical build spec
│
├── reports/                             scorecards (canonical, cited from paper)
│   ├── phase31_long_scorecard.txt       ← canonical cross-phase scorecard
│   ├── phase2_unbounded_scorecard_aggressive.txt   ← canonical Phase 2*
│   ├── phase3_long_audit.json, phase31_long_audit.json
│   ├── _legacy/                         historical artifacts
│
├── research_data/                       LFS-tracked SQLite databases
│   ├── runs_phase3_long.sqlite          Phase 3 canonical (5 × 500)
│   ├── runs_v3.sqlite.part_{00,01}      500K-hand Phase 1 legacy dataset
│
├── visualizer/poker_table.html          1927-line single-file viewer
│
└── tests/, etc.
```

---

## 9. The manuscript: structure, history, key conventions

### 9.1 Current structure (12 pages, IMRaD + phase-by-phase Results)

```
Title block (badge + category + author + affiliation + abstract block)
1. Introduction                       plain-language, eBay/lending examples
2. Background                         single 4-paragraph narrative arc
3. Methodology
   3.1 Game environment
   3.2 The eight agent archetypes (visual gallery + Table A bounds)
   3.3 Categorical posterior over types (Eqs 1-3, identifiability note)
   3.4 Four agent architectures (P1/P2/P3/P3.1 + P2* sub-experiment)
   3.5 Experimental design (seeds, hand counts, temperature disclosure)
   3.6 Metrics (rtp + 6 secondary metrics, post-hoc caveat, bootstrap on n=5)
4. Results
   4.1 Phase 1: trust as a liability (trust-vs-stack fig + Box 1 + classification)
   4.2 Phase 2: bounded HC (bounded-vs-unbounded fig)
   4.3 Phase 2*: unbounded HC (Nash fig + drift fig)
   4.4 Phase 3: LLM personality alone (behavioral-shift table)
   4.5 Phase 3.1: reasoning scaffolds (econ inversion fig + table + TMA fig + Box 2)
5. Discussion                          6 flowing paragraphs (no bullets)
6. Limitations                         3 themed paragraphs (power / reprod / design)
7. Conclusion                          + 3 prioritized follow-ups
Appendix: Mentor Checklist             table mapping requests to resolutions
   + 2 placeholder boxes (scaffold ablation, Hand 3)
Sources and Acknowledgments
References (15 entries)
Supplementary Materials
```

### 9.2 LaTeX conventions

- **Style:** Science (AAAS) journal mimicry. Red `RESEARCH ARTICLE`
  badge, "COMPUTER SCIENCE | GAME THEORY" category, large serif
  title, bold sans-serif lead-paragraph abstract block.
- **Body:** `twocolumn`, 10pt, `mathptmx` (Times-like serif) + `helvet`
  (Helvetica-like sans). pdfLaTeX-compatible; preamble has a commented
  XeLaTeX block for actual Minion Pro.
- **Section headings:** uppercase bold sans-serif via `titlesec`, with
  a red vertical-bar accent prefix.
- **Footer:** italic citation block + page number + red horizontal
  rule (the Science branding element).
- **Citations:** `natbib` with `numbers,round` options;
  `\citenumfont{\textit{#1}}` makes citation numbers italic.
- **Archetype names:** ALWAYS use `\arch{Name}` macro for color-coded
  bold rendering. Defined in preamble.
- **Boxed hands:** `tcolorbox` with `storyhand` style (scienceRed
  title bar, gray background). Currently rendered INLINE (not in
  `figure*` floats) so they appear exactly where introduced.
- **Figures inline:** Per-phase figures use `\begin{figure}[H]`
  (`float` package's force-here) at column width. The headline ladder
  is the only `figure*` (full text width).
- **Float barriers:** `\FloatBarrier` after each phase subsection
  (`placeins` package) prevents figures bleeding into the wrong
  phase.

### 9.3 Compile

```bash
cd paper_resources/manuscript
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Expect: ~12 pages, 2.6 MB, no overfull `\hbox` warnings except a
harmless one for the file-header comment block.

### 9.4 Footnotes (16+ poker-jargon footnotes already in place)

Defined at first use of each term:
- preflop/flop/turn/river — combined at §3.1 line ~417
- four-bet cap — §3.1
- side pot — §3.1
- showdown — §3.1
- bluff, value bet, fold equity — combined at honesty-score defn
- br/vbr/cr acronyms — first archetype card (Oracle)
- chain-of-thought — §2 Background
- Pearson r — §1 Introduction (where "Pearson correlation" first appears in prose)
- walkover — §4.1 Phase 1
- VPIP, PFR, AF, SU — §4.4 Phase 3 (at the behavioral-shift table)
- hand rank — §4.1 (at Box 1 intro)
- 3-bet/4-bet — §4.1 (at Box 1 intro)
- c-bet — §4.5 (at Box 2 intro)
- tell — §4.5 (at Box 2 intro)
- L1 distance — §4.2 (at "mean per-agent L1 drift")
- hole cards — §1 Introduction

---

## 10. Peer-review audit history (the iterative refinement loop)

The user has commissioned two external peer-review audits and acted
on both. Both audits and their responses are now folded into the
manuscript.

### 10.1 Audit v1 (brutal)

- **Verdict:** Desk-reject at Science. Workshop-publishable after
  substantial revision.
- **30 items** flagged. Addressed:
  - Empty bibliography → 15 references now render with `\citep{...}`
  - "Inherently rewards exploitation" framing → softened to "in our
    zero-sum testbed under simple agent policies"
  - "Trap broken" claim → "substantially attenuated; not establishable
    as zero at n=5"
  - Six contributions → trimmed to three
  - "Bayesian" framing → "Bayes-flavoured" with clean justification
  - Identifiability "ceiling" → reframed as a design choice
  - Mirror/IPD claim → softened to "suggestive, not definitive"
  - Cross-domain implications → marked conjectural with zero-sum/
    positive-sum caveat
  - Limitations → expanded to 11 items (later compressed into 3 themed
    paragraphs per user request)
  - Hand-count asymmetry → flagged explicitly in Methods
  - Temperature 1.0 disclosure → moved into Methods body
  - Multiple-comparisons caveat for 6 secondary metrics → added
  - Bootstrap "126 distinct combinations" caveat → added

### 10.2 Audit v2 (differential)

- **Verdict:** 18/30 fully addressed, 8 partial, 4 unaddressed (all
  cosmetic). Substantial improvement.
- **Unaddressed items now closed:**
  - Figure 1 SD bars → bootstrap 95% CIs (regenerated
    `make_paper_figures.py`, both `01_four_tier_ladder.png` and
    `01b_five_tier_ladder_with_unbounded.png` now have bootstrap CIs)
  - Tables 3 & 4 redundancy → Table 4 (`economic_inversion.tex`) cut
    from main.tex (still exists on disk as a backup)
  - "Farming" undefined → defined on first use in §Metrics
  - Contribution 3 reframed as a methodological testbed claim
  - Stacked-hedge phrase tightened
- **Bibliography expanded:** Southey et al.\ 2005, Ganzfried & Sandholm
  2015, Glosten & Milgrom 1985, Liu et al.\ 2024 (AgentBench)

---

## 11. Experimental gaps (must be flagged honestly)

These experiments would substantially strengthen the paper but
cannot be run from the LaTeX environment — they require API access
and compute. The manuscript flags them in Limitations and Conclusion
as the priority follow-ups.

| Priority | Experiment | Estimated cost | What it resolves |
|---|---|---|---|
| **P0** | n=20 Phase 3.1 replication at 500-hand horizon | $68–$226 (varies) | Tightens CI on the load-bearing Phase 3.1 claim |
| **P0** | Phase 3 + 3.1 re-run at temperature=0.0 | ~$50 | Removes the only reproducibility flaw |
| **P1** | Three-way Phase 3.1 scaffold ablation | $50–$100 | Supports the "all three scaffolds required" claim in main text |
| **P1** | Multi-LLM replication (Gemini, GPT-4o-mini) | $15–$35 | Demonstrates effect is not Haiku-specific |
| **P1** | Honesty-function sensitivity (2 alternative forms) | $0 (offline) | Closes the "mechanically anchored" caveat |
| P2 | n=20 at the original 150-hand Phase 3.1 horizon (cheaper) | ~$68 | Lower-cost version of P0 #1 |
| P3 | No-limit Hold'em port | weeks | Tests generality beyond fixed-limit |
| P3 | Second testbed (iterated trust game) | weeks | Tests generality beyond poker |

**Minimum viable next step:** P0 #1 + P0 #2 = $118, 2 days. If the n=20
replication confirms the attenuation, the paper becomes workshop-
defensible. If it does not, the "trap broken" finding turns out to
have been small-sample artifact — also a publishable result.

---

## 12. Recent user feedback (in chronological order)

The user has iterated rapidly on the manuscript layout. Read this
section carefully so you can track what they've asked for and what
they're likely to ask for next.

1. **"Use the Evolution-of-Trust palette"** (commit `8704844`) — the
   user provided 8 specific HEX codes for archetype colors. These
   are now in the preamble as `\definecolor{cOracle}{HTML}{A8B5C3}`
   etc. Mirror at `#CDD3D8` is borderline light on white. Do not
   change without asking.

2. **"Run a peer-review audit"** (commits `4ceafe3`, `0222ada`) — the
   user pasted two brutal external audits. Each round, address what
   you can in code/prose and document what's experimental. The user
   explicitly said: "just document the gaps in the paper" (i.e., do
   not try to run new experiments).

3. **"Include footnotes for poker terms, mathematical bounds for
   each archetype, plain-language intro, narrative background,
   narrative discussion, page 7 has too many words, more figures
   and hands, weave them into the text"** (commit `244a6b0`) — the
   user gave 9 specific requests. All addressed.

4. **Mentor revision** (commit `3a50cd8`) — the user pasted a 17-page
   text version of the manuscript incorporating mentor feedback.
   Major changes: plain-language intro opener ("Trust is hard to
   verify directly..."), Background as 4-paragraph narrative with
   explicit "First/Second/Third/Fourth" markers, Table A with full
   6-column archetype bounds, 30+ footnotes target, mentor checklist
   appendix, NEW FIGURE 2 (posterior schematic — not yet built),
   NEW FIGURE 11 (scaffold ablation — placeholder), NEW HAND 3 (P1
   Sentinel value denial — placeholder). All ported to LaTeX.

5. **"Phase-by-phase Results with figures inline"** (commit `8da340f`,
   the latest) — the user pointed out that `figure*[!t]/[!b]` placement
   was still floating figures away from their text. Fix: restructure
   Results into 5 phase subsections, convert per-phase figures from
   `figure*` to `figure[H]` (single-column, forced-inline via float
   package's `[H]`), add `\FloatBarrier` between phases.

**Common pattern:** the user iterates on layout. Default to LaTeX
fixes, compile, send PDF + .tex via `SendUserFile`, commit, push.

---

## 13. Critical "don't touch" list

Things that should not be modified without an explicit instruction:

| File / region | Why |
|---|---|
| `archetype_params.py` | Spec file. The byte-identical mean params of Sentinel/Mirror-default/Judge-cooperative are LOAD-BEARING for the identifiability claim. |
| `preflop_lookup.py` | Spec file. 169-hand classification cached and deterministic. |
| `test_cases.py` (phase1) | Spec file. Real assertions live in `stage_extras.py`. |
| `base_agent.py` Stage-5 trust flow | Audited; every archetype subclass depends on the exact `observe_action` → posterior update → `_observe_opponent_action` hook sequence. |
| `engine/game.py` `_showdown` | Side-pot logic. Modified in commit `57cca9a1`; chip conservation verified across 200 hands. Don't re-modify without rerunning `tests/test_engine_sidepot.py`. |
| `trust/bayesian_model.py` cached constants | `_LAMBDA, _EPS, _TPW` are cached at module import. If you override `config.TRUST` at runtime, you MUST also patch these constants. See `run_sensitivity.py` for the correct pattern. |
| `paper_resources/manuscript/main.tex` archetype color definitions | User's Evolution-of-Trust brand palette. Do not alter without asking. |
| `paper_resources/manuscript/main.tex` archetype card descriptions | Compressed to ~18 words each in commit `244a6b0` for page-7 density. Re-expanding regresses earlier work. |

---

## 14. Useful workflows

### 14.1 Compile the manuscript

```bash
cd /home/user/Poker_trust/paper_resources/manuscript
rm -f main.aux main.log main.pdf main.bbl main.blg main.out
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Result: `main.pdf`, ~12 pages, 2.6 MB. Send via `SendUserFile`.

### 14.2 Regenerate figures (after editing `make_paper_figures.py`)

```bash
cd /home/user/Poker_trust
python3 analysis/make_paper_figures.py
```

Outputs to `paper_resources/figures/`. The script reads from
hardcoded `R_BY_PHASE` in `make_paper_figures.py` (provenance comment
documents the source) and from `paper_resources/data/phase{3,31}_stats.json`
for the trust-vs-stack plot.

### 14.3 Regenerate tables and bootstrap CSV

```bash
python3 analysis/make_paper_tables.py
python3 analysis/bootstrap_ci.py --csv > paper_resources/data/r_bootstrap_ci.csv
```

### 14.4 Run unit tests (verify nothing's broken)

```bash
python3 tests/test_trust_model.py         # 27/27
python3 tests/test_engine_sidepot.py      # 18/18
python3 phase1/run_tests.py --stage 1     # fast
python3 phase1/run_tests.py --stage 2     # fast
python3 phase1/run_tests.py --stage 4     # ~1 min (runs sim)
python3 phase3/validate_phase31.py        # 50/50 (no API needed)
```

Stage 5 / 6 / 7 are slower; Stage 5.3 and 6.1 are EXPECTED to fail
(aspirational tests; documented in `CLAUDE.md`).

### 14.5 Commit + push

The user's repo uses a local 127.0.0.1 mirror that **cannot delete
remote branches** (returns HTTP 403). All other git operations work
normally. Push goes to `origin/main`. The user explicitly authorized
pushing to main; don't push to feature branches without asking.

---

## 15. Gotchas

1. **Float placement in twocolumn:** `figure*` (full-width) cannot use
   `[H]` from the float package. Use `figure[H]` (single column) for
   forced inline placement; use `figure*[!ht]` for full-width
   figures that may float. The headline ladder is the only `figure*`
   in the manuscript.

2. **Bibliography rendering:** If you see "References undefined" or
   an empty bibliography, you forgot `bibtex` between pdflatex runs.
   Pipeline is always `pdflatex → bibtex → pdflatex → pdflatex`.

3. **Footnotes inside captions break:** never put `\footnote{...}`
   inside a `\caption{...}` argument; it will cause an obscure
   `\caption@ydblarg has extra }` error. Put the footnote in the
   body prose that references the figure.

4. **`\footnote` inside `tcolorbox`:** works, but only renders if the
   box is NOT inside a `figure*` float. Current state: boxes are
   inline (not in floats), so footnotes inside them work.

5. **`\arch{Wall}` in math mode:** the `\arch` macro emits
   `\textbf{...}` which is text-mode. If you need to use an archetype
   name in math (e.g., a subscript), wrap with `\text{...}` or just
   write the name in normal text.

6. **The local-mirror git remote at `127.0.0.1`:** returns HTTP 403
   on remote branch deletes. The user must do those from Windows.
   All other git operations work fine.

7. **`pdflatex` not always available:** if `which pdflatex` returns
   nothing, run `apt-get install -y --fix-missing texlive-latex-base
   texlive-latex-extra texlive-fonts-recommended`.

8. **`matplotlib` not always available:** if regenerating figures
   fails, `pip install matplotlib`.

9. **LFS data not pullable from local mirror:** The
   `runs_phase3_long.sqlite` etc. files are LFS pointers; the actual
   content lives on the user's Windows machine. The server has only
   pointer files. Headline data is in `paper_resources/data/phase{3,31}_stats.json`,
   which is small and committed directly.

10. **User has been quick to push back on poor work.** They will say
    "this isn't working out" or "do better" if a deliverable misses.
    Read their feedback carefully and address what they actually
    asked for, not what's easy to address.

---

## 16. Key numbers — cheat sheet to memorize

### Headline ladder
```
P1:    r = -0.752 ± 0.073    (every per-seed |r| in [0.61, 0.81])
P2:    r = -0.637 ± 0.125    Δ=+0.116 vs P1
P2*:   r = -0.609 ± 0.221    Δ=+0.028 vs P2 (Nash falsification — agents diverge)
P3:    r = -0.510 ± 0.268    Δ=+0.127 vs P2
P3.1:  r = -0.094 ± 0.301    Δ=+0.416 vs P3 (the attenuation step)
       95% bootstrap CI [-0.32, +0.20]
       Per-seed: {-0.289, -0.338, -0.327, +0.047, +0.435}
```

### Phase 1 mechanism
```
Firestorm fold equity: 87.1%
Firestorm showdown win rate: 38.5%   (below 1/n = 12.5%)
Wall mean rebuys per seed: ~9.4 (Phase 1)
Wall rebuys in Phase 3.1: 0
```

### Phase 2* convergence
```
Initial cluster spread (L1, 8 agents in 36-dim): 5.82
Final cluster spread (aggressive HC): ≥7.5 on every seed
Mean convergence index: 1.324 (>1 means diverged)
Mean per-agent L1 drift: 3.4 (vs 0.3 in weak HC; 11×)
```

### Phase 3 / 3.1 cost
```
P3:    43,943 calls    $33.10    5 × 500 hands
P3.1:  11,953 calls    ~$17       5 × 150 hands
n=20 P3.1 replication (the priority follow-up): ~$60–$226 depending on horizon
```

### Identifiability
```
Sentinel / Mirror-default / Judge-cooperative: byte-identical mean parameters
Posterior entropy floor: log_2(3) ≈ 1.58 bits
Predator's reliable classifications: 3/7 (Wall ~1.00, Firestorm ~0.82, sometimes Phantom)
```

### Constants
```
λ = 0.95         (decay rate; effective memory 1/(1-λ) = 20 hands)
ε = 0.05         (noise floor in likelihood update)
seeds = {42, 137, 256, 512, 1024}   (same across all phases)
```

---

## 17. Next steps menu (what to do when the user comes back)

The user typically asks for one of these:

| Likely user ask | Files to touch |
|---|---|
| "Tighten section X" | `paper_resources/manuscript/main.tex` |
| "Add a footnote for term Y" | `main.tex`, drop `\footnote{...}` at first use |
| "Regenerate figures with updated style" | `analysis/make_paper_figures.py`, then run it |
| "I ran the n=20 experiment, here are the numbers" | Update `R_BY_PHASE` in `make_paper_figures.py`, regen figs, update Phase 3.1 prose in `main.tex` |
| "Compile and send the PDF" | Compile via §14.1, `SendUserFile` for PDF + .tex |
| "I need a writeup of X for Arpit" | Add a new note in `paper_resources/notes/` |
| "Change the color of archetype X" | Modify `\definecolor{c<Name>}{HTML}{...}` in main.tex preamble |
| "Refresh the bibliography" | Add entries to `references.bib`, add `\citep{...}` at first use |

**When in doubt:**
1. Compile the current PDF first to see the baseline state.
2. Make the smallest possible change that satisfies the ask.
3. Compile again. Verify it works.
4. Send PDF + .tex via `SendUserFile`.
5. Commit with a descriptive HEREDOC commit message.
6. Push to main.

---

## 18. Where the project lives outside the repo

- **Author's Polygence program:** mentor is Arpit Bansal (last meeting
  2026-04-30, the one that motivated Phase 2*).
- **Author's email:** rachit.agrawal@sahyadrischool.org
- **Author's GitHub:** RachitAgrawal146
- **Repo URL:** https://github.com/RachitAgrawal146/Poker_trust
- **Anthropic Console:** for Phase 3 / 3.1 LLM runs (user-funded)
- **Overleaf:** the author works on the final paper externally in
  Overleaf; this LaTeX is the source they upload there.

---

## 19. Files to read if you have time after this handoff

In priority order:

1. `CLAUDE.md` (repo root) — short, dense project memory
2. `paper_resources/notes/PROJECT_ORIENTATION.md` — long, detailed
   project explanation
3. `paper_resources/notes/ARPIT_MEETING_FAQ.md` — 32 prepared Q&As
4. `paper_resources/notes/methods_disclosures.md` — methodological
   caveats that MUST appear in any final paper
5. `paper_resources/manuscript/main.tex` (preamble only, lines 1–250) — to
   understand the LaTeX styling conventions
6. `paper_resources/interesting_hands/EVOLUTION_STORY.md` — the
   cross-phase narrative arc with canonical hands
7. `docs/stage5_identifiability.md` — the mathematical proof of the
   $\log_2(3)$ identifiability floor
8. `docs/worked_examples.md` — Bayesian posterior walkthrough with
   real numbers

---

## 20. Final note

This is a high-school research project, single-authored, that the
student has invested substantial effort in. The work is real, the
engineering is solid, the statistical claims are honestly hedged,
and the manuscript has been through two rounds of external peer
review and dozens of small revisions. The author is iterating
quickly toward a polished Polygence submission and, if the n=20
replication confirms the attenuation, a workshop submission
afterwards. Treat the work with the seriousness it deserves but
match the author's pace — they prefer fast turnarounds with
focused changes over long, ambitious rewrites.
