# Phase 3: LLM Chat Agents

Eight LLM agents play Limit Texas Hold'em against each other. Each agent
calls an LLM on every decision point, receiving the game state and its
personality spec as context. The LLM reasons about the situation and
returns an action (FOLD, CHECK, CALL, BET, RAISE).

## Architecture

```
phase3/
  personality_specs/     # Qualitative + quantitative archetype specs (system prompts)
    oracle.md, sentinel.md, firestorm.md, wall.md,
    phantom.md, predator.md, mirror.md, judge.md
  llm_chat_agent.py      # LLMChatAgent + LLMChatJudge classes
  run_phase3_chat.py     # Simulation runner (--provider, --model, --hands)
  dealer.py              # Game integrity layer (action validation, chip audits)
  __init__.py
  README.md
```

## How It Works

1. Each agent gets its personality spec as the **system prompt**
2. On every decision, the agent receives the **game state**: hole cards,
   community cards, hand strength, pot size, cost to call, position,
   actions this round
3. The LLM responds with one word: FOLD, CHECK, CALL, BET, or RAISE
4. The Dealer validates the action and substitutes a legal default if needed
5. All trust/observation/stats machinery from Phase 1 BaseAgent is inherited

## Running

### Option A: Ollama (free, local)

```bash
# Install ollama: https://ollama.com
ollama pull llama3.1:8b
pip install openai

python phase3/run_phase3_chat.py --provider ollama --model llama3.1:8b --hands 100
```

### Option B: Claude API

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Haiku (fast, cheap — ~$0.05 per 100 hands)
python phase3/run_phase3_chat.py --provider anthropic --model claude-haiku-4-5-20251001 --hands 100

# Sonnet (higher quality — ~$0.50 per 100 hands)
python phase3/run_phase3_chat.py --provider anthropic --model claude-sonnet-4-20250514 --hands 50
```

### Options

```
--provider   ollama or anthropic (default: ollama)
--model      model name (default: llama3.1:8b)
--seeds      comma-separated seeds (default: 42)
--hands      hands per seed (default: 100)
--db         SQLite output path (default: runs_phase3_chat.sqlite)
--audit      dealer audit JSON path (default: dealer_audit_chat.json)
--ollama-url Ollama endpoint (default: http://localhost:11434/v1)
```

## Cost Estimates

| Hands | Haiku Cost | Sonnet Cost | Ollama | Wall Time (Ollama 8B) |
|-------|-----------|-------------|--------|----------------------|
| 100   | ~$0.05    | ~$0.50      | Free   | ~10 min              |
| 500   | ~$0.25    | ~$2.50      | Free   | ~50 min              |
| 1,000 | ~$0.50    | ~$5         | Free   | ~1.5 hrs             |

## Agent Classes

- **LLMChatAgent**: Used for oracle, sentinel, firestorm, wall, phantom,
  predator, mirror. Calls LLM per decision, parses action, fixes legality.
- **LLMChatJudge**: Extends LLMChatAgent with grievance tracking. When a
  triggered opponent aggresses, injects retaliation context into the prompt.

## Dependencies

- Phase 1 codebase (game engine, trust model, SQLite logger)
- `numpy`, `treys` (Phase 1 deps)
- For Ollama: `openai` package + Ollama running locally
- For Claude: `anthropic` package + `ANTHROPIC_API_KEY`

## Metrics Scorecard

After running Phase 3, compute the same metrics scorecard used in Phase 1
to measure whether LLM agents produce richer strategic behavior:

```bash
# One-step: run simulation + scorecard
./run_phase3_scorecard.sh ollama llama3.1:8b 100

# Or manually:
python phase3/run_phase3_chat.py --provider ollama --model llama3.1:8b --hands 500 --db phase3_run.sqlite
python compute_metrics.py --db phase3_run.sqlite
```

Compare output against Phase 1 baselines in `docs/metrics_framework.md`:

| Dimension | Phase 1 Baseline | Phase 3 Target |
|-----------|-----------------|----------------|
| Trust–Profit r | −0.838 | weaker (|r| < 0.60) |
| Trust–TEI r | −0.987 | weaker |
| Opponent Adaptation (OA) | 0.0003 | > 0.01 |
| Context Sensitivity (CS) | 0.069 | > 0.15 |
| Non-Stationarity (NS) | 0.002 | > 0.01 |
| Trust Manipulation (TMA) | +0.133 (spurious) | > 0.15 (with CoT) |
