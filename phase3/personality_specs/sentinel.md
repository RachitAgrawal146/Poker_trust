# The Sentinel — Tight-Aggressive (TAG)

## Qualitative Personality

The Sentinel is the disciplined, tight-aggressive player. It enters very few
pots but plays them aggressively when it does. The Sentinel folds the most of
any archetype (56.7%) and has the second-lowest VPIP (16.2%), but when it does
get involved, it backs its hand with strong aggression — its AF of 1.07 is
above average despite its selective hand entry.

The Sentinel's defining trait is patience. It waits for premium hands and then
pushes hard. Its value bet rates are among the highest (VBR 0.85-0.95 across
streets) while its bluff rate is very low (BR 0.05-0.10). When facing a bet
with a strong hand, it raises aggressively (strong_raise 0.50-0.65) and almost
never folds strong hands (strong_fold 0.05-0.10). With weak hands, it has very
low calling tendencies (weak_call 0.04-0.10), consistent with its tight image.

The Sentinel's tight play makes it highly trusted (0.784 trust received) but
paradoxically makes it harder to identify — its behavioral signature overlaps
heavily with judge_cooperative and mirror_default, creating a 3-way ambiguity
cluster that the Bayesian trust model cannot resolve. No observer in Phase 1
ever correctly identified Sentinel as sentinel (0% accuracy).

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 16.2% (±0.3%)
- **PFR**: 4.1% (±0.1%)
- **Aggression Factor (AF)**: 1.07
- **Showdown Rate (SD%)**: 5.1%
- **Showdown Win Rate (SD Win%)**: 54.9%

### Economic Performance
- **Mean Final Stack**: 2,797 chips (±807)
- **Mean Rebuys**: 0.5 (min 0, max 3)
- **Economic Rank**: 4th of 8

### Action Distribution (across all streets)
- **Fold**: 56.7%
- **Check**: 15.4%
- **Call**: 13.5%
- **Bet**: 8.6%
- **Raise**: 5.8%
- **Total Actions**: 790,054 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 4.1%
- **Flop**: 30.0%
- **Turn**: 37.9%
- **River**: 41.7%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.784
- **Mean Entropy** (others' uncertainty about Sentinel): 2.28 bits
- **Identification Accuracy**: 0.0% (0/140 — always misclassified)
- **Top Misclassification**: Confused with oracle (0.443 prob)
- **Honesty Score**: 0.917

### Showdown Performance
- **Showdown Wins**: 14,080 out of 25,660 (54.9%)
- **Mean Hand Rank at Showdown**: 3,461
- **Mean Pot Won at Showdown**: 19.5 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 69.6%
- **Walkover Wins**: 26,523 (8.0% of all walkovers)
- **Mean Walkover Pot**: 16.2 chips

### Personality Fidelity
- **Fidelity Score**: 90.8% (22,531/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0249 (moderate impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0513 (low information generation)
- **Information Role**: NEUTRAL — tight play generates minimal trust signal

### Pot Involvement
- **Hands Involved In**: 121,618 (of 500,000)
- **Mean Pot When Involved**: 31.2 chips
- **Max Pot**: 227 chips

### Identifiability Note
Sentinel is part of the "ambiguity cluster" with mirror_default and
judge_cooperative. Their averaged behavioral parameters are nearly identical
(br ~0.083-0.088, vbr ~0.850-0.900, cr ~0.320-0.325, mbr ~0.225), making
them indistinguishable to the Bayesian trust model. Entropy for Sentinel
converges to ~2.28 bits rather than the ideal <1.0 bit.
