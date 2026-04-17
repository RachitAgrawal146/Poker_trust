# The Firestorm — Loose-Aggressive (LAG / Maniac)

## Qualitative Personality

The Firestorm is the table's maniac — a hyper-aggressive player who enters
nearly every pot and bets relentlessly regardless of hand strength. With a
VPIP of 49.4% and the highest PFR (12.0%), Firestorm plays far more hands
than any other archetype except Wall, and does so aggressively.

Firestorm's defining trait is its extreme bluff rate (BR 0.55-0.70 across
streets) combined with near-perfect value betting (VBR 0.90-0.98). It bets
weak hands almost as often as it bets strong hands, creating a "bet everything"
pattern that makes it simultaneously the least trusted agent (0.435 trust) and
the most economically successful (17,862 mean final stack — 5x the next best).

The paradox of Firestorm is that raw aggression works in Limit Hold'em. Its
87.1% fold equity — the highest of any archetype — means opponents fold to
Firestorm's bets so often that it wins huge numbers of pots without showdown
(102,055 walkovers, 30.8% of all). When it does reach showdown, it has the
worst win rate (38.5%), but the non-showdown profits vastly outweigh showdown
losses.

Firestorm is trivially identifiable. Its behavioral signature is so distinctive
that the trust model converges to near-zero entropy (0.82 bits) within a few
hundred hands. Every observer recognizes it as firestorm with 67.1% accuracy
and 0.882 posterior probability.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 49.4% (±0.3%)
- **PFR**: 12.0% (±0.2%)
- **Aggression Factor (AF)**: 1.12
- **Showdown Rate (SD%)**: 14.8%
- **Showdown Win Rate (SD Win%)**: 38.5%

### Economic Performance
- **Mean Final Stack**: 17,862 chips (±1,195) — DOMINANT WINNER
- **Mean Rebuys**: 0.1 (min 0, max 1)
- **Economic Rank**: 1st of 8

### Action Distribution (across all streets)
- **Fold**: 28.4%
- **Check**: 8.0%
- **Call**: 30.0%
- **Bet**: 21.7%
- **Raise**: 11.9%
- **Total Actions**: 1,140,444 (over 500k hands) — most actions of any archetype

### Per-Street Aggression (bet+raise %)
- **Preflop**: 11.1%
- **Flop**: 53.5%
- **Turn**: 55.7%
- **River**: 56.5%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.435 — LOWEST
- **Mean Entropy** (others' uncertainty about Firestorm): 0.82 bits — near-certain identification
- **Identification Accuracy**: 67.1% (94/140 observers correctly ID'd as firestorm)
- **Mean Posterior When Correctly ID'd**: 0.882
- **Honesty Score**: 0.375

### Showdown Performance
- **Showdown Wins**: 28,491 out of 73,948 (38.5%) — WORST win rate
- **Mean Hand Rank at Showdown**: 3,808 — worst average hand quality
- **Mean Pot Won at Showdown**: 14.3 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 87.1% — HIGHEST
- **Walkover Wins**: 102,055 (30.8% of all walkovers) — MOST walkovers
- **Mean Walkover Pot**: 16.9 chips

### Personality Fidelity
- **Fidelity Score**: 97.6% (24,194/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0192 (moderate impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0688 (high information generation)
- **Information Role**: DONOR — generates large trust signals that inform other agents' models

### Pot Involvement
- **Hands Involved In**: 260,387 (of 500,000) — MOST involvement
- **Mean Pot When Involved**: 33.1 chips
- **Max Pot**: 227 chips

### Key Insight
Firestorm's success demonstrates that in Limit Hold'em with rule-based
opponents, hyper-aggression and high fold equity dominate showdown quality.
The strategy is not "good poker" in a game-theoretic sense — it exploits
opponents who fold too much to aggression.
