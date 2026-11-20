# R1 rule-based experiments: analysis plan

Fixed before the full runs. The commit that adds this file also adds the code;
the full run is launched by a later commit that only changes
`r1_plan.json`. Nothing below changes after that commit except to record
technical failures and reruns.

## Question

In the earlier runs the archetype that others trusted most earned least. Two
explanations are possible. (1) Playing style: the trusted archetypes are the
passive or tight ones, and they lose to aggressive ones whoever is watching.
(2) Reputation: opponents use what they have inferred about a player against
that player. The earlier roster cannot separate them, because only one of
eight agents ever consults its posterior. These runs separate them.

## Design

Rule-based agents only. Three layers.

* **Style only (`no_read`).** No agent's play depends on what it has inferred
  about anyone. Any profit gap is playing style.
* **Reading switched on in one controlled way.** A single response rule,
  identical for every agent (`r1_agents.py`): holding a Medium or Weak hand
  and facing a bet or raise, the agent multiplies its calling probability by
  `f = 1 + beta * (T_ref - T) / (1 - T_ref)`, where `T` is its trust score
  for the bettor and `T_ref` the trust score of the uniform prior. It calls
  more against players it believes bluff more than an unknown player and
  folds more against players it believes bluff less. Strong hands and raising
  probabilities are untouched; `beta = 0` is `no_read` exactly.
* **Controls with no correct reading**: a placebo that reads a random other
  seat, a matched loosening of the same calling probabilities, and random
  action noise.

| Condition | Definition | Purpose |
|---|---|---|
| `no_read` | Predator on its baseline table, Mirror on its default table, Judge never triggers | Style only |
| `published` | The earlier roster (Predator exploits, Mirror copies, Judge retaliates) | How much the earlier roster's own reading channels matter |
| `read_target_X_b10` (8) | `no_read` plus the rule at `beta = 1`, applied only to bets by archetype X | **Cost of being read**, per archetype |
| `read_all_b05`, `_b10`, `_b20` | Rule applied to every bettor, `beta` = 0.5, 1, 2 | The table when everyone reads everyone; dose-response |
| `read_true_b10` | Rule uses the bettor's true type instead of the posterior | Effect of inference error |
| `shuffled_b10` | Rule uses the trust score of a random other seat, redrawn each hand | Placebo: effects that need no correct attribution |
| `loose_matched_b10` | No reading; the same calling probabilities are multiplied by the mean factor that `read_all_b10` realised, by street and bucket | Rules out "the table simply calls more or less" |
| `noise_005`, `noise_010` | `no_read`, each decision replaced by a random legal action with probability 0.05 or 0.10 | Does noise alone weaken the trust-outcome association |
| `published_legacy`, `no_read_legacy` | The first two under the earlier protocol: 200-chip stacks with rebuys, fixed seat order | Continuity with the earlier runs; size of the protocol change |

Protocol for all other conditions: 100,000-chip stacks, so no seat can go
broke and there are no rebuys, all-ins or side pots; seat order permuted per
seed (derived from the seed); the trust model exactly as in the earlier runs;
current engine.

`loose_matched_b10` factors come from a pilot of `read_all_b10` on seeds 9001
and 9002 (2,500 hands each), which are not among the seeds below.

## Sample

20 seeds: 42, 137, 256, 512, 1024, 12666, 13927, 14942, 19277, 29004, 41939,
42908, 58556, 69218, 70875, 72385, 73280, 77153, 86890, 99769 (the list frozen
in `phase3/run_phase31_replication.py`). 10,000 hands per seed, 200,000 hands
per condition, 20 conditions. No interim looks. A seed is rerun only after a
technical failure, and that is logged in `research_data/r1/`.

## Outcomes and statistics

* **Outcome:** win rate, net chips per 100 hands, shown in big blinds
  (2 chips). Net chips of a hand is the stack after minus the stack before;
  every hand sums to zero. Final stack is not used as an outcome.
* **Unit of replication:** the seed. Every interval is a t-interval over the
  20 per-seed values. Contrasts against `no_read` are paired by seed.
* **Trust statistic:** the mean, over the seven observers, of the trust score
  held about a seat, averaged over snapshots taken every 100 hands after the
  first 500. The final-snapshot value used earlier is reported for continuity.
* **Primary quantity: cost of being read.** For archetype X, its win rate
  under `read_target_X_b10` minus its win rate under `no_read`. Eight
  two-sided paired t-tests, Holm-adjusted.
* **Primary summary:** the slope of the cost of being read on the archetype's
  non-bluff rate (the honesty score), fitted per seed over the eight
  archetypes, with a t-interval over seeds. A negative slope means the
  archetypes that bluff least lose most from being read; a positive slope
  means the archetypes that bluff most lose most.
* **Secondary:** per-condition Pearson and Spearman r between trust and win
  rate over the eight archetypes, per seed, summarised across seeds; win
  rates under `read_all` at the three strengths; each control against
  `read_all_b10` and `no_read`; showdown and non-showdown win rates; realised
  fold rates against each bettor.
* A correlation over eight hand-designed archetypes describes that design and
  nothing wider. It is reported as a description, not as a population
  estimate.

## What each outcome would mean

| Result | Reading |
|---|---|
| `no_read` shows the same negative trust-outcome association as `published` | The earlier association is playing style, not reputation |
| Cost of being read is larger for low-bluff archetypes (negative slope) | Being legible penalises the players who bluff least: the transparency paradox holds in this testbed |
| Cost of being read is larger for high-bluff archetypes (positive slope) | Reputation protects the players who bluff least; the paradox does not hold here |
| `shuffled_b10` reproduces the changes of `read_all_b10` | The changes do not depend on reading the right player |
| `loose_matched_b10` reproduces them | The changes are a general shift in calling frequency |
| `read_true_b10` differs from `read_all_b10` | Inference error in the posterior matters |
| Noise weakens the association in `no_read` | Unpredictable play alone can flatten the association |

## Known limits, stated in advance

* The trust model is the earlier one, unchanged. Its likelihood weights the
  three hand buckets equally when the hand is unknown.
* The response rule is one rule among many possible ones. The strength sweep
  and the controls describe this rule.
* Eight archetypes with hand-set tables; hand buckets from equity against one
  random hand.
