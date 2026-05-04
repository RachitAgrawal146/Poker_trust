# The Evolution of the Trust Trap, in Eight Hands

> A guided tour through the four-tier ladder of this project, told as
> a sequence of representative hands. Each hand is a single,
> human-readable transcript that illustrates one specific moment in
> the project's narrative arc.
>
> **The arc has four acts.** Act 1 establishes the trap (Phase 1).
> Act 2 shows that numerical adaptation cannot escape it (Phases 2
> bounded and 2-unbounded). Act 3 shows that even LLM agents in
> character cannot escape it (Phase 3). Act 4 shows what does break
> it: reasoning scaffolding (Phase 3.1).

## How to use this document

Each hand has:
- **Slot ID** — a stable label (e.g. `A1.1`) used by `extract_story_hands.py`
- **Phase** — which run produced this hand
- **Selection** — the SQL fingerprint that picks the hand
- **Transcript** — either inlined here (if the SQLite is on the
  server) or a reference to the per-phase output file

Extracted transcripts live in `paper_resources/interesting_hands/`:
- `p2-unbounded_story.txt` — extracted on this server (full transcripts)
- `p1_story.txt`, `p2-bounded_story.txt`, `p3_story.txt`, `p31_story.txt`
  — produced by running `extract_story_hands.py` on the corresponding
  Windows-side SQLites (see "Extraction" at the end)

---

## Act 1 — The Trust Trap Reveals Itself (Phase 1, frozen rules)

### Slot A1.1 — Firestorm's biggest walkover

> *Phase 1 / 5 seeds × 10,000 hands / canonical run.*
>
> **The dynamic:** Firestorm bets aggressively preflop. Seven other
> agents fold. Firestorm wins the pot uncontested. This is **fold
> equity in raw form** — Firestorm's economic dominance comes not
> from winning showdowns but from preventing them.

This hand is the visible edge of the iceberg. With 87.1% fold
equity, Firestorm collects ~31% of all walkover pots in Phase 1.
The agents that drop below 0.40 trust are precisely the agents that
extract chips.

### Slot A1.2 — Wall pays off Firestorm

> *Phase 1.*
>
> **The dynamic:** Firestorm bets on every street with a weak hand.
> Wall — the calling station — calls all the way down. At showdown,
> Firestorm's hand is genuinely weak; Wall's hand is moderate. But
> because Wall is positionally last and tends to peel cheaply, the
> chips that Wall paid into the pot exceed the pot Wall wins.

This is **the trust trap in microcosm**. Wall's reputation profile
(trust = 0.962, perfect classification accuracy) is paid for in
chips, hand by hand. There is no single moment where Wall makes a
"bad" decision — every call is locally rational given Wall's
pot-odds-only logic. The aggregate cost is what makes it a trap.

### Slot A1.3 — First trust collapse

> *Phase 1, hand index varies by seed (~150–250).*
>
> **The dynamic:** the first hand on which Oracle's posterior over
> Firestorm crosses below 0.40. By this point, Oracle has watched
> Firestorm bet weak hands at showdown enough times that the
> Bayesian posterior has shifted from the initial uniform prior to
> a near-certain `firestorm` classification.

This is the moment **the trust system has done its job**. Oracle now
"knows" Firestorm is a maniac with high confidence — and yet
Firestorm continues to dominate the table economically. The trust
system's accuracy is exactly *not* the bottleneck on the trap.

---

## Act 2 — Numerical Adaptation Falls Short (Phases 2-bounded and 2-unbounded)

### Slot A2.1 — Late-game adapted hand (Phase 2 bounded)

> *Phase 2 bounded, hand index ≥ 7000.*
>
> **The dynamic:** by the late game, every agent has had ~35 hill-
> climber cycles. Adaptation has nudged each agent's parameters
> within their archetype-shaped bound boxes. Look for a hand where
> Firestorm bet aggressively but lost the showdown — these are
> rarer in late game than early game, but visible.

Phase 2's effect is real (Δr = +0.115) but small. Looking at this
hand alongside A1.1 and A1.2 should make the gap visceral: yes,
adaptation has done *something*, but Firestorm still has the largest
stack and Wall is still going broke.

### Slot A2.2 — Phase 2 UNBOUNDED, biggest pot of seed 42 (extracted)

> **Phase 2 unbounded** / 5 seeds × 10,000 hands / runs_phase2_unbounded.sqlite.
>
> **The dynamic:** with bounds removed, every agent's hill-climber
> can drift its parameters anywhere in [0, 1]^36. The hypothesis
> from Arpit (mentor meeting 2026-04-30) was that economically-
> motivated agents would converge to a Nash-equilibrium / Oracle
> profile. The data falsifies this:
> - **Firestorm's mean stack: 7,861 chips** (40× starting)
> - **Wall's mean stack: 195 chips** (zero growth, 30 rebuys)
> - Trust-profit r drops to **−0.779** (deeper than Phase 1)

Why this matters: the trap is not a parameter-space limitation. With
full freedom of [0, 1]^36, agents *still* preserve their archetype
identity, because the trust posterior is computed against Phase 1's
likelihood tables and rewards canonical archetype play. The
*reputation system itself* is the binding constraint.

The extracted hand transcript is in
`paper_resources/interesting_hands/p2-unbounded_story.txt` (slot A1.1).
Hand 1471 of seed 42, final pot 105 chips, Firestorm walkover after
4-bet on the turn forced Wall and Oracle out.

---

## Act 3 — LLM Personalities Without Reasoning (Phase 3)

### Slot A3.1 — LLM Wall mechanically calls down

> *Phase 3 / 5 seeds × 500 hands / Anthropic Haiku via API.*
>
> **The dynamic:** the LLM playing Wall reads its personality spec
> ("you are the calling station; rarely fold; almost never raise")
> and follows it literally. Even when the hand state should suggest
> a fold (multiple bets, bad pot odds, weak hand), the LLM calls.

Phase 3's surprise is that giving the agents natural language did
**not** unlock strategic adaptation. The LLM is faithful to its
personality but does not reason about the game state — it produces
the *form* of the archetype without the *cognition*. Trust-profit r
softens only by Δ = +0.127, comparable to Phase 2.

### Slot A3.2 — Phantom bluff caught

> *Phase 3, late game.*
>
> **The dynamic:** the LLM playing Phantom delivers a confident river
> bet on a weak hand. Some opponent calls; Phantom loses the showdown.

In Phase 3, Phantom occasionally pulls off bluffs (just like in Phase
1) but the LLM doesn't *vary* the bluff frequency or sizing in
response to opponents — it produces Phantom-as-personality, not
Phantom-as-strategist.

---

## Act 4 — Reasoning Breaks the Trap (Phase 3.1)

### Slot A4.1 — Wall value-bets against Firestorm

> *Phase 3.1, late game (hand ≥ 100).*
>
> **The dynamic:** Wall, augmented with chain-of-thought + per-opponent
> memory + adaptive strategy notes, **bets** with a strong hand —
> something canonical Wall almost never does. The CoT trace shows
> Wall reasoning: *"Firestorm has bet every street regardless of
> board; my pair is likely good; raise to extract."*

This is the **trap-inversion moment**. Wall (highest trust, 0.85)
goes from rank-8-of-8 in Phase 3 to **rank-1-of-8 in Phase 3.1**
because moments like this start happening. The cooperative archetype
stops being a calling station and starts using its trust as
strategic camouflage.

### Slot A4.2 — Sentinel "trust farming"

> *Phase 3.1, mid-game (hand ≥ 75).*
>
> **The dynamic:** Sentinel's adaptive strategy notes (visible in the
> agent state) explicitly say things like "build trust by playing
> tight early, then pressure when opponents fold to me". Mid-game,
> Sentinel raises into a multi-way pot and gets credit (folds) from
> opponents who classify it as `sentinel` and weight its raises as
> value bets.

Sentinel's TMA score (Trust Manipulation Awareness) is **+0.704** in
Phase 3.1 — the second-highest of all archetypes. The agent has
explicitly learned to *use its reputation* as an asset.

### Slot A4.3 — Trap-inverted hand (positive-r seed)

> *Phase 3.1, seed 512 or seed 1024.*
>
> **The dynamic:** in two of five seeds, the trust-profit r flips to
> **positive** (+0.047, +0.435). Look for a hand from these seeds
> where the most-trusted agent (Wall) wins a large pot through a
> deliberate strategic move — not a fluke.

Two of five seeds inverting the trap is a small-N result, but the
*existence* of trap inversion under this scaffolding is the strongest
single piece of evidence in the paper that the trap is not a
structural property of multi-agent reputation systems.

---

## Bonus — A_x: Biggest pot of every run

For each phase, `extract_story_hands.py` also dumps the single largest
pot of the run as a "spectacle" hand. These are useful as visual
hooks for talks/demos even if they don't carry narrative weight.

---

## Extraction

To populate the per-phase story files from the canonical SQLites:

```bash
# Phase 1 (canonical 5 × 10000 frozen-rules dataset)
python3 analysis/extract_story_hands.py \
    --db runs_phase1_long.sqlite --phase P1

# Phase 2 bounded (canonical 5 × 10000 hill-climbing)
python3 analysis/extract_story_hands.py \
    --db runs_phase2_long.sqlite --phase P2-bounded

# Phase 2 UNBOUNDED (already on server; transcripts inlined above)
python3 analysis/extract_story_hands.py \
    --db runs_phase2_unbounded.sqlite --phase P2-unbounded

# Phase 3 (5 × 500 LLM personalities)
python3 analysis/extract_story_hands.py \
    --db runs_phase3_long.sqlite --phase P3

# Phase 3.1 (5 × 150 LLM + reasoning)
python3 analysis/extract_story_hands.py \
    --db runs_phase31_long.sqlite --phase P3.1
```

Each command writes to
`paper_resources/interesting_hands/<phase>_story.txt`.

The Phase 2 unbounded story file is already populated on the server.
Phase 1, Phase 2 bounded, Phase 3, and Phase 3.1 require the
corresponding SQLite, which lives on the user's Windows machine
(LFS-tracked, gitignored). On Windows, run the same commands above
inside the repo root after pulling.

## Mapping to paper sections

| Slot | Best paper home |
|---|---|
| A1.1 Firestorm walkover     | §5.3 Firestorm Dominance Mechanism |
| A1.2 Wall pays off Firestorm | §5.2 Phase 1 Trust-Profit Anticorrelation |
| A1.3 Trust collapse          | §5.1 Phase 1 Behavioral Profiles |
| A2.1 Late-game adapted       | §5.5 Phase 2 Bounded Optimization Results |
| A2.2 Phase 2 unbounded       | §5.5 Phase 2 (the new sub-experiment) |
| A3.1 LLM Wall mechanical     | §5.7 Phase 3 LLM Personality Role-Players |
| A3.2 Phantom bluff caught    | §5.7 Phase 3 |
| A4.1 Wall value-bets         | §5.8 Phase 3.1 (the inversion moment) |
| A4.2 Sentinel trust-farming  | §5.8 Phase 3.1 (TMA discussion) |
| A4.3 Trap-inverted hand      | §5.8 Phase 3.1 |

For an appendix-style paper, slots A1.2, A2.2, A4.1, and A4.3 are the
four most important: they are the trap, the falsified hypothesis, the
inversion, and the proof of inversion respectively.
