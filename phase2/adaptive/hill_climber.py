"""
HillClimber -- bounded online hill-climbing optimizer for AdaptiveAgents.

Algorithm (per agent, run independently):

  Repeat:
      Phase = baseline. Run eval_window hands using current_params.
                       Record baseline_profit = windowed mean P/L.
                       Pick a random (round, metric); perturb by +/- delta.
                       Clamp to the archetype's bounds. Apply to agent.
      Phase = trial.    Run eval_window hands using perturbed params.
                       Record trial_profit = windowed mean P/L.
                       If trial_profit > baseline_profit:
                           accept (current_params <- perturbed)
                       else:
                           revert (agent params <- current_params)
                       Decay delta toward min_delta.

Two implementation notes the runner relies on:

  * "P/L this hand" comes from the runner, not from the agent. A rebuy
    is an external infusion of chips; the runner must pass the
    rebuy-adjusted stack delta so the climber doesn't reward the agent
    for going broke and being topped up.

  * For Judge, get_live_params() returns
    ``{"pre_trigger": ..., "post_trigger": ...}`` and
    ARCHETYPE_BOUNDS["judge"] mirrors that shape. The climber picks a
    state at random per cycle; both states optimize independently.

Logging: every cycle (regardless of accept/reject) appends one entry
to ``self.log``. The runner serializes the union of all climbers'
logs to optimization_log.json after the run.
"""

from __future__ import annotations

import sys as _sys
from copy import deepcopy
from pathlib import Path as _Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from phase2.adaptive.adaptive_agent import AdaptiveAgent, AdaptiveJudge  # noqa: E402
from phase2.adaptive.bounds import ARCHETYPE_BOUNDS  # noqa: E402

__all__ = ["HillClimber"]


_ROUNDS = ("preflop", "flop", "turn", "river")
_METRIC_KEYS = (
    "br", "vbr", "cr", "mbr",
    "strong_raise", "strong_call", "strong_fold",
    "med_raise", "weak_call",
)


class HillClimber:
    """Per-agent hill-climbing optimizer.

    Parameters
    ----------
    agent
        The AdaptiveAgent (or AdaptiveJudge) being optimized.
    eval_window
        Hands per phase (baseline OR trial). One full perturbation
        cycle takes 2 * eval_window hands.
    delta
        Initial perturbation magnitude (added to or subtracted from a
        single (round, metric) value per cycle).
    min_delta
        Floor for delta after geometric decay.
    decay_rate
        Per-cycle multiplier on delta. Applied at the end of each
        trial phase regardless of accept/reject.
    rng
        numpy Generator -- determines which parameter is perturbed and
        the sign. Pass a seeded generator for reproducibility.
    """

    def __init__(
        self,
        agent: AdaptiveAgent,
        eval_window: int = 200,
        delta: float = 0.03,
        min_delta: float = 0.005,
        decay_rate: float = 0.995,
        rng: Optional[np.random.Generator] = None,
        bounds: Optional[Dict[str, Any]] = None,
    ) -> None:
        if eval_window < 1:
            raise ValueError("eval_window must be >= 1")
        if delta <= 0 or min_delta <= 0:
            raise ValueError("delta values must be positive")
        if decay_rate <= 0 or decay_rate > 1:
            raise ValueError("decay_rate must be in (0, 1]")

        self.agent = agent
        self.eval_window = int(eval_window)
        self.delta = float(delta)
        self.min_delta = float(min_delta)
        self.decay_rate = float(decay_rate)
        self.rng = rng if rng is not None else np.random.default_rng()
        self.bounds = bounds if bounds is not None else ARCHETYPE_BOUNDS

        # Snapshot of the params we last measured a baseline against. If a
        # trial perturbation is rejected, the agent's params revert to this.
        self._current_params: Any = deepcopy(self.agent.get_live_params())

        # Phase machinery.
        self._phase: str = "baseline"  # "baseline" or "trial"
        self._phase_profits: List[float] = []
        self._baseline_profit: Optional[float] = None
        self._cycle_index: int = 0  # increments every full cycle

        # Per-cycle perturbation context (set when transitioning baseline -> trial)
        self._trial_state_key: Optional[str] = None  # judge only; "pre_trigger" / "post_trigger"
        self._trial_round: Optional[str] = None
        self._trial_metric: Optional[str] = None
        self._trial_old_value: Optional[float] = None
        self._trial_new_value: Optional[float] = None
        self._trial_delta_used: Optional[float] = None  # signed

        # Public log; runner serializes after the run.
        self.log: List[Dict[str, Any]] = []

        # Take an initial snapshot at hand 0 so trajectory plots include
        # the starting point.
        self.agent.record_snapshot(0)

    # ------------------------------------------------------------------
    # Hook called by the runner after every hand.
    # ------------------------------------------------------------------
    def on_hand_end(self, hand_number: int, hand_profit: float) -> None:
        self._phase_profits.append(float(hand_profit))

        if len(self._phase_profits) < self.eval_window:
            return

        windowed_mean = sum(self._phase_profits) / len(self._phase_profits)

        if self._phase == "baseline":
            self._baseline_profit = windowed_mean
            # Re-snapshot current params so the revert path is exact.
            self._current_params = deepcopy(self.agent.get_live_params())
            self._perturb_random_param()
            self._phase = "trial"
            self._phase_profits = []
            return

        # Trial phase complete.
        trial_profit = windowed_mean
        accepted = trial_profit > (self._baseline_profit or 0.0)

        if accepted:
            # Lock in the current (perturbed) params as the new baseline.
            self._current_params = deepcopy(self.agent.get_live_params())
        else:
            # Revert.
            self.agent.update_params(deepcopy(self._current_params))

        self.log.append(
            {
                "cycle": self._cycle_index,
                "hand_number": hand_number,
                "seat": self.agent.seat,
                "archetype": self.agent.archetype,
                "state_key": self._trial_state_key,  # None for non-Judge
                "round": self._trial_round,
                "metric": self._trial_metric,
                "old_value": self._trial_old_value,
                "new_value": self._trial_new_value,
                "delta_used": self._trial_delta_used,
                "baseline_profit": self._baseline_profit,
                "trial_profit": trial_profit,
                "accepted": accepted,
                "delta_at_cycle": self.delta,
            }
        )

        # Trajectory snapshot at end of every cycle.
        self.agent.record_snapshot(hand_number)

        # Decay delta and reset for next cycle.
        self.delta = max(self.min_delta, self.delta * self.decay_rate)
        self._cycle_index += 1
        self._phase = "baseline"
        self._phase_profits = []
        self._baseline_profit = None
        self._trial_state_key = None
        self._trial_round = None
        self._trial_metric = None
        self._trial_old_value = None
        self._trial_new_value = None
        self._trial_delta_used = None

    # ------------------------------------------------------------------
    # Internal helpers.
    # ------------------------------------------------------------------
    def _perturb_random_param(self) -> None:
        """Pick a random (state?, round, metric), perturb +/- delta,
        clamp to bounds, apply to the agent in place."""
        is_judge = isinstance(self.agent, AdaptiveJudge)

        if is_judge:
            state_key = "pre_trigger" if self.rng.random() < 0.5 else "post_trigger"
            round_name = _ROUNDS[int(self.rng.integers(0, len(_ROUNDS)))]
            metric = _METRIC_KEYS[int(self.rng.integers(0, len(_METRIC_KEYS)))]
            sign = 1.0 if self.rng.random() < 0.5 else -1.0
            signed_delta = sign * self.delta
            lo, hi = self.bounds["judge"][state_key][round_name][metric]
            live = self.agent.get_live_params()  # {pre_trigger:..., post_trigger:...}
            old = float(live[state_key][round_name][metric])
            new = max(lo, min(hi, old + signed_delta))
            live[state_key][round_name][metric] = new
            self._trial_state_key = state_key
        else:
            arch_key = _archetype_to_bounds_key(self.agent.archetype)
            round_name = _ROUNDS[int(self.rng.integers(0, len(_ROUNDS)))]
            metric = _METRIC_KEYS[int(self.rng.integers(0, len(_METRIC_KEYS)))]
            sign = 1.0 if self.rng.random() < 0.5 else -1.0
            signed_delta = sign * self.delta
            lo, hi = self.bounds[arch_key][round_name][metric]
            live = self.agent.get_live_params()  # flat per-round dict
            old = float(live[round_name][metric])
            new = max(lo, min(hi, old + signed_delta))
            live[round_name][metric] = new
            self._trial_state_key = None

        self._trial_round = round_name
        self._trial_metric = metric
        self._trial_old_value = old
        self._trial_new_value = new
        self._trial_delta_used = signed_delta

    # ------------------------------------------------------------------
    # Convenience for the runner / analysis.
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        accepted = sum(1 for e in self.log if e["accepted"])
        return {
            "seat": self.agent.seat,
            "archetype": self.agent.archetype,
            "cycles": self._cycle_index,
            "accepted": accepted,
            "rejected": self._cycle_index - accepted,
            "current_delta": self.delta,
        }


# ---------------------------------------------------------------------------
# archetype string -> bounds key
# ---------------------------------------------------------------------------
def _archetype_to_bounds_key(archetype: str) -> str:
    """Map BaseAgent.archetype string to ARCHETYPE_BOUNDS key.

    'predator' -> 'predator_baseline', 'mirror' -> 'mirror_default',
    everything else passes through (oracle, sentinel, firestorm,
    wall, phantom). 'judge' is handled separately by the climber."""
    if archetype == "predator":
        return "predator_baseline"
    if archetype == "mirror":
        return "mirror_default"
    return archetype
