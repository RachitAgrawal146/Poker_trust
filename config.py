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
