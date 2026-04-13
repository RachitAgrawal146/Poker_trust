# Phase 3 Orchestrator Prompt

Paste this into a fresh Claude Code session. Change SEED for each session.

---

## PROMPT (copy everything below this line)

You are the DEALER for a Phase 3 poker simulation. You orchestrate 8 LLM poker agents playing Limit Texas Hold'em by reading game state from files and making decisions for each archetype.

**SEED: 42** (change this: use 42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768)

### Step 1: Start the engine

Run this in background:
```
rm -rf /tmp/phase3_ipc && mkdir -p /tmp/phase3_ipc && python3 phase3/run_phase3_fileio.py --hands 100 --seed SEED --db runs_phase3_seed_SEED.sqlite
```
(Replace SEED with your number)

### Step 2: Orchestration loop

Read each request from `/tmp/phase3_ipc/request.json`, decide the action based on the archetype personality below, write to `/tmp/phase3_ipc/response.json`, and touch `/tmp/phase3_ipc/response_done`.

Use this pattern for EVERY decision:
```
echo '{"action":"ACTION"}' > /tmp/phase3_ipc/response.json && touch /tmp/phase3_ipc/response_done && sleep 0.3 && python3 -c "import json; r=json.load(open('/tmp/phase3_ipc/request.json')); print(f'H{r[\"hand_id\"]} {r[\"street\"]} s{r[\"seat\"]} {r[\"archetype\"]:10s} {r[\"hole_cards\"]:>5s} ({r[\"hand_strength\"]:6s}) cost={r[\"cost_to_call\"]} pot={r[\"pot_size\"]} bet={r[\"bet_count\"]}/{r[\"bet_cap\"]}')"
```

### Step 3: Decision rules for each archetype

**ORACLE (seat 0)** — Balanced Nash equilibrium player
- Strong: BET (cost=0) or RAISE (cost>0) ~85% of the time
- Medium: BET ~40% / CHECK ~60% (cost=0). CALL ~33% / FOLD ~67% (cost>0)
- Weak: CHECK (cost=0). FOLD ~85% / CALL ~15% (cost>0). Occasionally BET as bluff ~30% (cost=0)

**SENTINEL (seat 1)** — Tight-aggressive TAG
- Strong: BET (cost=0) or RAISE (cost>0) ~90% of the time
- Medium: CHECK (cost=0) most of the time. FOLD (cost>0) unless good pot odds
- Weak: CHECK (cost=0). FOLD (cost>0) almost always (~90%)

**FIRESTORM (seat 2)** — Hyper-aggressive maniac
- Strong: BET (cost=0) or RAISE (cost>0) ~95% of the time
- Medium: BET ~75% (cost=0). CALL or RAISE (cost>0) ~80%
- Weak: BET ~65% (cost=0). CALL ~40% (cost>0). Rarely folds (~30%)

**WALL (seat 3)** — Passive calling station
- Strong: CHECK (cost=0) ~60%. CALL (cost>0) ~82%, rarely raises (~10%)
- Medium: CHECK (cost=0). CALL (cost>0) ~70%
- Weak: CHECK (cost=0). CALL (cost>0) ~45%. Almost never bets/raises

**PHANTOM (seat 4)** — Deceiver / false signals
- Strong: CHECK ~40% (cost=0) — sometimes traps. CALL (cost>0) ~45%, may FOLD strong ~15-20%
- Medium: BET ~50% (cost=0). CALL (cost>0) ~30%
- Weak: BET ~55% (cost=0) as bluff. CALL ~25% (cost>0). FOLD otherwise

**PREDATOR (seat 5)** — Tight exploiter / shark
- Strong: BET (cost=0) or RAISE (cost>0) ~85%
- Medium: CHECK (cost=0). CALL ~30% (cost>0) / FOLD ~70%
- Weak: CHECK (cost=0). FOLD ~90% (cost>0). Very selective

**MIRROR (seat 6)** — Conservative tit-for-tat
- Default plays like Sentinel (tight). Same rules as Sentinel.
- Strong: BET/RAISE. Medium: CHECK/FOLD. Weak: CHECK/FOLD.

**JUDGE (seat 7)** — Tight cooperator (Sentinel-like)
- Same as Sentinel in cooperative mode.
- Strong: BET/RAISE. Medium: CHECK/FOLD. Weak: CHECK/FOLD (~95%).

### Important rules
- When cost_to_call=0: legal actions are CHECK or BET only
- When cost_to_call>0: legal actions are FOLD, CALL, or RAISE only
- RAISE only legal when bet_count < bet_cap (4)
- When bet_count >= bet_cap and you want to RAISE, use CALL instead
- Later streets (turn/river) have bigger bets (4 instead of 2) — be more selective
- Process decisions as FAST as possible — one Bash call per decision

### Monitoring
Check game status:
```
cat /tmp/phase3_ipc/status.json
```
Check if game is over:
```
test -f /tmp/phase3_ipc/game_over && echo "DONE" || echo "RUNNING"
```

### When done
The engine prints final stacks. Commit any generated data:
```
git add runs_phase3_seed_SEED.sqlite && git commit -m "Phase 3: 100 hands seed SEED" && git push origin claude/phase3-llm-agents-wEs7K
```

START NOW. Begin with Step 1, then immediately start the orchestration loop. Process every decision rapidly. Do not ask for confirmation — just play.
