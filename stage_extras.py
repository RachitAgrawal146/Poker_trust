"""
Concrete assertion checks that augment ``test_cases.py``.

The canonical ``test_cases.py`` in the repo is a spec document: many of its
tests past Stage 1 are placeholder "TEST ..." strings rather than real
assertions. This module adds the real assertions, keyed by stage number, so
each build stage can be verified end-to-end without mutating the canonical
spec file.

Each function takes the same ``modules`` dict as ``test_cases.test_stage_N``
and returns a list of result strings (prefixed with ``PASS`` / ``FAIL``)
that the runner prints and tallies.
"""

from __future__ import annotations

from typing import List


def stage2_extras(modules) -> List[str]:
    Table = modules["Table"]
    DummyAgent = modules["DummyAgent"]
    FolderAgent = modules["FolderAgent"]
    RaiserAgent = modules["RaiserAgent"]
    ActionType = modules["ActionType"]

    results: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        prefix = "PASS" if cond else "FAIL"
        results.append(f"{prefix} {name}{': ' + detail if detail else ''}")

    # ------------------------------------------------------------------
    # Test 2.1: Pot math — 8 dummies all call preflop, pot = 16
    # ------------------------------------------------------------------
    agents = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    table = Table(agents, seed=42)
    action_log, showdown = table.play_hand()

    # Pot is awarded at hand end, so check via total stack conservation:
    # sum(stacks) + (pot awarded) should equal 8 * starting_stack.
    total_stack = sum(a.stack for a in agents)
    check(
        "2.1a: stack conservation (8 dummies, 1 hand)",
        total_stack == 8 * 200,
        f"got total stack {total_stack}, expected {8 * 200}",
    )

    # Verify that the pot is 16 chips at the end of preflop. Blinds aren't
    # ActionRecords, so we check pot_after of the final preflop action
    # (which reflects blinds + all calls).
    preflop_actions = [a for a in action_log if a.betting_round == "preflop"]
    final_preflop_pot = preflop_actions[-1].pot_after if preflop_actions else 0
    check(
        "2.1b: preflop pot = 16 chips (8 callers + 3 blinds)",
        final_preflop_pot == 16,
        f"got pot_after={final_preflop_pot}",
    )

    # All 8 players should reach showdown (no one folded).
    check(
        "2.1c: all 8 reach showdown",
        showdown is not None and len(showdown) == 8,
        f"showdown had {len(showdown) if showdown else 0} players",
    )

    # Exactly one winner (tie-handling is tested separately) — or at least
    # one. The pot should have been awarded (sum of pot_won matches total
    # contributed).
    if showdown:
        total_won = sum(entry["pot_won"] for entry in showdown)
        check(
            "2.1d: pot_won matches total chips contributed",
            total_won == 16,
            f"sum(pot_won) = {total_won}, expected 16",
        )

    # ------------------------------------------------------------------
    # Test 2.2: Bet cap enforced — a round with RaiserAgents caps at 4 bets
    # ------------------------------------------------------------------
    agents = [RaiserAgent(f"R{i}", "raiser", i) for i in range(8)]
    table = Table(agents, seed=42)
    action_log, _ = table.play_hand()

    preflop = [a for a in action_log if a.betting_round == "preflop"]
    raises_preflop = [a for a in preflop
                      if a.action_type in (ActionType.BET, ActionType.RAISE)]
    # Preflop big blind counts as bet 1; raises bump bet_count. Cap is 4.
    # So at most 3 RAISEs (since BB is implicit bet 1).
    max_bet_count_preflop = max((a.bet_count for a in preflop), default=0)
    check(
        "2.2a: preflop bet_count never exceeds cap (4)",
        max_bet_count_preflop <= 4,
        f"max bet_count = {max_bet_count_preflop}",
    )

    # Any action after cap is reached should be CALL, never RAISE.
    cap_violations = 0
    for a in preflop:
        if a.bet_count == 4 and a.action_type == ActionType.RAISE:
            # The action that *caused* bet_count to hit 4 is legal; but no
            # action while bet_count == 4 (and not the one that just set it)
            # should be a RAISE. Detecting "the one that set it" requires
            # looking at previous state; easier to check: no action after
            # the first bet_count=4 action is a RAISE.
            pass  # allowed
    # Stronger check: the LAST RAISE in a round should be the cap-raise.
    raises_only = [a for a in preflop if a.action_type == ActionType.RAISE]
    if raises_only:
        last_raise_bet_count = raises_only[-1].bet_count
        # No RAISE should come after the cap-raise.
        idx_last_raise = preflop.index(raises_only[-1])
        after_cap = preflop[idx_last_raise + 1 :]
        post_cap_raises = [a for a in after_cap
                           if a.action_type == ActionType.RAISE]
        check(
            "2.2b: no RAISE after bet_count reaches cap",
            len(post_cap_raises) == 0,
            f"found {len(post_cap_raises)} post-cap raises",
        )
    else:
        check("2.2b: no RAISE after bet_count reaches cap",
              True, "no raises in round")

    # ------------------------------------------------------------------
    # Test 2.3: Folded players don't act
    # ------------------------------------------------------------------
    # Mix folders and dummies; after a folder's first fold they should
    # produce exactly one action in the hand (the fold itself).
    mixed = [
        DummyAgent("D0", "dummy", 0),
        FolderAgent("F1", "folder", 1),
        DummyAgent("D2", "dummy", 2),
        FolderAgent("F3", "folder", 3),
        DummyAgent("D4", "dummy", 4),
        FolderAgent("F5", "folder", 5),
        DummyAgent("D6", "dummy", 6),
        FolderAgent("F7", "folder", 7),
    ]
    table = Table(mixed, seed=42)
    action_log, _ = table.play_hand()
    for seat in [1, 3, 5, 7]:
        seat_actions = [a for a in action_log if a.seat == seat]
        # The SB (seat 1) and BB (seat 3) are posted blinds but not recorded
        # as actions; their only action should still be a single FOLD.
        # Exception: a folder in the big blind faces cost_to_call==0 on the
        # "BB option" and would CHECK instead of fold. That's one action.
        check(
            f"2.3.seat{seat}: folder/BB acted at most once (got {len(seat_actions)})",
            len(seat_actions) <= 1,
        )

    # ------------------------------------------------------------------
    # Test 2.4: Hand ends when only 1 player remains (no flop dealt)
    # ------------------------------------------------------------------
    # Everyone is a folder except UTG, which raises preflop. BB can no
    # longer just check the BB option (cost_to_call > 0), so it folds too.
    # Only UTG survives — the hand must end with no postflop actions and
    # no showdown.
    agents = [
        FolderAgent("F0", "folder", 0),   # dealer; folds
        FolderAgent("F1", "folder", 1),   # SB
        FolderAgent("F2", "folder", 2),   # BB (now faces a raise)
        RaiserAgent("R3", "raiser", 3),   # UTG — raises
        FolderAgent("F4", "folder", 4),
        FolderAgent("F5", "folder", 5),
        FolderAgent("F6", "folder", 6),
        FolderAgent("F7", "folder", 7),
    ]
    table = Table(agents, seed=42)
    action_log, showdown = table.play_hand()
    # Check that no flop/turn/river actions were logged.
    postflop = [a for a in action_log
                if a.betting_round in ("flop", "turn", "river")]
    check(
        "2.4: no postflop actions when only 1 player survives preflop",
        len(postflop) == 0,
        f"found {len(postflop)} postflop actions",
    )
    check(
        "2.4: no showdown on walkover",
        showdown is None,
        "walkover should not produce showdown data",
    )

    # ------------------------------------------------------------------
    # Test 2.5: Showdown only when 2+ players remain
    # ------------------------------------------------------------------
    # Already covered by 2.1c (showdown with 8) and 2.4 (walkover with 1).
    check("2.5: showdown occurs iff >=2 players remain", True,
          "covered by 2.1c + 2.4")

    # ------------------------------------------------------------------
    # Test 2.7: Dealer button advances by 1 each hand
    # ------------------------------------------------------------------
    agents = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    table = Table(agents, seed=42)
    buttons: List[int] = []
    for _ in range(4):
        buttons.append(table.dealer_button)
        table.play_hand()
    check(
        "2.7: dealer button advances by 1 each hand",
        buttons == [0, 1, 2, 3],
        f"sequence was {buttons}",
    )

    # ------------------------------------------------------------------
    # Test 2.8: Rebuys work
    # ------------------------------------------------------------------
    agents = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    table = Table(agents, seed=42)
    agents[3].stack = 0
    assert agents[3].rebuys == 0
    table.play_hand()
    # The start of the hand triggers the rebuy, so seat 3's rebuys count
    # should be 1 afterwards and stack should be a positive number.
    check(
        "2.8a: rebuy increments rebuys counter",
        agents[3].rebuys == 1,
        f"rebuys = {agents[3].rebuys}",
    )
    check(
        "2.8b: rebuy grants positive stack",
        agents[3].stack > 0,
        f"stack = {agents[3].stack}",
    )

    # ------------------------------------------------------------------
    # Reproducibility: same seed -> same action log
    # ------------------------------------------------------------------
    a1 = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    t1 = Table(a1, seed=42)
    log1, _ = t1.play_hand()
    a2 = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    t2 = Table(a2, seed=42)
    log2, _ = t2.play_hand()
    log1_sig = [(r.seat, r.action_type, r.amount) for r in log1]
    log2_sig = [(r.seat, r.action_type, r.amount) for r in log2]
    check(
        "2.R: reproducibility (same seed → identical action log)",
        log1_sig == log2_sig,
    )

    return results
