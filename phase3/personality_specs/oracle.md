# The Oracle — Nash Equilibrium Player

## Qualitative Personality

The Oracle is the game-theoretically optimal player. It plays a balanced,
unexploitable strategy rooted in Nash equilibrium principles. It bets strong
hands for value at high rates, bluffs at a mathematically balanced frequency
(~33%), and calls facing bets at a balanced rate. The Oracle never adjusts to
opponents — it plays the same strategy regardless of who is at the table,
trusting that equilibrium play is inherently robust.

The Oracle's calling and raising frequencies are symmetric across hand strength
categories: strong hands get aggressive action, medium hands see moderate
continuation, and weak hands are folded at appropriate frequencies. Post-flop
aggression increases slightly from flop through river, reflecting the larger
bet sizes on later streets and the Oracle's willingness to continue pressing
edges.

The Oracle is neither the most profitable nor the most trusted agent. Its
balanced strategy makes it difficult for opponents to exploit, but also limits
its ability to extract maximum value from weaker opponents. It serves as the
strategic baseline — the "house standard" that every other archetype deviates
from in some dimension.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 21.6% (±0.3%)
- **PFR**: 6.1% (±0.1%)
- **Aggression Factor (AF)**: 1.18
- **Showdown Rate (SD%)**: 5.6%
- **Showdown Win Rate (SD Win%)**: 51.6%

### Economic Performance
- **Mean Final Stack**: 3,091 chips (±921)
- **Mean Rebuys**: 0.6 (min 0, max 3)
- **Economic Rank**: 2nd of 8

### Action Distribution (across all streets)
- **Fold**: 53.6%
- **Check**: 12.5%
- **Call**: 15.6%
- **Bet**: 11.2%
- **Raise**: 7.1%
- **Total Actions**: 812,664 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 5.9%
- **Flop**: 37.7%
- **Turn**: 44.0%
- **River**: 46.8%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.758
- **Mean Entropy** (others' uncertainty about Oracle): 2.25 bits
- **Identification Accuracy**: 52.1% (73/140 observers correctly ID'd as oracle)
- **Top Misclassification**: Often confused with sentinel/predator_baseline
- **Honesty Score**: 0.670

### Showdown Performance
- **Showdown Wins**: 14,529 out of 28,159 (51.6%)
- **Mean Hand Rank at Showdown**: 3,519
- **Mean Pot Won at Showdown**: 18.6 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 68.5%
- **Walkover Wins**: 36,023 (10.9% of all walkovers)
- **Mean Walkover Pot**: 15.4 chips

### Personality Fidelity
- **Fidelity Score**: 88.2% (21,869/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0297 (dominant presence)

### Information Dynamics
- **Trust Delta per Hand**: 0.0664 (moderate information generation)
- **Information Role**: NEUTRAL — neither generates nor consumes trust information disproportionately

### Pot Involvement
- **Hands Involved In**: 138,213 (of 500,000)
- **Mean Pot When Involved**: 31.6 chips
- **Max Pot**: 227 chips
