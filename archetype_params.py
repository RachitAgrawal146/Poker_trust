"""
ARCHETYPE PARAMETERS — CODE-READY
==================================
Every number from The Eight Archetypes Specification, structured for direct import.

Usage:
    from archetype_params import ARCHETYPE_PARAMS, ARCHETYPE_AVERAGES, HONESTY_SCORES

    # Get the Sentinel's Bluff Rate on the Turn:
    br = ARCHETYPE_PARAMS["sentinel"]["turn"]["br"]  # 0.08

    # Get average params for trust model likelihood computation:
    avg_br = ARCHETYPE_AVERAGES["sentinel"]["br"]  # 0.083
"""

# =============================================================================
# PER-ROUND PARAMETERS (for agent DECISIONS)
# =============================================================================
# Structure: ARCHETYPE_PARAMS[archetype][betting_round][metric]
# 
# Metrics:
#   br  = Bluff Rate: P(bet | Weak hand)
#   vbr = Value Bet Rate: P(bet | Strong hand)
#   cr  = Call Rate: P(call | facing bet), regardless of hand strength
#   mbr = Medium Hand Bet Rate: P(bet | Medium hand)
#
# Additional metrics for facing-a-bet decisions:
#   strong_raise  = P(raise | Strong hand, facing bet)
#   strong_call   = P(call | Strong hand, facing bet)  
#   strong_fold   = P(fold | Strong hand, facing bet)
#   med_raise     = P(raise | Medium hand, facing bet)
#   weak_call     = P(call | Weak hand, facing bet)
# =============================================================================

ARCHETYPE_PARAMS = {

    # =========================================================================
    # THE ORACLE — Nash Equilibrium
    # =========================================================================
    "oracle": {
        "preflop": {
            "br": 0.33, "vbr": 0.95, "cr": 0.33, "mbr": 0.50,
            "strong_raise": 0.60, "strong_call": 0.35, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.15,
        },
        "flop": {
            "br": 0.33, "vbr": 0.90, "cr": 0.33, "mbr": 0.45,
            "strong_raise": 0.60, "strong_call": 0.35, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.15,
        },
        "turn": {
            "br": 0.33, "vbr": 0.85, "cr": 0.33, "mbr": 0.40,
            "strong_raise": 0.55, "strong_call": 0.38, "strong_fold": 0.07,
            "med_raise": 0.05, "weak_call": 0.12,
        },
        "river": {
            "br": 0.33, "vbr": 0.80, "cr": 0.33, "mbr": 0.35,
            "strong_raise": 0.50, "strong_call": 0.40, "strong_fold": 0.10,
            "med_raise": 0.05, "weak_call": 0.10,
        },
    },

    # =========================================================================
    # THE SENTINEL — Tight-Aggressive (TAG)
    # =========================================================================
    "sentinel": {
        "preflop": {
            "br": 0.10, "vbr": 0.95, "cr": 0.40, "mbr": 0.30,
            "strong_raise": 0.65, "strong_call": 0.30, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.10,
        },
        "flop": {
            "br": 0.10, "vbr": 0.90, "cr": 0.35, "mbr": 0.25,
            "strong_raise": 0.60, "strong_call": 0.35, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.08,
        },
        "turn": {
            "br": 0.08, "vbr": 0.90, "cr": 0.30, "mbr": 0.20,
            "strong_raise": 0.55, "strong_call": 0.38, "strong_fold": 0.07,
            "med_raise": 0.03, "weak_call": 0.06,
        },
        "river": {
            "br": 0.05, "vbr": 0.85, "cr": 0.25, "mbr": 0.15,
            "strong_raise": 0.50, "strong_call": 0.40, "strong_fold": 0.10,
            "med_raise": 0.02, "weak_call": 0.04,
        },
    },

    # =========================================================================
    # THE FIRESTORM — Loose-Aggressive (LAG / Maniac)
    # =========================================================================
    "firestorm": {
        "preflop": {
            "br": 0.70, "vbr": 0.98, "cr": 0.70, "mbr": 0.80,
            "strong_raise": 0.75, "strong_call": 0.23, "strong_fold": 0.02,
            "med_raise": 0.25, "weak_call": 0.40,
        },
        "flop": {
            "br": 0.65, "vbr": 0.95, "cr": 0.65, "mbr": 0.75,
            "strong_raise": 0.70, "strong_call": 0.27, "strong_fold": 0.03,
            "med_raise": 0.20, "weak_call": 0.35,
        },
        "turn": {
            "br": 0.60, "vbr": 0.92, "cr": 0.60, "mbr": 0.70,
            "strong_raise": 0.65, "strong_call": 0.30, "strong_fold": 0.05,
            "med_raise": 0.18, "weak_call": 0.30,
        },
        "river": {
            "br": 0.55, "vbr": 0.90, "cr": 0.55, "mbr": 0.65,
            "strong_raise": 0.60, "strong_call": 0.33, "strong_fold": 0.07,
            "med_raise": 0.15, "weak_call": 0.25,
        },
    },

    # =========================================================================
    # THE WALL — Passive / Calling Station
    # =========================================================================
    "wall": {
        "preflop": {
            "br": 0.05, "vbr": 0.55, "cr": 0.80, "mbr": 0.15,
            "strong_raise": 0.15, "strong_call": 0.80, "strong_fold": 0.05,
            "med_raise": 0.02, "weak_call": 0.55,
        },
        "flop": {
            "br": 0.05, "vbr": 0.50, "cr": 0.75, "mbr": 0.12,
            "strong_raise": 0.12, "strong_call": 0.82, "strong_fold": 0.06,
            "med_raise": 0.02, "weak_call": 0.50,
        },
        "turn": {
            "br": 0.03, "vbr": 0.45, "cr": 0.70, "mbr": 0.10,
            "strong_raise": 0.10, "strong_call": 0.82, "strong_fold": 0.08,
            "med_raise": 0.01, "weak_call": 0.42,
        },
        "river": {
            "br": 0.02, "vbr": 0.40, "cr": 0.65, "mbr": 0.08,
            "strong_raise": 0.08, "strong_call": 0.82, "strong_fold": 0.10,
            "med_raise": 0.01, "weak_call": 0.35,
        },
    },

    # =========================================================================
    # THE PHANTOM — Deceiver / False Signal Generator
    # =========================================================================
    "phantom": {
        "preflop": {
            "br": 0.60, "vbr": 0.65, "cr": 0.30, "mbr": 0.55,
            "strong_raise": 0.40, "strong_call": 0.45, "strong_fold": 0.15,
            "med_raise": 0.08, "weak_call": 0.35,
        },
        "flop": {
            "br": 0.55, "vbr": 0.60, "cr": 0.25, "mbr": 0.50,
            "strong_raise": 0.35, "strong_call": 0.45, "strong_fold": 0.20,
            "med_raise": 0.06, "weak_call": 0.30,
        },
        "turn": {
            "br": 0.50, "vbr": 0.55, "cr": 0.20, "mbr": 0.45,
            "strong_raise": 0.30, "strong_call": 0.45, "strong_fold": 0.25,
            "med_raise": 0.04, "weak_call": 0.22,
        },
        "river": {
            "br": 0.45, "vbr": 0.50, "cr": 0.15, "mbr": 0.40,
            "strong_raise": 0.25, "strong_call": 0.45, "strong_fold": 0.30,
            "med_raise": 0.03, "weak_call": 0.15,
        },
    },

    # =========================================================================
    # THE PREDATOR — Exploiter / Shark (BASELINE parameters)
    # These are used when no opponent has been classified with > 60% confidence.
    # See PREDATOR_EXPLOIT_TABLE for per-opponent-type adjustments.
    # =========================================================================
    "predator_baseline": {
        "preflop": {
            "br": 0.25, "vbr": 0.90, "cr": 0.35, "mbr": 0.40,
            "strong_raise": 0.60, "strong_call": 0.35, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.12,
        },
        "flop": {
            "br": 0.25, "vbr": 0.85, "cr": 0.35, "mbr": 0.35,
            "strong_raise": 0.55, "strong_call": 0.38, "strong_fold": 0.07,
            "med_raise": 0.05, "weak_call": 0.10,
        },
        "turn": {
            "br": 0.20, "vbr": 0.80, "cr": 0.30, "mbr": 0.30,
            "strong_raise": 0.50, "strong_call": 0.40, "strong_fold": 0.10,
            "med_raise": 0.04, "weak_call": 0.08,
        },
        "river": {
            "br": 0.15, "vbr": 0.80, "cr": 0.30, "mbr": 0.25,
            "strong_raise": 0.45, "strong_call": 0.42, "strong_fold": 0.13,
            "med_raise": 0.03, "weak_call": 0.06,
        },
    },

    # =========================================================================
    # THE MIRROR — Tit-for-Tat (DEFAULT parameters, before mirroring kicks in)
    # =========================================================================
    "mirror_default": {
        "preflop": {
            "br": 0.12, "vbr": 0.90, "cr": 0.38, "mbr": 0.30,
            "strong_raise": 0.62, "strong_call": 0.33, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.10,
        },
        "flop": {
            "br": 0.10, "vbr": 0.85, "cr": 0.35, "mbr": 0.25,
            "strong_raise": 0.58, "strong_call": 0.36, "strong_fold": 0.06,
            "med_raise": 0.05, "weak_call": 0.08,
        },
        "turn": {
            "br": 0.08, "vbr": 0.85, "cr": 0.30, "mbr": 0.20,
            "strong_raise": 0.53, "strong_call": 0.39, "strong_fold": 0.08,
            "med_raise": 0.04, "weak_call": 0.06,
        },
        "river": {
            "br": 0.05, "vbr": 0.80, "cr": 0.25, "mbr": 0.15,
            "strong_raise": 0.48, "strong_call": 0.42, "strong_fold": 0.10,
            "med_raise": 0.03, "weak_call": 0.05,
        },
    },

    # =========================================================================
    # THE JUDGE — Grudger (COOPERATIVE state, identical to Sentinel)
    # =========================================================================
    "judge_cooperative": {
        "preflop": {
            "br": 0.10, "vbr": 0.95, "cr": 0.40, "mbr": 0.30,
            "strong_raise": 0.65, "strong_call": 0.30, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.10,
        },
        "flop": {
            "br": 0.10, "vbr": 0.90, "cr": 0.35, "mbr": 0.25,
            "strong_raise": 0.60, "strong_call": 0.35, "strong_fold": 0.05,
            "med_raise": 0.05, "weak_call": 0.08,
        },
        "turn": {
            "br": 0.08, "vbr": 0.90, "cr": 0.30, "mbr": 0.20,
            "strong_raise": 0.55, "strong_call": 0.38, "strong_fold": 0.07,
            "med_raise": 0.03, "weak_call": 0.06,
        },
        "river": {
            "br": 0.05, "vbr": 0.85, "cr": 0.25, "mbr": 0.15,
            "strong_raise": 0.50, "strong_call": 0.40, "strong_fold": 0.10,
            "med_raise": 0.02, "weak_call": 0.04,
        },
    },

    # =========================================================================
    # THE JUDGE — Grudger (RETALIATORY state, post-trigger)
    # =========================================================================
    "judge_retaliatory": {
        "preflop": {
            "br": 0.70, "vbr": 0.95, "cr": 0.15, "mbr": 0.70,
            "strong_raise": 0.70, "strong_call": 0.25, "strong_fold": 0.05,
            "med_raise": 0.20, "weak_call": 0.05,
        },
        "flop": {
            "br": 0.65, "vbr": 0.92, "cr": 0.12, "mbr": 0.65,
            "strong_raise": 0.65, "strong_call": 0.28, "strong_fold": 0.07,
            "med_raise": 0.15, "weak_call": 0.04,
        },
        "turn": {
            "br": 0.60, "vbr": 0.90, "cr": 0.10, "mbr": 0.60,
            "strong_raise": 0.60, "strong_call": 0.30, "strong_fold": 0.10,
            "med_raise": 0.12, "weak_call": 0.03,
        },
        "river": {
            "br": 0.55, "vbr": 0.85, "cr": 0.08, "mbr": 0.55,
            "strong_raise": 0.55, "strong_call": 0.32, "strong_fold": 0.13,
            "med_raise": 0.10, "weak_call": 0.02,
        },
    },
}


# =============================================================================
# PREDATOR EXPLOIT TABLE
# =============================================================================
# When the Predator classifies an opponent with > 60% confidence, it blends
# toward these parameters. The blend factor alpha = min(1, (max_post - 0.6)/0.3).
#
# Structure: PREDATOR_EXPLOIT[target_type] = {round: {metric: value}}
# Only the metrics that CHANGE from baseline are listed. Unlisted metrics
# use baseline values.
# =============================================================================

PREDATOR_EXPLOIT = {
    "oracle": {
        # Nothing to exploit — play baseline (near-equilibrium)
        "preflop": {"br": 0.33, "vbr": 0.90, "cr": 0.33, "mbr": 0.40},
        "flop":    {"br": 0.33, "vbr": 0.85, "cr": 0.33, "mbr": 0.35},
        "turn":    {"br": 0.33, "vbr": 0.80, "cr": 0.33, "mbr": 0.30},
        "river":   {"br": 0.33, "vbr": 0.80, "cr": 0.33, "mbr": 0.25},
    },
    "sentinel": {
        # TAG folds too much → bluff more, call less
        "preflop": {"br": 0.45, "vbr": 0.85, "cr": 0.25, "mbr": 0.45},
        "flop":    {"br": 0.45, "vbr": 0.85, "cr": 0.25, "mbr": 0.40},
        "turn":    {"br": 0.40, "vbr": 0.82, "cr": 0.22, "mbr": 0.35},
        "river":   {"br": 0.38, "vbr": 0.80, "cr": 0.20, "mbr": 0.30},
    },
    "firestorm": {
        # LAG bluffs too much → stop bluffing, call down bluffs, max value bet
        "preflop": {"br": 0.10, "vbr": 0.95, "cr": 0.60, "mbr": 0.30},
        "flop":    {"br": 0.10, "vbr": 0.95, "cr": 0.60, "mbr": 0.25},
        "turn":    {"br": 0.08, "vbr": 0.92, "cr": 0.55, "mbr": 0.22},
        "river":   {"br": 0.05, "vbr": 0.90, "cr": 0.55, "mbr": 0.18},
    },
    "wall": {
        # Wall never folds → never bluff, max value bet
        "preflop": {"br": 0.05, "vbr": 0.98, "cr": 0.35, "mbr": 0.25},
        "flop":    {"br": 0.03, "vbr": 0.98, "cr": 0.35, "mbr": 0.20},
        "turn":    {"br": 0.02, "vbr": 0.96, "cr": 0.30, "mbr": 0.18},
        "river":   {"br": 0.01, "vbr": 0.95, "cr": 0.30, "mbr": 0.15},
    },
    "phantom": {
        # Phantom folds to raises → raise more, call down bluffs
        "preflop": {"br": 0.15, "vbr": 0.90, "cr": 0.55, "mbr": 0.35},
        "flop":    {"br": 0.12, "vbr": 0.88, "cr": 0.55, "mbr": 0.30},
        "turn":    {"br": 0.10, "vbr": 0.85, "cr": 0.50, "mbr": 0.25},
        "river":   {"br": 0.08, "vbr": 0.82, "cr": 0.50, "mbr": 0.22},
    },
    "predator_baseline": {
        # Mirror match → play equilibrium
        "preflop": {"br": 0.33, "vbr": 0.90, "cr": 0.33, "mbr": 0.40},
        "flop":    {"br": 0.33, "vbr": 0.85, "cr": 0.33, "mbr": 0.35},
        "turn":    {"br": 0.33, "vbr": 0.80, "cr": 0.33, "mbr": 0.30},
        "river":   {"br": 0.33, "vbr": 0.80, "cr": 0.33, "mbr": 0.25},
    },
    "mirror_default": {
        # Avoid triggering retaliation → cautious, low bluff
        "preflop": {"br": 0.20, "vbr": 0.90, "cr": 0.35, "mbr": 0.35},
        "flop":    {"br": 0.18, "vbr": 0.88, "cr": 0.35, "mbr": 0.30},
        "turn":    {"br": 0.15, "vbr": 0.85, "cr": 0.32, "mbr": 0.25},
        "river":   {"br": 0.12, "vbr": 0.82, "cr": 0.30, "mbr": 0.22},
    },
    "judge_cooperative": {
        # Stay below grievance threshold → very cautious bluffing
        "preflop": {"br": 0.15, "vbr": 0.90, "cr": 0.35, "mbr": 0.35},
        "flop":    {"br": 0.12, "vbr": 0.88, "cr": 0.33, "mbr": 0.30},
        "turn":    {"br": 0.10, "vbr": 0.85, "cr": 0.30, "mbr": 0.25},
        "river":   {"br": 0.08, "vbr": 0.82, "cr": 0.28, "mbr": 0.20},
    },
}


# =============================================================================
# AVERAGED PARAMETERS (for trust model LIKELIHOOD computation only)
# =============================================================================
# These are the averages across all 4 betting rounds, used in the Bayesian
# update when computing P(action | type_k). Do NOT use these for agent decisions.
# =============================================================================

ARCHETYPE_AVERAGES = {
    "oracle":           {"br": 0.330, "vbr": 0.875, "cr": 0.330, "mbr": 0.425},
    "sentinel":         {"br": 0.083, "vbr": 0.900, "cr": 0.325, "mbr": 0.225},
    "firestorm":        {"br": 0.625, "vbr": 0.938, "cr": 0.625, "mbr": 0.725},
    "wall":             {"br": 0.038, "vbr": 0.475, "cr": 0.725, "mbr": 0.113},
    "phantom":          {"br": 0.525, "vbr": 0.575, "cr": 0.225, "mbr": 0.475},
    "predator_baseline":{"br": 0.213, "vbr": 0.838, "cr": 0.325, "mbr": 0.325},
    "mirror_default":   {"br": 0.088, "vbr": 0.850, "cr": 0.320, "mbr": 0.225},
    "judge_cooperative":{"br": 0.083, "vbr": 0.900, "cr": 0.325, "mbr": 0.225},
    "judge_retaliatory":{"br": 0.625, "vbr": 0.905, "cr": 0.113, "mbr": 0.625},
}


# =============================================================================
# HONESTY SCORES (for trust score computation)
# =============================================================================
# honesty(type) = 1 - BR(type)
# T(A→B) = Σ P(B = type_k) × honesty(type_k)
# =============================================================================

HONESTY_SCORES = {
    "oracle":           1 - 0.330,  # 0.670
    "sentinel":         1 - 0.083,  # 0.917
    "firestorm":        1 - 0.625,  # 0.375
    "wall":             1 - 0.038,  # 0.962
    "phantom":          1 - 0.525,  # 0.475
    "predator_baseline":1 - 0.213,  # 0.787
    "mirror_default":   1 - 0.088,  # 0.912
    "judge_cooperative":1 - 0.083,  # 0.917
    "judge_retaliatory":1 - 0.625,  # 0.375
}

# For trust computation, we use ONLY the 8 main types (not separate judge states).
# The Judge's honesty depends on its current state per-opponent.
# For the PRIOR trust computation (before any observations), use judge_cooperative.
TRUST_TYPE_LIST = [
    "oracle", "sentinel", "firestorm", "wall",
    "phantom", "predator_baseline", "mirror_default", "judge_cooperative"
]


# =============================================================================
# SEATING ARRANGEMENT
# =============================================================================
# Fixed seats for reproducibility. Seat 0 = first dealer.
# =============================================================================

SEATING = [
    {"seat": 0, "name": "The Oracle",    "archetype": "oracle"},
    {"seat": 1, "name": "The Sentinel",  "archetype": "sentinel"},
    {"seat": 2, "name": "The Firestorm", "archetype": "firestorm"},
    {"seat": 3, "name": "The Wall",      "archetype": "wall"},
    {"seat": 4, "name": "The Phantom",   "archetype": "phantom"},
    {"seat": 5, "name": "The Predator",  "archetype": "predator"},
    {"seat": 6, "name": "The Mirror",    "archetype": "mirror"},
    {"seat": 7, "name": "The Judge",     "archetype": "judge"},
]
