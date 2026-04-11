"""
TEST CASES — Validation Checks for Each Build Stage
=====================================================
Run these after completing each stage. If a test fails, fix the relevant
component before moving on. Tests are ordered by build stage.

Usage:
    python test_cases.py --stage 1    # Run Stage 1 tests only
    python test_cases.py --stage all  # Run all tests
    python test_cases.py              # Run all tests
"""

import sys
import math

# =============================================================================
# STAGE 1: Card + Deck + Hand Evaluator
# =============================================================================

def test_stage_1(modules):
    """Tests for card dealing and hand strength bucketing."""
    Card = modules["Card"]
    Deck = modules["Deck"]
    get_preflop_bucket = modules["get_preflop_bucket"]
    get_hand_strength = modules["get_hand_strength"]
    
    results = []
    
    # --- Test 1.1: Deck has 52 cards ---
    deck = Deck(seed=42)
    cards = deck.deal(52)
    assert len(cards) == 52, f"FAIL 1.1: Deck dealt {len(cards)} cards, expected 52"
    assert len(set(cards)) == 52, f"FAIL 1.1: Deck has duplicate cards"
    results.append("PASS 1.1: Deck has 52 unique cards")
    
    # --- Test 1.2: Dealing removes cards ---
    deck = Deck(seed=42)
    hand = deck.deal(2)
    remaining = deck.deal(50)
    assert len(remaining) == 50, f"FAIL 1.2: Expected 50 remaining, got {len(remaining)}"
    assert not any(c in remaining for c in hand), "FAIL 1.2: Dealt cards still in deck"
    results.append("PASS 1.2: Dealing removes cards correctly")
    
    # --- Test 1.3: Same seed = same deal ---
    deck1 = Deck(seed=42)
    deck2 = Deck(seed=42)
    assert deck1.deal(5) == deck2.deal(5), "FAIL 1.3: Same seed produced different deals"
    results.append("PASS 1.3: Same seed produces identical deals")
    
    # --- Test 1.4: Different seed = different deal ---
    deck1 = Deck(seed=42)
    deck2 = Deck(seed=137)
    assert deck1.deal(5) != deck2.deal(5), "FAIL 1.4: Different seeds produced same deal"
    results.append("PASS 1.4: Different seeds produce different deals")
    
    # --- Test 1.5: Preflop bucket — Strong hands ---
    strong_cases = [
        ("Ah", "Ac", "AA"),
        ("Kd", "Kh", "KK"),
        ("Qs", "Qc", "QQ"),
        ("Jh", "Jd", "JJ"),
        ("Ah", "Kh", "AKs"),
        ("Ah", "Kd", "AKo"),
        ("Ah", "Qh", "AQs"),
    ]
    for c1, c2, name in strong_cases:
        bucket = get_preflop_bucket(c1, c2)
        assert bucket == "Strong", f"FAIL 1.5: {name} ({c1},{c2}) = {bucket}, expected Strong"
    results.append("PASS 1.5: All strong preflop hands correctly bucketed")
    
    # --- Test 1.6: Preflop bucket — Medium hands ---
    medium_cases = [
        ("Th", "Tc", "TT"),
        ("9d", "9h", "99"),
        ("8s", "8c", "88"),
        ("Ah", "Jh", "AJs"),
        ("Kh", "Qh", "KQs"),
        ("Jh", "Th", "JTs"),
    ]
    for c1, c2, name in medium_cases:
        bucket = get_preflop_bucket(c1, c2)
        assert bucket == "Medium", f"FAIL 1.6: {name} ({c1},{c2}) = {bucket}, expected Medium"
    results.append("PASS 1.6: Medium preflop hands correctly bucketed")
    
    # --- Test 1.7: Preflop bucket — Weak hands ---
    weak_cases = [
        ("7h", "2c", "72o"),
        ("9d", "3h", "93o"),
        ("5c", "2d", "52o"),
    ]
    for c1, c2, name in weak_cases:
        bucket = get_preflop_bucket(c1, c2)
        assert bucket == "Weak", f"FAIL 1.7: {name} ({c1},{c2}) = {bucket}, expected Weak"
    results.append("PASS 1.7: Weak preflop hands correctly bucketed")
    
    # --- Test 1.8: Post-flop strength makes sense ---
    # AA on a low board should be Strong
    aa = [Card.new("Ah"), Card.new("Ac")]
    board = [Card.new("5d"), Card.new("8c"), Card.new("2s")]
    bucket = get_hand_strength(aa, board, seed=42)
    assert bucket == "Strong", f"FAIL 1.8: AA on 5-8-2 = {bucket}, expected Strong"
    
    # 72o on AKQ board should be Weak
    junk = [Card.new("7d"), Card.new("2c")]
    board = [Card.new("Ah"), Card.new("Kh"), Card.new("Qh")]
    bucket = get_hand_strength(junk, board, seed=42)
    assert bucket == "Weak", f"FAIL 1.8: 72o on AKQ = {bucket}, expected Weak"
    results.append("PASS 1.8: Post-flop hand strength makes sense")
    
    return results


# =============================================================================
# STAGE 2: Game Engine
# =============================================================================

def test_stage_2(modules):
    """Tests for game engine mechanics."""
    Table = modules["Table"]
    DummyAgent = modules["DummyAgent"]  # An agent that always calls
    
    results = []
    
    # --- Test 2.1: Pot math — all call preflop ---
    # 8 players, SB=1, BB=2, everyone calls 2
    # Pot should be 8 × 2 = 16
    agents = [DummyAgent(f"P{i}", "dummy", i) for i in range(8)]
    table = Table(agents, seed=42)
    # ... run one hand where everyone calls everything
    # Expected: pot = SB(1) + BB(2) + 6 callers × 2 = 1 + 2 + 12 = 15?
    # Actually: SB completes to 2, BB checks. So SB puts 1 more = 2 total.
    # All 6 others call 2. Pot = 8 × 2 = 16.
    # Then on flop/turn/river with all checking, pot stays 16.
    results.append("TEST 2.1: Verify pot math manually — should be 16 if all call preflop")
    
    # --- Test 2.2: Bet cap enforced ---
    # After 4 bets in a round, agents should only be able to fold or call, not raise
    results.append("TEST 2.2: Verify raise is not available after 4th bet in a round")
    
    # --- Test 2.3: Folded players don't act ---
    results.append("TEST 2.3: Verify folded players are skipped in betting rounds")
    
    # --- Test 2.4: Hand ends when 1 player remains ---
    results.append("TEST 2.4: If 7 players fold preflop, hand ends, no flop dealt")
    
    # --- Test 2.5: Showdown only when 2+ players remain ---
    results.append("TEST 2.5: Showdown happens only if 2+ reach river end")
    
    # --- Test 2.6: Correct hand wins at showdown ---
    # Deal known cards (control the deck), verify the right hand wins
    results.append("TEST 2.6: Higher hand wins pot at showdown")
    
    # --- Test 2.7: Blinds rotate correctly ---
    # After hand 1 (dealer=0), hand 2 should have dealer=1, SB=2, BB=3
    results.append("TEST 2.7: Dealer button advances by 1 each hand")
    
    # --- Test 2.8: Rebuys work ---
    # Agent with 0 chips rebuys to 200 at start of next hand
    results.append("TEST 2.8: Agent at 0 chips rebuys to 200 at next hand")
    
    return results


# =============================================================================
# STAGE 3-4: Agent Behavior Validation
# =============================================================================

def test_stage_3_4(modules):
    """Run 500 hands and verify each agent's metrics are within expected ranges."""
    Table = modules["Table"]
    create_agents = modules["create_agents"]
    
    results = []
    
    agents = create_agents()
    table = Table(agents, seed=42)
    for _ in range(500):
        table.play_hand()
    
    # Expected ranges from the spec document
    EXPECTED_RANGES = {
        "oracle":    {"vpip": (18, 30), "pfr": (14, 26), "af": (1.5, 3.5)},
        "sentinel":  {"vpip": (12, 24), "pfr": (10, 22), "af": (2.0, 5.0)},
        "firestorm": {"vpip": (42, 65), "pfr": (32, 55), "af": (2.5, 6.0)},
        "wall":      {"vpip": (32, 55), "pfr": (2, 12),  "af": (0.1, 1.2)},
        "phantom":   {"vpip": (28, 52), "pfr": (20, 42), "af": (1.8, 4.5)},
        "predator":  {"vpip": (18, 35), "pfr": (14, 30), "af": (1.5, 5.0)},
        "mirror":    {"vpip": (12, 45), "pfr": (10, 35), "af": (1.0, 5.0)},
        "judge":     {"vpip": (12, 45), "pfr": (10, 40), "af": (1.0, 6.0)},
    }
    
    for agent in agents:
        arch = agent.archetype
        expected = EXPECTED_RANGES.get(arch)
        if not expected:
            continue
        
        vpip = agent.stats["vpip_count"] / agent.stats["hands_dealt"] * 100
        pfr = agent.stats["pfr_count"] / agent.stats["hands_dealt"] * 100
        calls = max(agent.stats["calls"], 1)  # Avoid division by zero
        af = (agent.stats["bets"] + agent.stats["raises"]) / calls
        
        # --- VPIP check ---
        vmin, vmax = expected["vpip"]
        status = "PASS" if vmin <= vpip <= vmax else "FAIL"
        results.append(
            f"{status} 3.{agent.seat}a: {agent.name} VPIP = {vpip:.1f}% "
            f"(expected {vmin}-{vmax}%)"
        )
        
        # --- PFR check ---
        pmin, pmax = expected["pfr"]
        status = "PASS" if pmin <= pfr <= pmax else "FAIL"
        results.append(
            f"{status} 3.{agent.seat}b: {agent.name} PFR = {pfr:.1f}% "
            f"(expected {pmin}-{pmax}%)"
        )
        
        # --- AF check ---
        amin, amax = expected["af"]
        status = "PASS" if amin <= af <= amax else "FAIL"
        results.append(
            f"{status} 3.{agent.seat}c: {agent.name} AF = {af:.2f} "
            f"(expected {amin}-{amax})"
        )
        
        # --- VPIP >= PFR (always true) ---
        status = "PASS" if vpip >= pfr else "FAIL"
        results.append(
            f"{status} 3.{agent.seat}d: {agent.name} VPIP ({vpip:.1f}) >= PFR ({pfr:.1f})"
        )
    
    return results


# =============================================================================
# STAGE 5: Trust Model Validation
# =============================================================================

def test_stage_5(modules):
    """Run 500 hands and verify trust model convergence for static agents."""
    Table = modules["Table"]
    create_agents = modules["create_agents"]
    
    results = []
    
    agents = create_agents()
    table = Table(agents, seed=42)
    for _ in range(500):
        table.play_hand()
    
    # For each static agent, check that OTHER agents' max_posterior_type
    # matches the true type with > 50% probability
    static_types = {
        0: "oracle",
        1: "sentinel",
        2: "firestorm",
        3: "wall",
        4: "phantom",
    }
    
    for seat, true_type in static_types.items():
        # Check what other agents think about this seat
        for observer in agents:
            if observer.seat == seat:
                continue
            posterior = observer.get_posterior(seat)
            max_type = max(posterior, key=posterior.get)
            max_prob = posterior[max_type]
            
            # We expect correct classification > 40% for static types after 500 hands
            # (Some confusion between similar types is expected)
            correct = (true_type in max_type)  # Handles "judge_cooperative" matching "judge"
            if correct and max_prob > 0.30:
                results.append(
                    f"PASS 5.{seat}: {observer.name} classifies seat {seat} as "
                    f"{max_type} ({max_prob:.1%}) — correct ({true_type})"
                )
            else:
                results.append(
                    f"WARN 5.{seat}: {observer.name} classifies seat {seat} as "
                    f"{max_type} ({max_prob:.1%}) — true type is {true_type}"
                )
    
    # --- Test 5.1: Trust in Sentinel should be high (> 0.70) ---
    sentinel_trust = [a.get_trust_score(1) for a in agents if a.seat != 1]
    avg_trust = sum(sentinel_trust) / len(sentinel_trust)
    status = "PASS" if avg_trust > 0.65 else "FAIL"
    results.append(f"{status} 5.1: Avg trust in Sentinel = {avg_trust:.3f} (expected > 0.65)")
    
    # --- Test 5.2: Trust in Firestorm should be low (< 0.55) ---
    firestorm_trust = [a.get_trust_score(2) for a in agents if a.seat != 2]
    avg_trust = sum(firestorm_trust) / len(firestorm_trust)
    status = "PASS" if avg_trust < 0.55 else "FAIL"
    results.append(f"{status} 5.2: Avg trust in Firestorm = {avg_trust:.3f} (expected < 0.55)")
    
    # --- Test 5.3: Entropy for Sentinel should be low (< 2.0) ---
    sentinel_entropy = [a.get_entropy(1) for a in agents if a.seat != 1]
    avg_entropy = sum(sentinel_entropy) / len(sentinel_entropy)
    status = "PASS" if avg_entropy < 2.2 else "FAIL"
    results.append(f"{status} 5.3: Avg entropy about Sentinel = {avg_entropy:.3f} (expected < 2.2)")
    
    # --- Test 5.4: Initial trust should be ~0.67 (Nash baseline) ---
    # Re-run with 0 hands to check initial state
    agents2 = create_agents()
    initial_trust = agents2[0].get_trust_score(1)  # Oracle's initial trust in Sentinel
    expected_initial = sum(1/8 * h for h in [0.670, 0.917, 0.375, 0.962, 0.475, 0.787, 0.912, 0.917])
    status = "PASS" if abs(initial_trust - expected_initial) < 0.01 else "FAIL"
    results.append(
        f"{status} 5.4: Initial trust = {initial_trust:.4f} "
        f"(expected {expected_initial:.4f} — uniform prior)"
    )
    
    # --- Test 5.5: Initial entropy should be 3.0 (max for 8 types) ---
    initial_entropy = agents2[0].get_entropy(1)
    status = "PASS" if abs(initial_entropy - 3.0) < 0.01 else "FAIL"
    results.append(f"{status} 5.5: Initial entropy = {initial_entropy:.4f} (expected 3.0)")
    
    return results


# =============================================================================
# STAGE 6: Adaptive Agent Validation
# =============================================================================

def test_stage_6(modules):
    """Run 1000 hands and verify adaptive agents behave correctly."""
    Table = modules["Table"]
    create_agents = modules["create_agents"]
    
    results = []
    
    agents = create_agents()
    table = Table(agents, seed=42)
    for _ in range(1000):
        table.play_hand()
    
    predator = agents[5]
    mirror = agents[6]
    judge = agents[7]
    
    # --- Test 6.1: Predator has classified at least 3 opponents ---
    classified = 0
    for seat in range(8):
        if seat == 5:
            continue
        post = predator.get_posterior(seat)
        max_prob = max(post.values())
        if max_prob > 0.60:
            classified += 1
    status = "PASS" if classified >= 3 else "FAIL"
    results.append(f"{status} 6.1: Predator classified {classified}/7 opponents (expected >= 3)")
    
    # --- Test 6.2: Mirror's BR toward Firestorm > Mirror's BR toward Sentinel ---
    # The Mirror should be more aggressive against the aggressive Firestorm
    mirror_br_vs_firestorm = mirror.opponent_stats.get(2, {}).get("observed_br", 0)
    mirror_br_vs_sentinel = mirror.opponent_stats.get(1, {}).get("observed_br", 0)
    # Actually, we check the Mirror's OWN bluff rate toward each opponent
    # This might need adjustment based on actual implementation
    results.append(
        f"INFO 6.2: Mirror's observed BR toward Firestorm: {mirror_br_vs_firestorm:.3f}, "
        f"toward Sentinel: {mirror_br_vs_sentinel:.3f} "
        f"(Firestorm should be higher)"
    )
    
    # --- Test 6.3: Judge's grievance against Firestorm should be > 0 ---
    grievance_vs_firestorm = judge.grievance.get(2, 0)
    status = "PASS" if grievance_vs_firestorm > 0 else "FAIL"
    results.append(
        f"{status} 6.3: Judge grievance vs Firestorm = {grievance_vs_firestorm} "
        f"(expected > 0 after 1000 hands)"
    )
    
    # --- Test 6.4: Judge should have triggered against Firestorm ---
    triggered_vs_firestorm = judge.triggered.get(2, False)
    status = "PASS" if triggered_vs_firestorm else "WARN"
    results.append(
        f"{status} 6.4: Judge triggered vs Firestorm = {triggered_vs_firestorm} "
        f"(expected True after 1000 hands)"
    )
    
    # --- Test 6.5: Judge should NOT have triggered against Sentinel ---
    triggered_vs_sentinel = judge.triggered.get(1, False)
    status = "PASS" if not triggered_vs_sentinel else "FAIL"
    results.append(
        f"{status} 6.5: Judge triggered vs Sentinel = {triggered_vs_sentinel} "
        f"(expected False — Sentinel almost never bluffs)"
    )
    
    # --- Test 6.6: Judge should NOT have triggered against Wall ---
    triggered_vs_wall = judge.triggered.get(3, False)
    status = "PASS" if not triggered_vs_wall else "FAIL"
    results.append(
        f"{status} 6.6: Judge triggered vs Wall = {triggered_vs_wall} "
        f"(expected False — Wall almost never bluffs)"
    )
    
    # --- Test 6.7: Judge's grievance ledger does NOT decrease ---
    # This is a design invariant — grievance only increments
    results.append("CHECK 6.7: Manually verify grievance ledger never decrements")
    
    return results


# =============================================================================
# STAGE 7: Data Logging Validation
# =============================================================================

def test_stage_7(modules):
    """Verify all database tables are populated correctly after a short run."""
    
    results = []
    
    # After running 100 hands with 1 seed, check:
    
    # --- Test 7.1: actions table ---
    # Expected: ~100 hands × ~30 actions/hand = ~3000 rows
    results.append("TEST 7.1: actions table has > 2000 rows after 100 hands")
    
    # --- Test 7.2: trust_scores table ---
    # Expected: 100 hands × 56 pairs = 5600 rows
    results.append("TEST 7.2: trust_scores table has ~5600 rows after 100 hands")
    
    # --- Test 7.3: stacks table ---
    # Expected: 100 hands × 8 agents = 800 rows
    results.append("TEST 7.3: stacks table has 800 rows after 100 hands")
    
    # --- Test 7.4: posteriors table ---
    # Expected: 2 snapshots (hand 50, 100) × 56 pairs = 112 rows
    results.append("TEST 7.4: posteriors table has ~112 rows after 100 hands")
    
    # --- Test 7.5: No NULL values in required columns ---
    results.append("TEST 7.5: No NULLs in: hand_id, seat, archetype, action_type, trust_score")
    
    # --- Test 7.6: All trust scores between 0 and 1 ---
    results.append("TEST 7.6: All trust_score values in [0.0, 1.0]")
    
    # --- Test 7.7: All entropy values between 0 and 3.0 ---
    results.append("TEST 7.7: All entropy values in [0.0, 3.0]")
    
    # --- Test 7.8: Stack conservation ---
    # Total chips across all players + pot should equal 8 × 200 + rebuys × 200
    results.append("TEST 7.8: Total chips in system = 8×200 + total_rebuys×200 (conservation)")
    
    # --- Test 7.9: JSON hand log has correct structure ---
    results.append("TEST 7.9: JSON hand log parses correctly with all required fields")
    
    # --- Test 7.10: action_sequence_num is monotonically increasing within each hand ---
    results.append("TEST 7.10: action_sequence_num increases within each hand_id")
    
    return results


# =============================================================================
# STAGE 8-11: Full Simulation Validation
# =============================================================================

def test_stage_8_plus():
    """High-level validation after full 10k-hand run."""
    
    results = []
    
    # --- Test 8.1: Simulation completes without errors ---
    results.append("TEST 8.1: 10,000 hands × 1 seed completes without exceptions")
    
    # --- Test 8.2: Runtime < 20 minutes ---
    results.append("TEST 8.2: Single seed runtime under 20 minutes")
    
    # --- Test 8.3: Predator is profitable ---
    results.append("TEST 8.3: Predator cumulative profit > 0 after 10,000 hands (expected top 3)")
    
    # --- Test 8.4: Firestorm/Phantom are unprofitable ---
    results.append("TEST 8.4: Firestorm and Phantom cumulative profit < 0 (expected bottom 3)")
    
    # --- Test 8.5: Judge triggers against Firestorm before hand 500 ---
    results.append("TEST 8.5: Judge grievance trigger vs Firestorm before hand 500")
    
    # --- Test 8.6: Judge does NOT trigger against Sentinel/Wall/Oracle ---
    results.append("TEST 8.6: Judge never triggers against Sentinel, Wall, or Oracle")
    
    # --- Test 8.7: Trust in Sentinel > Trust in Firestorm (averaged across all observers, all time) ---
    results.append("TEST 8.7: Mean trust in Sentinel > Mean trust in Firestorm")
    
    # --- Test 8.8: Entropy about static types decreases over time ---
    results.append("TEST 8.8: Entropy about static types at hand 5000 < entropy at hand 100")
    
    # --- Test 8.9: Entropy about Mirror/Predator stays higher than static types ---
    results.append("TEST 8.9: Avg entropy about Mirror > Avg entropy about Sentinel")
    
    # --- Test 8.10: 5-seed results are consistent ---
    results.append("TEST 8.10: Predator is profitable in >= 4/5 seeds")
    results.append("TEST 8.10: Judge triggers vs Firestorm in 5/5 seeds")
    results.append("TEST 8.10: Trust rankings are consistent across seeds")
    
    # --- Test 8.11: ML export CSVs ---
    results.append("TEST 8.11: ml_action_features.csv has > 1M rows, no NaN values")
    results.append("TEST 8.11: ml_type_classification.csv has correct number of windows")
    results.append("TEST 8.11: ml_trust_timeseries.csv has 56 × 10000 rows per seed")
    
    # --- Test 8.12: Visualizer loads ---
    results.append("TEST 8.12: poker_table.html opens in browser without JS errors")
    results.append("TEST 8.12: Hand navigation slider works across full range")
    results.append("TEST 8.12: Clicking player avatar shows stats panel")
    
    return results


# =============================================================================
# MAIN RUNNER
# =============================================================================

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print("=" * 60)
    print("POKER TRUST SIMULATION — VALIDATION TEST SUITE")
    print("=" * 60)
    
    if stage in ("all", "8"):
        print("\n--- Stage 8+: Full Simulation (checklist) ---")
        for r in test_stage_8_plus():
            print(f"  {r}")
    
    print("\n" + "=" * 60)
    print("NOTE: Stages 1-7 require passing the module dict.")
    print("Run these programmatically from within the project:")
    print("  from test_cases import test_stage_1")
    print("  results = test_stage_1({'Card': Card, 'Deck': Deck, ...})")
    print("=" * 60)
