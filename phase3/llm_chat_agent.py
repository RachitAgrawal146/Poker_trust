"""
Phase 3 — LLM Chat Agent

Each agent calls an LLM (Claude API or Ollama) on every decision point.
The LLM receives the game state as a structured prompt and returns one of:
FOLD, CHECK, CALL, BET, RAISE.

Supports two providers:
  - "anthropic": Claude via the Anthropic SDK (requires ANTHROPIC_API_KEY)
  - "ollama": Any local model via Ollama's OpenAI-compatible endpoint

The personality spec (from phase3/personality_specs/) is loaded as the
system prompt so each agent plays in character.

Usage::

    client = make_client("ollama", "llama3.1:8b")
    agent = LLMChatAgent(
        seat=0, name="LLM-Oracle", archetype="oracle",
        client=client, model="llama3.1:8b", provider="ollama",
    )
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from treys import Card as TreysCard

from agents.base_agent import BaseAgent
from engine.actions import ActionType
from engine.evaluator import get_hand_strength
from engine.game import GameState

__all__ = ["LLMChatAgent", "LLMChatJudge", "make_client"]

_SPECS_DIR = Path(__file__).resolve().parent / "personality_specs"

# ---------------------------------------------------------------------------
# Card rendering helpers
# ---------------------------------------------------------------------------

def _card_str(card_int: int) -> str:
    """Convert a treys int card to a readable string like 'As', 'Kh'."""
    return TreysCard.int_to_str(card_int)


def _cards_str(cards: list) -> str:
    """Convert a list of treys int cards to a readable string."""
    if not cards:
        return "none"
    return " ".join(_card_str(c) for c in cards)


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _load_personality_spec(archetype: str) -> str:
    """Load the qualitative personality section from the spec file."""
    spec_path = _SPECS_DIR / f"{archetype}.md"
    if not spec_path.exists():
        return f"You are a {archetype} poker player."
    text = spec_path.read_text(encoding="utf-8")
    # Extract just the Qualitative Personality section (before the numbers)
    marker = "## Quantitative Targets"
    idx = text.find(marker)
    if idx > 0:
        text = text[:idx].strip()
    return text


def _build_system_prompt(archetype: str, seat: int) -> str:
    """Build the system prompt for an LLM poker agent."""
    personality = _load_personality_spec(archetype)
    return f"""{personality}

---

You are playing Limit Texas Hold'em at an 8-player table. You are seat {seat}.

RULES:
- Small blind = 1, Big blind = 2
- Small bet = 2 (preflop/flop), Big bet = 4 (turn/river)
- Bet cap = 4 per round (1 bet + 3 raises)
- You must respond with EXACTLY ONE of: FOLD, CHECK, CALL, BET, RAISE
- When cost_to_call = 0: you can CHECK or BET
- When cost_to_call > 0: you can FOLD, CALL, or RAISE
- RAISE is only legal if bet_count < bet_cap (4)

RESPOND WITH ONLY THE ACTION NAME. No explanation. Just one word: FOLD, CHECK, CALL, BET, or RAISE."""


# ---------------------------------------------------------------------------
# Game state prompt builder
# ---------------------------------------------------------------------------

def _build_decision_prompt(
    game_state: GameState,
    hole_cards: list,
    hand_strength: str,
    archetype: str,
) -> str:
    """Build the user message describing the current game state."""
    hole_str = _cards_str(hole_cards) if hole_cards else "unknown"
    community_str = _cards_str(game_state.community_cards)

    # Summarize actions this round
    action_lines = []
    for a in (game_state.actions_this_round or []):
        action_lines.append(f"  Seat {a.seat} ({a.archetype}): {a.action_type.value}")
    actions_str = "\n".join(action_lines) if action_lines else "  (none yet)"

    return f"""Street: {game_state.betting_round}
Your hole cards: {hole_str}
Community cards: {community_str}
Hand strength: {hand_strength}

Pot: {game_state.pot_size} chips
Cost to call: {game_state.cost_to_call}
Bet count this round: {game_state.bet_count}/{game_state.bet_cap}
Bet size: {game_state.bet_size}

Your stack: {game_state.player_stack}
Players remaining: {game_state.num_active_players}
Your position: {game_state.player_position} (0=dealer)

Actions this round:
{actions_str}

Your action:"""


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

_ACTION_MAP = {
    "fold": ActionType.FOLD,
    "check": ActionType.CHECK,
    "call": ActionType.CALL,
    "bet": ActionType.BET,
    "raise": ActionType.RAISE,
}


def _parse_action(text: str) -> Optional[ActionType]:
    """Parse an LLM response into an ActionType."""
    cleaned = text.strip().lower()
    # Try direct match first
    if cleaned in _ACTION_MAP:
        return _ACTION_MAP[cleaned]
    # Try to find an action word anywhere in the response
    for word in ["raise", "call", "bet", "check", "fold"]:
        if word in cleaned:
            return _ACTION_MAP[word]
    return None


# ---------------------------------------------------------------------------
# Provider clients
# ---------------------------------------------------------------------------

def make_client(provider: str, model: str, **kwargs) -> Any:
    """Create an API client for the given provider.

    Parameters
    ----------
    provider : "anthropic", "ollama", or "claude-cli"
    model : model name (e.g. "claude-haiku-4-5-20251001" or "llama3.1:8b")

    Returns
    -------
    Client object (Anthropic, OpenAI-compatible, or None for claude-cli).
    """
    if provider == "anthropic":
        import anthropic
        return anthropic.Anthropic()
    elif provider == "ollama":
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "Ollama support requires the 'openai' package.\n"
                "Install with: pip install openai"
            )
        base_url = kwargs.get("base_url", "http://localhost:11434/v1")
        return OpenAI(base_url=base_url, api_key="ollama")
    elif provider == "claude-cli":
        # Shells out to the local `claude --print` binary; no client object needed.
        return None
    else:
        raise ValueError(
            f"Unknown provider: {provider}. Use 'anthropic', 'ollama', or 'claude-cli'."
        )


def _call_llm(
    client: Any,
    provider: str,
    model: str,
    system_prompt: str,
    user_message: str,
    max_retries: int = 1,
) -> str:
    """Call the LLM and return the raw text response."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if provider == "anthropic":
                # Cache the system prompt: personality specs are constant per
                # archetype across an entire run, so caching cuts input cost
                # by ~10x on the cached portion (~$0.08/M vs $0.80/M for
                # Haiku). The user message (game state) is not cached
                # because it changes every call.
                response = client.messages.create(
                    model=model,
                    max_tokens=16,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_message}],
                )
                return response.content[0].text
            elif provider == "claude-cli":
                import subprocess
                combined = f"{system_prompt}\n\n---\n\n{user_message}"
                # cwd=/tmp keeps the nested `claude` from loading the repo's
                # CLAUDE.md (which would pollute every poker decision and add
                # ~25s of context-loading overhead per call).
                result = subprocess.run(
                    ["claude", "--print", "--model", model, combined],
                    capture_output=True, text=True, timeout=60, cwd="/tmp",
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"claude CLI exited {result.returncode}: "
                        f"{result.stderr.strip()[:200]}"
                    )
                return result.stdout.strip()
            else:
                # OpenAI-compatible (Ollama)
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=16,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                )
                return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(0.5)
                continue
            raise RuntimeError(f"LLM call failed after {max_retries + 1} attempts: {e}")


# ---------------------------------------------------------------------------
# LLMChatAgent
# ---------------------------------------------------------------------------

class LLMChatAgent(BaseAgent):
    """Agent that calls an LLM for every decision.

    Inherits all trust/observation/stats machinery from BaseAgent.
    Only overrides decide_action to call the LLM instead of sampling
    from parameter tables.
    """

    def __init__(
        self,
        seat: int,
        name: str,
        archetype: str,
        client: Any,
        model: str,
        provider: str = "ollama",
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(name=name, archetype=archetype, seat=seat, rng=rng)
        self._client = client
        self._model = model
        self._provider = provider
        self._system_prompt = _build_system_prompt(archetype, seat)

        # Stats
        self.llm_calls: int = 0
        self.llm_failures: int = 0
        self.llm_total_time: float = 0.0

    def decide_action(self, game_state: GameState) -> ActionType:
        import sys
        rng = self.rng or np.random.default_rng()

        # Compute hand strength (cached per street).
        # Use fewer MC samples than Phase 1 (100 vs 1000) since the LLM
        # makes the strategic decision anyway — the bucket is just context.
        round_key = game_state.betting_round
        hs = self._hs_cache.get(round_key)
        if hs is None:
            print(f"    {self.name} computing hand strength ({round_key})...",
                  end="", flush=True)
            t_hs = time.time()
            hs = get_hand_strength(
                self.hole_cards,
                game_state.community_cards,
                rng=rng,
                num_samples=50,
            )
            print(f" {hs} ({time.time()-t_hs:.1f}s)", flush=True)
            self._hs_cache[round_key] = hs

        # Build prompt and call LLM
        user_msg = _build_decision_prompt(
            game_state, self.hole_cards, hs, self.archetype
        )

        print(f"    {self.name} calling LLM...", end="", flush=True)
        t0 = time.time()
        try:
            response = _call_llm(
                self._client, self._provider, self._model,
                self._system_prompt, user_msg,
            )
            self.llm_calls += 1
            elapsed = time.time() - t0
            action = _parse_action(response)
            print(f" -> {response.strip()!r} ({elapsed:.1f}s)", flush=True)
        except RuntimeError as e:
            self.llm_failures += 1
            elapsed = time.time() - t0
            print(f" FAILED ({elapsed:.1f}s)", flush=True)
            if self.llm_failures <= 5:
                print(f"    [LLM ERROR] {self.name}: {e}", file=sys.stderr, flush=True)
            return ActionType.CHECK if game_state.cost_to_call == 0 else ActionType.FOLD
        finally:
            self.llm_total_time += time.time() - t0

        # Parse response (action was set above in the try block)
        if action is None:
            self.llm_failures += 1
            return ActionType.CHECK if game_state.cost_to_call == 0 else ActionType.FOLD

        # Basic legality fix (the Dealer also validates, but do a quick fix here)
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

    # Provide a dummy get_params (required by ABC but unused)
    def get_params(self, betting_round: str, game_state: GameState) -> dict:
        return {}


# ---------------------------------------------------------------------------
# LLMChatJudge — adds grievance tracking on top of LLMChatAgent
# ---------------------------------------------------------------------------

class LLMChatJudge(LLMChatAgent):
    """LLM Chat agent with Judge's grievance/retaliation mechanic.

    The LLM decides actions, but the system prompt shifts to include
    retaliation context when a triggered opponent is aggressing.
    """

    JUDGE_TAU = 5

    def __init__(self, seat: int, client: Any, model: str,
                 provider: str = "ollama",
                 name: str = "LLM-Judge",
                 rng: Optional[np.random.Generator] = None) -> None:
        super().__init__(
            seat=seat, name=name, archetype="judge",
            client=client, model=model, provider=provider, rng=rng,
        )
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
            weak_found = False
            for round_name in rounds:
                board = _community_slice_for_round(community_cards, round_name)
                bucket = _fast_bucket(hole, board, rng=self.rng)
                if bucket == "Weak":
                    weak_found = True
                    break
            if not weak_found:
                continue
            new_count = self.grievance.get(seat, 0) + 1
            self.grievance[seat] = new_count
            if new_count >= self.JUDGE_TAU and not self.triggered.get(seat, False):
                self.triggered[seat] = True

    def decide_action(self, game_state: GameState) -> ActionType:
        # Inject retaliation context into the system prompt if triggered
        retaliation_active = False
        for seat in self._bluff_candidates:
            if self.triggered.get(seat, False):
                retaliation_active = True
                break

        if retaliation_active:
            orig = self._system_prompt
            self._system_prompt = orig + (
                "\n\n**RETALIATION MODE ACTIVE.** An opponent at this table has "
                "repeatedly bluffed against you (5+ confirmed weak-hand bluffs). "
                "Play extremely aggressively against them: raise frequently, "
                "bluff more, and do not call passively. Punish the deceiver."
            )
            result = super().decide_action(game_state)
            self._system_prompt = orig
            return result

        return super().decide_action(game_state)

    def grievance_summary(self):
        out = []
        for seat in sorted(self.grievance):
            out.append((
                seat, self.grievance[seat],
                bool(self.triggered.get(seat, False)), None,
            ))
        return out
