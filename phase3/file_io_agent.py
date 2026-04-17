"""
Phase 3 — File I/O Agent for Claude Code Orchestration

Agents whose decide_action communicates via files, allowing Claude Code
to act as the LLM backend. The engine runs in a background process:

1. Agent hits a decision point → writes game state to request file
2. Agent polls for response file
3. Claude Code reads request, decides (via sub-agent), writes response
4. Agent picks up response and returns the action

This avoids external API calls entirely — Claude Code's own inference
handles every decision, using its subscription rather than per-call billing.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from treys import Card as TreysCard

from agents.base_agent import BaseAgent
from engine.actions import ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState

__all__ = ["FileIOAgent", "FileIOJudge"]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
IPC_DIR = Path("/tmp/phase3_ipc")
REQUEST_FILE = IPC_DIR / "request.json"
RESPONSE_FILE = IPC_DIR / "response.json"
READY_FILE = IPC_DIR / "request_ready"
DONE_FILE = IPC_DIR / "response_done"
GAME_OVER_FILE = IPC_DIR / "game_over"


def _ensure_ipc_dir():
    IPC_DIR.mkdir(parents=True, exist_ok=True)
    for f in [REQUEST_FILE, RESPONSE_FILE, READY_FILE, DONE_FILE, GAME_OVER_FILE]:
        if f.exists():
            f.unlink()


# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------

def _card_str(card_int: int) -> str:
    return TreysCard.int_to_str(card_int)

def _cards_str(cards: list) -> str:
    if not cards:
        return "none"
    return " ".join(_card_str(c) for c in cards)


# ---------------------------------------------------------------------------
# FileIOAgent
# ---------------------------------------------------------------------------

class FileIOAgent(BaseAgent):
    """Agent that pauses at each decision and waits for a file-based response."""

    def __init__(
        self,
        seat: int,
        name: str,
        archetype: str,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype=archetype, seat=seat, rng=rng)

    def decide_action(self, game_state: GameState) -> ActionType:
        rng = self.rng or np.random.default_rng()

        # Compute hand strength (cached per street)
        round_key = game_state.betting_round
        hs = self._hs_cache.get(round_key)
        if hs is None:
            hs = get_hand_strength(
                self.hole_cards,
                game_state.community_cards,
                rng=rng,
                num_samples=50,
            )
            self._hs_cache[round_key] = hs

        # Build request
        hole_str = _cards_str(self.hole_cards) if self.hole_cards else "unknown"
        community_str = _cards_str(game_state.community_cards)

        actions_this_round = []
        for a in (game_state.actions_this_round or []):
            actions_this_round.append({
                "seat": a.seat,
                "archetype": a.archetype,
                "action": a.action_type.value,
            })

        request = {
            "seat": self.seat,
            "name": self.name,
            "archetype": self.archetype,
            "hand_id": game_state.hand_id,
            "street": game_state.betting_round,
            "hole_cards": hole_str,
            "community_cards": community_str,
            "hand_strength": hs,
            "pot_size": game_state.pot_size,
            "cost_to_call": game_state.cost_to_call,
            "bet_count": game_state.bet_count,
            "bet_cap": game_state.bet_cap,
            "bet_size": game_state.bet_size,
            "player_stack": game_state.player_stack,
            "num_active_players": game_state.num_active_players,
            "player_position": game_state.player_position,
            "actions_this_round": actions_this_round,
        }

        # Write request and signal ready
        with open(REQUEST_FILE, "w") as f:
            json.dump(request, f)
        READY_FILE.touch()

        # Poll for response (Claude Code will write it)
        timeout = 300  # 5 minute timeout per decision
        start = time.time()
        while not DONE_FILE.exists():
            if time.time() - start > timeout:
                # Timeout — fallback to check/fold
                return ActionType.CHECK if game_state.cost_to_call == 0 else ActionType.FOLD
            time.sleep(0.05)

        # Read response
        try:
            with open(RESPONSE_FILE, "r") as f:
                resp = json.load(f)
            action_str = resp.get("action", "fold").lower()
        except (json.JSONDecodeError, FileNotFoundError):
            action_str = "fold"
        finally:
            # Clean up for next request (use missing_ok to avoid race conditions)
            try:
                DONE_FILE.unlink(missing_ok=True)
            except TypeError:
                # Python < 3.8 fallback
                if DONE_FILE.exists():
                    DONE_FILE.unlink()
            try:
                READY_FILE.unlink(missing_ok=True)
            except TypeError:
                if READY_FILE.exists():
                    READY_FILE.unlink()

        # Parse action
        action_map = {
            "fold": ActionType.FOLD,
            "check": ActionType.CHECK,
            "call": ActionType.CALL,
            "bet": ActionType.BET,
            "raise": ActionType.RAISE,
        }
        action = action_map.get(action_str, ActionType.FOLD)

        # Legality fix
        if game_state.cost_to_call == 0:
            if action in (ActionType.FOLD, ActionType.CALL):
                action = ActionType.CHECK
            elif action == ActionType.RAISE:
                action = ActionType.BET
        else:
            if action == ActionType.CHECK:
                action = ActionType.FOLD
            elif action == ActionType.BET:
                action = ActionType.RAISE if game_state.bet_count < game_state.bet_cap else ActionType.CALL
            elif action == ActionType.RAISE and game_state.bet_count >= game_state.bet_cap:
                action = ActionType.CALL

        return action

    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return {}


# ---------------------------------------------------------------------------
# FileIOJudge — adds grievance tracking
# ---------------------------------------------------------------------------

class FileIOJudge(FileIOAgent):
    """File IO agent with Judge's grievance/retaliation mechanic."""

    JUDGE_TAU = 5

    def __init__(self, seat: int, name: str = "LLM-Judge",
                 rng: Optional[np.random.Generator] = None) -> None:
        super().__init__(seat=seat, name=name, archetype="judge", rng=rng)
        self.grievance: Dict[int, int] = {}
        self.triggered: Dict[int, bool] = {}
        self._bluff_candidates: Dict[int, List[str]] = {}

    def on_hand_start(self, hand_id: int) -> None:
        super().on_hand_start(hand_id)
        self._bluff_candidates = {}

    def _observe_opponent_action(self, record) -> None:
        if self._folded_this_hand:
            return
        if record.action_type not in (ActionType.BET, ActionType.RAISE):
            return
        self._bluff_candidates.setdefault(record.seat, []).append(
            record.betting_round
        )

    def observe_showdown(self, showdown_data, community_cards=None) -> None:
        super().observe_showdown(showdown_data, community_cards=community_cards)
        if not showdown_data or not community_cards:
            return
        from agents.base_agent import _community_slice_for_round, _fast_bucket
        for entry in showdown_data:
            seat = entry["seat"]
            if seat == self.seat:
                continue
            hole = entry.get("hole_cards")
            if not hole:
                continue
            rounds = self._bluff_candidates.get(seat)
            if not rounds:
                continue
            for round_name in rounds:
                board = _community_slice_for_round(community_cards, round_name)
                bucket = _fast_bucket(hole, board, rng=self.rng)
                if bucket == "Weak":
                    new_count = self.grievance.get(seat, 0) + 1
                    self.grievance[seat] = new_count
                    if new_count >= self.JUDGE_TAU and not self.triggered.get(seat, False):
                        self.triggered[seat] = True
                    break

    def grievance_summary(self):
        out = []
        for seat in sorted(self.grievance):
            out.append((seat, self.grievance[seat],
                        bool(self.triggered.get(seat, False)), None))
        return out
