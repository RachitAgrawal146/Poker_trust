# The Predator — Exploiter / Shark

## Qualitative Personality

The Predator is the table's shark — an adaptive agent that uses its Bayesian
posteriors to classify opponents and then exploit their weaknesses. It starts
with conservative baseline parameters (similar to a slightly looser Sentinel)
and transitions to opponent-specific exploit strategies when it classifies an
opponent with >60% posterior confidence.

The Predator's baseline play is tight and controlled: VPIP 18.5%, PFR 4.1%,
AF 0.83. It enters few pots and plays them with moderate aggression. But the
real power lies in its exploit table — when it identifies an opponent, it
shifts strategy: bluffing more against tight players (Sentinel), calling down
against maniacs (Firestorm), never bluffing against calling stations (Wall),
and raising more against players who fold to pressure (Phantom).

In Phase 1, the Predator successfully classified 2 of 7 opponents with >60%
confidence: Wall (1.000 posterior, perfect) and Firestorm (0.82 posterior,
high confidence). The remaining opponents fell below the 0.60 threshold due
to the sentinel/mirror/judge ambiguity cluster. The blend factor
alpha = min(1, (max_post - 0.6)/0.3) controls how aggressively the exploit
parameters are applied.

Economically, the Predator is middle-of-the-pack: 1,125 mean final stack
with 2.7 mean rebuys. Its exploitation capability is limited by the
identifiability ceiling — it can only fully exploit the two most distinctive
opponents (Wall and Firestorm), while the ambiguity cluster prevents
exploitation of the other five.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 18.5% (±0.1%)
- **PFR**: 4.1% (±0.1%)
- **Aggression Factor (AF)**: 0.83
- **Showdown Rate (SD%)**: 5.6%
- **Showdown Win Rate (SD Win%)**: 52.8%

### Economic Performance
- **Mean Final Stack**: 1,125 chips (±854)
- **Mean Rebuys**: 2.7 (min 0, max 8)
- **Economic Rank**: 6th of 8

### Action Distribution (across all streets)
- **Fold**: 55.0%
- **Check**: 14.3%
- **Call**: 16.7%
- **Bet**: 7.8%
- **Raise**: 6.1%
- **Total Actions**: 806,391 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 4.0%
- **Flop**: 28.4%
- **Turn**: 35.2%
- **River**: 39.6%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.765
- **Mean Entropy** (others' uncertainty about Predator): 2.43 bits
- **Identification Accuracy**: 30.0% (42/140)
- **Top Misclassification**: Confused with phantom (0.381 prob)
- **Honesty Score**: 0.787

### Classification Performance (Predator's view of opponents)
At hand milestones [100, 500, 1000, 2500, 5000, 10000]:
- **Oracle (S0)**: 0.30 → 0.34 → 0.34 → 0.32 → 0.30 → 0.32 (never classified)
- **Sentinel (S1)**: 0.29 → 0.33 → 0.28 → 0.28 → 0.26 → 0.28 (never classified)
- **Firestorm (S2)**: 0.81 → 0.84 → 0.80 → 0.83 → 0.81 → 0.82 (CLASSIFIED >0.60)
- **Wall (S3)**: 1.00 → 1.00 → 1.00 → 1.00 → 1.00 → 1.00 (PERFECTLY classified)
- **Phantom (S4)**: 0.51 → 0.51 → 0.50 → 0.46 → 0.52 → 0.51 (near-threshold)
- **Mirror (S6)**: 0.26 → 0.28 → 0.27 → 0.29 → 0.25 → 0.28 (never classified)
- **Judge (S7)**: 0.25 → 0.26 → 0.28 → 0.29 → 0.29 → 0.26 (never classified)

### Showdown Performance
- **Showdown Wins**: 14,828 out of 28,109 (52.8%)
- **Mean Hand Rank at Showdown**: 3,516
- **Mean Pot Won at Showdown**: 18.5 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 66.4%
- **Walkover Wins**: 28,034 (8.5% of all walkovers)
- **Mean Walkover Pot**: 15.9 chips

### Personality Fidelity
- **Fidelity Score**: 92.2% (22,866/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0169 (minimal impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0583 (moderate information generation)
- **Information Role**: CONSUMER — the primary consumer of trust information, using posteriors to select exploit strategies

### Pot Involvement
- **Hands Involved In**: 132,576 (of 500,000)
- **Mean Pot When Involved**: 31.7 chips
- **Max Pot**: 211 chips

### Adaptive Behavior
The Predator blends from baseline toward exploit parameters using:
`alpha = min(1.0, (max_posterior - 0.60) / 0.30)`

When alpha > 0, the Predator uses:
`effective_param = (1 - alpha) * baseline + alpha * exploit[target_type]`

Key exploit adjustments:
- vs Wall: Stop bluffing (BR→0.01-0.05), max value bet (VBR→0.95-0.98)
- vs Firestorm: Stop bluffing (BR→0.05-0.10), call down bluffs (CR→0.55-0.60)
- vs Sentinel: Bluff more (BR→0.38-0.45), call less (CR→0.20-0.25)
- vs Phantom: Raise more, call down bluffs (CR→0.50-0.55)
