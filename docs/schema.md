# SQLite schema reference

Every `runs.sqlite` database produced by `run_sim.py` contains six
tables that capture everything an analysis workflow needs: per-run
metadata, per-hand state, per-action logs, showdown reveals,
trust-snapshot history, and per-agent final stats. This document is
the authoritative schema reference plus a cookbook of example queries
for the Phase 1 research questions.

See `data/schema.sql` for the exact DDL and `data/sqlite_logger.py`
for the write path.

## Tables at a glance

| Table | Grain | Key columns | Rough row count per 10 000-hand seed |
|---|---|---|---|
| `runs` | one per seed per sim | `run_id` PK | 1 |
| `hands` | one per hand played | `(run_id, hand_id)` PK | ~10 000 |
| `actions` | one per agent action | `(run_id, hand_id, sequence_num)` | ~160 000 |
| `showdowns` | one per seat at showdown | `(run_id, hand_id, seat)` | ~6 000 |
| `trust_snapshots` | one per (observer, target) pair at hand-end | `(run_id, hand_id, observer, target)` | **~560 000** |
| `agent_stats` | one per seat per run (terminal) | `(run_id, seat)` PK | 8 |

`trust_snapshots` is by far the largest table. At 5 seeds × 10 000
hands × 8 observers × 7 targets = **2 800 000 rows** for the canonical
research run. Use the `(run_id, hand_id)` composite index when
filtering &mdash; every per-hand child table has one.

## `runs`

Root table. One row per `run_sim.py --seeds` list entry.

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER PK AUTOINCREMENT | Sequential, starts at 1 |
| `seed` | INTEGER | The RNG seed passed via `--seeds` |
| `num_hands` | INTEGER | Hands requested (not necessarily hands played if a run is interrupted) |
| `num_seats` | INTEGER | Always 8 in Phase 1 |
| `started_at` | TEXT | ISO-8601 UTC timestamp |
| `label` | TEXT | Optional `--label` from the CLI |
| `git_sha` | TEXT | Populated if available |

Query to list every completed run in a database:

```sql
SELECT run_id, seed, num_hands, started_at, label
FROM runs
ORDER BY run_id;
```

## `hands`

One row per hand. The `hand_id` restarts at 1 for each `run_id`
(matches `table.hand_number` in the engine).

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER NOT NULL | FK → `runs.run_id` |
| `hand_id` | INTEGER NOT NULL | 1-indexed within a run |
| `dealer` | INTEGER | Dealer button seat |
| `sb_seat` | INTEGER | Small blind seat |
| `bb_seat` | INTEGER | Big blind seat |
| `final_pot` | INTEGER | Chips awarded at the end of the hand |
| `had_showdown` | INTEGER (0/1) | Did 2+ players reach the river? |
| `walkover_winner` | INTEGER NULL | Seat that won by fold, or NULL if showdown |

Composite PK `(run_id, hand_id)`. No separate index needed.

## `actions`

One row per agent action. This is the main event log.

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER NOT NULL | FK → `hands.run_id` |
| `hand_id` | INTEGER NOT NULL | FK → `hands.hand_id` |
| `sequence_num` | INTEGER NOT NULL | Monotonic within a hand (1-indexed) |
| `seat` | INTEGER NOT NULL | Acting seat 0..7 |
| `archetype` | TEXT NOT NULL | "oracle", "sentinel", ..., "judge" |
| `betting_round` | TEXT NOT NULL | "preflop", "flop", "turn", "river" |
| `action_type` | TEXT NOT NULL | "fold", "check", "call", "bet", "raise" |
| `amount` | INTEGER NOT NULL | Chips moved by THIS action (0 for fold/check) |
| `pot_before` | INTEGER NOT NULL | Pot size immediately before this action |
| `pot_after` | INTEGER NOT NULL | Pot size immediately after |
| `stack_before` | INTEGER NOT NULL | Acting agent's stack before |
| `stack_after` | INTEGER NOT NULL | Acting agent's stack after |
| `bet_count` | INTEGER NOT NULL | Bets + raises so far this round (for cap tracking) |
| `current_bet` | INTEGER NOT NULL | Max per-player round contribution so far |

Index: `idx_actions_run_hand ON (run_id, hand_id)`.

## `showdowns`

One row per seat that reached showdown. `walkover_winner` hands produce
zero rows here.

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER NOT NULL | |
| `hand_id` | INTEGER NOT NULL | |
| `seat` | INTEGER NOT NULL | |
| `hole_cards` | TEXT NOT NULL | JSON list of treys Card ints, e.g. `"[268442665, 16787479]"` |
| `hand_rank` | INTEGER NOT NULL | treys rank (lower = better) |
| `won` | INTEGER NOT NULL | 0 or 1 |
| `pot_won` | INTEGER NOT NULL | Chips awarded (0 for losers) |

Index: `idx_showdowns_run_hand ON (run_id, hand_id)`.

To decode `hole_cards` into human-readable form you need `treys`:

```python
import json
from treys import Card
hole = json.loads(row['hole_cards'])
pretty = [Card.int_to_str(c) for c in hole]  # e.g. ['Ah', 'Kd']
```

## `trust_snapshots`

The Bayesian-trust time series. One row per (observer, target) pair
per hand. Inserted at the end of each hand, after the engine has
settled the pot and all trust posteriors have been updated.

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER NOT NULL | |
| `hand_id` | INTEGER NOT NULL | |
| `observer_seat` | INTEGER NOT NULL | The seat whose posterior this represents |
| `target_seat` | INTEGER NOT NULL | The seat this posterior is *about* |
| `trust` | REAL NOT NULL | `trust_score()` in [0, 1] |
| `entropy` | REAL NOT NULL | `entropy()` in [0, 3] bits |
| `top_archetype` | TEXT NOT NULL | Name of the highest-posterior archetype |
| `top_prob` | REAL NOT NULL | Probability mass on `top_archetype` in [0, 1] |

Index: `idx_trust_run_hand ON (run_id, hand_id)`.

**Scale note**: with 8 seats, every hand writes 8 × 7 = 56 rows. At
10 000 hands per seed, that's 560 000 rows per seed &mdash; the largest
table by a wide margin. Always filter on `run_id` and `hand_id` to
keep queries fast.

## `agent_stats`

One row per (run, seat). Written once at the end of the run with the
terminal cumulative stats for each agent.

| Column | Type | Description |
|---|---|---|
| `run_id` | INTEGER NOT NULL | |
| `seat` | INTEGER NOT NULL | |
| `archetype` | TEXT NOT NULL | |
| `hands_dealt` | INTEGER NOT NULL | Always equals `num_hands` in Phase 1 |
| `vpip_count` | INTEGER NOT NULL | Hands with any preflop call/bet/raise |
| `pfr_count` | INTEGER NOT NULL | Hands with any preflop bet/raise |
| `bets` | INTEGER NOT NULL | Total BET actions across the run |
| `raises` | INTEGER NOT NULL | Total RAISE actions |
| `calls` | INTEGER NOT NULL | Total CALL actions |
| `folds` | INTEGER NOT NULL | Total FOLD actions |
| `checks` | INTEGER NOT NULL | Total CHECK actions |
| `showdowns` | INTEGER NOT NULL | Times this seat reached showdown |
| `showdowns_won` | INTEGER NOT NULL | Times this seat won at showdown |
| `final_stack` | INTEGER NOT NULL | Chips held after the last hand |
| `rebuys` | INTEGER NOT NULL | Times this seat rebought |

Composite PK `(run_id, seat)`.

## Research query cookbook

Every query below assumes you've opened the database with:

```bash
# Python
import sqlite3
db = sqlite3.connect('runs.sqlite')
db.row_factory = sqlite3.Row
```

```bash
# CLI
sqlite3 runs.sqlite
```

### 1. Cross-seed chip outcome per archetype

Who beats whom over the whole research dataset? Averages and
standard deviations across all seeds:

```sql
SELECT
    archetype,
    AVG(final_stack)           AS mean_stack,
    AVG(final_stack + rebuys * 200) AS mean_adjusted,
    COUNT(*)                   AS num_seeds,
    ROUND(AVG(final_stack), 1) AS mean_raw,
    ROUND(
        SQRT(AVG((final_stack - (
            SELECT AVG(final_stack) FROM agent_stats a2 WHERE a2.archetype = a1.archetype
        )) * (final_stack - (
            SELECT AVG(final_stack) FROM agent_stats a3 WHERE a3.archetype = a1.archetype
        )))), 1) AS stack_stddev
FROM agent_stats a1
GROUP BY archetype
ORDER BY mean_stack DESC;
```

### 2. VPIP / PFR / AF comparison with Stage 4 measured values

Sanity check that the archetype behavior matches the Stage 4 test
results (Firestorm ~50% VPIP, Sentinel ~15%, Wall ~55%):

```sql
SELECT
    archetype,
    ROUND(100.0 * AVG(vpip_count * 1.0 / hands_dealt), 1) AS vpip_pct,
    ROUND(100.0 * AVG(pfr_count  * 1.0 / hands_dealt), 1) AS pfr_pct,
    ROUND(AVG((bets + raises) * 1.0 / CASE WHEN calls > 0 THEN calls ELSE 1 END), 2) AS af
FROM agent_stats
GROUP BY archetype
ORDER BY vpip_pct DESC;
```

### 3. Predator's posterior about each opponent, over time

How quickly does the Predator classify each opponent? This pulls the
top-archetype label and probability at key hand milestones:

```sql
SELECT
    t.hand_id,
    t.target_seat,
    a.archetype AS true_archetype,
    t.top_archetype AS predator_thinks,
    ROUND(t.top_prob, 3) AS prob,
    ROUND(t.trust, 3) AS trust,
    ROUND(t.entropy, 3) AS entropy
FROM trust_snapshots t
JOIN agent_stats a ON t.target_seat = a.seat AND t.run_id = a.run_id
WHERE t.run_id = 1
  AND t.observer_seat = 5             -- Predator is at seat 5
  AND t.target_seat != 5
  AND t.hand_id IN (100, 500, 1000, 2500, 5000, 10000)
ORDER BY t.hand_id, t.target_seat;
```

Expected: Wall (seat 3) identified at ~100% within 100 hands,
Firestorm (seat 2) within ~500 hands. Sentinel (seat 1) never
drops below ~33% top_prob because it clusters with Mirror and Judge.

### 4. When did Judge first trigger retaliation against Firestorm?

Judge (seat 7) switches to retaliatory params when `grievance[seat=2]`
reaches 5. We can detect the transition by finding the first hand
where Judge's `br` (computed from the actions table) jumps toward the
retaliatory value of 0.70:

```sql
-- Rolling 50-hand preflop bet rate for Judge across all runs
WITH judge_preflop AS (
    SELECT
        run_id,
        hand_id,
        SUM(CASE WHEN action_type IN ('bet','raise') THEN 1 ELSE 0 END) AS bets_raises,
        COUNT(*) AS actions
    FROM actions
    WHERE seat = 7 AND betting_round = 'preflop'
    GROUP BY run_id, hand_id
)
SELECT
    run_id,
    hand_id,
    SUM(bets_raises) OVER (
        PARTITION BY run_id ORDER BY hand_id
        ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) * 1.0 /
    NULLIF(SUM(actions) OVER (
        PARTITION BY run_id ORDER BY hand_id
        ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ), 0) AS rolling_br_50
FROM judge_preflop
WHERE hand_id IN (100, 250, 500, 1000, 2500, 5000, 10000)
ORDER BY run_id, hand_id;
```

If the Judge ever triggers, the rolling `br` should jump from ~0.10
(cooperative) toward ~0.70 (retaliatory) after the trigger hand.

### 5. Mean trust TOWARD each archetype (table-wide view)

For each target, average the trust that all other agents hold toward
it at the final hand of each run:

```sql
WITH final_hand AS (
    SELECT run_id, MAX(hand_id) AS last_hand FROM trust_snapshots GROUP BY run_id
)
SELECT
    ag.archetype AS target_archetype,
    ROUND(AVG(t.trust), 3) AS mean_trust,
    ROUND(AVG(t.entropy), 3) AS mean_entropy,
    COUNT(*) AS sample_size
FROM trust_snapshots t
JOIN final_hand fh ON t.run_id = fh.run_id AND t.hand_id = fh.last_hand
JOIN agent_stats ag ON t.run_id = ag.run_id AND t.target_seat = ag.seat
GROUP BY ag.archetype
ORDER BY mean_trust DESC;
```

Expected ordering (Phase 1 research hypothesis): Wall &gt; Sentinel
&asymp; Judge &asymp; Mirror &gt; Oracle &gt; Predator &gt; Phantom &gt; Firestorm.

### 6. Pot size distribution by archetype

Which archetypes drive the biggest pots? (Useful for showing how
much Firestorm "stirs the pot" relative to Sentinel.)

```sql
SELECT
    a.archetype,
    COUNT(DISTINCT a.run_id || '-' || a.hand_id) AS hands_involved,
    ROUND(AVG(h.final_pot), 1) AS mean_pot,
    ROUND(MAX(h.final_pot), 1) AS max_pot
FROM actions a
JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
WHERE a.betting_round = 'preflop'
  AND a.action_type IN ('bet', 'raise', 'call')
GROUP BY a.archetype
ORDER BY mean_pot DESC;
```

### 7. Showdown win rate per archetype

```sql
SELECT
    s.archetype_true AS archetype,
    SUM(s.won) AS wins,
    COUNT(*)   AS showdowns,
    ROUND(100.0 * SUM(s.won) / COUNT(*), 1) AS win_pct
FROM (
    SELECT
        sd.won,
        ag.archetype AS archetype_true
    FROM showdowns sd
    JOIN agent_stats ag ON sd.run_id = ag.run_id AND sd.seat = ag.seat
) s
GROUP BY s.archetype_true
ORDER BY win_pct DESC;
```

### 8. Sanity check: chip conservation

Every run should have `chip_delta = 0`:

```sql
SELECT
    run_id,
    SUM(final_stack) AS total_stack,
    SUM(rebuys) * 200 AS rebuy_chips,
    SUM(final_stack) - (SUM(rebuys) + 8) * 200 AS chip_delta
FROM agent_stats
GROUP BY run_id;
```

`chip_delta` should be exactly 0 for every `run_id`. If it's not, the
run is contaminated &mdash; investigate side-pot logic or rebuy accounting
before using the data.

### 9. Sanity check: orphan actions

Every `actions.hand_id` must exist in `hands`:

```sql
SELECT COUNT(*) AS orphan_actions
FROM actions a
LEFT JOIN hands h ON a.run_id = h.run_id AND a.hand_id = h.hand_id
WHERE h.hand_id IS NULL;
```

Should always return 0.

### 10. Trust convergence curve (for plotting)

Pull the mean trust + mean entropy about a specific seat, averaged
across all observers, at every hand. Output is suitable for a line
plot in matplotlib / pandas / whatever:

```sql
SELECT
    hand_id,
    ROUND(AVG(trust),   4) AS mean_trust,
    ROUND(AVG(entropy), 4) AS mean_entropy
FROM trust_snapshots
WHERE run_id = 1 AND target_seat = 2     -- Firestorm
GROUP BY hand_id
ORDER BY hand_id;
```

For a faster plot on large databases, sample every Nth hand:

```sql
... WHERE run_id = 1 AND target_seat = 2 AND hand_id % 50 = 0 ...
```

## Python helper snippets

### Open, query, close

```python
import sqlite3
db = sqlite3.connect('runs.sqlite')
db.row_factory = sqlite3.Row

rows = db.execute("SELECT * FROM runs").fetchall()
for r in rows:
    print(f"run {r['run_id']}: seed={r['seed']} hands={r['num_hands']}")

db.close()
```

### Bulk-load trust snapshots into pandas (for plotting)

```python
import pandas as pd
import sqlite3

db = sqlite3.connect('runs.sqlite')
df = pd.read_sql_query(
    "SELECT hand_id, observer_seat, target_seat, trust, entropy "
    "FROM trust_snapshots WHERE run_id = 1",
    db,
)
# Pivot so each (observer, target) is a column and rows are hands
pivot = df.pivot_table(
    index='hand_id',
    columns=['observer_seat', 'target_seat'],
    values='trust',
)
```

## Performance tips

1. **Always filter on `run_id` first**, then `hand_id`. Both are in
   the composite indexes, and SQLite uses them in declaration order.
2. **Use `EXPLAIN QUERY PLAN`** before running expensive queries:
   ```sql
   EXPLAIN QUERY PLAN
   SELECT ... FROM trust_snapshots WHERE ...;
   ```
   It should report `USING INDEX idx_trust_run_hand`. If it reports
   `SCAN TABLE`, your WHERE clause isn't index-friendly.
3. **Open with `PRAGMA synchronous = NORMAL` for reads** on large
   databases &mdash; skips fsync but is safe for read-only analysis.
4. **Stream large result sets** via `cursor.execute(...)` + `for row in cursor`
   rather than `fetchall()` when rows are in the millions.
