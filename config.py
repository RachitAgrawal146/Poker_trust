"""
Central configuration for the Poker Trust Simulation.

All tunable parameters live here. No magic numbers elsewhere. Later stages
extend this file with simulation, trust-model, and per-agent sections; Stage 1
only needs the hand-strength thresholds.
"""

# =============================================================================
# HAND STRENGTH BUCKETING
# =============================================================================
# Monte Carlo equity thresholds used by engine.evaluator.get_hand_strength.
#   win_pct > strong_threshold  → "Strong"
#   win_pct > medium_threshold  → "Medium"
#   otherwise                   → "Weak"
# =============================================================================
HAND_STRENGTH = {
    "strong_threshold": 0.66,
    "medium_threshold": 0.33,
    "monte_carlo_samples": 1000,
}

# =============================================================================
# TABLE CONSTANTS
# =============================================================================
NUM_PLAYERS = 8
DEFAULT_SEED = 42


# =============================================================================
# SIMULATION / LIMIT HOLD'EM RULES
# =============================================================================
# Blinds, bet sizes, and stack / rebuy economics. All numbers are in chip
# units. Small bet applies pre-flop and on the flop; big bet on turn and
# river. Bet cap is 1 bet + 3 raises per round (standard limit hold'em).
# =============================================================================
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
