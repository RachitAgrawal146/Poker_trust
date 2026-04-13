# The Mirror — Tit-for-Tat / Mimicry Agent

## Qualitative Personality

The Mirror is an adaptive agent that copies the behavioral profile of its most
active opponent. It starts with conservative default parameters (similar to
Sentinel) and gradually shifts its play to match the opponent who has taken the
most actions against it. This creates a "tit-for-tat" dynamic where the Mirror
reflects the table's dominant behavioral patterns back at the other players.

The Mirror's default play is tight and disciplined: VPIP 18.6%, PFR 5.2%,
AF 0.88. These defaults keep it safe while it gathers enough observations to
start mirroring. The mirroring mechanism works by tracking per-opponent
behavioral statistics (observed_vpip, observed_br, observed_cr) during live
play via the `_observe_opponent_action` hook, then at decision time copying
the most-active opponent's metrics into its parameter table.

In practice, the Mirror's mirroring is subtle — it never fully becomes another
archetype, but adjusts its tendencies toward whichever opponent is most active.
Because Firestorm generates the most actions (1,140,444 total), the Mirror
often gravitates toward slightly more aggressive play over time. Its rolling
AF shows variability (0.74-0.98) as it shifts between mirroring different
opponents.

The Mirror is moderately identifiable (47.9% accuracy) but with low confidence
(0.251 posterior). It falls within the sentinel/mirror/judge ambiguity cluster,
making confident identification difficult. Its trust profile is similar to
Sentinel's, and it has the highest personality fidelity (99.1%) because its
mirroring mechanism keeps it close to established behavioral patterns.

## Quantitative Targets (from Phase 1 v3 data, 20 seeds x 25,000 hands)

### Core Behavioral Stats
- **VPIP**: 18.6% (±0.2%)
- **PFR**: 5.2% (±0.1%)
- **Aggression Factor (AF)**: 0.88
- **Showdown Rate (SD%)**: 6.5%
- **Showdown Win Rate (SD Win%)**: 54.8%

### Economic Performance
- **Mean Final Stack**: 2,856 chips (±897)
- **Mean Rebuys**: 0.6 (min 0, max 3)
- **Economic Rank**: 3rd of 8

### Action Distribution (across all streets)
- **Fold**: 53.6%
- **Check**: 16.2%
- **Call**: 16.1%
- **Bet**: 6.9%
- **Raise**: 7.2%
- **Total Actions**: 817,504 (over 500k hands)

### Per-Street Aggression (bet+raise %)
- **Preflop**: 5.1%
- **Flop**: 27.3%
- **Turn**: 32.2%
- **River**: 34.4%

### Trust Profile
- **Mean Trust Received** (from other agents): 0.798
- **Mean Entropy** (others' uncertainty about Mirror): 2.45 bits
- **Identification Accuracy**: 47.9% (67/140)
- **Mean Posterior When Correctly ID'd**: mirror_default at 0.251
- **Honesty Score**: 0.912

### Mirror-Specific Trust Evolution
Trust received at milestones (from run 1):
- **h50**: trust=0.839, entropy=2.468
- **h100**: trust=0.847, entropy=2.428
- **h1000**: trust=0.836, entropy=2.444
- **h10000**: trust=0.833, entropy=2.485

### Showdown Performance
- **Showdown Wins**: 17,837 out of 32,570 (54.8%)
- **Mean Hand Rank at Showdown**: 3,431 — BEST mean hand quality
- **Mean Pot Won at Showdown**: 17.6 chips

### Fold Equity / Walkover Performance
- **Fold Equity**: 58.6%
- **Walkover Wins**: 29,260 (8.8% of all walkovers)
- **Mean Walkover Pot**: 15.5 chips

### Personality Fidelity
- **Fidelity Score**: 99.1% (24,569/24,801 windows in-range) — HIGHEST

### Ecological Footprint
- **Footprint Score**: 0.0222 (moderate impact)

### Information Dynamics
- **Trust Delta per Hand**: 0.0530 (moderate information generation)
- **Information Role**: CATALYST — moderately consumes trust information while generating its own signal

### Pot Involvement
- **Hands Involved In**: 128,243 (of 500,000)
- **Mean Pot When Involved**: 31.8 chips
- **Max Pot**: 212 chips

### Adaptive Behavior
The Mirror's mimicry mechanism:
1. Tracks per-opponent stats via `_observe_opponent_action` (VPIP, BR, CR per opponent)
2. At decision time, identifies the opponent with the most observed actions
3. Blends its default parameters toward the most-active opponent's observed metrics
4. The blend is gradual — the Mirror never fully becomes another archetype

### Trust Signature
Mirror's trust signature is nearly identical to Judge's (min_dist=0.033),
making them the most redundant pair in the trust model. Both fall within the
sentinel/mirror/judge ambiguity cluster.
