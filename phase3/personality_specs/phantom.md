# The Phantom — Deceiver / False Signal Generator

## Qualitative Personality

The Phantom is the table's deceiver — a player designed to generate misleading
signals. It has a high bluff rate (BR 0.45-0.60 across streets) combined with
an unusually low value bet rate (VBR 0.50-0.65, lowest of all archetypes).
This creates an inverted betting pattern: the Phantom bets weak hands almost
as frequently as strong hands, and sometimes *more* frequently than it bets
medium hands.

The Phantom's deceptive strategy extends to its facing-bet behavior. It has
the highest strong_fold rates (0.15-0.30 across streets) — it sometimes folds
strong hands when facing a bet, which is deeply unusual and creates confusing
signals for opponents trying to model its behavior. Its weak_call rates
(0.15-0.35) are moderate, meaning it sometimes calls with junk to maintain
unpredictability.

Economically, the Phantom is disastrous: 129 mean final stack (worst of all)
with 58.1 mean rebuys. Its deception doesn't translate to profit because in
Limit Hold'em, the bet sizes are fixed — the Phantom can't leverage its
unpredictability into outsized pots the way a no-limit deceiver could.

Despite its deceptive intent, the Phantom is actually well-identified (92.1%
accuracy, 0.447 posterior). Its distinct combination of high bluffing + low
value betting + high strong_fold creates a unique behavioral signature that
the trust model picks up. Its trust score (0.667) falls between the
aggressive archetypes and the tight ones.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 38.7% (±0.4%)
- **PFR**: 7.7% (±0.2%)
- **Aggression Factor (AF)**: 0.67
- **Showdown Rate (SD%)**: 6.4%
- **Showdown Win Rate (SD Win%)**: 54.9%

### Economic Performance
- **Mean Final Stack**: 129 chips (±79) — WORST
- **Mean Rebuys**: 58.1 (min 47, max 64)
- **Economic Rank**: 8th of 8 (worst)

### Action Distribution (across all streets)
- **Fold**: 45.7%
- **Check**: 11.9%
- **Call**: 25.4%
- **Bet**: 10.2%
- **Raise**: 6.8%
- **Total Actions**: 928,816 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 7.1%
- **Flop**: 29.9%
- **Turn**: 32.5%
- **River**: 33.1%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.667
- **Mean Entropy** (others' uncertainty about Phantom): 2.17 bits
- **Identification Accuracy**: 92.1% (129/140 observers correctly ID'd as phantom)
- **Mean Posterior When Correctly ID'd**: 0.447
- **Honesty Score**: 0.475

### Showdown Performance
- **Showdown Wins**: 17,545 out of 31,954 (54.9%)
- **Mean Hand Rank at Showdown**: 3,573
- **Mean Pot Won at Showdown**: 14.6 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 53.1%
- **Walkover Wins**: 43,689 (13.2% of all walkovers)
- **Mean Walkover Pot**: 12.5 chips

### Personality Fidelity
- **Fidelity Score**: 98.1% (24,332/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0164 (minimal impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0936 (HIGHEST information generation)
- **Information Role**: DONOR — generates the most trust signal per hand, ironically making itself easier to identify

### Pot Involvement
- **Hands Involved In**: 212,052 (of 500,000)
- **Mean Pot When Involved**: 27.4 chips
- **Max Pot**: 227 chips

### Trust Signature Distinctiveness
- **Minimum distance to nearest archetype**: 0.285 (to oracle) — DISTINCTIVE
- Phantom's trust signature is the 3rd most distinctive, after firestorm and wall

### Key Insight
The Phantom generates more trust information per hand than any other archetype
(0.0936 delta), but this high signal generation is self-defeating — it makes
the Phantom easy to identify despite its deceptive intent. In a trust-aware
ecosystem, being a "noisy" deceiver is worse than being a quiet one.
