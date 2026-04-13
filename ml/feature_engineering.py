"""Feature definitions and transforms for Phase 2 ML training.

Each action row from the Phase 1 SQLite database becomes one training
example. Features are derived entirely from the persisted columns in the
``actions`` and ``hands`` tables — no hand_strength_bucket is stored in the
schema, so we work without it by default and optionally enrich from
showdown data when available.

Persisted action columns (from data/schema.sql):
    run_id, hand_id, sequence_num, seat, archetype, betting_round,
    action_type, amount, pot_before, pot_after, stack_before, stack_after,
    bet_count, current_bet

Derived features (7 dimensions without hand strength, 8 with):
    0. betting_round     : float in {0.0, 0.25, 0.5, 0.75}
    1. pot_normalized    : float, pot_before / 200.0
    2. stack_normalized  : float, stack_before / 200.0
    3. cost_to_call_norm : float, derived from action context / 200.0
    4. bet_count_norm    : float, bet_count / 4.0
    5. position_norm     : float, (seat - dealer) mod 8 / 7.0
    6. is_facing_bet     : float, 1.0 if cost_to_call > 0, else 0.0
    7. hand_strength     : float in {0.0, 0.5, 1.0} (OPTIONAL — only for
                           showdown-revealed hands; None if unavailable)

All features normalized to [0, 1].

Label:
    action_type: int in {0, 1, 2, 3, 4}
        0 = fold, 1 = check, 2 = call, 3 = bet, 4 = raise
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

FEATURE_NAMES_BASE = [
    "betting_round", "pot_normalized", "stack_normalized",
    "cost_to_call_norm", "bet_count_norm", "position_norm",
    "is_facing_bet",
]

FEATURE_NAMES_WITH_HS = FEATURE_NAMES_BASE + ["hand_strength"]

ACTION_LABELS = ["fold", "check", "call", "bet", "raise"]
ACTION_TO_INT = {a: i for i, a in enumerate(ACTION_LABELS)}
INT_TO_ACTION = {i: a for a, i in ACTION_TO_INT.items()}

ARCHETYPES = [
    "oracle", "sentinel", "firestorm", "wall",
    "phantom", "predator", "mirror", "judge",
]

_ROUND_MAP = {"preflop": 0.0, "flop": 0.25, "turn": 0.5, "river": 0.75}
_HS_MAP = {"Strong": 1.0, "Medium": 0.5, "Weak": 0.0}

# Starting stack for normalization (from config.py SIMULATION).
_STARTING_STACK = 200.0


def action_row_to_features(
    row: dict,
    dealer: int,
    hand_strength: Optional[str] = None,
) -> Optional[Tuple[List[float], int]]:
    """Convert a database action row + hand-level context to (features, label).

    Parameters
    ----------
    row : dict
        A row from the ``actions`` table (sqlite3.Row or dict with column
        names as keys).
    dealer : int
        Dealer seat for this hand (from the ``hands`` table). Used to
        compute position_relative_to_dealer.
    hand_strength : str or None
        "Strong", "Medium", or "Weak" if known (e.g. from showdown reveal).
        None if unknown — the feature is omitted from the vector.

    Returns
    -------
    (features, label) or None if the row cannot be featurized.
    """
    action = row["action_type"]
    label = ACTION_TO_INT.get(action)
    if label is None:
        return None

    betting_round = _ROUND_MAP.get(row["betting_round"], 0.0)
    pot_norm = row["pot_before"] / _STARTING_STACK
    stack_norm = row["stack_before"] / _STARTING_STACK

    # Derive cost_to_call from context:
    #   - For CALL actions, amount = chips paid to match = cost_to_call.
    #   - For FOLD, there was a cost but the player didn't pay. Approximate
    #     from (current_bet - already contributed this round). Since we don't
    #     have per-round contribution, use current_bet as upper bound proxy.
    #   - For CHECK/BET, cost_to_call = 0 by definition.
    #   - For RAISE, the player paid more than cost_to_call. Use current_bet
    #     before this action as the cost they faced.
    if action == "call":
        cost = row["amount"] / _STARTING_STACK
    elif action == "fold":
        # Approximate: current_bet is the max anyone has put in this round.
        # The folder faced at most this much. Cap at a reasonable value.
        cost = min(row.get("current_bet", 2), 8) / _STARTING_STACK
    elif action == "raise":
        # The raiser faced a cost_to_call before raising. Approximate from
        # current_bet before the raise (which is the bet level they matched
        # plus the raise increment). Use half of current_bet as proxy.
        cost = min(row.get("current_bet", 2), 8) / _STARTING_STACK
    else:
        cost = 0.0

    bet_count_norm = row.get("bet_count", 0) / 4.0
    position = ((row["seat"] - dealer) % 8) / 7.0
    is_facing = 1.0 if action in ("fold", "call", "raise") else 0.0

    features = [
        betting_round, pot_norm, stack_norm,
        cost, bet_count_norm, position, is_facing,
    ]

    if hand_strength is not None:
        hs_val = _HS_MAP.get(hand_strength)
        if hs_val is None:
            return None
        features.append(hs_val)

    return features, label


def get_feature_names(include_hand_strength: bool) -> List[str]:
    """Return the ordered feature name list matching the feature vector."""
    if include_hand_strength:
        return list(FEATURE_NAMES_WITH_HS)
    return list(FEATURE_NAMES_BASE)
