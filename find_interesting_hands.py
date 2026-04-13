#!/usr/bin/env python3
"""Find narratively interesting hands from the v3 dataset.

Usage: python find_interesting_hands.py --db runs_v3.sqlite > interesting_hands.txt
"""
import sqlite3
import sys
import json
from treys import Card

def card_str(treys_int):
    """Convert treys integer to readable string like 'Ah', 'Kd'."""
    try:
        return Card.int_to_str(treys_int)
    except Exception:
        return str(treys_int)

def cards_str(json_str):
    """Convert JSON list of treys ints to readable string."""
    try:
        ints = json.loads(json_str)
        return " ".join(card_str(c) for c in ints)
    except Exception:
        return json_str

def print_hand(db, run_id, hand_id, label=""):
    """Print complete hand details."""
    print(f"\n{'='*80}")
    print(f"  HAND #{hand_id} — {label}")
    print(f"{'='*80}")

    # Hand metadata
    row = db.execute("""
        SELECT dealer, sb_seat, bb_seat, final_pot, had_showdown, walkover_winner
        FROM hands WHERE run_id=? AND hand_id=?
    """, (run_id, hand_id)).fetchone()
    if not row:
        print("  [Hand not found]")
        return
    dealer, sb, bb, pot, sd, wo = row
    print(f"  Dealer=S{dealer}  SB=S{sb}  BB=S{bb}  Final Pot={pot}  "
          f"{'SHOWDOWN' if sd else 'WALKOVER to S'+str(wo)}")
    print()

    # Actions
    print("  ACTIONS:")
    print(f"  {'Seq':>3s}  {'Seat':8s}  {'Archetype':14s}  {'Round':8s}  {'Action':6s}  "
          f"{'Amt':>4s}  {'Pot':>8s}  {'Stack':>10s}  {'Bets':>4s}")
    print(f"  {'-'*3}  {'-'*8}  {'-'*14}  {'-'*8}  {'-'*6}  "
          f"{'-'*4}  {'-'*8}  {'-'*10}  {'-'*4}")
    for r in db.execute("""
        SELECT sequence_num, seat, archetype, betting_round, action_type, amount,
               pot_before, pot_after, stack_before, stack_after, bet_count
        FROM actions WHERE run_id=? AND hand_id=? ORDER BY sequence_num
    """, (run_id, hand_id)):
        seq, seat, arch, rnd, act, amt, pb, pa, sb2, sa, bc = r
        print(f"  {seq:3d}  S{seat:<7d}  {arch:14s}  {rnd:8s}  {act:6s}  "
              f"{amt:4d}  {pb:3d}->{pa:3d}  {sb2:4d}->{sa:4d}  {bc:4d}")

    # Showdown
    sd_rows = db.execute("""
        SELECT seat, archetype, hole_cards, hand_rank, won, pot_won
        FROM showdowns WHERE run_id=? AND hand_id=? ORDER BY hand_rank
    """, (run_id, hand_id)).fetchall()
    if sd_rows:
        print()
        print("  SHOWDOWN:")
        for seat, arch, hc, rank, won, pw in sd_rows:
            w = "WINNER" if won else "      "
            print(f"    S{seat} ({arch:12s})  {cards_str(hc):12s}  "
                  f"rank={rank:5d}  {w}  pot_won={pw}")

    # Trust snapshot (selected pairs)
    print()
    print("  TRUST SNAPSHOT (selected):")
    for r in db.execute("""
        SELECT observer_seat, target_seat, trust, entropy, top_archetype, top_prob
        FROM trust_snapshots WHERE run_id=? AND hand_id=?
        ORDER BY observer_seat, target_seat
    """, (run_id, hand_id)):
        obs, tgt, tr, ent, ta, tp = r
        # Only print interesting pairs
        if (obs == 7 and tgt == 2) or (obs == 5 and tgt in (2,3)) or \
           (tgt == 2 and obs in (0,3,7)) or (tgt == 7 and obs == 2) or \
           (obs == 6 and tgt == 2):
            print(f"    S{obs}->S{tgt}: trust={tr:.3f}  H={ent:.2f}  "
                  f"top={ta} p={tp:.3f}")


def main():
    db_path = "runs_v3.sqlite"
    for arg in sys.argv[1:]:
        if arg.startswith("--db"):
            continue
        if not arg.startswith("-"):
            db_path = arg
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            db_path = sys.argv[idx + 1]

    db = sqlite3.connect(db_path)
    RUN = 1  # seed=42

    print("=" * 80)
    print("  INTERESTING HANDS FROM THE v3 DATASET")
    print(f"  Database: {db_path}  |  Run: {RUN} (seed=42)")
    print("=" * 80)

    # ---------------------------------------------------------------
    # 1. JUDGE'S FIRST TRIGGER — find the first 5 hands where
    #    Firestorm (S2) bet/raised AND lost at showdown to Judge (S7)
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 1: JUDGE GRIEVANCE BUILDUP (Firestorm caught bluffing vs Judge)")
    bluff_hands = db.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=a.hand_id AND s2.seat=2
        JOIN showdowns s7 ON s7.run_id=? AND s7.hand_id=a.hand_id AND s7.seat=7
        WHERE a.run_id=? AND a.seat=2 AND a.action_type IN ('bet','raise')
          AND s2.won=0 AND s7.won=1
        ORDER BY a.hand_id
        LIMIT 8
    """, (RUN, RUN, RUN)).fetchall()

    for i, (hid,) in enumerate(bluff_hands):
        print_hand(db, RUN, hid,
                   f"Grievance #{i+1}: Firestorm caught bluffing against Judge")

    # ---------------------------------------------------------------
    # 2. FIRESTORM FOLD EQUITY — biggest pots won by walkover
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 2: FIRESTORM FOLD EQUITY (everyone folds to aggression)")
    for (hid,) in db.execute("""
        SELECT hand_id FROM hands
        WHERE run_id=? AND walkover_winner=2
        ORDER BY final_pot DESC LIMIT 3
    """, (RUN,)):
        print_hand(db, RUN, hid, "Firestorm wins big pot — nobody calls")

    # ---------------------------------------------------------------
    # 3. WALL CATCHES FIRESTORM — biggest pot where Wall beats Firestorm
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 3: WALL CATCHES FIRESTORM (passive justice)")
    for row in db.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=h.hand_id AND s2.seat=2
        JOIN showdowns s3 ON s3.run_id=? AND s3.hand_id=h.hand_id AND s3.seat=3
        WHERE h.run_id=? AND s3.won=1 AND s2.won=0
        ORDER BY h.final_pot DESC LIMIT 3
    """, (RUN, RUN, RUN)):
        print_hand(db, RUN, row[0], "Wall catches Firestorm at showdown")

    # ---------------------------------------------------------------
    # 4. BIGGEST POTS OVERALL (max action)
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 4: BIGGEST POTS (maximum action)")
    for row in db.execute("""
        SELECT hand_id, final_pot, had_showdown FROM hands
        WHERE run_id=? ORDER BY final_pot DESC LIMIT 3
    """, (RUN,)):
        label = f"MASSIVE POT ({row[1]} chips) — {'showdown' if row[2] else 'walkover'}"
        print_hand(db, RUN, row[0], label)

    # ---------------------------------------------------------------
    # 5. PREDATOR EXPLOITATION — hands where Predator exploits a
    #    classified opponent (bet rate changes when facing Wall/Firestorm)
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 5: PREDATOR EXPLOITATION (adaptive play)")
    # Find hands late in the game where Predator wins big against Wall or Firestorm
    for row in db.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns s5 ON s5.run_id=? AND s5.hand_id=h.hand_id AND s5.seat=5 AND s5.won=1
        JOIN showdowns s3 ON s3.run_id=? AND s3.hand_id=h.hand_id AND s3.seat=3 AND s3.won=0
        WHERE h.run_id=? AND h.hand_id > 500
        ORDER BY h.final_pot DESC LIMIT 2
    """, (RUN, RUN, RUN)):
        print_hand(db, RUN, row[0], "Predator beats Wall (exploitation)")

    for row in db.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns s5 ON s5.run_id=? AND s5.hand_id=h.hand_id AND s5.seat=5 AND s5.won=1
        JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=h.hand_id AND s2.seat=2 AND s2.won=0
        WHERE h.run_id=? AND h.hand_id > 500
        ORDER BY h.final_pot DESC LIMIT 2
    """, (RUN, RUN, RUN)):
        print_hand(db, RUN, row[0], "Predator beats Firestorm (exploitation)")

    # ---------------------------------------------------------------
    # 6. MIRROR IN ACTION — hands where Mirror is active with the
    #    most-aggressive opponent (Firestorm) showing reciprocal behavior
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 6: MIRROR RECIPROCITY (mirroring aggression)")
    for row in db.execute("""
        SELECT h.hand_id
        FROM hands h
        JOIN showdowns s6 ON s6.run_id=? AND s6.hand_id=h.hand_id AND s6.seat=6
        JOIN showdowns s2 ON s2.run_id=? AND s2.hand_id=h.hand_id AND s2.seat=2
        WHERE h.run_id=? AND h.hand_id > 300
        ORDER BY h.final_pot DESC LIMIT 3
    """, (RUN, RUN, RUN)):
        print_hand(db, RUN, row[0], "Mirror vs Firestorm at showdown")

    # ---------------------------------------------------------------
    # 7. TRUST COLLAPSE — find hands where trust toward Firestorm
    #    drops sharply (first hand where trust < 0.40)
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 7: TRUST COLLAPSE (Firestorm's reputation crashes)")
    row = db.execute("""
        SELECT hand_id FROM trust_snapshots
        WHERE run_id=? AND target_seat=2 AND observer_seat=0 AND trust < 0.40
        ORDER BY hand_id LIMIT 1
    """, (RUN,)).fetchone()
    if row:
        print_hand(db, RUN, row[0],
                   "Oracle's trust in Firestorm drops below 0.40 for first time")

    # Also find the hand just before for contrast
    if row:
        prev = db.execute("""
            SELECT hand_id FROM trust_snapshots
            WHERE run_id=? AND target_seat=2 AND observer_seat=0 AND hand_id < ? AND trust >= 0.50
            ORDER BY hand_id DESC LIMIT 1
        """, (RUN, row[0])).fetchone()
        if prev:
            print_hand(db, RUN, prev[0],
                       "Just before trust collapse — Oracle still trusts Firestorm at 0.50+")

    # ---------------------------------------------------------------
    # 8. PHANTOM'S DECEPTION — Phantom bluffs and gets caught
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 8: PHANTOM DECEPTION (the liar who can't take a punch)")
    for row in db.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        JOIN showdowns s4 ON s4.run_id=? AND s4.hand_id=a.hand_id AND s4.seat=4 AND s4.won=0
        WHERE a.run_id=? AND a.seat=4 AND a.action_type='bet'
          AND a.betting_round='river'
        ORDER BY a.hand_id LIMIT 2
    """, (RUN, RUN)):
        print_hand(db, RUN, row[0], "Phantom river bluff caught at showdown")

    # ---------------------------------------------------------------
    # 9. JUDGE POST-TRIGGER — first hand AFTER trigger where Judge
    #    retaliates against Firestorm
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 9: JUDGE RETALIATES (post-trigger aggression)")
    # Find hands after ~hand 250 where Judge raises/bets and Firestorm is involved
    for row in db.execute("""
        SELECT DISTINCT a.hand_id
        FROM actions a
        WHERE a.run_id=? AND a.seat=7 AND a.action_type IN ('bet','raise')
          AND a.hand_id > 250 AND a.hand_id < 500
          AND a.hand_id IN (
              SELECT DISTINCT hand_id FROM actions WHERE run_id=? AND seat=2
              AND action_type IN ('bet','raise')
          )
        ORDER BY a.hand_id LIMIT 3
    """, (RUN, RUN)):
        print_hand(db, RUN, row[0],
                   "Judge retaliates — aggressive play while Firestorm aggresses")

    # ---------------------------------------------------------------
    # 10. SENTINEL COOPERATION — a calm hand between honest players
    # ---------------------------------------------------------------
    print("\n\n>>> CATEGORY 10: COOPERATIVE EQUILIBRIUM (honest players, clean hand)")
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
    """, (RUN, RUN, RUN, RUN)):
        print_hand(db, RUN, row[0],
                   "Oracle vs Sentinel heads-up — honest players, clean poker")

    db.close()
    print("\n" + "=" * 80)
    print("  END OF INTERESTING HANDS")
    print("=" * 80)


if __name__ == "__main__":
    main()
