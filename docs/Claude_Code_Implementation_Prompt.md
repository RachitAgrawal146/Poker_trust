# IMPLEMENTATION PROMPT — PHASE 1: AI AGENTS
## Multi-Agent Trust Dynamics Simulation in 8-Player Limit Texas Hold'em

---

## READ FIRST

The attached `The_Eight_Archetypes_Specification.docx` contains the complete definitions of all 8 agent archetypes, their exact mathematical parameters per betting round, the Bayesian trust model, and the expected emergent dynamics. **READ THAT DOCUMENT FULLY BEFORE WRITING ANY CODE.** This prompt tells you HOW to build. The spec tells you WHAT each agent does.

---

## WHAT THIS IS

This is **Phase 1** of a two-phase research project:

- **Phase 1 (this build):** 8 rule-based AI agents play 10,000 hands of Limit Hold'em. Every agent uses hand-coded parameters and Bayesian inference. No machine learning. No training. No loss functions. These are classical AI agents — expert systems with probability tables.

- **Phase 2 (future):** ML models will be trained on Phase 1's data to replace the hand-coded rules. Neural networks learn exploitation strategies instead of lookup tables. Classifiers learn opponent types instead of Bayes' theorem. Then ML agents play the same game and we compare results.

**Your job is Phase 1 only.** But the data you log must be rich enough to serve as training data for Phase 2. Every decision, every observation, every trust update — logged, structured, and ML-ready.

---

## TECH STACK

- **Language:** Python 3.10+
- **Core:** NumPy, Pandas, Matplotlib, Seaborn
- **Poker evaluation:** `treys` (`pip install treys`)
- **Database:** SQLite (primary), CSV exports (secondary)
- **Visualizer:** Single-file HTML/JS/CSS (reads from JSON data exports)
- **RNG:** `numpy.random.Generator` with explicit seeds for full reproducibility

---

## PROJECT STRUCTURE

```
poker_trust_sim/
│
├── README.md
├── requirements.txt
├── config.py                      # ALL parameters. No magic numbers elsewhere.
│
├── engine/
│   ├── __init__.py
│   ├── card.py                    # Card, Deck (wraps treys)
│   ├── hand_evaluator.py          # Monte Carlo equity → Strong/Medium/Weak bucketing
│   ├── game.py                    # Single hand of Limit Hold'em
│   └── table.py                   # 8-seat table manager, dealer rotation, rebuys
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py              # Abstract base with trust model
│   ├── oracle.py                  # Nash Equilibrium
│   ├── sentinel.py                # Tight-Aggressive
│   ├── firestorm.py               # Loose-Aggressive
│   ├── wall.py                    # Passive / Calling Station
│   ├── phantom.py                 # Deceiver
│   ├── predator.py                # Exploiter (adaptive)
│   ├── mirror.py                  # Tit-for-Tat (adaptive)
│   └── judge.py                   # Grudger (adaptive)
│
├── trust/
│   ├── __init__.py
│   ├── bayesian_model.py          # Posterior updates, decay, noise
│   ├── trust_metrics.py           # Trust score, entropy computation
│   └── grievance_ledger.py        # Judge's per-opponent counter
│
├── data/
│   ├── __init__.py
│   ├── logger.py                  # Writes to SQLite + JSON hand logs
│   ├── schemas.py                 # Table/column definitions
│   └── exporter.py                # CSV + ML-ready dataset generation
│
├── visualizer/
│   └── poker_table.html           # Self-contained poker table replay viewer
│
├── analysis/
│   ├── __init__.py
│   ├── visualizations.py          # Publication-ready plots
│   └── statistics.py              # Confidence intervals, significance tests
│
├── run_simulation.py              # Main entry point
├── run_analysis.py                # Post-sim visualization
└── run_sensitivity.py             # ε, λ, τ parameter sweeps
```

---

## CONFIG.PY

```python
SIMULATION = {
    "num_hands": 10_000,
    "num_seeds": 5,
    "seeds": [42, 137, 256, 512, 1024],
    "starting_stack": 200,
    "small_blind": 1,
    "big_blind": 2,
    "small_bet": 2,
    "big_bet": 4,
    "bet_cap": 4,
}

TRUST_MODEL = {
    "lambda_decay": 0.95,
    "epsilon_noise": 0.05,
    "third_party_weight": 0.8,
    "num_types": 8,
    "initial_prior": 1/8,
}

HAND_STRENGTH = {
    "strong_threshold": 0.66,
    "medium_threshold": 0.33,
    "monte_carlo_samples": 1000,
}

PREDATOR = {
    "classification_threshold": 0.60,
    "alpha_denominator": 0.30,
}

MIRROR = {
    "smoothing_factor": 0.60,
    "br_floor": 0.03,
    "br_ceiling": 0.55,
}

JUDGE = {
    "tau_default": 5,
}

SENSITIVITY = {
    "epsilon_values": [0.02, 0.05, 0.10],
    "lambda_values": [0.90, 0.95, 0.99],
    "tau_values": [3, 5, 8],
}

# Per-archetype AVERAGE params (for trust model likelihood computation only)
# For agent DECISIONS, use the per-round tables from the spec document
ARCHETYPE_PARAMS = {
    "oracle":    {"br": 0.33, "vbr": 0.875, "cr": 0.33, "mbr": 0.425},
    "sentinel":  {"br": 0.083, "vbr": 0.90, "cr": 0.325, "mbr": 0.225},
    "firestorm": {"br": 0.625, "vbr": 0.9375, "cr": 0.625, "mbr": 0.725},
    "wall":      {"br": 0.0375, "vbr": 0.475, "cr": 0.725, "mbr": 0.1125},
    "phantom":   {"br": 0.525, "vbr": 0.575, "cr": 0.225, "mbr": 0.475},
    "predator":  {"br": 0.2125, "vbr": 0.8375, "cr": 0.325, "mbr": 0.325},
    "mirror":    {"br": 0.0875, "vbr": 0.85, "cr": 0.32, "mbr": 0.225},
    "judge_coop":{"br": 0.083, "vbr": 0.90, "cr": 0.325, "mbr": 0.225},
    "judge_ret": {"br": 0.625, "vbr": 0.905, "cr": 0.1125, "mbr": 0.625},
}
```

---

## ENGINE IMPLEMENTATION

### Card + Deck
- Wrap `treys` library. Use `treys.Card` for representation and `treys.Evaluator` for hand ranking.
- Deck class: init with 52 cards, shuffle with seeded RNG, deal N cards, track remaining.

### Hand Evaluator
```python
def get_hand_strength_bucket(hole_cards, community_cards, rng, num_samples=1000):
    """
    Returns "Strong", "Medium", or "Weak".
    
    Pre-flop (no community cards): use lookup table.
    Post-flop: Monte Carlo equity estimation.
    
    Pre-flop lookup:
        Strong: AA, KK, QQ, JJ, AKs, AKo, AQs
        Medium: TT-77, AJs-ATs, KQs-KJs, QJs-JTs, AQo-AJo
        Weak: everything else
    
    Post-flop: deal random opponent hands + remaining community cards
    num_samples times, evaluate, compute win percentage.
        win_pct > 0.66 → Strong
        win_pct > 0.33 → Medium
        else → Weak
    """
```

**PERFORMANCE NOTE:** Post-flop Monte Carlo is the bottleneck. Cache equity results for identical (hole_cards, community_cards) combinations within a hand (multiple agents may evaluate against the same board). Consider reducing samples to 500 for non-showdown decisions and using 1000 only when accuracy matters (close to bucket boundaries).

### Game Engine — Single Hand

```python
class Hand:
    def __init__(self, table, deck, rng):
        self.players = [p for p in table.seats if p.stack > 0]
        self.pot = 0
        self.community_cards = []
        self.action_log = []  # Every action recorded here
        self.showdown_data = None
    
    def play(self):
        self._post_blinds()
        self._deal_hole_cards()
        
        if self._betting_round("preflop"):  # Returns False if only 1 player left
            self._deal_community(3)  # Flop
            if self._betting_round("flop"):
                self._deal_community(1)  # Turn
                if self._betting_round("turn"):
                    self._deal_community(1)  # River
                    self._betting_round("river")
        
        if self._count_active() >= 2:
            self._showdown()
        else:
            self._award_pot_to_last_standing()
        
        return self.action_log, self.showdown_data
```

Betting round logic:
- Track: current bet level (0-4), amount each player has put in this round
- Action order: pre-flop starts left of big blind; post-flop starts left of dealer
- A round ends when: all active players have acted at least once AND all bets are matched
- Player can only act if they haven't folded and have chips
- On each player's turn, call `agent.decide_action(game_state)` where game_state includes:
  - community_cards, pot_size, current_bet_level, cost_to_call
  - betting_round ("preflop"/"flop"/"turn"/"river")
  - num_active_players, player's stack, player's position
  - list of actions taken so far in this round (for context)

### Table Manager

```python
class Table:
    def __init__(self, agents, rng):
        self.seats = agents  # 8 agents, fixed seats
        self.dealer_button = 0
        self.hand_number = 0
    
    def play_hand(self):
        self.hand_number += 1
        self._handle_rebuys()  # Any agent at 0 gets 200
        deck = Deck(self.rng)
        hand = Hand(self, deck, self.rng)
        action_log, showdown_data = hand.play()
        
        # CRITICAL: broadcast to ALL agents
        for agent in self.seats:
            for action_entry in action_log:
                is_direct = (agent.seat == action_entry.actor_seat or 
                           agent was in the same hand)
                agent.observe_action(action_entry, is_direct)
            
            if showdown_data:
                agent.observe_showdown(showdown_data)
        
        self._rotate_dealer()
        return action_log, showdown_data
```

---

## AGENT IMPLEMENTATION

### Base Agent

All 8 agents share this base. The base class owns the trust model. Subclasses only override `get_params()` and optionally `decide_action()` for adaptive agents.

```python
class BaseAgent(ABC):
    def __init__(self, name, archetype, seat):
        self.name = name
        self.archetype = archetype
        self.seat = seat
        self.stack = 200
        self.hole_cards = None
        self.rebuys = 0
        self.hands_played = 0
        
        # Trust model
        self.posteriors = {}  # seat -> {archetype_name: probability}
        # Initialize in set_opponents() after table is built
        
        # Per-opponent observation tracking
        self.opponent_stats = {}  # seat -> {observed_br, observed_vbr, ...}
        
        # Cumulative self-stats (for validation)
        self.stats = {
            "vpip_count": 0, "pfr_count": 0, "hands_dealt": 0,
            "bets": 0, "raises": 0, "calls": 0, "folds": 0, "checks": 0,
            "showdowns": 0, "showdowns_won": 0, "saw_flop": 0
        }
    
    def decide_action(self, game_state):
        hs = get_hand_strength_bucket(self.hole_cards, game_state.community)
        params = self.get_params(game_state.betting_round, game_state)
        
        if game_state.current_bet == 0:
            # Check or Bet
            if hs == "Strong":
                prob = params["vbr"]
            elif hs == "Medium":
                prob = params["mbr"]
            else:
                prob = params["br"]
            return BET if rng.random() < prob else CHECK
        
        else:
            # Fold, Call, or Raise
            if hs == "Strong":
                raise_p = params.get("strong_raise", 0.60)
                call_p = params.get("strong_call", 0.35)
            elif hs == "Medium":
                raise_p = params.get("med_raise", 0.05)
                call_p = params["cr"]
            else:
                raise_p = 0.0
                call_p = params.get("weak_call", 0.15)
            
            roll = rng.random()
            if roll < raise_p and game_state.bet_count < BET_CAP:
                return RAISE
            elif roll < raise_p + call_p:
                return CALL
            else:
                return FOLD
    
    @abstractmethod
    def get_params(self, betting_round, game_state) -> dict:
        """Return action probabilities for current context."""
        pass
```

### Static Agents

Each static agent's `get_params()` returns fixed values from the spec document's per-round tables. Example for Sentinel:

```python
class Sentinel(BaseAgent):
    PARAMS = {
        "preflop": {"br": 0.10, "vbr": 0.95, "cr": 0.40, "mbr": 0.30, ...},
        "flop":    {"br": 0.10, "vbr": 0.90, "cr": 0.35, "mbr": 0.25, ...},
        "turn":    {"br": 0.08, "vbr": 0.90, "cr": 0.30, "mbr": 0.20, ...},
        "river":   {"br": 0.05, "vbr": 0.85, "cr": 0.25, "mbr": 0.15, ...},
    }
    
    def get_params(self, betting_round, game_state):
        return self.PARAMS[betting_round]
```

Do the same for Oracle, Firestorm, Wall, Phantom — each with their own per-round values from the spec.

### Adaptive Agents — Special Logic

**Predator:**
```python
def get_params(self, betting_round, game_state):
    # Find the primary opponent in this pot
    opponents_in_pot = game_state.active_opponent_seats
    
    # For each opponent, check classification confidence
    best_target = None
    best_alpha = 0
    for opp_seat in opponents_in_pot:
        post = self.posteriors[opp_seat]
        max_type = max(post, key=post.get)
        max_prob = post[max_type]
        if max_prob > PREDATOR["classification_threshold"]:
            alpha = min(1.0, (max_prob - 0.60) / 0.30)
            if alpha > best_alpha:
                best_target = (opp_seat, max_type, alpha)
                best_alpha = alpha
    
    baseline = self.BASELINE_PARAMS[betting_round]
    
    if best_target is None:
        return baseline
    
    _, target_type, alpha = best_target
    exploit = self.EXPLOIT_TABLE[target_type][betting_round]
    
    # Blend: alpha * exploit + (1-alpha) * baseline
    return {k: alpha * exploit[k] + (1-alpha) * baseline[k] 
            for k in baseline}
```

**Mirror:**
```python
def get_params(self, betting_round, game_state):
    opponents = game_state.active_opponent_seats
    if not opponents:
        return self.DEFAULT_PARAMS[betting_round]
    
    # Weighted average of mirrored params across active opponents
    weights = [game_state.pot_contribution(s) for s in opponents]
    total_w = sum(weights) or 1
    
    blended = {}
    for key in ["br", "vbr", "cr", "mbr"]:
        default_val = self.DEFAULT_PARAMS[betting_round][key]
        mirrored = sum(
            w * (0.6 * self.opponent_stats[s].get(f"observed_{key}", default_val) 
                 + 0.4 * default_val)
            for s, w in zip(opponents, weights)
        ) / total_w
        
        # Clamp BR
        if key == "br":
            mirrored = max(0.03, min(0.55, mirrored))
        
        blended[key] = mirrored
    
    return blended
```

**Judge:**
```python
def __init__(self, ...):
    super().__init__(...)
    self.grievance = {}  # seat -> int count
    self.triggered = {}  # seat -> bool

def get_params(self, betting_round, game_state):
    # Check if ANY opponent in this pot has triggered
    for opp_seat in game_state.active_opponent_seats:
        if self.triggered.get(opp_seat, False):
            return self.RETALIATORY_PARAMS[betting_round]
    return self.COOPERATIVE_PARAMS[betting_round]  # Same as Sentinel

def observe_showdown(self, showdown_data):
    super().observe_showdown(showdown_data)
    for entry in showdown_data:
        if entry.seat == self.seat:
            continue
        # Was I in this hand AND did this opponent bluff against me?
        if (self._was_in_hand(entry.hand_id) and 
            entry.hand_strength == "Weak" and 
            entry.did_bet_or_raise):
            self.grievance[entry.seat] = self.grievance.get(entry.seat, 0) + 1
            if self.grievance[entry.seat] >= JUDGE["tau_default"]:
                self.triggered[entry.seat] = True
```

---

## TRUST MODEL

### Bayesian Update

```python
def bayesian_update(self, opponent_seat, observation, is_direct=True):
    eps = TRUST_MODEL["epsilon_noise"]
    lam = TRUST_MODEL["lambda_decay"]
    weight = 1.0 if is_direct else TRUST_MODEL["third_party_weight"]
    
    posterior = self.posteriors[opponent_seat]
    
    for arch_name, prior_prob in posterior.items():
        arch_params = ARCHETYPE_PARAMS[arch_name]
        
        if observation.hand_revealed:
            likelihood = direct_likelihood(observation, arch_params)
        else:
            likelihood = marginal_likelihood(observation, arch_params)
        
        # Trembling hand
        num_actions = observation.num_available_actions
        adjusted = (1 - eps) * likelihood + eps * (1 / num_actions)
        
        # Decay prior, then update
        decayed = prior_prob ** lam
        posterior[arch_name] = decayed * (adjusted ** weight)
    
    # Normalize
    total = sum(posterior.values())
    for k in posterior:
        posterior[k] /= total if total > 0 else 1

def trust_score(self, opponent_seat):
    """T(self → opponent) = Σ P(type_k) × (1 - BR_k)"""
    return sum(
        prob * (1 - ARCHETYPE_PARAMS[arch]["br"])
        for arch, prob in self.posteriors[opponent_seat].items()
    )

def entropy(self, opponent_seat):
    """H = -Σ P_k × log2(P_k)"""
    return -sum(
        p * math.log2(p) if p > 0 else 0
        for p in self.posteriors[opponent_seat].values()
    )
```

---

## DATA LOGGING

### SQLite Tables

**`hands`** — One row per hand
```sql
hand_id, seed, dealer_seat, pot_size, num_players_showdown,
winner_seat, winner_archetype, winning_hand_rank,
community_cards_json
```

**`actions`** — One row per action (the biggest table: ~1.6M rows for 10k hands × 5 seeds)
```sql
action_id, hand_id, seed, seat, archetype,
betting_round, action_type, amount,
pot_before, pot_after, stack_before, stack_after,
hand_strength_bucket, action_sequence_num,
num_opponents_remaining, position_relative_to_dealer
```

**`showdowns`** — One row per player per showdown
```sql
showdown_id, hand_id, seed, seat, archetype,
hole_cards_json, hand_strength_bucket, hand_rank,
won, pot_won, was_bluff_caught
```

**`trust_scores`** — One row per (observer, target) per hand (56 pairs × 10k = 560k per seed)
```sql
hand_id, seed, observer_seat, observer_archetype,
target_seat, target_archetype,
trust_score, entropy,
max_posterior_type, max_posterior_prob
```

**`posteriors`** — Full distribution, logged every 50 hands
```sql
hand_id, seed, observer_seat, observer_archetype,
target_seat, target_archetype,
p_oracle, p_sentinel, p_firestorm, p_wall,
p_phantom, p_predator, p_mirror, p_judge
```

**`stacks`** — One row per agent per hand
```sql
hand_id, seed, seat, archetype,
stack, total_rebuys, cumulative_profit
```

**`grievances`** — Judge-specific, logged every hand
```sql
hand_id, seed, target_seat, target_archetype,
grievance_count, threshold, triggered, trigger_hand_id
```

**`agent_metrics`** — Rolling behavioral stats, every 50 hands
```sql
hand_id, seed, seat, archetype,
measured_br, measured_vbr, measured_cr,
vpip, pfr, af, afq, wtsd, w_dollar_sd,
three_bet_pct, fold_to_bet, fold_to_raise
```

**`simulation_meta`** — One row per seed
```sql
seed, num_hands, lambda, epsilon, tau,
start_time, end_time,
total_showdowns, total_rebuys_json, final_standings_json
```

### JSON Hand Log (for the Visualizer)

In addition to SQLite, export a JSON file per seed containing EVERY hand's full detail for the replay visualizer:

```json
{
  "seed": 42,
  "hands": [
    {
      "hand_id": 1,
      "dealer": 0,
      "blinds": {"small": {"seat": 1, "amount": 1}, "big": {"seat": 2, "amount": 2}},
      "players": [
        {
          "seat": 0, "name": "The Oracle", "archetype": "oracle",
          "hole_cards": ["Ah", "Kd"], "stack_before": 200,
          "stack_after": 210, "hand_strength": "Strong"
        },
        ...
      ],
      "community_cards": {
        "flop": ["Qs", "Jh", "3c"],
        "turn": ["7d"],
        "river": ["2s"]
      },
      "actions": [
        {
          "round": "preflop", "seat": 3, "action": "raise",
          "amount": 4, "pot_after": 7
        },
        ...
      ],
      "showdown": [
        {"seat": 0, "hand_rank": "high_card", "won": true, "pot_won": 14},
        {"seat": 3, "hand_rank": "pair", "won": false, "pot_won": 0}
      ],
      "trust_snapshot": {
        "0": {"1": 0.87, "2": 0.45, ...},
        ...
      }
    },
    ...
  ]
}
```

**NOTE:** The full JSON for 10,000 hands will be large (~50-100MB). For the visualizer, also generate a lightweight index file listing just hand_id, pot_size, winner, and whether showdown occurred, so the visualizer can lazy-load individual hands on demand.

### ML-Ready CSV Exports (for Phase 2)

Generate these AFTER the simulation completes. They are derived datasets, not raw logs.

**`ml_action_features.csv`** — For training action-prediction models
```
hand_id, seed, seat, archetype, is_adaptive,
hand_strength_numeric (S=1.0, M=0.5, W=0.0),
betting_round_numeric (preflop=0, flop=1, turn=2, river=3),
pot_normalized, stack_normalized,
num_opponents_in_hand, bet_count_this_round,
position_relative_to_dealer, is_in_blinds,
rolling_vpip_50, rolling_pfr_50, rolling_af_50,
rolling_br_50, rolling_vbr_50, rolling_cr_50,
avg_trust_received, avg_trust_given, avg_entropy_received,
→ action_taken (TARGET: fold=0, check=1, call=2, bet=3, raise=4)
```

**`ml_type_classification.csv`** — For archetype identification models
```
One row per agent per 50-hand window.

Features: vpip, pfr, af, afq, wtsd, w_dollar_sd,
measured_br, measured_vbr, measured_cr,
fold_to_bet, fold_to_raise, three_bet_pct,
avg_pot_entered, showdown_frequency,
bet_freq_preflop, bet_freq_flop, bet_freq_turn, bet_freq_river

→ true_archetype (TARGET: 8-class label)
→ is_adaptive (TARGET: binary)
```

**`ml_trust_timeseries.csv`** — For trust prediction models
```
hand_id, seed, observer_archetype, target_archetype,
trust_score, entropy, trust_delta, entropy_delta,
observer_is_adaptive, target_is_adaptive,
hands_since_last_showdown, cumulative_bluffs_caught,
target_recent_br_20, target_recent_vbr_20,
→ trust_collapse_next_200 (TARGET: binary — does trust drop below 0.3?)
→ trust_direction_next_100 (TARGET: increase / stable / decrease / collapse)
```

---

## THE POKER TABLE VISUALIZER

Build a single self-contained HTML file (`poker_table.html`) that replays hands from the JSON log. This is not a live game — it's a replay viewer for analyzing what happened.

### Visual Design

The aesthetic should feel like a premium online poker client — dark felt green table, realistic card faces, clean chip animations. Think PokerStars meets a research dashboard.

**Table layout:**
- Oval poker table in the center of the screen, dark green felt texture (#1a472a gradient)
- 8 player positions arranged around the oval (2 top, 2 bottom, 2 left, 2 right)
- Each seat shows:
  - Player avatar/icon (a distinctive colored circle with the archetype's initial: O, S, F, W, P, Pr, M, J)
  - Player name (e.g., "The Oracle")
  - Current stack (chips displayed as a number)
  - Hole cards (face-down by default, revealed on hover or at showdown)
  - A colored ring around the avatar indicating current trust level (green = high, yellow = neutral, red = low — based on the TABLE AVERAGE trust toward this player)
  - A subtle glow when it's the player's turn to act

**Center of table:**
- Community cards (dealt one stage at a time during replay)
- Pot size display
- Hand number / total hands counter

**Action feed:**
- Right side panel showing the action log for the current hand
- Each action shows: player name, action type, amount, and a small colored dot for the archetype
- Scrollable for hands with many actions

### Interactive Features

**Hand Navigation:**
- Slider at the bottom to scrub through hands (1 to 10,000)
- Play/Pause button for auto-advancing
- Speed control (1x, 2x, 5x, 10x)
- Jump to hand by number
- Filter: "Show only showdown hands" / "Show only Judge trigger hands" / "Show all"

**Player Click (the most important feature):**
Clicking a player's avatar opens a stats panel overlay showing that player's real-time statistics AT THAT POINT IN THE SIMULATION:

```
THE SENTINEL — Seat 2
Hand 847 / 10,000

BEHAVIORAL STATS (cumulative to this hand):
  VPIP:        17.2%
  PFR:         15.1%
  AF:          3.4
  WTSD:        26.3%
  W$SD:        61.2%
  Fold to Bet: 58.4%
  3-Bet %:     6.1%

CORE METRICS (rolling 50 hands):
  Bluff Rate:      0.08
  Value Bet Rate:  0.91
  Call Rate:       0.34

TRUST PROFILE:
  Others' trust in me: 0.88 (avg)
  My trust in others:
    Oracle:     0.71  ████████░░
    Firestorm:  0.34  ████░░░░░░
    Wall:       0.93  ██████████
    Phantom:    0.41  █████░░░░░
    Predator:   0.62  ███████░░░
    Mirror:     0.86  █████████░
    Judge:      0.89  █████████░

CLASSIFICATION (what others think I am):
    Avg posterior: 82% Sentinel, 9% Oracle, 5% Judge, ...

STACK: 234 chips (+34 profit, 0 rebuys)
```

**Trust Heatmap Toggle:**
Button that overlays an 8×8 trust heatmap on top of the table, showing all T(A→B) values at the current hand. Color-coded cells. Can be toggled on/off.

**Showdown Reveal:**
When replaying a showdown hand, cards flip with a subtle animation. Bluffs caught are highlighted in red. Value bets highlighted in green.

### Technical Implementation

- Single HTML file with inline CSS and JS
- Reads from `hands_index.json` (lightweight) and lazy-loads individual hands from `hand_XXXX.json` chunks
- No external dependencies except fonts (load from Google Fonts CDN)
- Use CSS Grid for the table layout, CSS transforms for card animations
- All data is read-only — the visualizer never modifies simulation data
- Should work in any modern browser

**Data chunking for the visualizer:**
Instead of one massive JSON, export hands in chunks of 100:
```
visualizer_data/
├── index.json           # {total_hands, seed, archetypes, ...}
├── hands_0001_0100.json
├── hands_0101_0200.json
├── ...
└── hands_9901_10000.json
```

The visualizer loads the index first, then fetches the relevant chunk when the user navigates to a hand.

---

## ANALYSIS VISUALIZATIONS

Generate these as PNG (300 DPI) and SVG after simulation completes:

1. **Trust Trajectory Grid** — 8×8 small multiples, T(row→col) over time, mean ± std band across seeds. Mark Judge trigger events.

2. **Entropy (Legibility) Plot** — One line per archetype: average entropy all others have about this type. Lower = more readable.

3. **Chip Stack Evolution** — 8 lines showing cumulative profit over time. Rebuy markers.

4. **Grievance Timeline** — 7 subplots: Judge's grievance count per opponent, horizontal threshold line, trigger markers.

5. **Trust Heatmaps** — 8×8 at hands 100, 500, 1000, 2000, 5000, 10000.

6. **Legibility Bar Chart** — Average entropy by archetype with error bars.

7. **Mirror-Judge Dedicated Plot** — Three panels: Mirror's BR toward Judge, Judge's grievance, T(Judge→Mirror). Trigger event marked.

8. **Pairwise Profitability Matrix** — 8×8 heatmap: average profit of row vs. column.

9. **Classification Accuracy Over Time** — How quickly do agents correctly identify each type? Plot % of agents whose max_posterior_type matches ground truth, per archetype, over time.

10. **Archetype Behavioral Fingerprints** — Radar/spider charts showing the 6 key metrics (BR, VBR, CR, VPIP, AF, WTSD) for each archetype. One chart per type. Useful for the paper's methodology section.

---

## BUILD ORDER

Test each component before moving on:

1. **Card + Deck + Evaluator** → Test: deal, evaluate, bucket correctly
2. **Game Engine** → Test: full hand with 8 dummy "always call" agents, verify pot math
3. **Base Agent + Oracle** → Test: Oracle plays 100 hands, verify VPIP/PFR/AF ranges
4. **All 5 static agents** → Test: 500 hands, all metrics within expected ranges
5. **Trust model** → Test: 500 hands, posteriors converge toward true types for statics
6. **3 adaptive agents** → Test: Predator adapts, Mirror mirrors, Judge triggers
7. **Data logger + SQLite** → Test: all tables populated, no NULLs
8. **Full simulation** → 10,000 hands × 1 seed, inspect data quality
9. **JSON export + Visualizer** → Load, navigate, click players
10. **Multi-seed runs** → 5 seeds, generate all plots
11. **ML export CSVs** → Validate column counts, dtypes, no missing values
12. **Sensitivity analysis** → Parameter sweeps

---

## CRITICAL RULES

1. **REPRODUCIBILITY**: Same seed = same results. Always. Every random call uses the seeded RNG.

2. **NO PRIVILEGED INFORMATION**: No agent knows any other agent's type, parameters, or whether they're adaptive. Everything is inferred from observed behavior.

3. **FULL OBSERVABILITY OF ACTIONS**: Every agent sees every action in every hand. Even if they folded on the flop, they see the turn and river actions.

4. **CARDS HIDDEN UNTIL SHOWDOWN**: Hole cards are private. Only revealed at showdown. If all but one player folds, the winner's cards stay hidden.

5. **PER-ROUND PARAMETERS**: Use the spec document's per-round tables for agent decisions. Pre-Flop, Flop, Turn, River values are different for each metric and each archetype. Do NOT average them.

6. **JUDGE'S GRIEVANCE ≠ TRUST**: The trust model (Bayesian, with decay) and the grievance ledger (integer counter, no decay, permanent) are separate systems. Both exist in the Judge simultaneously. They can disagree — the Judge's trust score for an opponent might improve while the grievance count stays locked.

7. **THE VISUALIZER IS NOT OPTIONAL**: It is a core deliverable, not a nice-to-have. The researcher needs to be able to watch individual hands play out to validate agent behavior and identify interesting moments for the paper.

8. **DATA IS THE PRODUCT**: The simulation exists to produce data. If the code runs but the data is incomplete, corrupted, or poorly structured, the build has failed. Every table, every column, every row matters.
