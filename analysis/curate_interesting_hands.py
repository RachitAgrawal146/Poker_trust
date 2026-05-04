"""Wrapper around find_interesting_hands.py: dump categorized hand
transcripts per seed into ``paper_resources/interesting_hands/``.

The categories were originally hand-tuned for the Phase 1 v3 dataset
(seed=42 hardcoded). This wrapper runs the same queries on every
run_id in any Phase-1/2-shaped SQLite, and writes one file per seed
plus a top-level highlights file with the most paper-worthy hands.

Usage::

    python3 analysis/curate_interesting_hands.py --db runs_phase2_unbounded.sqlite
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

# Reuse the existing print_hand and category logic.
from analysis import find_interesting_hands as fih  # noqa: E402


def per_seed_dump(db_path: Path, run_id: int, seed: int,
                  outdir: Path) -> Path:
    """Run the full find_interesting_hands flow for one run_id and
    capture stdout into a text file. The original script hardcodes
    RUN=1, so we monkey-patch that constant for the duration of the
    call."""
    out_path = outdir / f"phase2_unbounded_seed_{seed}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(db_path))
    buf = io.StringIO()

    # Re-implement the main() body inline so we can pass our own (db, RUN)
    # rather than relying on argv parsing.
    print_hand = fih.print_hand
    R = run_id

    with redirect_stdout(buf):
        print("=" * 80)
        print(f"  INTERESTING HANDS  --  seed {seed}, run_id {run_id}")
        print(f"  Database: {db_path}")
        print("=" * 80)

        print("\n\n>>> CATEGORY 1: JUDGE GRIEVANCE BUILDUP "
              "(Firestorm caught bluffing vs Judge)")
        bluff_hands = db.execute("""
            SELECT DISTINCT a.hand_id
            FROM actions a
            JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=a.hand_id AND s2.seat=2
            JOIN showdowns s7 ON s7.run_id=? AND s7.hand_id=a.hand_id AND s7.seat=7
            WHERE a.run_id=? AND a.seat=2 AND a.action_type IN ('bet','raise')
              AND s2.won=0 AND s7.won=1
            ORDER BY a.hand_id
            LIMIT 5
        """, (R, R, R)).fetchall()
        for i, (hid,) in enumerate(bluff_hands):
            print_hand(db, R, hid,
                       f"Grievance #{i+1}: Firestorm caught bluffing against Judge")

        print("\n\n>>> CATEGORY 2: FIRESTORM FOLD EQUITY "
              "(everyone folds to aggression)")
        for (hid,) in db.execute("""
            SELECT hand_id FROM hands
            WHERE run_id=? AND walkover_winner=2
            ORDER BY final_pot DESC LIMIT 3
        """, (R,)):
            print_hand(db, R, hid, "Firestorm wins big pot — nobody calls")

        print("\n\n>>> CATEGORY 3: WALL CATCHES FIRESTORM (passive justice)")
        for row in db.execute("""
            SELECT h.hand_id
            FROM hands h
            JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=h.hand_id AND s2.seat=2
            JOIN showdowns s3 ON s3.run_id=? AND s3.hand_id=h.hand_id AND s3.seat=3
            WHERE h.run_id=? AND s3.won=1 AND s2.won=0
            ORDER BY h.final_pot DESC LIMIT 3
        """, (R, R, R)):
            print_hand(db, R, row[0], "Wall catches Firestorm at showdown")

        print("\n\n>>> CATEGORY 4: BIGGEST POTS (maximum action)")
        for row in db.execute("""
            SELECT hand_id, final_pot, had_showdown FROM hands
            WHERE run_id=? ORDER BY final_pot DESC LIMIT 3
        """, (R,)):
            label = (f"MASSIVE POT ({row[1]} chips) -- "
                     f"{'showdown' if row[2] else 'walkover'}")
            print_hand(db, R, row[0], label)

        print("\n\n>>> CATEGORY 5: TRUST COLLAPSE "
              "(Firestorm's reputation crashes)")
        row = db.execute("""
            SELECT hand_id FROM trust_snapshots
            WHERE run_id=? AND target_seat=2 AND observer_seat=0 AND trust < 0.40
            ORDER BY hand_id LIMIT 1
        """, (R,)).fetchone()
        if row:
            print_hand(db, R, row[0],
                       "Oracle's trust in Firestorm drops below 0.40 for first time")

        print("\n\n>>> CATEGORY 6: PHANTOM DECEPTION "
              "(the liar who can't take a punch)")
        for row in db.execute("""
            SELECT DISTINCT a.hand_id
            FROM actions a
            JOIN showdowns s4 ON s4.run_id=? AND s4.hand_id=a.hand_id AND s4.seat=4 AND s4.won=0
            WHERE a.run_id=? AND a.seat=4 AND a.action_type='bet'
              AND a.betting_round='river'
            ORDER BY a.hand_id LIMIT 2
        """, (R, R)):
            print_hand(db, R, row[0], "Phantom river bluff caught at showdown")

        print("\n\n>>> CATEGORY 7: COOPERATIVE EQUILIBRIUM "
              "(honest players, clean hand)")
        for row in db.execute("""
            SELECT h.hand_id
            FROM hands h
            JOIN showdowns s0 ON s0.run_id=? AND s0.hand_id=h.hand_id AND s0.seat=0
            JOIN showdowns s1 ON s1.run_id=? AND s1.hand_id=h.hand_id AND s1.seat=1
            WHERE h.run_id=? AND h.final_pot > 20
              AND h.hand_id NOT IN (
                  SELECT hand_id FROM actions WHERE run_id=? AND seat IN (2,3,4)
                  AND action_type NOT IN ('fold')
              )
            ORDER BY h.final_pot DESC LIMIT 2
        """, (R, R, R, R)):
            print_hand(db, R, row[0],
                       "Oracle vs Sentinel heads-up -- honest players, clean poker")

        print("\n" + "=" * 80)
        print(f"  END OF SEED {seed}")
        print("=" * 80)

    db.close()
    out_path.write_text(buf.getvalue(), encoding="utf-8")
    print(f"  wrote {out_path}")
    return out_path


def write_highlights(out_paths: list, dst: Path) -> None:
    """Concatenate the BIGGEST POT from each seed into a single
    paper-ready highlights file."""
    sections = []
    for src in out_paths:
        text = src.read_text(encoding="utf-8")
        # Pull just the BIGGEST POTS section
        marker = ">>> CATEGORY 4:"
        end_marker = ">>> CATEGORY 5:"
        i = text.find(marker)
        j = text.find(end_marker)
        if i >= 0 and j > i:
            sections.append(f"\n--- from {src.name} ---\n")
            sections.append(text[i:j])
    if sections:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            "INTERESTING HANDS HIGHLIGHTS\n"
            "Biggest pots from every seed in the Phase 2 unbounded run.\n"
            + "\n".join(sections),
            encoding="utf-8",
        )
        print(f"  wrote {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", required=True,
        help="Phase 1/2-shaped SQLite to extract from.",
    )
    parser.add_argument(
        "--outdir", default="paper_resources/interesting_hands",
        help="Where to write per-seed text files.",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists() or db_path.stat().st_size < 5000:
        print(f"ERROR: {db_path} missing or LFS-pointer", file=sys.stderr)
        return 2

    out_dir = _REPO_ROOT / args.outdir

    conn = sqlite3.connect(str(db_path))
    runs = conn.execute("SELECT run_id, seed FROM runs ORDER BY seed").fetchall()
    conn.close()

    out_paths = []
    for run_id, seed in runs:
        out_paths.append(per_seed_dump(db_path, run_id, seed, out_dir))

    write_highlights(out_paths, out_dir / "_highlights.txt")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
