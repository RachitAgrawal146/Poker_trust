# Interesting Hands from the v3 Dataset

**Source:** runs_v3.sqlite, Run 1 (seed=42), 25,000 hands

---

## 1. The Grievance Ledger: How the Judge Learns to Hate

### Hand #14 — Grievance #1

The Firestorm's first offense. Just 14 hands into the simulation, the Firestorm (Td 3h — complete junk) raises the Judge's flop bet, then calls the Judge's river bet. At showdown, the Judge's 9d 2d (rank 889) beats the Firestorm's Td 3h (rank 4206). The Judge's grievance counter ticks from 0 to 1.

By hand 14, the table already has the Firestorm pegged — Oracle's trust is 0.377 with 99.0% confidence it's a firestorm type. The Firestorm's reputation collapsed in under 15 hands.

### Hand #934 — Grievance #5: The Trigger

The pivotal moment. The Firestorm holds 2h Qs (absolute trash) but raises the flop and bets the turn against the Judge, who holds Tc Ks (top pair). The Judge calls down and wins at showdown. Grievance crosses threshold τ=5. **From this hand forward, the Judge will never cooperate with the Firestorm again.**

Every observer has the Firestorm at trust=0.375 (minimum) with 100% confidence. The Firestorm itself thinks the Judge is an "oracle" (p=0.686) — it has no idea it just sealed its own fate.

### Hand #1014 — Grievance #6: Post-Trigger

Now triggered, the Firestorm tries a river raise with Ah Tc against the Judge's As 4s (flush, rank 588). The Judge calls and wins 35 chips. The grievance mechanic is now fully active — every future hand where the Firestorm bets will face retaliatory aggression.

---

## 2. Fold Equity: How the Firestorm Prints Money

### Hand #2343 — 140-Chip Walkover

The largest walkover in the dataset from this seed. Six players enter preflop. The pot balloons to 140 chips across four streets of escalating aggression — bets, raises, re-raises. On the river, the Firestorm raises to 140, and both the Phantom and Predator fold. Nobody sees the Firestorm's cards. The Firestorm's stack: 1,050 chips after collecting 140 without showdown. This is fold equity distilled — pure profit from aggression, zero risk of losing at showdown.

### Hand #24423 — Late-Game Dominance

Hand 24,423 of 25,000. The Firestorm's stack is **16,800 chips** — 84x the starting stack. It collects 110 chips in a walkover by raising the river after the Judge and Phantom both fold. Even the Judge (stack 1,613) can't afford to fight the Firestorm's mountain of chips. Economic power compounds: the rich get richer because opponents can't afford to call.

---

## 3. Wall Catches Firestorm: Passive Justice

### Hand #18045 — The 211-Chip Monster (Biggest Pot in the Dataset)

Five players reach showdown in a 211-chip pot — the largest single pot in 25,000 hands. The action is extraordinary: bet caps hit on flop, turn, AND river. The Wall holds 3d 3c (a set of threes, rank 306). The Firestorm holds Js Jd (rank 2868). The Sentinel has 7c Qh. Oracle and Mirror also lose.

The Wall — with only 163 chips at the start of this hand — wins 211 chips and nearly triples its stack. This is the Wall's one superpower: when it actually has a hand, its stubbornness pays off spectacularly. Everyone bets into it because the Wall "always calls" — but this time, the Wall has the goods.

### Hand #5296 — Split Pot Justice

Wall (5c 4s) and Mirror (4h 5s) hold the same hand and split a 131-chip pot, beating the Firestorm's 2c Qc (rank 3860). The Firestorm bet and raised on every street with queen-high — pure bluff. Both the Wall and Mirror called every bet. When two honest players gang up on a bluffer, the bluffer loses.

---

## 4. Predator Exploitation

### Hand #4835 — Predator Beats Wall (130 chips)

The Predator holds Ah 5s and makes a flush (rank 175). It value-bets aggressively against the Wall (As 4d, rank 1642) and Firestorm (Tc Jc, rank 2503), raising on the river to extract maximum value. Trust snapshot confirms: Predator has Wall classified at 100% (trust=0.962, p=1.000) and Firestorm at 100% (trust=0.375, p=1.000). This is textbook exploitation — the Predator knows the Wall will call everything, so it bets its strong hand for maximum value.

### Hand #6236 — Predator Beats Firestorm (170 chips)

A massive 170-chip pot. The Predator (3h Ad, rank 2336) narrowly beats the Firestorm (Ts 3s, rank 2349) and Sentinel (8c 8h, rank 3140). Four rounds of capped betting. The Predator's exploit strategy against Firestorm is "stop bluffing, call down, max value bet" — and here it works perfectly. The Predator knows the Firestorm bluffs constantly, so it calls every raise and wins at showdown.

---

## 5. Mirror Reciprocity

### Hand #6684 — Mirror Beats Firestorm (165 chips)

The Mirror holds Ah Kd (rank 1600) against the Firestorm's As Ts (rank 1875). Both play aggressively — the Mirror raises preflop, the Firestorm 3-bets, and the pot reaches 165 chips through four streets of capped action. The Mirror matches the Firestorm's aggression blow for blow, and its superior hand wins. This is tit-for-tat in action: the Mirror reflects the Firestorm's aggression and profits because its hand is slightly better.

### Hand #708 — The Mirror Loses to the Firestorm (164 chips)

The flip side. The Mirror holds Kh Kc (pocket kings, rank 2633) but the Firestorm has Kd 4d and makes a flush (rank 394). The Mirror raises the river with what it thinks is a strong hand, but the Firestorm's lucky flush beats it. Even reciprocity can't overcome card luck. The Mirror loses 164 chips despite playing correctly — variance is real.

---

## 6. Trust Collapse: Hands #5 and #7

### Hand #5 — Before the Collapse

Oracle's trust in Firestorm: **0.522**. Entropy: 2.16 bits. The Oracle is still uncertain — it thinks the Firestorm is 45.2% likely to be a firestorm type, but hasn't committed. The Firestorm folds preflop (one of the rare times), so no new evidence.

### Hand #7 — After the Collapse

Two hands later. The Firestorm (6c 9d) bets the flop and river against the Mirror (Ks Kh), gets called, and loses. At showdown, the Firestorm's bluff is revealed. Oracle's trust crashes from 0.522 to **0.377** — a 28% drop in two hands. Entropy plummets from 2.16 to 0.12 bits. The Oracle is now 98.6% certain it's facing a firestorm. The Firestorm's reputation never recovers.

**This is the fastest trust collapse in the dataset.** From uncertain to condemned in 2 hands, driven by a single confirmed bluff at showdown.

---

## 7. Phantom Deception

### Hand #642 — Phantom River Bluff Caught

The Phantom (Qs 5s) bets the river against the Wall (Kc 3h). The Wall — true to form — calls. The Phantom's queen-high loses to the Wall's king-high. This is the Phantom's fundamental problem: it bluffs into the one opponent that never folds. The Wall's passive stubbornness is the perfect counter to the Phantom's deception.

---

## 8. Judge Retaliates (Hand #262)

### The First Retaliatory Hand

Hand 262 — just after the Judge's grievance threshold would have been crossed in this local sequence. The Firestorm (2d Kh, rank 4212) bets and raises the river against the Judge (6h As, rank 2507). The Judge re-raises to cap. But the Oracle (Tc Jc, rank 1876) wins the 132-chip pot.

The trust snapshot reveals the aftermath: the Firestorm's trust from the Judge's perspective is 0.518 — still above the 0.375 floor, meaning the trigger hasn't quite fired yet in this specific hand. But the Judge's aggressive river play (bet → raise to cap) against the Firestorm is the signature of building hostility.

---

## 9. Cooperative Equilibrium (Hand #11110)

### Clean Poker Between Honest Players

Oracle raises preflop with Qh Qd. Sentinel 3-bets with Qs As. Everyone else folds — the chaos agents (Firestorm, Phantom, Wall) are out. What follows is pure poker between two disciplined players: raises on every street, capped on the flop, aggressive but principled betting through the river. Oracle's pocket queens (rank 192) beat the Sentinel's ace-queen (rank 2600).

No bluffs. No deception. No grievances. Just two honest players testing each other's hand strength through legitimate aggression. The 63-chip pot goes to the stronger hand. This is what poker looks like when trust is high on both sides — aggressive but fair.

---

## Summary: What These Hands Tell Us

| Hand | Lesson |
|------|--------|
| #7 | Trust collapses in 2 hands — one confirmed bluff destroys a reputation |
| #14→#934 | Grievance accumulates slowly (14→934 = 920 hands for 5 bluffs) but triggers irreversibly |
| #2343 | Fold equity is free money — the Firestorm never has to show its cards |
| #18045 | The Wall's one moment of glory — when it has a real hand, everyone pays it off |
| #6684 | Mirror reciprocity works — match aggression with better cards |
| #708 | But variance is real — even correct play loses to lucky flushes |
| #4835 | Exploitation works — the Predator extracts maximum value from classified opponents |
| #642 | The Phantom's fatal flaw — bluffing into calling stations is economic suicide |
| #11110 | Cooperative equilibrium exists — honest players produce clean, aggressive poker |

**The overarching narrative:** Trust forms fast (Wall identified by hand 5), collapses fast (Firestorm condemned by hand 7), and never recovers. Deception pays economically (Firestorm stack 16,800) but destroys reputation (trust 0.375). Honesty is noble but exploitable (Wall trust 0.962, stack 174). The only winning strategy is *selective* deception with the judgment to know when to fight and when to fold — which is exactly what the Predator and Mirror attempt, with mixed results.
