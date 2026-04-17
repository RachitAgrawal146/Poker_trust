# The Judge — Grudger / Conditional Cooperator

## Qualitative Personality

The Judge is a conditional cooperator that starts as a tight, honest player
(identical to Sentinel) but switches to aggressive retaliation against any
opponent it catches bluffing too many times. It maintains a per-opponent
"grievance ledger" and triggers retaliation permanently against an opponent
once that opponent accumulates 5 confirmed bluffs (tau=5) against the Judge.

In its cooperative state, the Judge plays like a Sentinel: tight entry (VPIP
15.9%), moderate aggression (AF 1.39 overall — the highest of any archetype),
high value betting (VBR 0.85-0.95), low bluffing (BR 0.05-0.10), and selective
showdowns (SD% 4.3%, the lowest). The Judge has the highest showdown win rate
(55.7%) because it only enters showdowns with strong hands.

When retaliation triggers against a specific opponent, the Judge switches to
extremely aggressive parameters for hands involving that opponent: BR jumps to
0.55-0.70 (from 0.05-0.10), CR drops to 0.08-0.15 (from 0.25-0.40), and
med_raise increases dramatically. The retaliatory state is permanent per
opponent — once triggered, the Judge never returns to cooperative play against
that opponent.

The Judge has the highest ecological footprint (0.0322) of any archetype,
meaning its presence has the largest impact on the game's trust dynamics. Its
dual-state nature (cooperative + retaliatory) makes it a powerful force in
shaping other agents' models, though in Phase 1 the retaliation was rarely
triggered (bet rates stayed below 0.30 across all seeds).

The Judge is poorly identified by other agents (0% accuracy, confused with
oracle at 0.265 probability) because its cooperative behavior is
indistinguishable from Sentinel and Mirror in the trust model.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 15.9% (±0.2%) — lowest
- **PFR**: 4.4% (±0.1%)
- **Aggression Factor (AF)**: 1.39 — HIGHEST
- **Showdown Rate (SD%)**: 4.3% — LOWEST
- **Showdown Win Rate (SD Win%)**: 55.7% — HIGHEST

### Economic Performance
- **Mean Final Stack**: 1,995 chips (±714)
- **Mean Rebuys**: 0.8 (min 0, max 5)
- **Economic Rank**: 5th of 8

### Action Distribution (across all streets)
- **Fold**: 58.8% — HIGHEST fold rate
- **Check**: 14.4%
- **Call**: 11.2%
- **Bet**: 8.8%
- **Raise**: 6.7%
- **Total Actions**: 766,480 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 4.4%
- **Flop**: 33.6%
- **Turn**: 45.4%
- **River**: 48.6%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.815
- **Mean Entropy** (others' uncertainty about Judge): 2.47 bits
- **Identification Accuracy**: 0.0% (0/140 — never correctly identified)
- **Top Misclassification**: Confused with oracle (0.265 prob)
- **Honesty Score**: 0.917 (cooperative) / 0.375 (retaliatory)

### Judge-Specific Retaliation Data
**Bet rate rolling window** (across seeds): 0.108-0.231 (no consistent retaliation)

**Judge aggression by opponent aggression status (fold rate when opponent aggressed vs passive):**
- vs oracle: aggressed 0.467, passive 0.599 (delta: -0.132)
- vs sentinel: aggressed 0.463, passive 0.596 (delta: -0.133)
- vs firestorm: aggressed 0.515, passive 0.622 (delta: -0.107)
- vs wall: aggressed 0.525, passive 0.592 (delta: -0.067)
- vs phantom: aggressed 0.462, passive 0.607 (delta: -0.145)
- vs predator: aggressed 0.454, passive 0.597 (delta: -0.143)
- vs mirror: aggressed 0.464, passive 0.599 (delta: -0.134)

**Trust received over time (run 1):**
- h100: 0.860, h500: 0.771, h1000: 0.811, h2000: 0.766, h5000: 0.732, h10000: 0.825

### Showdown Performance
- **Showdown Wins**: 11,906 out of 21,379 (55.7%) — BEST win rate
- **Mean Hand Rank at Showdown**: 3,449
- **Mean Pot Won at Showdown**: 19.8 chips — highest pot wins

### Fold Equity / Walkover Performance
- **Fold Equity**: 70.9%
- **Walkover Wins**: 27,911 (8.4% of all walkovers)
- **Mean Walkover Pot**: 16.2 chips

### Personality Fidelity
- **Fidelity Score**: 92.5% (22,949/24,801 windows in-range)

### Ecological Footprint
- **Footprint Score**: 0.0322 — HIGHEST (dominant presence)

### Information Dynamics
- **Trust Delta per Hand**: 0.0578 (moderate information generation)
- **Information Role**: CATALYST — its dual-state nature has outsized impact on trust dynamics

### Pot Involvement
- **Hands Involved In**: 120,221 (of 500,000)
- **Mean Pot When Involved**: 30.9 chips
- **Max Pot**: 227 chips

### Dual-State Parameters
**Cooperative State** (judge_cooperative — identical to Sentinel):
- BR: 0.05-0.10, VBR: 0.85-0.95, CR: 0.25-0.40, MBR: 0.15-0.30

**Retaliatory State** (judge_retaliatory — triggered after tau=5 bluffs):
- BR: 0.55-0.70, VBR: 0.85-0.95, CR: 0.08-0.15, MBR: 0.55-0.70
- strong_raise: 0.55-0.70, med_raise: 0.10-0.20, weak_call: 0.02-0.05

### Retaliation Mechanism
1. Judge observes each opponent's actions via `_observe_opponent_action`
2. At showdown, if opponent bet/raised with a Weak hand → +1 grievance
3. When grievance count reaches tau=5 for a specific opponent → permanent switch
4. Retaliatory parameters applied ONLY against the triggering opponent
5. Other opponents continue to receive cooperative treatment

### Trust Signature
Judge and Mirror have the most similar trust signatures (distance=0.033).
Both fall within the sentinel/mirror/judge ambiguity cluster, making all
three indistinguishable to the Bayesian trust model.
