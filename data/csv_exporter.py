"""CSV exporters for ML-ready research datasets (Stage 11).

The visualizer JSON exporter is rich but heavy — one 8-archetype seat roster
over 10k hands weighs tens of megabytes and bundles every posterior snapshot.
For analysis notebooks and ML pipelines we want flat, per-row tables with
stable column schemas instead. This module provides three writers:

- ``write_actions_csv`` — one row per ``ActionRecord`` (the finest grain).
- ``write_hands_csv``   — one row per played hand.
- ``write_agent_stats_csv`` — one row per seat at end of run.

All three use only the stdlib ``csv`` module — no pandas dependency — so the
exporter can run on a bare Python install. Schemas intentionally mirror the
fields already surfaced by ``data/visualizer_export.py`` where possible so
the two exporters stay in sync as new stages land.

Observer 0 convention
---------------------
Per the Stage 10/11 spec, the Oracle in seat 0 is the designated "live"
observer: every action row carries Oracle's current belief about the acting
seat (trust score, entropy, top-archetype guess). These are captured at
hand-end because the engine does not expose mid-hand snapshots — the value
is the same for every action in a given hand, which is fine for downstream
aggregation and matches what the visualizer already ships.

CSV writers call ``flush`` explicitly to make byte-identical-output tests
robust across platforms (Windows vs POSIX line endings are pinned via
``newline=""`` on the open-call).
"""

from __future__ import annotations

import csv
import os
from typing import Iterable, List, Optional

from trust import TRUST_TYPE_LIST


__all__ = [
    "write_actions_csv",
    "write_hands_csv",
    "write_agent_stats_csv",
    "ACTIONS_HEADER",
    "HANDS_HEADER",
    "AGENT_STATS_HEADER",
]


# =============================================================================
# Column schemas — exported so tests can assert against them.
# =============================================================================
ACTIONS_HEADER: List[str] = [
    "run_id",
    "hand_id",
    "seq",
    "round",
    "seat",
    "archetype",
    "action_type",
    "amount",
    "pot_before",
    "pot_after",
    "stack_before",
    "stack_after",
    "bet_count",
    "current_bet",
    "trust_this_seat_from_observer_0",
    "entropy_this_seat_from_observer_0",
    "top_archetype_from_observer_0",
    "top_archetype_prob_from_observer_0",
]

HANDS_HEADER: List[str] = [
    "run_id",
    "hand_id",
    "dealer",
    "sb_seat",
    "bb_seat",
    "final_pot",
    "had_showdown",
    "walkover_winner",
] + [f"mean_trust_into_seat_{i}" for i in range(8)]

AGENT_STATS_HEADER: List[str] = [
    "run_id",
    "seat",
    "name",
    "archetype",
    "hands_dealt",
    "vpip_pct",
    "pfr_pct",
    "af",
    "showdowns",
    "showdowns_won",
    "final_stack",
    "rebuys",
]


# =============================================================================
# Helpers
# =============================================================================
def _ensure_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _observer0_snapshot(agents, hand_seats: Iterable[int]) -> dict:
    """Return Oracle-seat-0's belief about every other seat at hand-end.

    ``{seat: (trust, entropy, top_arch, top_prob)}``. Falls back to neutral
    values for self (seat 0) and seats the observer has not yet seen.
    """
    observer = agents[0]
    snap: dict = {}
    has_trust = hasattr(observer, "trust_score")
    has_posterior = hasattr(observer, "posteriors")
    for seat in hand_seats:
        if seat == observer.seat or not has_trust:
            snap[seat] = ("", "", "", "")
            continue
        trust = float(observer.trust_score(seat))
        entropy = float(observer.entropy(seat))
        top_arch: str = ""
        top_prob: float = 0.0
        if has_posterior:
            post = observer.posteriors.get(seat)
            if post is not None:
                try:
                    idx = int(post.argmax())
                    top_arch = TRUST_TYPE_LIST[idx]
                    top_prob = float(post[idx])
                except Exception:
                    top_arch = ""
                    top_prob = 0.0
        snap[seat] = (trust, entropy, top_arch, top_prob)
    return snap


def _mean_trust_into(agents, target_seat: int) -> Optional[float]:
    """Table-average of every *other* agent's trust_score toward ``target_seat``.

    Returns ``None`` if any agent lacks the Stage 5 trust interface — the
    caller writes an empty cell for pre-Stage-5 rosters.
    """
    vals: List[float] = []
    for a in agents:
        if a.seat == target_seat:
            continue
        if not hasattr(a, "trust_score"):
            return None
        vals.append(float(a.trust_score(target_seat)))
    if not vals:
        return None
    return sum(vals) / len(vals)


# =============================================================================
# Writers
# =============================================================================
def write_actions_csv(hands, agents, output_path: str, run_id: str) -> int:
    """One row per ``ActionRecord`` across every hand. Returns row count.

    ``hands`` must be the list of ``Hand`` objects returned from
    ``table.play_hand`` / ``table.last_hand`` in play order — we read
    ``hand.action_log`` directly and attach a snapshot of observer-0's
    hand-end trust view.
    """
    _ensure_dir(output_path)
    n_rows = 0
    seats = list(range(len(agents)))
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ACTIONS_HEADER)
        for hand in hands:
            snap = _observer0_snapshot(agents, seats)
            for rec in hand.action_log:
                trust, entropy, top_arch, top_prob = snap.get(
                    rec.seat, ("", "", "", "")
                )
                writer.writerow([
                    run_id,
                    rec.hand_id,
                    rec.sequence_num,
                    rec.betting_round,
                    rec.seat,
                    rec.archetype,
                    rec.action_type.value,
                    rec.amount,
                    rec.pot_before,
                    rec.pot_after,
                    rec.stack_before,
                    rec.stack_after,
                    rec.bet_count,
                    rec.current_bet,
                    trust,
                    entropy,
                    top_arch,
                    top_prob,
                ])
                n_rows += 1
    return n_rows


def write_hands_csv(hands, agents, output_path: str, run_id: str) -> int:
    """One row per played hand. Returns row count.

    ``mean_trust_into_seat_N`` is the table-average of every OTHER agent's
    trust toward seat N, captured at hand-end. For the 8-seat roster we
    always emit 8 columns even if a seat never saw a hand (then the value
    is still the initial-prior trust ≈ 0.752).
    """
    _ensure_dir(output_path)
    n_rows = 0
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HANDS_HEADER)
        for hand in hands:
            walkover_winner = getattr(hand, "_walkover_winner", "")
            had_showdown = hand.showdown_data is not None
            row = [
                run_id,
                hand.hand_id,
                hand.dealer_seat,
                hand.sb_seat,
                hand.bb_seat,
                hand.final_pot,
                int(had_showdown),
                walkover_winner if walkover_winner != "" else "",
            ]
            for seat in range(8):
                mt = _mean_trust_into(agents, seat)
                row.append("" if mt is None else mt)
            writer.writerow(row)
            n_rows += 1
    return n_rows


def write_agent_stats_csv(agents, run_id: str, output_path: str) -> int:
    """One row per seat summarizing end-of-run behavioral stats."""
    _ensure_dir(output_path)
    n_rows = 0
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(AGENT_STATS_HEADER)
        for a in sorted(agents, key=lambda x: x.seat):
            stats = getattr(a, "stats", {})
            hands_dealt = stats.get("hands_dealt", 0)
            vpip_pct = (a.vpip() * 100.0) if hasattr(a, "vpip") else 0.0
            pfr_pct = (a.pfr() * 100.0) if hasattr(a, "pfr") else 0.0
            af = a.af() if hasattr(a, "af") else 0.0
            writer.writerow([
                run_id,
                a.seat,
                a.name,
                a.archetype,
                hands_dealt,
                f"{vpip_pct:.4f}",
                f"{pfr_pct:.4f}",
                f"{af:.4f}",
                stats.get("showdowns", 0),
                stats.get("showdowns_won", 0),
                a.stack,
                getattr(a, "rebuys", 0),
            ])
            n_rows += 1
    return n_rows
