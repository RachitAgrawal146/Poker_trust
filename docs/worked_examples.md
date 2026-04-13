# WORKED EXAMPLES
## Complete Hand Walkthrough + Bayesian Update with Real Numbers

---

## EXAMPLE 1: One Complete Hand

### Setup
- Hand #147, Seed 42
- Dealer: Seat 0 (Oracle)
- Small Blind: Seat 1 (Sentinel) posts 1
- Big Blind: Seat 2 (Firestorm) posts 2
- All players start this hand with 200 chips (simplified for clarity)

### Deal
```
Seat 0 (Oracle):    Ah Kd   → Preflop bucket: STRONG (AKo)
Seat 1 (Sentinel):  9c 9h   → Preflop bucket: MEDIUM (99)
Seat 2 (Firestorm): Jh 7h   → Preflop bucket: WEAK (J7s — not in medium range)
Seat 3 (Wall):      Qs Td   → Preflop bucket: WEAK (QTo — not in medium range)
Seat 4 (Phantom):   6d 6c   → Preflop bucket: WEAK (66 — medium for some archetypes but below 77 threshold)
Seat 5 (Predator):  Ac Jc   → Preflop bucket: MEDIUM (AJs)
Seat 6 (Mirror):    3h 2s   → Preflop bucket: WEAK (32o)
Seat 7 (Judge):     Kh Qh   → Preflop bucket: MEDIUM (KQs)
```

### Pre-Flop Betting Round (Small Bet = 2)
Action order: Left of big blind → around to big blind (Seats 3,4,5,6,7,0,1,2)

```
Pot starts: 3 (1 SB + 2 BB)

Seat 3 (Wall, WEAK):
  - No bet pending (BB is not a "bet" for action purposes — but actually in 
    limit holdem preflop the BB IS a bet, so seats must call 2 or raise to 4)
  - Facing a bet of 2. Wall has WEAK hand. 
  - Wall's CR preflop = 0.80. weak_call = 0.55.
  - Roll: 0.31 → 0.31 < 0.55 → CALL (puts in 2)
  - Pot: 5

Seat 4 (Phantom, WEAK):
  - Facing bet of 2. Phantom has WEAK hand.
  - Phantom's preflop: weak_call = 0.10
  - Roll: 0.72 → 0.72 > 0.10 → FOLD
  - Pot: 5

Seat 5 (Predator, MEDIUM):
  - Facing bet of 2. Predator has MEDIUM hand.
  - Predator baseline preflop CR = 0.35, med_raise = 0.05
  - Roll: 0.22 → 0.22 < 0.05+0.35=0.40 → CALL (puts in 2)
  - Pot: 7

Seat 6 (Mirror, WEAK):
  - Facing bet of 2. Mirror has WEAK hand.
  - Mirror default preflop: weak_call = 0.10
  - Roll: 0.88 → 0.88 > 0.10 → FOLD
  - Pot: 7

Seat 7 (Judge, MEDIUM):
  - Facing bet of 2. Judge cooperative preflop CR = 0.40, med_raise = 0.05
  - Roll: 0.03 → 0.03 < 0.05 → RAISE to 4
  - Pot: 11

Seat 0 (Oracle, STRONG):
  - Facing raise of 4. Oracle strong_raise = 0.60, strong_call = 0.35
  - Roll: 0.45 → 0.45 < 0.60 → RAISE to 6 (3-bet)
  - Pot: 17

Seat 1 (Sentinel, MEDIUM):
  - Facing 3-bet of 6. Sentinel CR = 0.40, med_raise = 0.05
  - Roll: 0.67 → 0.67 > 0.45 → FOLD
  - Pot: 17

Seat 2 (Firestorm, WEAK):
  - Facing 3-bet of 6 (needs to put in 4 more). Firestorm weak_call = 0.40
  - Roll: 0.29 → 0.29 < 0.40 → CALL (puts in 4 more, total 6)
  - Pot: 21

Seat 3 (Wall, WEAK):
  - Facing 3-bet of 6 (needs 4 more). Wall weak_call = 0.55
  - Roll: 0.41 → 0.41 < 0.55 → CALL (puts in 4 more)
  - Pot: 25

Seat 5 (Predator, MEDIUM):
  - Facing 3-bet of 6 (needs 4 more). CR = 0.35
  - Roll: 0.52 → 0.52 > 0.40 → FOLD
  - Pot: 25

Seat 7 (Judge, MEDIUM):
  - Facing 3-bet (needs 2 more). CR = 0.40
  - Roll: 0.38 → 0.38 < 0.40 → CALL (puts in 2 more)
  - Pot: 27
```

**Active players after pre-flop: Seats 0 (Oracle), 2 (Firestorm), 3 (Wall), 7 (Judge)**

### Flop
Community cards: **Ks 8d 4c**

Hand strength re-evaluation:
```
Seat 0 (Oracle):    Ah Kd + Ks 8d 4c → Pair of Kings, Ace kicker → STRONG
Seat 2 (Firestorm): Jh 7h + Ks 8d 4c → No pair, no draw → WEAK
Seat 3 (Wall):      Qs Td + Ks 8d 4c → No pair, gutshot (need J) → WEAK
Seat 7 (Judge):     Kh Qh + Ks 8d 4c → Pair of Kings, Queen kicker → STRONG
```

### Flop Betting Round (Small Bet = 2)
Action order: Left of dealer → (Seats 2, 3, 7, 0)
```
Pot: 27

Seat 2 (Firestorm, WEAK):
  - No bet pending. Firestorm flop BR = 0.65
  - Roll: 0.41 → 0.41 < 0.65 → BET 2 (bluff!)
  - Pot: 29

Seat 3 (Wall, WEAK):
  - Facing bet of 2. Wall flop CR = 0.75, weak_call = 0.50
  - Roll: 0.33 → CALL
  - Pot: 31

Seat 7 (Judge, STRONG):
  - Facing bet of 2. Judge coop flop: strong_raise = 0.60, strong_call = 0.35
  - Roll: 0.22 → RAISE to 4
  - Pot: 35

Seat 0 (Oracle, STRONG):
  - Facing raise of 4 (needs 4). Oracle strong_raise = 0.60, strong_call = 0.35
  - Roll: 0.51 → 0.51 < 0.60 → RAISE to 6 (3-bet on flop)
  - Pot: 41

Seat 2 (Firestorm, WEAK):
  - Facing 3-bet on flop (needs 4 more). Firestorm weak_call = 0.35
  - Roll: 0.58 → FOLD (even the Firestorm gives up sometimes)
  - Pot: 41

Seat 3 (Wall, WEAK):
  - Facing 3-bet (needs 4 more). Wall weak_call = 0.50
  - Roll: 0.44 → CALL
  - Pot: 45

Seat 7 (Judge, STRONG):
  - Facing 3-bet (needs 2 more). Judge strong_call = 0.35, strong_raise = 0.60
  - Roll: 0.18 → RAISE to 8 (cap! 4th bet)
  - Pot: 47 + 2 = 49
  
  (Wait — bet cap is 4 bets. Firestorm bet(1), Judge raised(2), Oracle raised(3), 
   Judge raises again(4) = cap reached)

Seat 0 (Oracle, STRONG):
  - Cap reached. Must call or fold. strong_call at cap ≈ high probability
  - CALL (puts in 2)
  - Pot: 51

Seat 3 (Wall, WEAK):
  - Cap reached. Must call or fold. weak_call = 0.50
  - Roll: 0.61 → FOLD (finally!)
  - Pot: 51
```

**Active after flop: Seats 0 (Oracle) and 7 (Judge)**

### Turn
Community: Ks 8d 4c **2h**

```
Seat 0: Ah Kd → Pair of Kings, Ace kicker → STRONG
Seat 7: Kh Qh → Pair of Kings, Queen kicker → STRONG
```

### Turn Betting (Big Bet = 4)
```
Pot: 51

Seat 7 (Judge, STRONG):
  - No bet pending. Judge coop turn VBR = 0.90
  - Roll: 0.14 → BET 4
  - Pot: 55

Seat 0 (Oracle, STRONG):
  - Facing bet of 4. Oracle turn: strong_raise = 0.55, strong_call = 0.38
  - Roll: 0.72 → 0.72 > 0.93 → FOLD? No, 0.72 < 0.55+0.38=0.93 → CALL
  - CALL (puts in 4)
  - Pot: 59
```

### River
Community: Ks 8d 4c 2h **Jc**

```
Seat 0: Ah Kd → Pair of Kings, Ace kicker → STRONG (still)
Seat 7: Kh Qh → Pair of Kings, Queen kicker → STRONG (still)
```

### River Betting (Big Bet = 4)
```
Pot: 59

Seat 7 (Judge, STRONG):
  - No bet pending. Judge coop river VBR = 0.85
  - Roll: 0.55 → BET 4
  - Pot: 63

Seat 0 (Oracle, STRONG):
  - Facing bet. Oracle river: strong_raise = 0.50, strong_call = 0.40
  - Roll: 0.33 → RAISE to 8
  - Pot: 71

Seat 7 (Judge, STRONG):
  - Facing raise (needs 4 more). strong_call = 0.40, strong_raise = 0.50
  - Roll: 0.62 → 0.62 > 0.50+0.40=0.90? No. 0.62 < 0.90 → CALL
  - CALL (puts in 4)
  - Pot: 75
```

### Showdown
```
Seat 0 (Oracle):  Ah Kd → Pair of Kings, Ace kicker
Seat 7 (Judge):   Kh Qh → Pair of Kings, Queen kicker

WINNER: Seat 0 (Oracle) — Ace kicker beats Queen kicker
Pot awarded: 75 chips to Oracle
```

### What Every Agent Observes

ALL 8 agents receive every action from this hand, even the ones who folded preflop:
- Phantom (folded preflop) sees that the Firestorm bet the flop and then folded to a 3-bet
- Mirror (folded preflop) sees the Oracle and Judge capping the flop
- At showdown, ALL agents see both Oracle's AKd and Judge's KQh
- Nobody sees the Firestorm's J7h (folded before showdown)

### Key Observations for Trust Updates
- The Firestorm bet the flop with a WEAK hand (J7h, no pair) and then folded — but since there was no showdown involving the Firestorm, nobody gets DIRECT evidence of the Firestorm's bluff. They only get indirect evidence (Firestorm bet, then folded to aggression).
- Both Oracle (AKd) and Judge (KQh) are revealed at showdown with STRONG hands. This is HONEST behavior from both — value betting with strong hands. All agents update toward higher trust for both.

---

## EXAMPLE 2: One Complete Bayesian Update Cycle

### Setup
Agent A = The Predator (Seat 5), observing Agent B = The Firestorm (Seat 2)

Current state (after 60 hands):
```
Predator's posterior about Firestorm (BEFORE this update):
  P(oracle)     = 0.04
  P(sentinel)   = 0.02
  P(firestorm)  = 0.51   ← trending toward correct classification
  P(wall)       = 0.01
  P(phantom)    = 0.28
  P(predator)   = 0.06
  P(mirror)     = 0.05
  P(judge)      = 0.03
  TOTAL         = 1.00
  
Current trust: T = Σ P_k × (1 - BR_k)
  = 0.04×0.670 + 0.02×0.917 + 0.51×0.375 + 0.01×0.962
  + 0.28×0.475 + 0.06×0.787 + 0.05×0.912 + 0.03×0.917
  = 0.027 + 0.018 + 0.191 + 0.010 + 0.133 + 0.047 + 0.046 + 0.028
  = 0.500

Current entropy: H = -Σ P_k × log2(P_k)
  = -(0.04×log2(0.04) + 0.02×log2(0.02) + 0.51×log2(0.51) + ...)
  ≈ 2.14 bits (out of max 3.0)
```

### Observation
Hand #61: Firestorm (Seat 2) bet on the river and the hand went to showdown. Firestorm's revealed hand was **WEAK** (7d 3c on a board of Ks Qh 9d 5c 2s — no pair, no draw). This is a confirmed bluff.

The Predator was in this hand (direct involvement, weight = 1.0).

### Step 1: Compute Likelihood for Each Type

"How likely is it that a player of type_k would bet the river with a Weak hand?"

This is simply the river Bluff Rate for each archetype:

```
P(river bet with Weak | oracle)     = BR_river_oracle    = 0.33
P(river bet with Weak | sentinel)   = BR_river_sentinel  = 0.05
P(river bet with Weak | firestorm)  = BR_river_firestorm = 0.55
P(river bet with Weak | wall)       = BR_river_wall      = 0.02
P(river bet with Weak | phantom)    = BR_river_phantom   = 0.45
P(river bet with Weak | predator)   = BR_river_predator  = 0.15
P(river bet with Weak | mirror)     = BR_river_mirror    = 0.05
P(river bet with Weak | judge_coop) = BR_river_judge     = 0.05
```

### Step 2: Apply Trembling Hand Noise (ε = 0.05)

Available actions on river facing no bet: bet or check (2 actions).
P_random = 1/2 = 0.50

```
Adjusted likelihood = (1 - 0.05) × raw_likelihood + 0.05 × 0.50

P_adj(oracle)     = 0.95 × 0.33 + 0.05 × 0.50 = 0.3135 + 0.025 = 0.3385
P_adj(sentinel)   = 0.95 × 0.05 + 0.05 × 0.50 = 0.0475 + 0.025 = 0.0725
P_adj(firestorm)  = 0.95 × 0.55 + 0.05 × 0.50 = 0.5225 + 0.025 = 0.5475
P_adj(wall)       = 0.95 × 0.02 + 0.05 × 0.50 = 0.0190 + 0.025 = 0.0440
P_adj(phantom)    = 0.95 × 0.45 + 0.05 × 0.50 = 0.4275 + 0.025 = 0.4525
P_adj(predator)   = 0.95 × 0.15 + 0.05 × 0.50 = 0.1425 + 0.025 = 0.1675
P_adj(mirror)     = 0.95 × 0.05 + 0.05 × 0.50 = 0.0475 + 0.025 = 0.0725
P_adj(judge)      = 0.95 × 0.05 + 0.05 × 0.50 = 0.0475 + 0.025 = 0.0725
```

### Step 3: Apply Exponential Decay to Prior (λ = 0.95)

Each prior probability is raised to the power of λ, which slightly flattens the distribution (pushing it toward uniform), allowing new evidence to have more impact:

```
Decayed prior = prior ^ 0.95

P_decay(oracle)     = 0.04 ^ 0.95  = 0.0435
P_decay(sentinel)   = 0.02 ^ 0.95  = 0.0221
P_decay(firestorm)  = 0.51 ^ 0.95  = 0.5238
P_decay(wall)       = 0.01 ^ 0.95  = 0.0112
P_decay(phantom)    = 0.28 ^ 0.95  = 0.2913
P_decay(predator)   = 0.06 ^ 0.95  = 0.0647
P_decay(mirror)     = 0.05 ^ 0.95  = 0.0540
P_decay(judge)      = 0.03 ^ 0.95  = 0.0330
```

### Step 4: Multiply Decayed Prior × Adjusted Likelihood

```
Unnormalized posterior = decayed_prior × adjusted_likelihood

raw(oracle)     = 0.0435 × 0.3385 = 0.01473
raw(sentinel)   = 0.0221 × 0.0725 = 0.001602
raw(firestorm)  = 0.5238 × 0.5475 = 0.28678
raw(wall)       = 0.0112 × 0.0440 = 0.000493
raw(phantom)    = 0.2913 × 0.4525 = 0.13181
raw(predator)   = 0.0647 × 0.1675 = 0.01084
raw(mirror)     = 0.0540 × 0.0725 = 0.003915
raw(judge)      = 0.0330 × 0.0725 = 0.002393

SUM = 0.45185
```

### Step 5: Normalize

```
NEW POSTERIOR (divide each by sum):

P(oracle)     = 0.01473 / 0.45185 = 0.0326  (was 0.04)   ↓
P(sentinel)   = 0.00160 / 0.45185 = 0.0035  (was 0.02)   ↓↓
P(firestorm)  = 0.28678 / 0.45185 = 0.6347  (was 0.51)   ↑↑ CORRECT DIRECTION
P(wall)       = 0.00049 / 0.45185 = 0.0011  (was 0.01)   ↓↓
P(phantom)    = 0.13181 / 0.45185 = 0.2917  (was 0.28)   ↑ (also bluffs a lot)
P(predator)   = 0.01084 / 0.45185 = 0.0240  (was 0.06)   ↓
P(mirror)     = 0.00392 / 0.45185 = 0.0087  (was 0.05)   ↓
P(judge)      = 0.00239 / 0.45185 = 0.0053  (was 0.03)   ↓
TOTAL         = 1.0000
```

### Step 6: Compute New Trust Score and Entropy

```
NEW TRUST SCORE: T = Σ P_k × (1 - BR_k)
  = 0.0326×0.670 + 0.0035×0.917 + 0.6347×0.375 + 0.0011×0.962
  + 0.2917×0.475 + 0.0240×0.787 + 0.0087×0.912 + 0.0053×0.917
  = 0.022 + 0.003 + 0.238 + 0.001 + 0.139 + 0.019 + 0.008 + 0.005
  = 0.435

Trust DROPPED from 0.500 to 0.435 — the confirmed bluff reduced trust.

NEW ENTROPY: H = -Σ P_k × log2(P_k)
  ≈ -(0.0326×(-4.94) + 0.0035×(-8.16) + 0.6347×(-0.66) + ...)
  ≈ 1.81 bits

Entropy DROPPED from 2.14 to 1.81 — the Predator is more confident about 
the Firestorm's type (probability mass concentrated on firestorm + phantom).
```

### What This Means

After this single confirmed river bluff:
- The Predator's belief that Seat 2 is a Firestorm jumped from 51% to 63%
- Sentinel and Wall probabilities collapsed (they almost never bluff the river)
- Phantom probability held steady (it also bluffs a lot)
- Trust dropped by 0.065 (from 0.50 to 0.435)
- The Predator is getting close to the 60% classification threshold for adaptation

After maybe 2-3 more confirmed bluffs, the Predator will hit α > 0 and begin blending toward the Firestorm exploit strategy (stop bluffing, call down, max value bet).

---

## EXAMPLE 3: The Judge's Grievance Trigger

### Setup
The Judge (Seat 7) has been playing for 350 hands. Against the Firestorm (Seat 2), the Judge's grievance ledger currently reads:

```
grievance[seat_2] = 4   (threshold τ = 5)
triggered[seat_2] = False
```

Four times in 350 hands, the Firestorm bet or raised against the Judge, the hand went to showdown, and the Firestorm revealed a Weak hand. Each time, the ledger incremented by 1.

### Hand #351
The Firestorm bets the turn with 6d 4s on a board of Kh Qc 9s 2d. The Judge calls with KsJd (Strong — pair of kings). The river is dealt (7h). The Firestorm bets again (bluffing). The Judge calls. At showdown:

- Firestorm reveals: 6d 4s → WEAK (no pair, no draw)
- Judge reveals: Ks Jd → STRONG (pair of kings)
- Judge wins the pot

### Grievance Update
The Firestorm bet with a Weak hand against the Judge at showdown.

```
grievance[seat_2] = 4 + 1 = 5
5 >= τ (5) → TRIGGERED!
triggered[seat_2] = True
trigger_hand = 351
```

### What Changes
From hand 352 onward, whenever the Judge is in a hand with the Firestorm:
- Judge uses RETALIATORY parameters (BR: 0.70, CR: 0.15) instead of COOPERATIVE (BR: 0.10, CR: 0.40)
- This is PERMANENT. Even if the Firestorm plays honestly for the next 1000 hands, the Judge never forgives
- The Judge's behavior toward ALL OTHER players remains unchanged (cooperative)

### What Other Agents See
Starting at hand 352, any agent observing the Judge in a pot with the Firestorm will notice:
- The Judge suddenly bluffs aggressively (BR jumps from 0.10 to 0.70)
- The Judge stops calling (CR drops from 0.40 to 0.15)
- This behavioral shift causes a spike in posterior entropy about the Judge
- Observers who only see the Judge against the Firestorm may reclassify the Judge as a LAG
- Observers who also see the Judge playing cooperatively with others will be confused — the Judge looks like two different players depending on the opponent
