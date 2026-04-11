"""
The Predator — Exploiter / Shark.

The only archetype that actively consumes its own Bayesian posteriors to
modify play. Reads ``self.posteriors`` (populated by Stage 5) for every
currently active opponent, finds the one it is most confidently classified
about, and blends its per-round parameters from ``predator_baseline``
toward the target-type exploit table in ``PREDATOR_EXPLOIT``.

Blend rule (from spec §10.4 and Claude_Code_Implementation_Prompt.md):

    if max_post > 0.60:
        alpha = min(1.0, (max_post - 0.60) / 0.30)
        params = alpha * exploit + (1 - alpha) * baseline
    else:
        params = baseline

- At 60 % confidence, alpha = 0 (still baseline).
- At 90 % confidence, alpha = 1 (fully exploiting the target type).
- Multi-way pots: pick whichever active opponent yields the largest
  alpha. This is "attack the most classified opponent first", which
  aligns with the spec's "adjusts toward most exploitable opponent".
- Early in the sim (flat posteriors) the Predator plays baseline, which
  is near-Oracle (equilibrium-ish) with a slightly looser bluff profile.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from archetype_params import ARCHETYPE_PARAMS, PREDATOR_EXPLOIT
from config import NUM_PLAYERS
from engine.game import GameState
from trust import TRUST_TYPE_LIST

__all__ = ["Predator"]


# Classification and blend-slope constants. Kept as module-level so tests
# and sensitivity sweeps can reference them without instantiating an agent.
CLASSIFICATION_THRESHOLD = 0.60
ALPHA_DENOMINATOR = 0.30


class Predator(BaseAgent):
    BASELINE_PARAMS = ARCHETYPE_PARAMS["predator_baseline"]

    def __init__(
        self,
        seat: int,
        name: str = "The Predator",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype="predator", seat=seat, rng=rng)

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        baseline = self.BASELINE_PARAMS[betting_round]

        opponents = game_state.active_opponent_seats or []

        best_alpha = 0.0
        best_target: Optional[str] = None
        for opp_seat in opponents:
            post = self.posteriors.get(opp_seat)
            if post is None:
                continue
            max_idx = int(np.argmax(post))
            max_prob = float(post[max_idx])
            if max_prob <= CLASSIFICATION_THRESHOLD:
                continue
            alpha = min(1.0, (max_prob - CLASSIFICATION_THRESHOLD) / ALPHA_DENOMINATOR)
            if alpha > best_alpha:
                best_alpha = alpha
                best_target = TRUST_TYPE_LIST[max_idx]

        if best_target is None or best_alpha <= 0.0:
            return dict(baseline)

        exploit_round = PREDATOR_EXPLOIT.get(best_target, {}).get(betting_round, {})
        if not exploit_round:
            return dict(baseline)

        # Blend baseline → exploit. Only the 4 headline metrics
        # (br/vbr/cr/mbr) are listed in PREDATOR_EXPLOIT; the facing-bet
        # sub-keys (strong_raise, strong_call, med_raise, weak_call,
        # strong_fold) fall through from baseline unchanged. Without this,
        # the Predator would lose its "how to react to being raised"
        # policy when it started exploiting a target.
        blended = dict(baseline)
        for key, exploit_val in exploit_round.items():
            base_val = baseline.get(key, exploit_val)
            blended[key] = best_alpha * exploit_val + (1.0 - best_alpha) * base_val
        return blended
