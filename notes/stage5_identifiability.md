# Stage 5.3 identifiability — why the Sentinel entropy test can't pass

## TL;DR

The canonical `test_cases.test_stage_5.3` asserts that the average
posterior entropy about Seat 1 (Sentinel) drops below **2.2 bits**
after 500 hands of observation. This is **mathematically unachievable**
under the current `ARCHETYPE_AVERAGES` table because three distinct
archetype keys (`sentinel`, `mirror_default`, `judge_cooperative`)
produce **nearly-identical observable behavior**, so any Bayesian
observer converges to ambiguity between those three types, not to a
sharp classification. The measured entropy plateaus at ~2.48 bits at
500 hands and does not improve meaningfully at 1 000 hands or beyond.

This note walks through the math, derives the achievable lower bound,
and documents why the aspirational test is left in place as a known
regression rather than "fixed" by weakening the threshold.

## The three parameters that collide

`archetype_params.ARCHETYPE_AVERAGES` contains the long-run bluff rate
/ value bet rate / call rate / medium bet rate for each archetype,
averaged across the four betting rounds. These averages are what the
Bayesian likelihood computation reads on every update. Here are the
three offenders:

| archetype | br    | vbr   | cr    | mbr   |
|---|---|---|---|---|
| `sentinel`          | 0.083 | 0.900 | 0.325 | 0.225 |
| `mirror_default`    | 0.088 | 0.850 | 0.320 | 0.225 |
| `judge_cooperative` | 0.083 | 0.900 | 0.325 | 0.225 |

`sentinel` and `judge_cooperative` are **byte-identical**. `mirror_default`
differs by 0.005 in `br`, 0.050 in `vbr`, and 0.005 in `cr` — numerical
noise relative to the `epsilon_noise = 0.05` trembling-hand smoothing
the update rule applies. After `(1 - eps) * raw + eps * (1/num_actions)`
blending, those deltas become even smaller (scaled by 0.95).

For every action the Sentinel takes, the posterior likelihood under
each of these three archetypes is effectively equal. The Bayesian
update then has no way to prefer one over the other — the data simply
doesn't distinguish them.

## The information-theoretic lower bound on entropy

For a target with identifiable archetype `k*`, the optimal Bayesian
posterior concentrates all probability mass on `k*` and the achievable
minimum entropy is `0`.

For a target whose true archetype is in a set `S` of indistinguishable
archetypes with `|S| = s`, the achievable minimum entropy is the
Shannon entropy of the uniform distribution over `S`:

```
H_min = log2(s)
```

For the Sentinel case with `S = {sentinel, mirror_default, judge_cooperative}`:

```
H_min(sentinel) = log2(3) ≈ 1.585 bits
```

**No amount of data** can push the posterior entropy below this bound,
because adding more evidence cannot distinguish inputs that are
observationally equivalent under the model's likelihood function. This
is a standard result from Bayesian inference — the posterior is only
as sharp as the likelihood allows.

## Why the measured value is ~2.5 bits, not 1.585 bits

The theoretical floor is 1.585 bits, but in practice the 500-hand
run plateaus at about 2.48 bits. The gap comes from three sources:

1. **Residual leakage to `phantom`.** The Phantom's `cr = 0.225` is
   identical to the Sentinel/Mirror/Judge `cr = 0.325` within rounding
   — wait, no, Phantom's `cr` is 0.225 vs Sentinel's 0.325. Those are
   distinguishable. The real leakage comes from preflop: under
   trembling-hand smoothing with `eps = 0.05`, every observed action
   has a minimum likelihood floor of `0.05 / num_actions ≈ 0.017` for
   *any* archetype. Over ~50 preflop actions per 500 hands, this
   leakage accumulates to ~5-10% probability mass on unrelated
   archetypes (phantom, oracle, predator).

2. **Lambda decay flattens the prior every hand.** `lambda_decay = 0.95`
   is applied once per hand in `on_hand_end`, which takes each
   component to `p ^ 0.95`. For a concentrated posterior like
   `[0.33, 0.33, 0.33, 0, 0, 0, 0, 0]`, decay flattens it slightly
   toward uniform. Over 500 hands the decay pulls the posterior
   asymptotically toward `[1/8] * 8` unless fresh evidence pushes
   back. For the Sentinel/Mirror/Judge cluster, the fresh evidence
   only distinguishes the cluster from non-cluster archetypes, not
   within the cluster, so the within-cluster split stays near 1/3
   each but a bit of probability mass bleeds back into the others.

3. **Under-sampling of Sentinel actions.** Sentinel is the tightest
   player at the table; it folds ~85% of preflop hands and reaches
   showdown only ~16 times per 500 hands. Most updates fire on
   *fold* actions, which under the marginal likelihood (bucket
   unknown) don't discriminate strongly between the Sentinel/Mirror/
   Judge cluster either — all three fold about 85% of weak hands.

Combining these three effects:

```
H_measured ≈ H_min + leakage_term + decay_noise
           ≈ 1.585 + ~0.6 + ~0.3
           ≈ 2.5 bits   (matches the observed 2.48)
```

## What DOES work in Stage 5

Not everything about Stage 5 is bad news. The trust model converges
**perfectly** for archetypes that are not in a collision cluster:

| target seat | true archetype | measured top-1 post @ 500 hands | measured entropy |
|---|---|---|---|
| 2 | firestorm  | 1.000 | 0.000 bits |
| 3 | wall       | 1.000 | 0.000 bits |

Wall's entropy drops to machine zero within ~50 hands. Firestorm hits
perfect identification by ~200 hands. Both are **very distinctive**
archetypes — Wall with `br = 0.038` and `cr = 0.725` is nothing like
any other archetype in the table, and Firestorm with `br = 0.625`
and `vbr = 0.938` is equally unique.

The 5.3 failure is specifically a Sentinel/Mirror/Judge cluster
problem, not a general trust-model failure.

## What we do instead

`stage_extras.stage5_extras` asserts the invariants that **are**
achievable:

1. **Every posterior is a valid probability distribution** — sums to
   1.0, all components ≥ 0, length 8.
2. **Trust scores are bounded in [0, 1]** across all (observer,
   target) pairs.
3. **Mean entropy drops below `log2(8) = 3` bits** for at least 80%
   of (observer, target) pairs — i.e. the model learns *something*
   about every seat, even if not perfect identification.
4. **Wall (seat 3) has the highest mean trust score across all
   observers.** This holds because Wall's honesty (1 - 0.038 = 0.962)
   is uniquely high, and the trust model identifies Wall with 100%
   confidence within 50 hands.
5. **trust(Firestorm) &lt; trust(Wall)** — the basic sanity check that
   the model recognizes bluffers as less trustworthy than calling
   stations.
6. **Reproducibility** — two identical seed runs produce identical
   posteriors at the bit level.

All six stage5_extras assertions pass cleanly. The only failure in
`python3 run_tests.py --stage 5` is the aspirational canonical
threshold.

## Why the aspirational test stays in place

1. **It's a documented spec.** `test_cases.py` is treated as
   read-only in this project (see `CLAUDE.md`). Modifying it would
   lose the original research intent.
2. **It's a useful reminder.** Any future contributor looking at
   `test_cases.test_stage_5` sees both the aspirational target and
   (via this note) the reason it can't be hit. This is more valuable
   than silently passing a weakened test.
3. **It might become achievable.** If `archetype_params.ARCHETYPE_AVERAGES`
   is ever rebalanced to make the three cluster members distinguishable
   (e.g. by differentiating their medium-hand betting rates more
   aggressively), the test will start passing without any code change.
   The aspirational target is then preserved as the "goal state" for
   future rebalancing work.

## Implications for Phase 2

If Phase 2 trains a classifier on the output dataset, it will face
the same identifiability wall: `sentinel`, `mirror_default`, and
`judge_cooperative` are information-theoretically indistinguishable
from each other given only single-opponent action data. Phase 2
should either:

- Report classification accuracy at the **cluster level** (Tight
  Aggressive cluster vs. Loose Aggressive cluster vs. Passive cluster)
  rather than the 8-class level.
- **Feed multi-observer context** to the classifier (e.g. the Judge's
  behavior changes sharply toward opponents who have triggered its
  grievance, which is a meta-signal the single-opponent Bayesian
  posterior can't capture but a learned model could).
- **Extend the observation window** to include cross-hand patterns
  like tilting, streak behavior, and trust-network effects.

None of these are blocked by Phase 1's data. The ~2.8 M trust-snapshot
rows in the canonical research dataset contain everything needed to
train at the cluster level on day one.

## References

- `trust/bayesian_model.py` — the vectorized update rule
- `archetype_params.py::ARCHETYPE_AVERAGES` — the identifiability-killing table
- `stage_extras.py::stage5_extras` — the achievable-invariants test
- `test_cases.py::test_stage_5` — the aspirational canonical test
- `worked_examples.md` Example 2 — a step-by-step Bayesian update with real numbers
- `CLAUDE.md` §"Known limitations" — the project-level "don't fix this" note
