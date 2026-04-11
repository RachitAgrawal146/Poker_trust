"""Bayesian trust model (Stage 5).

Every agent maintains a posterior distribution over the 8 archetype types
for every other seat it has observed. The model is updated on two signals:

1. Every observed action (live, bucket unknown) — marginal likelihood.
2. Showdown reveals — the opponent's hole cards + community cards let us
   pin down their hand-strength bucket and apply a sharpened update.

See ``trust.bayesian_model`` for the math and ``worked_examples.md`` for a
walkthrough with real numbers.
"""

from trust.bayesian_model import (
    initial_posterior,
    update_posterior,
    decay_posterior,
    trust_score,
    entropy,
    posterior_to_dict,
    dict_to_posterior,
    TRUST_TYPE_LIST,
)

__all__ = [
    "initial_posterior",
    "update_posterior",
    "decay_posterior",
    "trust_score",
    "entropy",
    "posterior_to_dict",
    "dict_to_posterior",
    "TRUST_TYPE_LIST",
]
