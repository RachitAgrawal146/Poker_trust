"""
Visualizer exporter.

Plays N hands with a given set of agents and writes a JSON payload that
``visualizer/poker_table.html`` can consume. The schema is designed to be
forward-compatible: Stage 3 adds real archetypes, Stage 5 adds trust
snapshots, Stage 6 adds grievance/trigger fields, and so on — each new
stage is additive. Fields the viewer doesn't recognize are simply ignored
by the UI, so old HTML + new JSON still renders.

Writing to a ``.js`` path produces a script file that assigns
``window.POKER_DATA`` — this lets the HTML viewer load data over ``file://``
without tripping the CORS check that ``fetch``-ing ``.json`` from disk
would trigger in Chrome.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from treys import Card

from config import NUM_PLAYERS
from engine.game import Hand
from engine.table import Table

__all__ = ["hand_to_dict", "run_and_export", "write_payload"]


def _card_str(c: int) -> str:
    """Convert a ``treys.Card`` int to a two-character string like ``'Ah'``.

    ``treys.Card.int_to_str`` already does this for us.
    """
    return Card.int_to_str(c)


def _cards(cs) -> List[str]:
    return [_card_str(c) for c in cs]


def _capture_trust_snapshot(table) -> Optional[dict]:
    """Return ``{observer_seat: {target_seat: trust_score}}`` at hand-end.

    Uses each agent's public ``trust_score(seat)`` accessor so the snapshot
    works for any agent that implements the Stage 5 interface (BaseAgent
    subclasses) and silently degrades for dummy agents that don't.
    """
    snapshot: dict = {}
    for obs in table.seats:
        if not hasattr(obs, "trust_score"):
            return None  # Pre-Stage-5 agent roster — skip the whole snapshot
        row: dict = {}
        for target in range(len(table.seats)):
            if target == obs.seat:
                continue
            row[str(target)] = float(obs.trust_score(target))
        snapshot[str(obs.seat)] = row
    return snapshot


def _capture_entropy_snapshot(table) -> Optional[dict]:
    """Same shape as the trust snapshot but with posterior entropy in bits."""
    snapshot: dict = {}
    for obs in table.seats:
        if not hasattr(obs, "entropy"):
            return None
        row: dict = {}
        for target in range(len(table.seats)):
            if target == obs.seat:
                continue
            row[str(target)] = float(obs.entropy(target))
        snapshot[str(obs.seat)] = row
    return snapshot


def _capture_top_archetype_snapshot(table) -> Optional[dict]:
    """``{observer_seat: {target_seat: [top_archetype, top_prob]}}``.

    Lets the viewer show the observer's best guess for each seat without
    shipping the full 8-element posterior. Returns ``None`` if any agent in
    the roster lacks the Stage 5 interface.
    """
    snapshot: dict = {}
    for obs in table.seats:
        posteriors = getattr(obs, "posteriors", None)
        if posteriors is None:
            return None
        row: dict = {}
        for target in range(len(table.seats)):
            if target == obs.seat:
                continue
            post = posteriors.get(target)
            if post is None:
                row[str(target)] = ["unknown", 0.125]
                continue
            try:
                from trust import TRUST_TYPE_LIST
                idx = int(post.argmax())
                row[str(target)] = [TRUST_TYPE_LIST[idx], float(post[idx])]
            except Exception:
                row[str(target)] = ["unknown", 0.125]
        snapshot[str(obs.seat)] = row
    return snapshot


def hand_to_dict(hand: Hand) -> dict:
    """Serialize one played ``Hand`` to a viewer-ready dict."""
    actions = []
    for rec in hand.action_log:
        actions.append(
            {
                "round": rec.betting_round,
                "seat": rec.seat,
                "type": rec.action_type.value,
                "amount": rec.amount,
                "pot_before": rec.pot_before,
                "pot_after": rec.pot_after,
                "bet_count": rec.bet_count,
                "current_bet": rec.current_bet,
                "sequence_num": rec.sequence_num,
                "stack_before": rec.stack_before,
                "stack_after": rec.stack_after,
            }
        )

    hole_cards = {str(s): _cards(cs) for s, cs in hand.hole_cards.items()}

    showdown: Optional[List[dict]] = None
    walkover_winner: Optional[int] = None
    if hand.showdown_data:
        showdown = [
            {
                "seat": e["seat"],
                "archetype": e["archetype"],
                "hole_cards": _cards(e["hole_cards"]),
                "hand_rank": e["hand_rank"],
                "won": e["won"],
                "pot_won": e["pot_won"],
            }
            for e in hand.showdown_data
        ]
    else:
        walkover_winner = getattr(hand, "_walkover_winner", None)

    num_seats = len(hand.table.seats)
    # Stage 5: snapshot each agent's view of every other agent at hand-end.
    trust_snapshot = _capture_trust_snapshot(hand.table)
    entropy_snapshot = _capture_entropy_snapshot(hand.table)
    top_archetype_snapshot = _capture_top_archetype_snapshot(hand.table)

    return {
        "hand_id": hand.hand_id,
        "dealer": hand.dealer_seat,
        "sb_seat": hand.sb_seat,
        "bb_seat": hand.bb_seat,
        "stacks_before": [hand.stack_before_hand[s] for s in range(num_seats)],
        "stacks_after": [hand.stack_after_hand[s] for s in range(num_seats)],
        "folded": [s in hand.folded for s in range(num_seats)],
        "hole_cards": hole_cards,
        "community": {
            "flop": _cards(hand.flop_cards),
            "turn": _cards(hand.turn_card),
            "river": _cards(hand.river_card),
        },
        "actions": actions,
        "final_pot": hand.final_pot,
        "showdown": showdown,
        "walkover_winner": walkover_winner,
        # Stage 5: trust / entropy / top-archetype snapshots per observer pair.
        "trust_snapshot": trust_snapshot,
        "entropy_snapshot": entropy_snapshot,
        "top_archetype_snapshot": top_archetype_snapshot,
        "grievances": None,         # Stage 6: Judge grievance counts
    }


def run_and_export(
    agents,
    num_hands: int,
    seed: int,
    output_path: str,
    stage: int,
    label: str,
) -> dict:
    """Run a Table for ``num_hands`` and write the visualizer payload.

    Returns the payload dict for in-process inspection.
    """
    table = Table(agents, seed=seed)
    hands_data = []
    for _ in range(num_hands):
        table.play_hand()
        hand = table.last_hand
        assert hand is not None
        hands_data.append(hand_to_dict(hand))

    payload = {
        "meta": {
            "stage": stage,
            "label": label,
            "seed": seed,
            "num_hands": num_hands,
            "num_seats": NUM_PLAYERS,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agents": [
                {
                    "seat": a.seat,
                    "name": a.name,
                    "archetype": a.archetype,
                }
                for a in agents
            ],
        },
        "hands": hands_data,
    }

    write_payload(payload, output_path)
    return payload


def write_payload(payload: dict, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if output_path.endswith(".js"):
        with open(output_path, "w") as f:
            f.write("// Auto-generated by data/visualizer_export.py — do not edit by hand.\n")
            f.write("window.POKER_DATA = ")
            json.dump(payload, f, indent=2)
            f.write(";\n")
    else:
        with open(output_path, "w") as f:
            json.dump(payload, f, indent=2)
