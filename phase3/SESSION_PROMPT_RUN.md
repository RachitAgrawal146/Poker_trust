# Phase 3 LLM Simulation — Claude Code Session Prompt

## What This Session Does

You are running Phase 3 of the Poker Trust Simulation. This session plays
8-player Limit Texas Hold'em where each player is controlled by YOU — Claude —
making decisions based on a personality spec. You are ALL EIGHT players
simultaneously, playing against yourself.

The game engine handles dealing, pot management, and showdowns. Your job is to
make poker decisions for each agent at each decision point, staying in character.

## Critical Context

This is a research project studying whether observation-based trust systems
inherently reward exploitation over cooperation. Phases 1 and 2 (rule-based
and ML agents) found a strong anticorrelation (r = −0.84) between how trusted
an agent is and how much money it makes. Phase 3 tests whether agents capable
of REASONING about trust can break this pattern.

We measure 6 metrics (see docs/metrics_framework.md):
- Trust Exploitation Index (TEI): profit from dynamics vs. card quality
- Context Sensitivity (CS): does behavior depend on recent history?
- Opponent Adaptation (OA): does behavior differ per opponent?
- Non-Stationarity (NS): does strategy change over time?
- Strategic Unpredictability (SU): how hard to classify?
- Trust Manipulation (TMA): does the agent manage its own reputation?

Phase 1 agents scored near-zero on OA, NS, and CS. Your job as LLM agents
is to see if reasoning can do better.

## How to Run

The simulation infrastructure is already built. Run this from the repo root:

```bash
cd /home/user/Poker_trust

# Install deps (if not already)
pip install treys numpy

# Run the Phase 3 simulation
python phase3/run_phase3_chat.py \
    --provider anthropic \
    --model claude-sonnet-4-6-20250514 \
    --hands 500 \
    --seeds 42 \
    --db runs_phase3.sqlite

# Then compute the metrics scorecard
python compute_metrics.py --db runs_phase3.sqlite
```

**IMPORTANT**: The `run_phase3_chat.py` script calls the Anthropic API
internally. The `--provider anthropic` flag uses the ANTHROPIC_API_KEY
environment variable. If that's not set, use Ollama instead:

```bash
ollama pull llama3.1:8b
pip install openai
python phase3/run_phase3_chat.py \
    --provider ollama --model llama3.1:8b \
    --hands 500 --seeds 42 --db runs_phase3.sqlite
```

## The Eight Personalities You Play

Each agent has a personality spec in `phase3/personality_specs/`. The system
prompt loaded from that file tells the LLM HOW to play. Here's a summary:

| Seat | Name | Personality | Key Behavior |
|------|------|-------------|-------------|
| 0 | Oracle | Nash baseline | Balanced, moderate aggression, hard to exploit |
| 1 | Sentinel | Tight-aggressive | Only plays strong hands, folds everything else |
| 2 | Firestorm | Maniac | Bets/raises EVERYTHING regardless of hand strength |
| 3 | Wall | Calling station | Calls everything, never bets, never folds |
| 4 | Phantom | Deceiver | Bets early rounds to bluff, folds to resistance later |
| 5 | Predator | Exploiter | Reads opponents, adjusts strategy to exploit weaknesses |
| 6 | Mirror | Tit-for-tat | Copies the play style of the most active opponent |
| 7 | Judge | Grudger | Cooperates until opponent bluffs 5 times, then retaliates forever |

## The Dealer

The Dealer layer (phase3/dealer.py) ensures game integrity:

1. **Action Validation**: Every LLM response is checked for legality.
   - cost_to_call == 0? Only CHECK or BET allowed.
   - cost_to_call > 0? Only FOLD, CALL, or RAISE allowed.
   - Bet cap reached? RAISE → CALL automatically.
   - Illegal actions are logged and substituted.

2. **Chip Conservation**: After every hand, total chips must equal
   (num_seats + rebuys) × starting_stack. Any discrepancy halts the run.

3. **Anomaly Detection**: Rolling VPIP and AF tracked per agent against
   personality spec targets. If an agent drifts beyond tolerance, it's flagged:
   - Firestorm VPIP too low → not aggressive enough
   - Wall AF too high → betting too much (should be passive)
   - etc.

   The dealer audit is saved to `dealer_audit_chat.json` at end of run.

## What To Check After The Run

1. **Dealer audit**: Review `dealer_audit_chat.json` for:
   - How many action substitutions (illegal LLM outputs)
   - Any chip conservation failures
   - Any personality anomalies (agents playing out of character)

2. **Metrics scorecard**: Run `python compute_metrics.py --db runs_phase3.sqlite`
   and compare against Phase 1 baselines:

   | Dimension | Phase 1 Baseline | Phase 3 Target |
   |-----------|-----------------|----------------|
   | Trust–Profit r | −0.838 | weaker? |
   | Trust–TEI r | −0.987 | weaker? |
   | Opponent Adaptation (OA) | 0.0003 | > 0.01 |
   | Context Sensitivity (CS) | 0.069 | > 0.15 |
   | Non-Stationarity (NS) | 0.002 | > 0.01 |

3. **LLM stats**: The runner prints per-agent LLM call counts, failure rates,
   and latency. Flag any agent with >10% failure rate.

## File Layout Reference

```
Poker_trust/
├── phase3/
│   ├── llm_chat_agent.py       # LLMChatAgent + LLMChatJudge
│   ├── dealer.py               # Action validation + chip audit + anomaly detection
│   ├── run_phase3_chat.py      # Simulation runner
│   ├── personality_specs/      # 8 personality markdown files (system prompts)
│   └── README.md
├── engine/                     # Game engine (shared with Phases 1+2)
├── agents/base_agent.py        # BaseAgent with trust model
├── trust/bayesian_model.py     # Bayesian posterior updates
├── data/sqlite_logger.py       # SQLite persistence
├── compute_metrics.py          # 6-dimension metrics scorecard
├── docs/metrics_framework.md   # Full metrics definitions + Phase 1 baselines
└── reports/metrics_scorecard.txt  # Phase 1 computed results
```

## Troubleshooting

- **"No module named anthropic"**: `pip install anthropic`
- **"No module named openai"**: `pip install openai` (needed for Ollama)
- **LLM call failures**: Check API key, model name, network. Failures fall back
  to CHECK (no bet) or FOLD (facing bet).
- **Simulation hangs**: Hand strength Monte Carlo can rarely loop. Kill and
  restart with same seed — engine is deterministic.
- **Dealer substitution rate >20%**: The LLM is struggling with action legality.
  Try a larger model (Sonnet instead of Haiku).

## Success Criteria

The run is successful if:
1. Chip conservation passes (no leaks)
2. Dealer substitution rate < 15%
3. All 8 personality anomalies are reasonable (check audit JSON)
4. Metrics scorecard completes without errors
5. Results are committed and pushed to the `main` branch

After completion, commit the scorecard output and dealer audit to the repo,
then push to main. Save the SQLite database locally (gitignored).
