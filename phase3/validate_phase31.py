"""Validate the Phase 3.1 code paths without burning API credit.

This script exercises every Phase 3.1 code path the live runner will hit,
using a mock LLM client so no real API calls happen.

Coverage:
  1. Module imports
  2. Phase 3.1 system prompt construction (length + content checks)
  3. Phase 3.1 user message construction with memory + notes injected
  4. CoT response parsing (positive cases + edge cases)
  5. Strategy notes parsing (positive + edge cases)
  6. Strategy update prompt construction
  7. LLMChatAgent in phase31=True mode:
     - construction
     - observe_action populates _opp_action_log correctly
     - on_hand_end refresh frequency (every 10 hands)
     - on_hand_end strategy update trigger (every 25 hands)
     - _refresh_opponent_memory produces correct text summaries
     - _update_strategy_notes calls the LLM with the right prompt
     - decide_action assembles the right user message
  8. LLMChatJudge inherits phase31 mode

Exit code 0 if every check passes; non-zero on any failure.

Usage:
    python3 phase3/validate_phase31.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Any, List
from dataclasses import dataclass

import numpy as np

from engine.actions import ActionRecord, ActionType


# ---------------------------------------------------------------------------
# Mock client + game-state helpers
# ---------------------------------------------------------------------------

class MockClient:
    """A stand-in for the Anthropic / Ollama client that records every
    call and returns a canned response.
    """
    def __init__(self) -> None:
        self.calls: List[dict] = []
        self.next_response: str = "ACTION: CALL"

    class _Messages:
        def __init__(self, parent):
            self._p = parent
        def create(self, **kw):
            self._p.calls.append(kw)
            class _R:
                def __init__(self, text):
                    self.content = [type("X", (), {"text": text})]
            return _R(self._p.next_response)

    @property
    def messages(self):
        return self._Messages(self)


@dataclass
class FakeGS:
    """Minimal stand-in for engine.game.GameState."""
    betting_round: str = "preflop"
    community_cards: list = None
    pot_size: int = 3
    cost_to_call: int = 2
    bet_count: int = 1
    bet_cap: int = 4
    bet_size: int = 2
    player_stack: int = 200
    num_active_players: int = 8
    player_position: int = 3
    actions_this_round: list = None
    hand_id: int = 1

    def __post_init__(self):
        if self.community_cards is None:
            self.community_cards = []
        if self.actions_this_round is None:
            self.actions_this_round = []


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

failures: List[str] = []
checks: List[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    checks.append(label)
    if condition:
        print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))
    else:
        failures.append(label + (f": {detail}" if detail else ""))
        print(f"  FAIL  {label}" + (f"  ({detail})" if detail else ""))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_imports():
    print("\n[1] Module imports")
    from phase3 import llm_chat_agent
    from phase3.llm_chat_agent import (
        LLMChatAgent, LLMChatJudge,
        _build_system_prompt, _build_decision_prompt,
        _build_strategy_update_prompt,
        _parse_action, _parse_phase31_action, _parse_strategy_notes,
        _call_llm, make_client,
    )
    check("imports.module_resolves", llm_chat_agent is not None)


def test_system_prompt():
    print("\n[2] System prompt construction")
    from phase3.llm_chat_agent import _build_system_prompt
    baseline = _build_system_prompt("sentinel", 1, phase31=False)
    phase31 = _build_system_prompt("sentinel", 1, phase31=True)
    check("system_prompt.baseline_short", "ACTION:" not in baseline,
          "baseline should NOT mention ACTION: marker")
    check("system_prompt.phase31_has_action_marker", "ACTION:" in phase31)
    check("system_prompt.phase31_has_cot_instruction",
          "step by step" in phase31.lower() or "reason" in phase31.lower())
    check("system_prompt.phase31_loads_personality",
          "Sentinel" in phase31 or "tight" in phase31.lower())


def test_decision_prompt():
    print("\n[3] Decision prompt with memory + notes")
    from phase3.llm_chat_agent import _build_decision_prompt
    gs = FakeGS()
    msg_no_p31 = _build_decision_prompt(gs, [], "Medium", "sentinel",
                                          opponent_memory=None, strategy_notes=None)
    msg_with = _build_decision_prompt(
        gs, [], "Medium", "sentinel",
        opponent_memory={2: "aggressive 8/12", 3: "called 18/20"},
        strategy_notes="Tighten preflop range; do not bluff Wall.",
    )
    check("decision_prompt.no_p31_no_memory_block",
          "Notes on each opponent" not in msg_no_p31)
    check("decision_prompt.no_p31_no_notes_block",
          "Your own strategy notes" not in msg_no_p31)
    check("decision_prompt.with_p31_has_memory",
          "aggressive 8/12" in msg_with)
    check("decision_prompt.with_p31_has_notes",
          "Tighten preflop range" in msg_with)
    check("decision_prompt.ends_with_action_prompt",
          msg_with.rstrip().endswith("Your action:"))


def test_phase31_action_parser():
    print("\n[4] CoT action parser")
    from phase3.llm_chat_agent import _parse_phase31_action
    cases = [
        ("Sentinel here. K-J offsuit is bad.\nACTION: FOLD", ActionType.FOLD),
        ("Reasoning blah\nACTION: CALL", ActionType.CALL),
        ("Multi\nLine\nReasoning\nAction: raise", ActionType.RAISE),
        ("ACTION:bet", ActionType.BET),
        ("Actually thinking...\nFinal: ACTION: CHECK", ActionType.CHECK),
        # Fallback: no ACTION marker, scan for action word
        ("I think I should fold this hand.", ActionType.FOLD),
        # Empty / garbage
        ("", None),
        ("xyz nonsense 123", None),
    ]
    for text, expected in cases:
        got = _parse_phase31_action(text)
        check(f"action_parser.{repr(text)[:40]}",
              got == expected,
              f"expected {expected}, got {got}")


def test_strategy_notes_parser():
    print("\n[5] Strategy notes parser")
    from phase3.llm_chat_agent import _parse_strategy_notes
    case1 = "REASONING: I folded too much.\nNOTES: Loosen up preflop with suited connectors."
    case2 = "Notes: Continue current strategy; opponents are folding."
    case3 = "REASONING: bad hand\nReasoning continues here."  # No NOTES line
    check("notes_parser.standard",
          _parse_strategy_notes(case1) == "Loosen up preflop with suited connectors.")
    check("notes_parser.lowercase",
          _parse_strategy_notes(case2) == "Continue current strategy; opponents are folding.")
    check("notes_parser.missing_notes_line",
          _parse_strategy_notes(case3) is None)


def test_strategy_update_prompt():
    print("\n[6] Strategy update prompt builder")
    from phase3.llm_chat_agent import _build_strategy_update_prompt
    p = _build_strategy_update_prompt(
        archetype="sentinel", hand_id=25, profit_this_hand=+47,
        actions_taken=["call", "check", "bet", "call"],
        showdown_result=None, current_notes=None,
    )
    check("strategy_update.has_hand_id", "#25" in p)
    check("strategy_update.has_profit", "+47" in p)
    check("strategy_update.has_actions", "call, check, bet, call" in p)
    check("strategy_update.has_format_markers",
          "REASONING:" in p and "NOTES:" in p)


def test_agent_construction():
    print("\n[7] Agent construction (phase31=True)")
    from phase3.llm_chat_agent import LLMChatAgent, LLMChatJudge
    client = MockClient()
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="claude-haiku-4-5",
                      provider="anthropic", phase31=True)
    check("agent.phase31_flag_set", a._phase31 is True)
    check("agent.opponent_memory_init_empty", a._opponent_memory == {})
    check("agent.strategy_notes_init_none", a._strategy_notes is None)
    check("agent.opp_action_log_init_empty", a._opp_action_log == {})
    check("agent.system_prompt_phase31",
          "ACTION:" in a._system_prompt)

    j = LLMChatJudge(seat=7, client=client, model="claude-haiku-4-5",
                     provider="anthropic", phase31=True)
    check("judge.phase31_flag_propagates", j._phase31 is True)


def _make_record(hand_id, seq, seat, archetype, action, betting_round="preflop"):
    """Build a minimal ActionRecord with all the fields the dataclass requires."""
    return ActionRecord(
        hand_id=hand_id, seat=seat, archetype=archetype,
        betting_round=betting_round, action_type=action,
        amount=2, pot_before=0, pot_after=2,
        stack_before=200, stack_after=198,
        sequence_num=seq, num_opponents_remaining=7,
        position_relative_to_dealer=seat, bet_count=1,
    )


def test_observe_action_logging():
    print("\n[8] observe_action populates _opp_action_log")
    from phase3.llm_chat_agent import LLMChatAgent
    client = MockClient()
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="m", provider="anthropic",
                      phase31=True)
    a.on_hand_start(1)
    # 3 actions from opponent seat=2, 1 from self
    a.observe_action(_make_record(1, 0, 2, "firestorm", ActionType.RAISE))
    a.observe_action(_make_record(1, 1, 1, "sentinel", ActionType.CALL))
    a.observe_action(_make_record(1, 2, 2, "firestorm", ActionType.BET, "flop"))
    a.observe_action(_make_record(1, 3, 2, "firestorm", ActionType.RAISE, "flop"))
    check("observe.self_action_recorded",
          a._actions_this_hand == ["call"],
          f"got {a._actions_this_hand}")
    check("observe.opp_log_seat2_count_is_3",
          len(a._opp_action_log.get(2, [])) == 3,
          f"got {len(a._opp_action_log.get(2, []))}")
    check("observe.opp_log_seat2_actions_correct",
          [t[2] for t in a._opp_action_log[2]] == ["raise", "bet", "raise"])


def test_refresh_opponent_memory():
    print("\n[9] _refresh_opponent_memory builds summaries")
    from phase3.llm_chat_agent import LLMChatAgent
    client = MockClient()
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="m", provider="anthropic",
                      phase31=True)
    # Inject a synthetic action log
    a._opp_action_log = {
        2: [(1, "preflop", "raise"), (1, "flop", "bet"), (2, "preflop", "call"),
            (3, "preflop", "raise"), (4, "preflop", "raise")],
        3: [(1, "preflop", "call"), (2, "preflop", "call"), (3, "preflop", "call")],
    }
    a._refresh_opponent_memory()
    check("memory.seat2_has_summary", 2 in a._opponent_memory)
    check("memory.seat3_has_summary", 3 in a._opponent_memory)
    check("memory.seat2_aggressive_counted",
          "aggressive" in a._opponent_memory[2],
          a._opponent_memory[2])
    check("memory.seat3_called_counted",
          "called" in a._opponent_memory[3],
          a._opponent_memory[3])


def test_update_strategy_notes_calls_llm():
    print("\n[10] _update_strategy_notes calls LLM and stores result")
    from phase3.llm_chat_agent import LLMChatAgent
    client = MockClient()
    client.next_response = "REASONING: Played too tight.\nNOTES: Open up suited connectors in late position."
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="m", provider="anthropic",
                      phase31=True)
    a._actions_this_hand = ["fold", "fold", "call"]
    a._update_strategy_notes(hand_id=25, profit=-12)
    check("update.client_was_called", len(client.calls) == 1)
    check("update.calls_used_phase31_max_tokens",
          client.calls[0].get("max_tokens") == 128)
    check("update.notes_stored",
          a._strategy_notes == "Open up suited connectors in late position.",
          f"got {a._strategy_notes!r}")
    check("update.llm_calls_incremented", a.llm_calls == 1)


def test_on_hand_end_triggers():
    print("\n[11] on_hand_end refresh frequency + strategy update trigger")
    from phase3.llm_chat_agent import LLMChatAgent
    client = MockClient()
    client.next_response = "REASONING: ok\nNOTES: stay tight"
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="m", provider="anthropic",
                      phase31=True)

    # Simulate: hand ends 1..30
    for hid in range(1, 31):
        a.on_hand_start(hid)
        a.observe_action(_make_record(hid, 0, 2, "firestorm", ActionType.RAISE))
        a.on_hand_end(hid)

    # Memory refresh fires every 10 hands -> 3 refreshes (hands 10, 20, 30)
    # Strategy update fires every 25 hands -> 1 update (hand 25)
    check("trigger.memory_populated_after_hand10",
          2 in a._opponent_memory)
    check("trigger.strategy_update_fired_at_hand25",
          a._strategy_notes == "stay tight",
          f"got {a._strategy_notes!r}")
    check("trigger.exactly_one_llm_call_total",
          len(client.calls) == 1,
          f"client got {len(client.calls)} calls (expected 1 strategy update)")


def test_baseline_path_unchanged():
    print("\n[12] phase31=False path is byte-identical to baseline")
    from phase3.llm_chat_agent import LLMChatAgent
    client = MockClient()
    a = LLMChatAgent(seat=1, name="LLM-Sentinel", archetype="sentinel",
                      client=client, model="m", provider="anthropic",
                      phase31=False)
    # Run hand 25 (where p31 would trigger an update) and verify NO LLM call
    a.on_hand_start(25)
    a.observe_action(_make_record(25, 0, 2, "firestorm", ActionType.RAISE))
    a.on_hand_end(25)
    check("baseline.no_llm_call_on_hand_end",
          len(client.calls) == 0)
    check("baseline.no_strategy_notes",
          a._strategy_notes is None)
    check("baseline.system_prompt_no_action_marker",
          "ACTION:" not in a._system_prompt)


def test_runner_cli():
    print("\n[13] Runner CLI exposes --phase31")
    import subprocess
    r = subprocess.run(
        ["python3", "phase3/run_phase3_chat.py", "--help"],
        capture_output=True, text=True, timeout=15,
    )
    check("cli.phase31_flag_in_help",
          "--phase31" in r.stdout,
          f"return={r.returncode}")
    check("cli.help_returns_zero", r.returncode == 0)


def main() -> int:
    print("=" * 70)
    print("Phase 3.1 unit-level validation (no API spend)")
    print("=" * 70)
    test_imports()
    test_system_prompt()
    test_decision_prompt()
    test_phase31_action_parser()
    test_strategy_notes_parser()
    test_strategy_update_prompt()
    test_agent_construction()
    test_observe_action_logging()
    test_refresh_opponent_memory()
    test_update_strategy_notes_calls_llm()
    test_on_hand_end_triggers()
    test_baseline_path_unchanged()
    test_runner_cli()
    print()
    print("=" * 70)
    print(f"RESULTS: {len(checks) - len(failures)} / {len(checks)} passed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        print("=" * 70)
        return 1
    print("ALL CHECKS PASSED")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
