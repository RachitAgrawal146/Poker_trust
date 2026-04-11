"""
PREFLOP HAND STRENGTH LOOKUP TABLE
====================================
All 169 distinct starting hand types, categorized as Strong/Medium/Weak.

Usage:
    from preflop_lookup import get_preflop_bucket
    
    bucket = get_preflop_bucket("Ah", "Ks")  # "Strong" (AKs)
    bucket = get_preflop_bucket("7d", "2c")  # "Weak"

Hand notation:
    "s" = suited (same suit), "o" = offsuit (different suits)
    Pairs are always the same rank, e.g., "AA", "KK"
"""


# =============================================================================
# STRONG HANDS (top ~8% of starting hands)
# Premium pairs and big suited/offsuit broadways
# Expected equity vs random hand: > 66%
# =============================================================================
STRONG_HANDS = {
    # Premium pairs
    "AA", "KK", "QQ", "JJ",
    # Big aces
    "AKs", "AKo", "AQs",
}

# =============================================================================
# MEDIUM HANDS (next ~12% of starting hands)
# Medium pairs, suited broadways, strong offsuit broadways
# Expected equity vs random hand: 33-66%
# =============================================================================
MEDIUM_HANDS = {
    # Medium-high pairs
    "TT", "99", "88", "77",
    # Suited broadways and connectors
    "AJs", "ATs", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs",
    # Strong offsuit broadways
    "AQo", "AJo", "ATo",
    # Suited aces
    "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    # Suited connectors
    "T9s", "98s", "87s", "76s", "65s",
}

# =============================================================================
# Everything else is WEAK
# Low pairs, offsuit junk, unsuited connectors, random hands
# Expected equity vs random hand: < 33%
# =============================================================================


def _normalize_hand(card1_str, card2_str):
    """
    Convert two card strings (e.g., "Ah", "Ks") into a canonical hand name
    (e.g., "AKs" or "AKo" or "AA").
    
    Card string format: rank + suit, e.g., "Ah", "Td", "9c", "2s"
    Ranks: A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2
    Suits: h, d, c, s
    """
    rank_order = "AKQJT98765432"
    
    r1, s1 = card1_str[0].upper(), card1_str[1].lower()
    r2, s2 = card2_str[0].upper(), card2_str[1].lower()
    
    # Ensure higher rank comes first
    if rank_order.index(r1) > rank_order.index(r2):
        r1, s1, r2, s2 = r2, s2, r1, s1
    
    if r1 == r2:
        return f"{r1}{r2}"  # Pair: "AA", "KK", etc.
    elif s1 == s2:
        return f"{r1}{r2}s"  # Suited: "AKs", "T9s", etc.
    else:
        return f"{r1}{r2}o"  # Offsuit: "AKo", "T9o", etc.


def get_preflop_bucket(card1_str, card2_str):
    """
    Returns "Strong", "Medium", or "Weak" for a given preflop hand.
    
    Args:
        card1_str: First card, e.g., "Ah", "Td"
        card2_str: Second card, e.g., "Ks", "9c"
    
    Returns:
        "Strong", "Medium", or "Weak"
    
    Examples:
        get_preflop_bucket("Ah", "Kh")  # "Strong" (AKs)
        get_preflop_bucket("Ah", "Kd")  # "Strong" (AKo)
        get_preflop_bucket("Td", "Tc")  # "Medium" (TT)
        get_preflop_bucket("9h", "8h")  # "Medium" (98s)
        get_preflop_bucket("7d", "2c")  # "Weak" (72o)
    """
    hand_name = _normalize_hand(card1_str, card2_str)
    
    if hand_name in STRONG_HANDS:
        return "Strong"
    elif hand_name in MEDIUM_HANDS:
        return "Medium"
    else:
        return "Weak"


def get_preflop_bucket_from_treys(treys_card1, treys_card2):
    """
    Same as get_preflop_bucket but accepts treys library Card integers.
    
    Usage with treys:
        from treys import Card
        c1 = Card.new("Ah")
        c2 = Card.new("Kd")
        bucket = get_preflop_bucket_from_treys(c1, c2)
    """
    from treys import Card
    s1 = Card.int_to_str(treys_card1)
    s2 = Card.int_to_str(treys_card2)
    return get_preflop_bucket(s1, s2)


# =============================================================================
# VPIP RANGES — Which hands each archetype voluntarily plays preflop
# =============================================================================
# These define the preflop hand selection for each static archetype.
# Adaptive archetypes start with their default range and may adjust.
# =============================================================================

# Oracle: ~22-25% of hands (VPIP 22-25)
ORACLE_PREFLOP_RANGE = STRONG_HANDS | MEDIUM_HANDS  # ~20% base, slightly wider

# Sentinel: ~15-20% of hands (VPIP 15-20)
SENTINEL_PREFLOP_RANGE = STRONG_HANDS | {
    "TT", "99", "88", "77",
    "AJs", "ATs", "KQs", "KJs", "QJs", "JTs",
    "AQo", "AJo",
}

# Firestorm: ~48-58% of hands (VPIP 48-58) — plays almost everything
# Instead of a whitelist, use a blacklist of the worst hands
FIRESTORM_FOLD_RANGE = {
    # Only folds the absolute worst hands
    "72o", "73o", "82o", "83o", "84o", "92o", "93o",
    "T2o", "T3o", "J2o", "Q2o", "32o", "42o", "43o",
    "52o", "53o", "62o", "63o", "64o",
}

# Wall: ~38-48% of hands (VPIP 38-48) — enters loose but passively
WALL_PREFLOP_RANGE = STRONG_HANDS | MEDIUM_HANDS | {
    "66", "55", "44", "33", "22",
    "KQo", "KJo", "KTo", "QJo", "QTo", "JTo",
    "54s", "43s", "T8s", "97s", "86s", "75s", "64s",
    "J9s", "Q9s", "K9s",
    "A9o", "A8o", "A7o", "A6o",
    "T9o", "98o", "87o",
}

# Phantom: ~35-45% of hands (VPIP 35-45)
PHANTOM_PREFLOP_RANGE = STRONG_HANDS | MEDIUM_HANDS | {
    "66", "55", "44", "33", "22",
    "KQo", "KJo", "KTo", "QJo", "QTo", "JTo",
    "54s", "T8s", "97s", "86s", "75s",
    "J9s", "Q9s", "K9s",
    "J8s", "T7s", "96s", "85s",
}
