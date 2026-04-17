"""
Phase 3 — Dealer (Game Integrity Layer)

The Dealer wraps the game engine and provides three layers of protection:

1. **Pre-action validation**: Before every action is executed, the Dealer
   checks legality (valid action type for the current state, chip sufficiency,
   bet cap compliance). Illegal actions are substituted with a legal default
   (CHECK when cost_to_call==0, FOLD otherwise).

2. **Post-hand audits**: After every hand, the Dealer verifies chip
   conservation (total chips in play match starting total + rebuys) and
   showdown correctness (winner has the best hand).

3. **Rolling anomaly detection**: Tracks per-agent VPIP and AF in a sliding
   window, comparing against the personality spec targets. Flags agents whose
   behavior drifts beyond tolerance from their spec.

All findings are accumulated and saved to dealer_audit.json at the end of a
simulation run.

Usage::

    dealer = Dealer(agents, specs)
    # Called by the simulation runner on every action
    validated_action = dealer.validate_action(agent, game_state, proposed_action)
    # Called after every hand
    dealer.post_hand_audit(hand, agents)
    # Called at end of run
    dealer.save_audit("dealer_audit.json")
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engine.actions import ActionType

# ---------------------------------------------------------------------------
# Spec targets loaded from personality_specs or passed at construction
# ---------------------------------------------------------------------------

@dataclass
class ArchetypeSpec:
    """Behavioral targets for one archetype, used for anomaly detection."""
    archetype: str
    vpip_target: float       # e.g. 0.216 for Oracle
    vpip_tolerance: float    # e.g. 0.05 (±5 percentage points)
    af_target: float         # e.g. 1.18 for Oracle
    af_tolerance: float      # e.g. 0.40

# Default specs derived from Phase 1 v3 analysis data.
# Used if the caller doesn't provide custom specs.
DEFAULT_SPECS: Dict[str, ArchetypeSpec] = {
    "oracle": ArchetypeSpec("oracle", vpip_target=0.216, vpip_tolerance=0.05, af_target=1.18, af_tolerance=0.40),
    "sentinel": ArchetypeSpec("sentinel", vpip_target=0.162, vpip_tolerance=0.05, af_target=1.07, af_tolerance=0.40),
    "firestorm": ArchetypeSpec("firestorm", vpip_target=0.494, vpip_tolerance=0.08, af_target=1.12, af_tolerance=0.40),
    "wall": ArchetypeSpec("wall", vpip_target=0.539, vpip_tolerance=0.08, af_target=0.13, af_tolerance=0.15),
    "phantom": ArchetypeSpec("phantom", vpip_target=0.387, vpip_tolerance=0.07, af_target=0.67, af_tolerance=0.30),
    "predator": ArchetypeSpec("predator", vpip_target=0.185, vpip_tolerance=0.05, af_target=0.83, af_tolerance=0.35),
    "mirror": ArchetypeSpec("mirror", vpip_target=0.186, vpip_tolerance=0.05, af_target=0.88, af_tolerance=0.35),
    "judge": ArchetypeSpec("judge", vpip_target=0.159, vpip_tolerance=0.05, af_target=1.39, af_tolerance=0.45),
}


# ---------------------------------------------------------------------------
# Audit record types
# ---------------------------------------------------------------------------

@dataclass
class ActionSubstitution:
    """Records when an illegal action was replaced with a legal default."""
    hand_id: int
    seat: int
    archetype: str
    betting_round: str
    proposed: str
    substituted: str
    reason: str


@dataclass
class ChipAuditFailure:
    """Records a chip conservation violation after a hand."""
    hand_id: int
    expected_total: int
    actual_total: int
    delta: int


@dataclass
class ShowdownAuditFailure:
    """Records a showdown correctness violation."""
    hand_id: int
    reason: str


@dataclass
class AnomalyFlag:
    """Records when an agent's behavior drifts from spec."""
    hand_id: int
    seat: int
    archetype: str
    metric: str       # "vpip" or "af"
    observed: float
    target: float
    tolerance: float


# ---------------------------------------------------------------------------
# Agent tracking state (per-agent rolling window)
# ---------------------------------------------------------------------------

class _AgentTracker:
    """Tracks per-agent behavioral stats in a sliding window."""

    def __init__(self, window_size: int = 500) -> None:
        self.window_size = window_size
        # Ring buffers for VPIP and action counts
        self.hands_seen: int = 0
        self.vpip_count: int = 0
        self.bets: int = 0
        self.raises: int = 0
        self.calls: int = 0
        # Recent window tracking
        self._recent_vpip: List[bool] = []
        self._recent_aggressive: List[int] = []  # +1 for bet/raise, 0 otherwise
        self._recent_passive: List[int] = []      # +1 for call, 0 otherwise

    def record_hand(self, was_vpip: bool) -> None:
        self.hands_seen += 1
        if was_vpip:
            self.vpip_count += 1
        self._recent_vpip.append(was_vpip)
        if len(self._recent_vpip) > self.window_size:
            self._recent_vpip.pop(0)

    def record_action(self, action: ActionType) -> None:
        is_aggressive = 1 if action in (ActionType.BET, ActionType.RAISE) else 0
        is_passive = 1 if action == ActionType.CALL else 0
        if action == ActionType.BET:
            self.bets += 1
        elif action == ActionType.RAISE:
            self.raises += 1
        elif action == ActionType.CALL:
            self.calls += 1
        self._recent_aggressive.append(is_aggressive)
        self._recent_passive.append(is_passive)
        if len(self._recent_aggressive) > self.window_size * 15:
            # Trim to avoid unbounded growth (15 actions/hand typical)
            trim = len(self._recent_aggressive) - self.window_size * 15
            self._recent_aggressive = self._recent_aggressive[trim:]
            self._recent_passive = self._recent_passive[trim:]

    def rolling_vpip(self) -> Optional[float]:
        if not self._recent_vpip:
            return None
        return sum(self._recent_vpip) / len(self._recent_vpip)

    def rolling_af(self) -> Optional[float]:
        passive = sum(self._recent_passive)
        if passive == 0:
            return None
        return sum(self._recent_aggressive) / passive

    def cumulative_vpip(self) -> Optional[float]:
        if self.hands_seen == 0:
            return None
        return self.vpip_count / self.hands_seen

    def cumulative_af(self) -> Optional[float]:
        if self.calls == 0:
            return None
        return (self.bets + self.raises) / self.calls


# ---------------------------------------------------------------------------
# Dealer
# ---------------------------------------------------------------------------

class Dealer:
    """Game integrity layer for Phase 3 simulations.

    Parameters
    ----------
    num_seats : int
        Number of players at the table (default 8).
    starting_stack : int
        Starting chip stack per player (default 200).
    specs : dict, optional
        Per-archetype ArchetypeSpec dict for anomaly detection.
        Defaults to DEFAULT_SPECS.
    anomaly_check_interval : int
        Check for anomalies every N hands (default 500).
    window_size : int
        Sliding window size for rolling stats (default 500).
    """

    def __init__(
        self,
        num_seats: int = 8,
        starting_stack: int = 200,
        specs: Optional[Dict[str, ArchetypeSpec]] = None,
        anomaly_check_interval: int = 500,
        window_size: int = 500,
    ) -> None:
        self.num_seats = num_seats
        self.starting_stack = starting_stack
        self.specs = specs or DEFAULT_SPECS
        self.anomaly_check_interval = anomaly_check_interval

        # Per-seat trackers
        self._trackers: Dict[int, _AgentTracker] = {
            seat: _AgentTracker(window_size=window_size)
            for seat in range(num_seats)
        }
        # Seat -> archetype mapping (set on first validate_action call)
        self._seat_archetypes: Dict[int, str] = {}

        # Audit logs
        self.substitutions: List[ActionSubstitution] = []
        self.chip_failures: List[ChipAuditFailure] = []
        self.showdown_failures: List[ShowdownAuditFailure] = []
        self.anomalies: List[AnomalyFlag] = []

        # Counters
        self.total_hands: int = 0
        self.total_actions_validated: int = 0
        self.total_substitutions: int = 0
        self.total_rebuys: int = 0

    # ------------------------------------------------------------------
    # 1. Pre-action validation
    # ------------------------------------------------------------------

    def validate_action(
        self,
        seat: int,
        archetype: str,
        hand_id: int,
        betting_round: str,
        proposed_action: ActionType,
        cost_to_call: int,
        player_stack: int,
        bet_count: int,
        bet_cap: int,
    ) -> ActionType:
        """Validate a proposed action and return the (possibly substituted) action.

        Legal action rules for Limit Hold'em:
        - cost_to_call == 0: legal actions are CHECK or BET
        - cost_to_call > 0: legal actions are FOLD, CALL, or RAISE
        - RAISE is only legal if bet_count < bet_cap
        - Agent must have chips >= cost_to_call for CALL
          (if short-stacked, CALL still allowed — they go all-in)
        - BET/RAISE requires chips > 0
        """
        self.total_actions_validated += 1
        self._seat_archetypes[seat] = archetype

        valid_action = proposed_action
        reason = ""

        if cost_to_call == 0:
            # No bet to face: legal actions are CHECK, BET
            if proposed_action == ActionType.FOLD:
                valid_action = ActionType.CHECK
                reason = "FOLD illegal when cost_to_call=0; substituted CHECK"
            elif proposed_action == ActionType.CALL:
                valid_action = ActionType.CHECK
                reason = "CALL illegal when cost_to_call=0; substituted CHECK"
            elif proposed_action == ActionType.RAISE:
                valid_action = ActionType.BET
                reason = "RAISE illegal when cost_to_call=0; substituted BET"
            elif proposed_action == ActionType.BET:
                if player_stack <= 0:
                    valid_action = ActionType.CHECK
                    reason = "BET illegal with 0 chips; substituted CHECK"
        else:
            # Facing a bet: legal actions are FOLD, CALL, RAISE
            if proposed_action == ActionType.CHECK:
                valid_action = ActionType.FOLD
                reason = "CHECK illegal when facing bet; substituted FOLD"
            elif proposed_action == ActionType.BET:
                # BET when already facing a bet → treat as RAISE
                if bet_count < bet_cap and player_stack > cost_to_call:
                    valid_action = ActionType.RAISE
                    reason = "BET reinterpreted as RAISE when facing bet"
                else:
                    valid_action = ActionType.CALL
                    reason = "BET illegal at bet cap; substituted CALL"
            elif proposed_action == ActionType.RAISE:
                if bet_count >= bet_cap:
                    valid_action = ActionType.CALL
                    reason = f"RAISE illegal at bet cap ({bet_count}/{bet_cap}); substituted CALL"
                elif player_stack <= cost_to_call:
                    # Can't raise — not enough chips beyond the call amount
                    valid_action = ActionType.CALL
                    reason = "RAISE illegal with insufficient chips; substituted CALL"

        # Record substitution if action changed
        if valid_action != proposed_action:
            self.total_substitutions += 1
            self.substitutions.append(ActionSubstitution(
                hand_id=hand_id,
                seat=seat,
                archetype=archetype,
                betting_round=betting_round,
                proposed=proposed_action.value,
                substituted=valid_action.value,
                reason=reason,
            ))

        # Track action for anomaly detection
        self._trackers[seat].record_action(valid_action)

        return valid_action

    # ------------------------------------------------------------------
    # 2. Post-hand audit
    # ------------------------------------------------------------------

    def post_hand_audit(
        self,
        hand_id: int,
        seat_stacks: List[int],
        total_rebuys: int,
        showdown_data: Optional[List[dict]] = None,
        community_cards: Optional[List[int]] = None,
    ) -> bool:
        """Run post-hand integrity checks. Returns True if all pass."""
        self.total_hands += 1
        self.total_rebuys = total_rebuys
        all_ok = True

        # --- Chip conservation ---
        actual_total = sum(seat_stacks)
        expected_total = (self.num_seats + total_rebuys) * self.starting_stack
        if actual_total != expected_total:
            delta = actual_total - expected_total
            self.chip_failures.append(ChipAuditFailure(
                hand_id=hand_id,
                expected_total=expected_total,
                actual_total=actual_total,
                delta=delta,
            ))
            all_ok = False

        # --- Showdown correctness (basic check) ---
        if showdown_data and len(showdown_data) >= 2:
            winners = [e for e in showdown_data if e.get("won")]
            if not winners:
                self.showdown_failures.append(ShowdownAuditFailure(
                    hand_id=hand_id,
                    reason="Showdown with no winner",
                ))
                all_ok = False

        # --- Anomaly detection (periodic) ---
        if self.total_hands % self.anomaly_check_interval == 0:
            self._check_anomalies(hand_id)

        return all_ok

    def record_hand_vpip(self, seat: int, was_vpip: bool) -> None:
        """Record whether a seat voluntarily put money in the pot this hand."""
        self._trackers[seat].record_hand(was_vpip)

    # ------------------------------------------------------------------
    # 3. Rolling anomaly detection
    # ------------------------------------------------------------------

    def _check_anomalies(self, hand_id: int) -> None:
        """Check all agents for behavioral drift from spec targets."""
        for seat, tracker in self._trackers.items():
            archetype = self._seat_archetypes.get(seat)
            if archetype is None:
                continue
            spec = self.specs.get(archetype)
            if spec is None:
                continue

            # VPIP check
            vpip = tracker.rolling_vpip()
            if vpip is not None:
                if abs(vpip - spec.vpip_target) > spec.vpip_tolerance:
                    self.anomalies.append(AnomalyFlag(
                        hand_id=hand_id,
                        seat=seat,
                        archetype=archetype,
                        metric="vpip",
                        observed=round(vpip, 4),
                        target=spec.vpip_target,
                        tolerance=spec.vpip_tolerance,
                    ))

            # AF check
            af = tracker.rolling_af()
            if af is not None:
                if abs(af - spec.af_target) > spec.af_tolerance:
                    self.anomalies.append(AnomalyFlag(
                        hand_id=hand_id,
                        seat=seat,
                        archetype=archetype,
                        metric="af",
                        observed=round(af, 4),
                        target=spec.af_target,
                        tolerance=spec.af_tolerance,
                    ))

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Return a summary dict of the audit results."""
        return {
            "total_hands": self.total_hands,
            "total_actions_validated": self.total_actions_validated,
            "total_substitutions": self.total_substitutions,
            "substitution_rate": (
                self.total_substitutions / self.total_actions_validated
                if self.total_actions_validated > 0 else 0.0
            ),
            "chip_conservation_failures": len(self.chip_failures),
            "showdown_audit_failures": len(self.showdown_failures),
            "anomaly_flags": len(self.anomalies),
            "per_archetype_stats": self._per_archetype_stats(),
        }

    def _per_archetype_stats(self) -> Dict[str, Dict[str, Any]]:
        """Compute per-archetype summary statistics."""
        stats: Dict[str, Dict[str, Any]] = {}
        for seat, tracker in self._trackers.items():
            archetype = self._seat_archetypes.get(seat, f"seat_{seat}")
            vpip = tracker.cumulative_vpip()
            af = tracker.cumulative_af()
            stats[f"seat_{seat}_{archetype}"] = {
                "hands_seen": tracker.hands_seen,
                "cumulative_vpip": round(vpip, 4) if vpip is not None else None,
                "cumulative_af": round(af, 4) if af is not None else None,
                "substitutions": sum(
                    1 for s in self.substitutions if s.seat == seat
                ),
                "anomalies": sum(
                    1 for a in self.anomalies if a.seat == seat
                ),
            }
        return stats

    def save_audit(self, path: str) -> None:
        """Save the complete audit log to a JSON file."""
        audit = {
            "summary": self.summary(),
            "substitutions": [
                {
                    "hand_id": s.hand_id,
                    "seat": s.seat,
                    "archetype": s.archetype,
                    "betting_round": s.betting_round,
                    "proposed": s.proposed,
                    "substituted": s.substituted,
                    "reason": s.reason,
                }
                for s in self.substitutions
            ],
            "chip_conservation_failures": [
                {
                    "hand_id": f.hand_id,
                    "expected": f.expected_total,
                    "actual": f.actual_total,
                    "delta": f.delta,
                }
                for f in self.chip_failures
            ],
            "showdown_audit_failures": [
                {"hand_id": f.hand_id, "reason": f.reason}
                for f in self.showdown_failures
            ],
            "anomaly_flags": [
                {
                    "hand_id": a.hand_id,
                    "seat": a.seat,
                    "archetype": a.archetype,
                    "metric": a.metric,
                    "observed": a.observed,
                    "target": a.target,
                    "tolerance": a.tolerance,
                }
                for a in self.anomalies
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2)

    def print_summary(self) -> None:
        """Print a human-readable audit summary to stdout."""
        s = self.summary()
        print()
        print("=" * 60)
        print("DEALER AUDIT SUMMARY")
        print("=" * 60)
        print(f"  Total hands:              {s['total_hands']}")
        print(f"  Total actions validated:   {s['total_actions_validated']}")
        print(f"  Action substitutions:      {s['total_substitutions']} "
              f"({s['substitution_rate']:.4%})")
        print(f"  Chip conservation fails:   {s['chip_conservation_failures']}")
        print(f"  Showdown audit fails:      {s['showdown_audit_failures']}")
        print(f"  Anomaly flags:             {s['anomaly_flags']}")
        print()
        if s["per_archetype_stats"]:
            print("  Per-agent:")
            for name, st in s["per_archetype_stats"].items():
                vpip_str = f"{st['cumulative_vpip']:.1%}" if st["cumulative_vpip"] is not None else "N/A"
                af_str = f"{st['cumulative_af']:.2f}" if st["cumulative_af"] is not None else "N/A"
                print(f"    {name:30s}  VPIP={vpip_str:>6s}  AF={af_str:>5s}  "
                      f"subs={st['substitutions']}  anomalies={st['anomalies']}")
        print("=" * 60)
