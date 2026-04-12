"""
Stage 7 persistent SQLite logger.

A ``SQLiteLogger`` owns one SQLite connection and writes the per-hand record
stream produced by the Stage 2 engine to the tables defined in
``data/schema.sql``. The ``Table`` class grew an optional ``logger`` kwarg in
Stage 7 — when set, ``Table.play_hand`` invokes ``logger.log_hand(run_id,
self.last_hand)`` after each hand so the engine itself never has to know
about persistence.

Design notes:

- The logger is **parallel** to ``data/visualizer_export.py``: the JSON
  exporter and the SQLite logger consume the same ``Hand`` object without
  interfering. Either (or both) can be attached to a run.
- We wrap the per-hand writes in a transaction to keep throughput high on
  the 10,000-hand research runs (~1M action rows per seed). Foreign-key
  enforcement is ON so orphan rows surface early in tests.
- Trust snapshots are optional: if the roster doesn't expose Stage 5's
  trust API (``posteriors``, ``trust_score``, ``entropy``), the logger
  silently skips the trust_snapshots table for that hand. Stage 4 and
  earlier agents remain loggable.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

from engine.actions import ActionRecord
from engine.game import Hand


__all__ = ["SQLiteLogger"]


_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def _git_sha() -> Optional[str]:
    """Best-effort current commit sha for run provenance."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        return out.decode("ascii").strip()
    except Exception:
        return None


class SQLiteLogger:
    """Opens a SQLite connection, creates tables on first use, and writes
    one row per engine event.

    Parameters
    ----------
    db_path : str
        Filesystem path, or ``":memory:"`` for an in-process database used
        by the stage7 extras.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path)) if db_path != ":memory:" else ""
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        # Foreign keys are off by default in SQLite; turn them on so the
        # extras' integrity checks catch broken writes.
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Batch writes aggressively — these runs generate ~1M actions per
        # seed and the default sync mode would dominate wall time.
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA journal_mode = MEMORY")
        self._create_tables()

    # ------------------------------------------------------------------
    def _create_tables(self) -> None:
        with open(_SCHEMA_PATH, "r") as f:
            ddl = f.read()
        self.conn.executescript(ddl)
        self.conn.commit()

    # ------------------------------------------------------------------
    def start_run(
        self,
        seed: int,
        num_hands: int,
        label: str,
        agents: Sequence,
    ) -> int:
        """Insert a ``runs`` row and return the new ``run_id``."""
        started = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO runs (seed, num_hands, num_seats, started_at, label, git_sha)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(seed),
                int(num_hands),
                int(len(agents)),
                started,
                label,
                _git_sha(),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    # ------------------------------------------------------------------
    def log_hand(self, run_id: int, hand: Hand) -> None:
        """Persist a single played ``Hand`` to all relevant tables.

        Wrapped in a single transaction so that a crash mid-run never leaves
        a partially-written hand behind.
        """
        if hand is None:
            return

        had_showdown = hand.showdown_data is not None
        walkover_winner: Optional[int] = None
        if not had_showdown:
            walkover_winner = getattr(hand, "_walkover_winner", None)

        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN")
            cur.execute(
                """
                INSERT INTO hands
                    (run_id, hand_id, dealer, sb_seat, bb_seat,
                     final_pot, had_showdown, walkover_winner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    int(hand.hand_id),
                    int(hand.dealer_seat),
                    int(hand.sb_seat),
                    int(hand.bb_seat),
                    int(hand.final_pot),
                    1 if had_showdown else 0,
                    walkover_winner,
                ),
            )
            self._insert_actions(cur, run_id, hand.hand_id, hand.action_log)
            if had_showdown:
                self._insert_showdowns(
                    cur, run_id, hand.hand_id, hand.showdown_data
                )
            self._insert_trust_snapshot(cur, run_id, hand)
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise

    # ------------------------------------------------------------------
    def _insert_actions(
        self,
        cur: sqlite3.Cursor,
        run_id: int,
        hand_id: int,
        action_log: Iterable[ActionRecord],
    ) -> None:
        rows = []
        for rec in action_log:
            rows.append(
                (
                    run_id,
                    int(hand_id),
                    int(rec.sequence_num),
                    int(rec.seat),
                    str(rec.archetype),
                    str(rec.betting_round),
                    rec.action_type.value,
                    int(rec.amount),
                    int(rec.pot_before),
                    int(rec.pot_after),
                    int(rec.stack_before),
                    int(rec.stack_after),
                    int(rec.bet_count),
                    int(rec.current_bet),
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO actions
                    (run_id, hand_id, sequence_num, seat, archetype,
                     betting_round, action_type, amount,
                     pot_before, pot_after, stack_before, stack_after,
                     bet_count, current_bet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    # ------------------------------------------------------------------
    def _insert_showdowns(
        self,
        cur: sqlite3.Cursor,
        run_id: int,
        hand_id: int,
        showdown_data: Iterable[dict],
    ) -> None:
        rows = []
        for entry in showdown_data:
            rows.append(
                (
                    run_id,
                    int(hand_id),
                    int(entry["seat"]),
                    json.dumps(list(entry["hole_cards"])),
                    int(entry["hand_rank"]),
                    1 if entry["won"] else 0,
                    int(entry["pot_won"]),
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO showdowns
                    (run_id, hand_id, seat, hole_cards, hand_rank, won, pot_won)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    # ------------------------------------------------------------------
    def _insert_trust_snapshot(
        self,
        cur: sqlite3.Cursor,
        run_id: int,
        hand: Hand,
    ) -> None:
        """Capture the full (observer, target) trust grid for Stage 5+ agents.

        Silently no-ops for rosters that don't expose the Stage 5 interface,
        so Stage 2/3/4 runs stay loggable.
        """
        seats = hand.table.seats
        try:
            from trust import TRUST_TYPE_LIST
        except Exception:
            TRUST_TYPE_LIST = None

        rows = []
        for observer in seats:
            posteriors = getattr(observer, "posteriors", None)
            trust_fn = getattr(observer, "trust_score", None)
            entropy_fn = getattr(observer, "entropy", None)
            if posteriors is None or trust_fn is None or entropy_fn is None:
                return  # Pre-Stage-5 roster — skip the whole grid.
            for target in seats:
                if target.seat == observer.seat:
                    continue
                post = posteriors.get(target.seat)
                if post is None or TRUST_TYPE_LIST is None:
                    top_arch = "unknown"
                    top_prob = 1.0 / 8
                else:
                    idx = int(post.argmax())
                    top_arch = TRUST_TYPE_LIST[idx]
                    top_prob = float(post[idx])
                rows.append(
                    (
                        run_id,
                        int(hand.hand_id),
                        int(observer.seat),
                        int(target.seat),
                        float(trust_fn(target.seat)),
                        float(entropy_fn(target.seat)),
                        top_arch,
                        top_prob,
                    )
                )
        if rows:
            cur.executemany(
                """
                INSERT INTO trust_snapshots
                    (run_id, hand_id, observer_seat, target_seat,
                     trust, entropy, top_archetype, top_prob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    # ------------------------------------------------------------------
    def log_agent_stats(self, run_id: int, table) -> None:
        """Write one ``agent_stats`` row per seat at the end of a run."""
        rows = []
        for agent in table.seats:
            stats = getattr(agent, "stats", {}) or {}
            rows.append(
                (
                    run_id,
                    int(agent.seat),
                    str(agent.archetype),
                    int(stats.get("hands_dealt", 0)),
                    int(stats.get("vpip_count", 0)),
                    int(stats.get("pfr_count", 0)),
                    int(stats.get("bets", 0)),
                    int(stats.get("raises", 0)),
                    int(stats.get("calls", 0)),
                    int(stats.get("folds", 0)),
                    int(stats.get("checks", 0)),
                    int(stats.get("showdowns", 0)),
                    int(stats.get("showdowns_won", 0)),
                    int(getattr(agent, "stack", 0)),
                    int(getattr(agent, "rebuys", 0)),
                )
            )
        self.conn.executemany(
            """
            INSERT INTO agent_stats
                (run_id, seat, archetype, hands_dealt,
                 vpip_count, pfr_count, bets, raises, calls, folds, checks,
                 showdowns, showdowns_won, final_stack, rebuys)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None  # type: ignore[assignment]
