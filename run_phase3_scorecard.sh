#!/usr/bin/env bash
#
# Run Phase 3 LLM simulation and compute the metrics scorecard.
#
# Prerequisites:
#   pip install anthropic   (for Claude)
#   OR: ollama pull llama3.1:8b   (for local, free)
#
# Usage:
#   # Free local (Ollama)
#   ./run_phase3_scorecard.sh ollama llama3.1:8b 100
#
#   # Claude Haiku (fast, ~$0.05 for 100 hands)
#   ./run_phase3_scorecard.sh anthropic claude-haiku-4-5-20251001 100
#
#   # Claude Sonnet (higher quality, ~$0.50 for 100 hands)
#   ./run_phase3_scorecard.sh anthropic claude-sonnet-4-6-20250514 100

set -e

PROVIDER="${1:-ollama}"
MODEL="${2:-llama3.1:8b}"
HANDS="${3:-100}"
SEED="${4:-42}"
DB="runs_phase3_scorecard.sqlite"

echo "=============================================="
echo "Phase 3 Scorecard Run"
echo "=============================================="
echo "  Provider: $PROVIDER"
echo "  Model:    $MODEL"
echo "  Hands:    $HANDS"
echo "  Seed:     $SEED"
echo "  DB:       $DB"
echo "=============================================="
echo ""

# Step 1: Run Phase 3 simulation
echo ">>> Step 1/2: Running Phase 3 simulation..."
python3 phase3/run_phase3_chat.py \
    --provider "$PROVIDER" \
    --model "$MODEL" \
    --hands "$HANDS" \
    --seeds "$SEED" \
    --db "$DB"

echo ""

# Step 2: Compute metrics scorecard
echo ">>> Step 2/2: Computing metrics scorecard..."
python3 compute_metrics.py --db "$DB"

echo ""
echo "=============================================="
echo "Done! Compare these values against Phase 1 baseline"
echo "in docs/metrics_framework.md"
echo "=============================================="
