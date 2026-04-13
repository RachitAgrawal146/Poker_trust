# The Wall — Passive / Calling Station

## Qualitative Personality

The Wall is the ultimate calling station — a passive player who almost never
bets or raises but calls with extraordinary frequency. With a VPIP of 53.9%
(highest of all archetypes) and a PFR of only 1.5% (lowest), the Wall enters
more pots than any other player but almost exclusively by calling rather than
raising. Its aggression factor of 0.13 is by far the lowest in the game.

The Wall's defining characteristic is its refusal to fold. It calls facing bets
with weak hands at rates of 0.35-0.55 across streets, and with strong hands
it almost always calls (strong_call 0.80-0.82) rather than raising
(strong_raise 0.08-0.15). This creates a "can't be bluffed" profile — but at
enormous economic cost. The Wall hemorrhages chips by paying off opponents'
value bets and rarely extracting value from its own strong hands.

Economically, the Wall is catastrophic: 174 mean final stack with 78.9 mean
rebuys per seed (1,578 total across 20 seeds). It goes broke repeatedly
because it calls too much with weak holdings. Despite this, it has the highest
trust score (0.962) because its low bluff rate (0.02-0.05) makes it the most
"honest" player at the table.

The Wall is perfectly identifiable. Every single observer in Phase 1 correctly
identified it as wall (100% accuracy, 1.000 posterior probability). Its
entropy converges to 0.001 bits — effectively zero uncertainty.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 53.9% (±0.3%) — HIGHEST
- **PFR**: 1.5% (±0.1%) — LOWEST
- **Aggression Factor (AF)**: 0.13 — LOWEST
- **Showdown Rate (SD%)**: 23.1% — HIGHEST
- **Showdown Win Rate (SD Win%)**: 49.0%

### Economic Performance
- **Mean Final Stack**: 174 chips (±103) — near-bankrupt
- **Mean Rebuys**: 78.9 (min 66, max 90) — MOST rebuys
- **Economic Rank**: 7th of 8

### Action Distribution (across all streets)
- **Fold**: 25.5%
- **Check**: 21.2%
- **Call**: 47.0% — HIGHEST call rate
- **Bet**: 4.5%
- **Raise**: 1.9% — LOWEST raise rate
- **Total Actions**: 1,357,692 (over 500k hands) — most total actions

### Per-Street Aggression (bet+raise %)
- **Preflop**: 1.3%
- **Flop**: 9.6%
- **Turn**: 10.3%
- **River**: 10.9%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.962 — HIGHEST
- **Mean Entropy** (others' uncertainty about Wall): 0.001 bits — PERFECTLY identified
- **Identification Accuracy**: 100.0% (140/140) — PERFECT
- **Mean Posterior**: 1.000
- **Honesty Score**: 0.962

### Showdown Performance
- **Showdown Wins**: 56,545 out of 115,348 (49.0%)
- **Mean Hand Rank at Showdown**: 3,757
- **Mean Pot Won at Showdown**: 12.3 chips — lowest pot wins

### Fold Equity / Walkover Performance
- **Fold Equity**: 50.1% — LOWEST
- **Walkover Wins**: 37,769 (11.4% of all walkovers)
- **Mean Walkover Pot**: 13.1 chips

### Personality Fidelity
- **Fidelity Score**: 75.2% (18,640/24,801 windows in-range) — LOWEST fidelity

### Ecological Footprint
- **Footprint Score**: 0.0235 (moderate impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0001 (very low information generation)
- **Information Role**: NEUTRAL — so predictable that it generates almost no new information

### Pot Involvement
- **Hands Involved In**: 309,011 (of 500,000) — second-most involvement
- **Mean Pot When Involved**: 27.9 chips
- **Max Pot**: 227 chips

### Key Insight
The Wall represents the worst economic strategy in this simulation: high trust
and perfect identifiability correlate with financial ruin. The trust-profit
correlation across all archetypes is r = -0.770, and Wall is the extreme
case — maximally trusted, minimally profitable.
