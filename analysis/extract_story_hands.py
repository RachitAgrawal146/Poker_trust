"""Extract paper-narrative story hands from any phase's SQLite.

The "evolution story" arc threads through all four phases (P1, P2,
P3, P3.1). Each story slot is a hand selected by a specific SQL
query that fingerprints the dynamic we want to illustrate. This
script is phase-agnostic: pass any Phase-1/2/3-shape SQLite and a
phase tag, and it emits a single text file with the slot transcripts.

Story slots emitted (each tagged with the act they belong to):
    A1.1  Firestorm's biggest walkover                     (Phase 1)
    A1.2  Wall pays off Firestorm bluff                    (Phase 1)
    A1.3  Trust collapse: Oracle->Firestorm < 0.40         (Phase 1)
    A2.1  Late-game hand showing adapted dynamics          (Phase 2)
    A3.1  LLM Wall mechanically calls down                 (Phase 3)
    A3.2  LLM Phantom bluff caught                         (Phase 3)
    A4.1  Wall value-bets against Firestorm                (Phase 3.1)
    A4.2  Sentinel trust-farming hand                      (Phase 3.1)
    A4.3  Trap-inverted hand (positive r seed)             (Phase 3.1)

Each slot picks the best matching hand the SQLite contains. Slots
that don't apply to the phase (e.g., "trust collapse" makes no
sense in P3.1's 150-hand window) are skipped automatically.

Usage::

    python3 analysis/extract_story_hands.py \\
        --db runs_phase2_unbounded.sqlite \\
        --phase P2-unbounded \\
        --out paper_resources/interesting_hands/p2_unbounded_story.txt
"""

from __future__ import annotations

import argparse
import io
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analysis import find_interesting_hands as fih  # noqa: E402


# Map archetype name -> seat number. Both Phase 1/2 and Phase 3/3.1
# use the same canonical seat order so this works everywhere.
SEAT_OF = {
    "oracle": 0, "sentinel": 1, "firestorm": 2, "wall": 3,
    "phantom": 4, "predator": 5, "mirror": 6, "judge": 7,
}


def _resolve_seat(conn, run_id, archetype_substring):
    """Look up seat by archetype substring (handles Phase 3's 'LLM-Firestorm'
    naming as well as Phase 1's bare 'firestorm')."""
    rows = conn.execute("""
        SELECT seat, archetype FROM agent_stats WHERE run_id=?
    """, (run_id,)).fetchall()
    target = archetype_substring.lower()
    for seat, arch in rows:
        if target in (arch or "").lower():
            return seat
    # Fall back to canonical seat order
    return SEAT_OF.get(archetype_substring.lower())


def _emit_slot(conn, run_id, hand_id, label, expected_dynamics):
    """Print one slot header + the hand transcript."""
    if hand_id is None:
        print(f"\n  [{label}] -- no matching hand found in this database\n")
        return
    print()
    print(f"  >>> {label}")
    print(f"      Expected dynamics: {expected_dynamics}")
    fih.print_hand(conn, run_id, hand_id, label)


# ---------------------------------------------------------------------------
# Slot queries
# ---------------------------------------------------------------------------

def slot_firestorm_walkover(conn, run_id):
    s_fs = _resolve_seat(conn, run_id, "firestorm")
    if s_fs is None:
        return None
    row = conn.execute("""
        SELECT hand_id FROM hands
        WHERE run_id=? AND walkover_winner=?
        ORDER BY final_pot DESC LIMIT 1
    """, (run_id, s_fs)).fetchone()
    return row[0] if row else None


def slot_wall_pays_off_firestorm(conn, run_id):
    """Hand where Firestorm bet/raised, won the showdown, AND Wall
    contributed to the pot via call. The "Wall pays off the bluff" hand
    is actually any showdown where Firestorm has weak cards but bets
    aggressively and Wall calls -- but in DB-only terms we approximate
    this as "Firestorm won showdown with hand_rank > 4000 (worse half)
    while Wall called preflop"."""
    s_fs = _resolve_seat(conn, run_id, "firestorm")
    s_wall = _resolve_seat(conn, run_id, "wall")
    if s_fs is None or s_wall is None:
        return None
    row = conn.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns sf ON sf.run_id=h.run_id AND sf.hand_id=h.hand_id
                          AND sf.seat=? AND sf.won=1 AND sf.hand_rank > 3500
        WHERE h.run_id=? AND h.had_showdown=1
          AND EXISTS (
            SELECT 1 FROM actions a
            WHERE a.run_id=h.run_id AND a.hand_id=h.hand_id
              AND a.seat=? AND a.action_type='call'
          )
        ORDER BY h.final_pot DESC LIMIT 1
    """, (s_fs, run_id, s_wall)).fetchone()
    return row[0] if row else None


def slot_trust_collapse(conn, run_id):
    """First hand where Oracle's posterior over Firestorm drops below 0.40."""
    s_fs = _resolve_seat(conn, run_id, "firestorm")
    s_or = _resolve_seat(conn, run_id, "oracle")
    if s_fs is None or s_or is None:
        return None
    row = conn.execute("""
        SELECT MIN(hand_id) FROM trust_snapshots
        WHERE run_id=? AND target_seat=? AND observer_seat=? AND trust < 0.40
    """, (run_id, s_fs, s_or)).fetchone()
    return row[0] if row and row[0] else None


def slot_late_game_adapted(conn, run_id):
    """A late-game hand (>= 70% through the run) where Firestorm bet
    aggressively but lost or got called -- a hand that shows the
    adaptive system has learned something."""
    s_fs = _resolve_seat(conn, run_id, "firestorm")
    if s_fs is None:
        return None
    total = conn.execute(
        "SELECT MAX(hand_id) FROM hands WHERE run_id=?", (run_id,)
    ).fetchone()[0] or 100
    cutoff = int(total * 0.7)
    row = conn.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns sf ON sf.run_id=h.run_id AND sf.hand_id=h.hand_id
                          AND sf.seat=? AND sf.won=0
        WHERE h.run_id=? AND h.hand_id >= ? AND h.had_showdown=1
        ORDER BY h.final_pot DESC LIMIT 1
    """, (s_fs, run_id, cutoff)).fetchone()
    return row[0] if row else None


def slot_phantom_bluff_caught(conn, run_id):
    s_ph = _resolve_seat(conn, run_id, "phantom")
    if s_ph is None:
        return None
    row = conn.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        JOIN showdowns s ON s.run_id=a.run_id AND s.hand_id=a.hand_id
                         AND s.seat=? AND s.won=0 AND s.hand_rank > 4000
        WHERE a.run_id=? AND a.seat=?
          AND a.action_type IN ('bet', 'raise')
          AND a.betting_round IN ('turn', 'river')
        ORDER BY a.hand_id LIMIT 1
    """, (s_ph, run_id, s_ph)).fetchone()
    return row[0] if row else None


def slot_wall_value_bet(conn, run_id):
    """A hand where Wall bet or raised AND won the showdown.
    Phase 3.1-specific dynamic: under reasoning, Wall stops being a
    pure calling station and starts extracting value with strong hands."""
    s_wall = _resolve_seat(conn, run_id, "wall")
    if s_wall is None:
        return None
    row = conn.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        JOIN showdowns s ON s.run_id=a.run_id AND s.hand_id=a.hand_id
                         AND s.seat=? AND s.won=1
        WHERE a.run_id=? AND a.seat=?
          AND a.action_type IN ('bet', 'raise')
        ORDER BY a.hand_id DESC LIMIT 1
    """, (s_wall, run_id, s_wall)).fetchone()
    return row[0] if row else None


def slot_sentinel_late_aggression(conn, run_id):
    """A late-game hand where Sentinel bet/raised in a big pot.
    Phase 3.1-specific: Sentinel "trust farming" -- builds reputation
    early, cashes in late."""
    s_sn = _resolve_seat(conn, run_id, "sentinel")
    if s_sn is None:
        return None
    total = conn.execute(
        "SELECT MAX(hand_id) FROM hands WHERE run_id=?", (run_id,)
    ).fetchone()[0] or 100
    cutoff = int(total * 0.5)
    row = conn.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        JOIN hands h ON h.run_id=a.run_id AND h.hand_id=a.hand_id
        WHERE a.run_id=? AND a.seat=?
          AND a.action_type IN ('bet', 'raise')
          AND h.hand_id >= ?
        ORDER BY h.final_pot DESC LIMIT 1
    """, (run_id, s_sn, cutoff)).fetchone()
    return row[0] if row else None


def slot_biggest_pot(conn, run_id):
    row = conn.execute("""
        SELECT hand_id FROM hands
        WHERE run_id=? ORDER BY final_pot DESC LIMIT 1
    """, (run_id,)).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

SLOTS = [
    ("A1.1  Firestorm walkover",
     "fold equity wins -- nobody calls Firestorm's aggression",
     slot_firestorm_walkover),
    ("A1.2  Wall pays off Firestorm",
     "the trap in microcosm: trustworthy player loses to bluffer",
     slot_wall_pays_off_firestorm),
    ("A1.3  First trust collapse",
     "Oracle's posterior of Firestorm crosses below 0.40",
     slot_trust_collapse),
    ("A2.1  Late-game adapted hand",
     "after thousands of hands, Firestorm sometimes loses",
     slot_late_game_adapted),
    ("A3.1  Phantom bluff caught",
     "deception works -- but not always",
     slot_phantom_bluff_caught),
    ("A4.1  Wall value-betting",
     "P3.1: trustworthy agent extracts value instead of being exploited",
     slot_wall_value_bet),
    ("A4.2  Sentinel late aggression",
     "P3.1: trust-farming -- early cooperation, late exploitation",
     slot_sentinel_late_aggression),
    ("A_x  Biggest pot of the run",
     "a context-free spectacle hand, useful regardless of phase",
     slot_biggest_pot),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True,
                        help="Phase-1/2/3-shape SQLite to extract from.")
    parser.add_argument("--phase", required=True,
                        help="Phase tag for the output (P1, P2-bounded, "
                             "P2-unbounded, P3, P3.1, ...).")
    parser.add_argument("--out", default=None,
                        help="Output text file. Default: "
                             "paper_resources/interesting_hands/<phase>_story.txt")
    parser.add_argument("--seed", type=int, default=None,
                        help="If set, only extract from this seed's run. "
                             "Default: use the first run in the DB.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: {db_path} not found", file=sys.stderr)
        return 2
    if db_path.stat().st_size < 5000:
        print(f"ERROR: {db_path} looks like an LFS pointer "
              f"({db_path.stat().st_size} bytes)", file=sys.stderr)
        return 2

    out_path = Path(args.out or
        f"paper_resources/interesting_hands/{args.phase.lower().replace('.', '')}_story.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    if args.seed is not None:
        runs = conn.execute(
            "SELECT run_id, seed FROM runs WHERE seed=? ORDER BY run_id",
            (args.seed,)
        ).fetchall()
    else:
        runs = conn.execute(
            "SELECT run_id, seed FROM runs ORDER BY run_id LIMIT 1"
        ).fetchall()

    if not runs:
        print(f"ERROR: no runs found in {db_path}", file=sys.stderr)
        return 2

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("=" * 80)
        print(f"  EVOLUTION-STORY HANDS  --  {args.phase}")
        print(f"  Source: {db_path}")
        print("=" * 80)

        for run_id, seed in runs:
            print()
            print(f"  ----- seed {seed} (run_id={run_id}) -----")
            for label, dynamics, fn in SLOTS:
                hid = fn(conn, run_id)
                _emit_slot(conn, run_id, hid, label, dynamics)
        print()
        print("=" * 80)
        print(f"  END {args.phase}")
        print("=" * 80)

    conn.close()
    out_path.write_text(buf.getvalue(), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
