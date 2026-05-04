#!/usr/bin/env bash
# Regenerate every artifact under paper_resources/ in one shot.
# Idempotent — safe to run repeatedly. Steps that need the unbounded
# SQLite are skipped automatically when the file is missing.
#
# Usage:
#   bash analysis/make_all_paper_resources.sh

set -euo pipefail

cd "$(dirname "$0")/.."

DB="runs_phase2_unbounded.sqlite"

echo "[1/5] Static figures from JSON + scorecards..."
python3 analysis/make_paper_figures.py

echo
echo "[2/5] Static tables (CSV + LaTeX)..."
python3 analysis/make_paper_tables.py

EXPECTED_SEEDS=5
SEED_COUNT=0
if [[ -f "$DB" && $(stat -c %s "$DB" 2>/dev/null || stat -f %z "$DB") -gt 5000 ]]; then
    SEED_COUNT=$(python3 -c "
import sqlite3, sys
try:
    c = sqlite3.connect('$DB')
    n = c.execute('SELECT COUNT(*) FROM agent_stats').fetchone()[0] // 8
    print(n)
except Exception:
    print(0)
")
fi

if [[ "$SEED_COUNT" -ge "$EXPECTED_SEEDS" ]]; then
    echo
    echo "[3/5] Phase 2 unbounded comparison (figures 07 + 10, scorecard, writeup)..."
    python3 analysis/phase2_unbounded_compare.py --db "$DB"

    echo
    echo "[4/5] Trajectory figures (08 + 09)..."
    python3 analysis/make_trajectory_figures.py --db "$DB" --tag phase2_unbounded

    echo
    echo "[5/5] Interesting hands per seed..."
    python3 analysis/curate_interesting_hands.py --db "$DB"
else
    echo
    echo "[3-5/5] SKIPPED: $DB has $SEED_COUNT/$EXPECTED_SEEDS completed seeds."
    echo "  Run (or wait for):"
    echo "    python3 phase2/adaptive/run_adaptive.py --hands 10000 \\"
    echo "        --seeds 42,137,256,512,1024 --db $DB \\"
    echo "        --trajectories phase2/adaptive/param_trajectories_unbounded.json \\"
    echo "        --optlog phase2/adaptive/optimization_log_unbounded.json \\"
    echo "        --unbounded"
fi

echo
echo "Done. paper_resources/ contents:"
find paper_resources -type f | sort
