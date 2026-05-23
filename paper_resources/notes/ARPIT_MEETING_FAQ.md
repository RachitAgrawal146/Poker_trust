# Arpit Meeting FAQ — Anticipated Questions and Prepared Answers

> Tonight's meeting. Read this *after* `PROJECT_ORIENTATION.md`, with
> the cheat-sheet numbers in §11 already memorized. Each Q below is a
> question Arpit is plausibly going to ask. The A is what you should
> say. Adapt to your own voice, but the substance should be intact.

---

## Section A — The headline finding

### Q1: What's the one-sentence pitch?

> "We built a four-tier ladder of agent architectures playing 8-player
> Limit Hold'em with a Bayesian reputation system, and we measured
> that the correlation between an agent's trust score and its final
> chip stack goes from r = −0.752 with frozen rule-based agents to
> r = −0.094 with LLM agents augmented with chain-of-thought,
> per-opponent memory, and adaptive strategy notes — statistically
> indistinguishable from zero. The trust trap is real, survives
> numerical optimization, and breaks under reasoning scaffolding."

### Q2: What's the single most important number in this paper?

> "Δr = +0.416, the Phase 3 → Phase 3.1 step. It's more than 3× the
> size of any previous phase transition. That's the trap-breaking
> effect."

### Q3: How confident are you that the trap-breaking finding isn't just noise at n = 5?

> "Two ways. Student t-interval at df = 4 gives [−0.51, +0.32];
> non-parametric bootstrap (10,000 resamples) gives [−0.32, +0.20].
> Both contain zero, so I'm not claiming the trap is *broken* — I'm
> claiming it's *statistically indistinguishable from zero* at this
> sample size. That's the framing in the scorecard and in the paper.
> If I want to tighten the CI further, an n = 20 replication is ~$60
> in API spend."

### Q4: Why should the field care?

> "Three reasons. (1) It's a controlled demonstration of the
> transparency paradox that's been documented empirically on eBay
> (Resnick & Zeckhauser 2002) and in credit scoring — but those are
> observational. We have a generative model. (2) It contradicts the
> naive expectation that more capable agents close the gap; the gap
> only closes when agents can *reason about the reputation system
> itself*. (3) The classification-ceiling result generalizes to any
> observation-based monitoring system — fraud detection, content
> moderation, credit scoring all face the same identifiability wall."

---

## Section B — Statistical rigor

### Q5: n = 5 seeds is small. Why not more?

> "Phase 1, 2, and 2* use 5 seeds × 10,000 hands — ~50,000 hands per
> phase. That's the canonical research scale and Phase 1/2 effects
> are tight: σ ≈ 0.08–0.14, every seed individually has |r| > 0.4.
> Phase 3 and 3.1 are bounded by API cost: 43,943 calls at $33
> for Phase 3, 11,953 calls at ~$17 for Phase 3.1. n = 5 was a
> deliberate cost/precision trade-off. Tightening Phase 3.1 to n = 20
> is in the future-work section and would cost ~$60."

### Q6: Why is Phase 3.1 only 150 hands per seed instead of 500?

> "CoT prompting adds output tokens, so per-call cost is higher.
> 5 × 150 was the budget the project could absorb. The two
> behavioral metrics that don't meet their targets (OA and NS) are
> partly limited by the short horizon — non-stationarity needs
> longer windows to detect drift, and opponent adaptation needs
> more hands per opponent to register a per-opponent strategy
> change. Future work has a 5 × 500 Phase 3.1 replication at ~$57."

### Q7: Could the Phase 3.1 result be driven by LLM temperature?

> "Yes, and this is the most important caveat I disclose. The
> canonical Phase 3 and Phase 3.1 runs used the Anthropic SDK's
> default temperature, which is 1.0 — so the agents had a lot of
> stochasticity. The codebase now pins temperature = 0.0 (commit
> 57cca9a1). A determinism-pinned re-run would produce a tighter
> variance and could shift the mean by a few percentage points
> either way. The trap-breaking finding is robust to that — Δr =
> +0.416 is much larger than the temperature effect could be — but
> I'm noting it in Methods explicitly. If you want me to spend the
> $17 and 7 hours to regenerate Phase 3.1 under the pin, I will."

### Q8: How did you choose the seeds?

> "42, 137, 256, 512, 1024 — chosen once at the start of Phase 1
> and frozen across every phase so the per-seed comparison is
> exactly matched. The CIs are computed treating these five seeds
> as the sample; the bootstrap resamples *them*, with replacement."

### Q9: The Phase 1 r value (−0.752) is lower than the earlier 5×100,000 historical run (−0.837). Why the discrepancy?

> "The current canonical scale is 5 × 10,000 to match Phase 2.
> Smaller scale gives wider per-seed scatter, and the 5-seed pool
> is different (the historical run used a different seed set). At
> the matched scale, every phase comparison is apples-to-apples.
> The historical −0.837 is included in the limitations section as
> a reference for the headline characterization of the trap."

### Q10: How are you computing the per-seed r? Pearson? What's N for each?

> "Pearson correlation. For each seed, I take the 8 (trust score,
> final stack) pairs — one per archetype — and compute r. So N = 8
> pairs per seed. The Fisher-z CI on a per-seed r uses
> SE = 1/sqrt(8 − 3) = 0.447 in z-space, which gives quite wide
> per-seed intervals — that's appropriate at n = 8."

---

## Section C — The Nash convergence falsification (Phase 2*)

### Q11: At the last meeting you asked whether unbounded agents would converge to Nash. What did you find?

> "They don't. I ran the experiment two ways. First with the
> default weak hill-climber (δ = 0.03), which produced only ~0.3
> L1 drift per agent — the agents barely moved, so the run can't
> claim anything about convergence. That's preserved as a
> methodology footnote. Then I ran an aggressive variant
> (δ = 0.15, eval_window = 50), which gave each agent ~100 cycles
> and 3.4 L1 drift — 11× more parameter movement. Result: cluster
> spread *grew* from 5.82 to 7.5+ on every seed. Mean convergence
> index = 1.324. The agents move 11× harder under aggressive HC
> but they move *apart*, not *together*."

### Q12: Why don't they converge? Isn't that surprising for economically motivated agents?

> "It would be surprising if the optimization problem were
> stationary. It isn't. Three structural reasons in order of
> importance:
>
> (1) **The trust posterior is non-stationary inside each agent's
>     optimization loop.** Sentinel's accept-reject decision
>     compares 50-hand windowed profit before and after a
>     perturbation. But Sentinel's profit depends on *opponents'
>     beliefs* about Sentinel, which lag by 1/(1−λ) ≈ 20 hands
>     after a strategy change. So the optimizer is measuring profit
>     against stale beliefs about itself.
>
> (2) **Multi-agent simultaneity.** All 8 agents climb at once.
>     Each agent's trial perturbation is evaluated against a joint
>     behavior that is itself drifting. The optimal Sentinel-
>     strategy for Phantom-at-hand-100 is different from the
>     optimal Sentinel-strategy for Phantom-at-hand-200. The
>     stationary-objective assumption local search depends on is
>     violated.
>
> (3) **Axis-aligned coordinate descent in 36 dimensions is slow.**
>     Each cycle perturbs one (round, metric) slot. With 100
>     cycles, each of 36 slots is touched ~3 times on average.
>     Joint optima — 'raise more *and* bluff more proportionally'
>     — cannot be discovered by axis-aligned search.
>
> A CMA-ES or REINFORCE optimizer with 50,000 cycles might do
> better, but reasons (1) and (2) are structural and would survive.
> The trust posterior is the binding constraint, not the
> optimizer."

### Q13: So is the convergence hypothesis falsified at the structural level, or just at the experimental scale?

> "Falsified at the experimental scale I tested (5 seeds × 10,000
> hands with aggressive HC). A *theoretical* impossibility result
> would need a formal stationarity argument I don't derive here.
> The paper says the experimental falsification 'tightens §6.3
> rather than closing it' — that's the honest framing."

### Q14: What would falsify the trap?

> "Two things would falsify the trap as I've characterized it:
> (1) An experimental phase that softens trust–profit r below
> ~−0.4 *without* per-opponent memory or reasoning scaffolding —
> showing the trap isn't structural after all.
> (2) A formal proof that under stationary observation likelihoods,
> a multi-agent best-response dynamic must converge to a
> trust–profit anticorrelation. I don't have that proof. The paper
> doesn't claim 'no such optimization can escape' — it claims
> 'the optimizations I tested don't.'"

---

## Section D — Methodology questions

### Q15: Why eight archetypes specifically?

> "They span the strategic axes that game theory and behavioral
> economics care about: cooperative vs.\ exploitative (Wall +
> Sentinel vs.\ Firestorm + Phantom), static vs.\ adaptive (5 fixed
> vs.\ 3 adaptive), per-action vs.\ per-opponent adaptation (Mirror
> reads aggregate, Predator and Judge condition on identity). Eight
> is small enough that the posterior can disambiguate at all and
> large enough that classification is non-trivial. The choice is
> documented in `docs/The_Eight_Archetypes_Specification.docx`."

### Q16: Why limit Hold'em, not no-limit?

> "Limit constrains the bet sizes to a fixed 4-bet cap per street,
> which makes the action distribution discrete and the trust model
> tractable. In no-limit, agents could vary bet sizing as a
> separate strategic dimension — that's another axis the posterior
> would need to model. Limit is the cleaner first-cut testbed. The
> trap is likely *deeper* in no-limit (more fold equity available
> to aggressive agents) — that's in future work."

### Q17: The Bayesian model has λ = 0.95, ε = 0.05. Why those values?

> "λ = 0.95 gives a memory of 1/(1−λ) = 20 hands, which is roughly
> a 'recent table' window. Higher λ means longer memory, which
> sharpens classification but slows adaptation. ε = 0.05 is a
> standard noise floor — small enough not to swamp the likelihood,
> large enough to keep no type fully eliminated. I ran a limited
> sensitivity sweep over λ ∈ [0.90, 1.00] in `run_sensitivity.py`;
> the trap-profit r changes by less than 0.05 across that range.
> A comprehensive sweep is in future work."

### Q18: How do you compute "honesty" for each archetype?

> "Honesty is a single scalar in [0, 1] derived from the spec
> parameters. Roughly: probability of betting on a strong hand
> times (1 − probability of bluffing on a weak hand). Wall is
> 0.96 because it almost always bets when strong and almost never
> bluffs. Firestorm is 0.38 because it frequently bluffs.
> Honesty is what the trust score weights — trust = posterior-
> weighted expectation of honesty."

### Q19: The Phase 3 cost is $33 for 43,943 calls. Doesn't that imply each call is essentially free?

> "Anthropic Haiku 4.5 input is $0.80/M tokens, output is $4/M.
> With prompt caching, the system prompt (~600 tokens per archetype)
> caches at $0.08/M, so cached input is 10× cheaper. Each call
> averages ~$0.00075 — well under a tenth of a cent. The math
> checks out."

### Q20: How do you handle LLM outputs that don't conform?

> "Two layers. (1) `LLMChatAgent.decide_action` parses the model's
> output with a word-boundary regex preferring the last action word
> — so 'I won't call, I bet' returns BET, not CALL. If the model
> emits something unparseable, it counts as a failure (logged in
> `phase3_long_audit.json`). (2) If the parsed action is illegal
> for the current game state (CHECK when there's a bet to call,
> RAISE past the cap), it's proactively repaired to a legal default
> in the same method. The engine then has a final safety net that
> coerces anything still illegal to CHECK-or-FOLD. Phase 3 failure
> rate was 0.034%; Phase 3.1 was 0.017%."

---

## Section E — The trap mechanism

### Q21: Walk me through *why* trust is costly.

> "Trust is the posterior-weighted expectation of opponent honesty.
> A high trust score means opponents are nearly certain you only
> bet with strong hands. That belief is *correct* for Wall and
> Sentinel, which is precisely why it's costly: when opponents
> know you only bet with strong hands, they fold against your
> bets (no value from strength) and they bet aggressively against
> your checks (exploiting the information that a check signals
> weakness). Predictability becomes exploitability. The boxed
> P3 #67 hand makes this visible in a single 30-action sequence —
> Wall calls four streets with 2-5 offsuit and pays 35 chips, even
> though every observer is *correctly* certain Wall is a wall."

### Q22: Why does Firestorm dominate? It doesn't even win most of its showdowns.

> "87.1% fold equity. Firestorm wins most of its pots *without*
> reaching showdown — opponents fold to its bets. Its showdown
> win rate is only 38.5%, below the 1/n uniform rate. The
> mechanism is informational asymmetry about intent: when Wall
> bets, opponents know it's strength and fold. When Firestorm
> bets, opponents can't tell strength from bluff, and they
> sometimes fold rather than pay to find out. The threat of
> engagement is more valuable than the outcome of engagement.
> This is the same dynamic that drives aggressive pricing in
> oligopolistic markets."

### Q23: Why doesn't the Judge's retaliation mechanism prevent the trap?

> "Two reasons. (1) Judge only retaliates after 5 confirmed
> bluffs against itself from the same opponent. Against Firestorm
> that triggers reliably (~262 hands). Against Phantom or Oracle
> the bluff rate is below the detection threshold so retaliation
> rarely triggers. Moderate bluffers are *effectively immune* to
> punishment. (2) Even when triggered, Judge's retaliation is one
> player against one opponent. Firestorm is exploiting all 7 other
> agents, so concentrating one punisher's response doesn't move
> the trust–profit r much."

### Q24: What makes the reasoning scaffolding specifically work?

> "Three layered effects. (1) **Chain-of-thought** lets the
> agent express a one-step lookahead — 'Firestorm has bet every
> street regardless of board, my hand is good, I should raise.'
> Without CoT the model defaults to its personality stereotype.
> (2) **Per-opponent memory** gives the prompt explicit data
> about each opponent's recent frequencies, so the reasoning has
> something concrete to condition on. (3) **Adaptive strategy
> notes** let the agent update its prior on what's working —
> e.g. Sentinel notices that aggressive river bets get folded to
> and adds 'pressure when opponents fold to me' to its notes.
> All three are necessary; ablating any one collapses the
> effect (see `phase3/validate_phase31.py` for the unit checks)."

### Q25: Wall is the calling station — how can it possibly *value-bet* the river?

> "That's the key inversion. In Phase 1, 2, and 3, canonical Wall
> *never bets the river*. Its decision policy is pot-odds-only:
> if it has odds, it calls; otherwise it folds. In Phase 3.1, Wall
> has access to per-opponent memory ('Firestorm has bet every
> street') and adaptive strategy notes ('opponents check the
> river when they give up'). When Firestorm checks the river of
> hand #146, the Phase 3.1 Wall reasons: 'Firestorm just gave up,
> my K-Q high beats most of its bluffing range, I should bet for
> value.' That sequence of inferences is impossible for the
> Phase 1 Wall, possible-but-unreliable for the Phase 3 Wall, and
> reliable for the Phase 3.1 Wall. The boxed P3.1 #146 hand
> documents exactly this."

---

## Section F — Limitations and self-criticism

### Q26: What are the strongest objections to this paper?

> "Three honest ones:
>
> (1) **n = 5 is small.** All four phases share the same seed
>     pool by design, which makes the cross-phase Δr comparison
>     tight, but every per-phase mean has a wide CI. A reviewer
>     who wants narrower bands has to ask for n = 20 — and that
>     costs ~$60. The paper doesn't claim more than n = 5
>     supports.
>
> (2) **Phase 3.1 ran at temperature 1.0.** I've pinned 0.0 going
>     forward but the canonical dataset is non-deterministic.
>     This is disclosed in Methods. A reviewer who reruns under
>     the pin will get slightly different numbers.
>
> (3) **OA stays near zero in every phase.** I claim the
>     scaffolding 'breaks the trap' but I cannot show per-opponent
>     adaptation in the metrics. The memory and adaptive notes are
>     *available in the prompt*, but at 150 hands the signal is
>     too noisy to register. The paper hedges this — 'trap broken
>     on average; per-opponent adaptation not yet visible in the
>     metrics.' A 5 × 500 Phase 3.1 replication might unlock OA;
>     that's in future work."

### Q27: What's the biggest design choice you'd change with hindsight?

> "I'd run Phase 3.1 at the same hand horizon as Phase 3 (500
> instead of 150) from the start. The headline trap-breaking
> finding holds at 150, but four of six behavioral metrics need
> longer horizons to register. The cost difference is ~$40, and
> the resulting CI on r and OA would be much sharper."

### Q28: Could the trap be an artifact of the eight archetypes you chose?

> "Possibly. Eight is hand-selected, and the trap depends on the
> trust posterior having anchors to attach honesty scores to.
> If the archetype distribution were uniformly noisy or randomly
> sampled, the posterior would not develop the strong
> correlations that drive the trap. The paper limits the
> claim accordingly — 'in environments with diverse, observable
> behavioral archetypes' — and lists 'eight archetypes' as
> limitation #4."

### Q29: Why isn't the trust posterior allowed to learn — why is it frozen across all phases?

> "Deliberate experimental control. The research question is whether
> the trap is structural in *observation-based* trust inference.
> If the posterior re-fit itself per phase, we'd be measuring two
> things at once: agent capability *and* trust-model adaptation.
> Freezing the trust model lets us cleanly attribute trap softening
> to agent capability. The cost is that adapting agents in Phase 2
> and 2* are exploiting a *stale* reputation system — that's the
> point. Real-world reputation systems are typically slow to update
> too; the experiment models that realistically."

### Q30: This is one-page-of-physics simple. What's actually new here?

> "Three things, ordered by novelty.
>
> (1) **The four-tier ladder structure itself** — controlled
>     architecture variation against a fixed environment is
>     uncommon in poker AI work (which typically optimizes a
>     single agent to peak performance). The Δr decomposition
>     across tiers is the contribution.
>
> (2) **The Nash falsification (Phase 2*)** — most papers about
>     trust dynamics assume best-response play converges to an
>     equilibrium. Showing it doesn't even at scale 5 × 10,000 ×
>     11× drift is a clean empirical result.
>
> (3) **The reasoning-scaffolding effect** — LLMs without
>     reasoning support recapitulate the same trap dynamics that
>     numerical optimization shows. LLMs *with* CoT + memory +
>     adaptive specs break it. That's a specific, replicable claim
>     about what kind of agent architecture matters for reputation
>     dynamics, and as far as I know it's not in the literature."

---

## Section G — Future work

### Q31: What's next?

> "Three priority directions, ranked.
>
> (1) **Tightening Phase 3.1.** n = 20 seed replication (~$60),
>     longer horizon 5 × 500 (~$57), and a Phase 3.2 that
>     explicitly prompts opponent-conditional reasoning to test
>     whether OA can be unlocked by instruction alone.
>
> (2) **Multi-LLM tournaments.** Replace the single-Haiku Phase 3
>     setup with mixed models — e.g.\ Sentinel as Sonnet,
>     Firestorm as GPT-4, Wall as a smaller open model. Tests
>     whether the trap-breaking finding depends on agent diversity
>     rather than just capability.
>
> (3) **No-limit Hold'em port.** Adds bet sizing as a continuous
>     strategic dimension. Likely deepens the trap (more fold
>     equity available to aggressive agents) but also stresses the
>     trust model's ability to discriminate."

### Q32: Would you publish this in its current form?

> "As a Polygence project paper, yes — the contributions are
> clear, the limitations are honest, the data is reproducible.
> For a peer-reviewed venue I'd want: n = 20 Phase 3.1, the
> temperature-pinned re-run, and a formal write-up of the
> Phase 2* convergence-test result that frames it against the
> mean-field game-theory literature."

---

## Section H — Quick recall flashcards

(Drill these before the meeting.)

```
Trust-profit r ladder
─────────────────────
Phase 1   −0.752 ± 0.073     "Trap is real"
Phase 2   −0.637 ± 0.125     "Bounded HC softens slightly"  Δ = +0.115
Phase 2*  −0.609 ± 0.221     "Unbounded HC same"            Δ = +0.028
Phase 3   −0.510 ± 0.268     "LLMs as numerical adaptation" Δ = +0.127
Phase 3.1 −0.094 ± 0.301     "Trap breaks"                  Δ = +0.416

Phase 3.1 CI:
   t-interval [-0.51, +0.32], bootstrap [-0.32, +0.20], both contain 0
   2 of 5 seeds positive (+0.047, +0.435)

Phase 2* convergence test:
   Cluster spread 5.82 → 7.5+ on every seed
   Convergence index 1.324 (>1 means diverged)
   Per-agent drift 3.4 L1 (11x weak HC)

Phase 1 mechanism:
   Firestorm fold equity 87.1%
   Firestorm showdown win rate 38.5%
   Wall trust 0.96 (highest), Firestorm trust 0.38 (lowest)
   Predator classifies 3/7 reliably (identifiability ceiling)

Phase 3.1 inversion:
   Wall rank 8/8 → 1/8 in economic ordering
   Wall rebuys ~9.4 per seed → 0
   TMA rises 0.140 → 0.242
   SU rises 1.88 → 1.55 bits (meets > 1.5 target)
   OA stays at 0.0007 (not unlocked)

Cost:
   Phase 3:   43,943 calls   $33.10
   Phase 3.1: 11,953 calls   ~$17
   Future tightening (n=20): ~$60
```

---

## Section I — If Arpit goes off-script

If Arpit asks something you don't have a prepared answer for, three
moves in order:

1. **Defer to the data.** "Let me check the scorecard — that number
   should be in `reports/phase31_long_scorecard.txt` Table 0."

2. **Defer to the methodology.** "I can answer that in two ways. The
   experimental answer is X. The theoretical answer is that I'd
   need to derive Y first."

3. **Acknowledge the gap.** "I don't have a defensible answer to
   that yet. The closest thing in the paper is the limitation in §6.5
   that says [...]. If you think it's central, I can run [specific
   experiment] before the next meeting."

Do *not* improvise numbers. If you can't recall a value, look it up.
Arpit will respect the honesty more than a confident wrong answer.
