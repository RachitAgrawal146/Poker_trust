-- SQLite schema for the Stage 7 persistent hand logger.
--
-- One database file can hold many simulation runs (one per seed, or many
-- parameter sweeps of the same seed). The ``runs`` table is the root and
-- every other table keys off ``run_id``.
--
-- Integer-only where possible; archetype names are short strings. Hole
-- cards are serialized as compact JSON ("[268442665,16787479]" style treys
-- ints) so the schema stays human-inspectable without a second table.
--
-- Indexes: every per-hand child table has an index on (run_id, hand_id)
-- because every per-hand read at analysis time filters on that composite
-- key.

CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    seed        INTEGER NOT NULL,
    num_hands   INTEGER NOT NULL,
    num_seats   INTEGER NOT NULL,
    started_at  TEXT    NOT NULL,
    label       TEXT,
    git_sha     TEXT
);

CREATE TABLE IF NOT EXISTS hands (
    run_id          INTEGER NOT NULL,
    hand_id         INTEGER NOT NULL,
    dealer          INTEGER NOT NULL,
    sb_seat         INTEGER NOT NULL,
    bb_seat         INTEGER NOT NULL,
    final_pot       INTEGER NOT NULL,
    had_showdown    INTEGER NOT NULL,
    walkover_winner INTEGER,
    PRIMARY KEY (run_id, hand_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS actions (
    run_id         INTEGER NOT NULL,
    hand_id        INTEGER NOT NULL,
    sequence_num   INTEGER NOT NULL,
    seat           INTEGER NOT NULL,
    archetype      TEXT    NOT NULL,
    betting_round  TEXT    NOT NULL,
    action_type    TEXT    NOT NULL,
    amount         INTEGER NOT NULL,
    pot_before     INTEGER NOT NULL,
    pot_after      INTEGER NOT NULL,
    stack_before   INTEGER NOT NULL,
    stack_after    INTEGER NOT NULL,
    bet_count      INTEGER NOT NULL,
    current_bet    INTEGER NOT NULL,
    FOREIGN KEY (run_id, hand_id) REFERENCES hands(run_id, hand_id)
);

CREATE TABLE IF NOT EXISTS showdowns (
    run_id      INTEGER NOT NULL,
    hand_id     INTEGER NOT NULL,
    seat        INTEGER NOT NULL,
    hole_cards  TEXT    NOT NULL,
    hand_rank   INTEGER NOT NULL,
    won         INTEGER NOT NULL,
    pot_won     INTEGER NOT NULL,
    FOREIGN KEY (run_id, hand_id) REFERENCES hands(run_id, hand_id)
);

CREATE TABLE IF NOT EXISTS trust_snapshots (
    run_id         INTEGER NOT NULL,
    hand_id        INTEGER NOT NULL,
    observer_seat  INTEGER NOT NULL,
    target_seat    INTEGER NOT NULL,
    trust          REAL    NOT NULL,
    entropy        REAL    NOT NULL,
    top_archetype  TEXT    NOT NULL,
    top_prob       REAL    NOT NULL,
    FOREIGN KEY (run_id, hand_id) REFERENCES hands(run_id, hand_id)
);

CREATE TABLE IF NOT EXISTS agent_stats (
    run_id         INTEGER NOT NULL,
    seat           INTEGER NOT NULL,
    archetype      TEXT    NOT NULL,
    hands_dealt    INTEGER NOT NULL,
    vpip_count     INTEGER NOT NULL,
    pfr_count      INTEGER NOT NULL,
    bets           INTEGER NOT NULL,
    raises         INTEGER NOT NULL,
    calls          INTEGER NOT NULL,
    folds          INTEGER NOT NULL,
    checks         INTEGER NOT NULL,
    showdowns      INTEGER NOT NULL,
    showdowns_won  INTEGER NOT NULL,
    final_stack    INTEGER NOT NULL,
    rebuys         INTEGER NOT NULL,
    PRIMARY KEY (run_id, seat),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_actions_run_hand
    ON actions(run_id, hand_id);
CREATE INDEX IF NOT EXISTS idx_showdowns_run_hand
    ON showdowns(run_id, hand_id);
CREATE INDEX IF NOT EXISTS idx_trust_run_hand
    ON trust_snapshots(run_id, hand_id);
