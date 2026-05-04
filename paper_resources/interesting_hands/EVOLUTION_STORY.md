# The Evolution of the Trust Trap, in Eight Hands

> A guided tour through the four-tier ladder of this project, told as
> a sequence of hands that were *actually played* in the canonical
> simulations. Each hand is referenced by its hand ID and source
> phase so the reader can pull the full transcript on demand.
>
> **The arc has four acts.** Act 1 establishes the trap (Phase 1).
> Act 2 shows that numerical adaptation cannot escape it (Phases 2
> bounded and 2-unbounded). Act 3 shows that even LLM agents in
> character cannot escape it (Phase 3). Act 4 shows what does break
> it: reasoning scaffolding (Phase 3.1).

## Cross-phase money-quote moment

| | Phase 3 hand #67 | Phase 3.1 hand #146 |
|---|---|---|
| **Wall's hole cards** | 2♠ 5♣ (rank 6749, trash) | K♥ Q♥ (rank 872, top pair) |
| **Wall's actions** | check / call × 4 streets | check, call, call, **bet** |
| **Result** | Wall loses 35 chips to Firestorm's J-J | Wall **wins** 32 chips from Firestorm's 8-Q |
| **Firestorm's response on river** | raise (canonical aggression) | check, then **call** Wall's bet |

Same archetype, same opponent, exactly two phases apart. **The
inversion is visible in a single hand.**

## File layout

Per-phase story files (one transcript per slot, all extracted by
`analysis/extract_story_hands.py`):

| File | Phase | Run scale | Slots populated |
|---|---|---|---|
| `p1_story.txt`           | Phase 1 (frozen)    | 5 × 10,000 | 8/8 |
| `p2-bounded_story.txt`   | Phase 2 bounded HC  | 5 × 10,000 | 8/8 |
| `p2-unbounded_story.txt` | Phase 2 unbounded   | 5 × 10,000 | 8/8 |
| `p3_story.txt`           | Phase 3 LLM         | 5 × 500    | 8/8 |
| `p31_story.txt`          | Phase 3.1 LLM+CoT   | 5 × 150    | **7/8 (no A1.2)** |

**P3.1 has no `Wall pays off Firestorm` hand.** This is itself a
finding: by Phase 3.1, Wall has stopped matching the SQL
fingerprint that picks out the trap-microcosm dynamic. The
search returns no hands. The trap has dissolved at the very level
of "is there an obvious example to point at?".

---

## Act 1 — The Trust Trap Reveals Itself (Phase 1, frozen rules)

### Slot A1.1 — Firestorm's biggest walkover

| Phase | Hand ID | Final pot | Notes |
|---|---|---|---|
| **P1**           | #2343 | 140 | seven folds, Firestorm uncontested |
| P2-bounded       | #1471 | 105 | smaller because adaptive defenders fold less |
| P2-unbounded agg | varies | varies | similar dynamic to P2-bounded |
| P3 (LLM)         | #274  | 34  | smaller pots in 500-hand window |
| P3.1 (LLM+CoT)   | #103  | 78  | still happens but smaller |

> **The dynamic.** Firestorm bets aggressively preflop. Most agents
> fold. Pot collected uncontested. This is **fold equity in raw
> form** — Firestorm's economic dominance comes from preventing
> showdowns, not winning them.

The best transcript to cite is **P1 hand #2343** (140-chip pot,
walkover to S2). With 87.1% fold equity in Phase 1, Firestorm
collects ~31% of all walkover pots in the run.

### Slot A1.2 — Wall pays off Firestorm

| Phase | Hand ID | Final pot | Wall's hole cards | Outcome |
|---|---|---|---|---|
| **P1**           | #7128 | 77  | (P1 calling-station play) | Wall loses |
| P2-bounded       | #7879 | 101 | similar | Wall loses |
| P2-unbounded agg | varies | — | similar | Wall loses |
| **P3 (LLM)**     | **#67** | **110** | **2♠ 5♣** (rank 6749) | **Wall loses 35 chips** |
| P3.1 (LLM+CoT)   | **none** | — | — | **does not occur** |

> **The dynamic.** Firestorm bets multiple streets. Wall — the
> calling station — calls all the way down with a hand it knows
> can't win. At showdown, Wall pays for the privilege of having
> "called". This is **the trust trap in microcosm.**
>
> P3 hand #67 is the most rhetorically powerful version because the
> LLM Wall does this with **2♠ 5♣** — the worst kind of hand —
> and the call is patently mechanical: the LLM is following its
> "calling station" personality literally, with no situational
> awareness.
>
> P3.1 *cannot* produce a hand matching this fingerprint. The
> reasoning scaffolding has eliminated the dynamic from the data.

### Slot A1.3 — First trust collapse

| Phase | Hand ID | Notes |
|---|---|---|
| **P1**           | #7    | Oracle's posterior of Firestorm crosses below 0.40 by hand 7 |
| P2-bounded       | #21   | similar — adaptation doesn't stop the inference |
| P2-unbounded agg | varies | similar |
| P3 (LLM)         | #22   | LLMs identify the bluffer essentially as fast |
| P3.1 (LLM+CoT)   | #31   | similar onset |

> **The dynamic.** The trust system identifies Firestorm as a
> bluffer within the first ~30 hands, with high confidence. **The
> trust system's accuracy is not the bottleneck on the trap** —
> Oracle "knows" Firestorm is a maniac with high confidence, and
> Firestorm continues to dominate economically anyway. The trap
> persists *because of* accurate trust inference, not despite it.

---

## Act 2 — Numerical Adaptation Falls Short (Phases 2-bounded and 2-unbounded)

### Slot A2.1 — Late-game adapted hand (Phase 2 bounded)

| Phase | Hand ID | Final pot | Notes |
|---|---|---|---|
| P1               | #8206 | 146 | reference: Firestorm losing in late-game |
| **P2-bounded**   | #7854 | 131 | the comparison case — adapted opponents |
| P2-unbounded agg | varies | — | similar dynamic |

The bounded P2 hand at #7854 (131-chip pot, Firestorm involved
in a late showdown) shows what adaptation *can* do — slightly
narrow Firestorm's edge — and what it cannot — overturn the
ordering.

### Slot A2.2 — Phase 2 unbounded (the falsified-convergence experiment)

> Documented separately in
> `paper_resources/notes/phase2_unbounded_writeup_aggressive.md`
> (canonical) with figures
> `07_phase2_bounded_vs_unbounded_aggressive.png`,
> `11_nash_convergence_spread_aggressive.png`,
> `13_nash_convergence_pca_aggressive.png`.
>
> **The headline.** Even with aggressive hill-climbing
> (delta = 0.15, 100 cycles per agent, 11× more parameter drift),
> agents do **not** converge. Cluster spread *grows* from 5.8 to
> 7.7. Mean trust-profit r is roughly unchanged from bounded P2
> (−0.609 vs −0.637). Firestorm still dominates economically
> (6,512 chips, 6× the next archetype).

This is the falsification of "if they all maximize, they converge
to Nash". Numerical optimization at any tested scale fails to
break the trap — only Phase 3.1's reasoning scaffolding does.

---

## Act 3 — LLM Personalities Without Reasoning (Phase 3)

### Slot A3.1 — Phantom bluff caught

| Phase | Hand ID | Final pot |
|---|---|---|
| P1               | #62  | 13  |
| P2-bounded       | #53  | 31  |
| P3 (LLM)         | #15  | 39  |
| P3.1 (LLM+CoT)   | #12  | 72  |

> **The dynamic.** Phantom bluffs the river with a weak hand and
> gets called by an honest opponent. The LLM Phantom in P3 produces
> the *form* of a bluff (river bet on weak cards) without the
> *cognition* (no reading of the calling-history-against-bluffs the
> opponent has shown). This is consistent with Phase 3's broader
> finding: LLMs follow personality specs faithfully but do not
> reason about game state.

### Slot A3.2 — LLM Wall mechanically calls down (= Slot A1.2 in P3)

P3 hand #67 doubles as the strongest A3-tier evidence: LLM Wall
calls down a 4-bet pot with **2♠ 5♣**. No reasoning agent — even a
calling station — should call a 4-bet preflop with these cards.
The LLM is producing personality, not strategy.

---

## Act 4 — Reasoning Breaks the Trap (Phase 3.1)

### Slot A4.1 — Wall value-bets against Firestorm  ★ THE INVERSION MOMENT

| Phase | Hand ID | Wall's hole cards | Wall's river action | Outcome |
|---|---|---|---|---|
| P1               | #9970 | (raised once, accidental) | bet | one of the rare P1 Wall raises |
| P2-bounded       | #9996 | similar accidents | bet | ditto |
| P3 (LLM)         | #448  | (LLM following spec) | bet | rare event in P3 |
| **P3.1 (LLM+CoT)** | **#146** | **K♥ Q♥** (rank 872) | **bet** | **Wall WINS 32 chips from Firestorm** |

> **The dynamic.** P3.1 hand #146 is the inversion moment in
> microcosm:
>
> - Firestorm raises preflop, c-bets flop, c-bets turn — canonical
>   aggression.
> - Wall calls each street, *gathering information*.
> - Firestorm **checks** the river — a tell that Firestorm doesn't
>   have a strong hand by river.
> - Wall **bets** the river with K♥ Q♥ (top pair, good kicker).
> - Firestorm calls with 8c Qc (rank 6075, much weaker).
> - **Wall wins 32 chips from Firestorm.**
>
> This is precisely the kind of move canonical Wall (and LLM-spec
> Wall in P3) would never make. The reasoning scaffolding lets
> Wall exploit Firestorm's exposed weakness while the trust system
> still classifies Wall as a passive caller.

This is **the single most important hand in the project** for
illustrating what reasoning scaffolding does. Use it as the
opening or closing hand of a talk.

### Slot A4.2 — Sentinel late aggression

| Phase | Hand ID | Final pot | Notes |
|---|---|---|---|
| P1               | #6236 | 170 | rare P1 Sentinel raise |
| P2-bounded       | #7234 | 160 | similar |
| P3 (LLM)         | #251  | 144 | LLM Sentinel raises in character |
| **P3.1 (LLM+CoT)** | **#85**  | **51** (walkover) | **Sentinel raises and everyone folds** |

> **The dynamic.** Sentinel — the second-most-trusted archetype —
> raises into a pot mid-game. In Phase 3.1, every other agent
> folds. Sentinel collects an uncontested walkover.
>
> This is the **trust farming** dynamic in microcosm. Sentinel's
> reputation as a tight value-bettor means its raise is
> automatically read as "value", and opponents fold. Sentinel's
> Phase 3.1 TMA score (Trust Manipulation Awareness) = +0.704 —
> the second-highest of all archetypes — captures this empirically.

### Slot A4.3 — Trap-inverted hand from positive-r seed

> Best extracted from seed 512 (r = +0.047) or seed 1024 (r = +0.435).
> See `paper_resources/data/per_seed_stacks_p31.csv` for which
> archetype won that seed; in seeds 512 and 1024, Wall and Sentinel
> are at or near the top.
>
> The current `extract_story_hands.py --seed N` flag pulls from a
> specific seed if you want to populate this slot specifically.

---

## Bonus — "Biggest pot of the run" per phase

| Phase | Hand ID | Final pot |
|---|---|---|
| P1               | #5651 | 170 |
| P2-bounded       | #2949 | 171 |
| P3               | #221  | 153 |
| P3.1             | #92   | 147 |

Useful as visual hooks for talks/demos even without specific
narrative weight.

---

## Mapping to paper sections

| Slot | Best paper home | Strongest evidence |
|---|---|---|
| A1.1 Firestorm walkover     | §5.3 Firestorm Dominance Mechanism | P1 #2343 |
| A1.2 Wall pays off Firestorm | §5.2 Phase 1 Trust-Profit Anticorrelation | **P3 #67** (most powerful — LLM Wall calls 4-bet with 2-5o) |
| A1.3 Trust collapse          | §5.1 Phase 1 Behavioral Profiles | P1 #7 |
| A2.1 Late-game adapted       | §5.5 Phase 2 Bounded | P2-bounded #7854 |
| A2.2 Phase 2 unbounded       | §5.5 Phase 2 (the new sub-experiment) | full writeup separately |
| A3.1 LLM mechanical          | §5.7 Phase 3 LLM | P3 #67 (same as A1.2 — strongest LLM-spec-as-personality evidence) |
| A4.1 Wall value-bets         | §5.8 Phase 3.1 (the inversion moment) | **P3.1 #146** — THE money hand |
| A4.2 Sentinel trust-farming  | §5.8 Phase 3.1 (TMA discussion) | P3.1 #85 |
| A4.3 Trap-inverted hand      | §5.8 Phase 3.1 (variance discussion) | extract from seed 512 or 1024 |

For an appendix-style paper, the **two most important hands** are:

1. **P3 hand #67** — the trap, in 30 actions, with LLM Wall calling 4-bets with 2-5o
2. **P3.1 hand #146** — the inversion, in 17 actions, with LLM Wall value-betting K-Q against a checking Firestorm

These two hands are 79 hands apart in completely different runs, yet
together they tell the entire story of the project.

---

## Extraction reference

To regenerate any of the per-phase story files:

```bash
python3 analysis/extract_story_hands.py --db <sqlite> --phase <tag>
```

Where `<tag>` is one of `P1`, `P2-bounded`, `P2-unbounded`, `P3`, `P3.1`.

To extract a specific seed (for slot A4.3):

```bash
python3 analysis/extract_story_hands.py --db runs_phase31_long.sqlite --phase P3.1-seed512 --seed 512
```

The script handles the LLM-prefixed agent names (e.g.
`LLM-Firestorm`) transparently.
