#!/usr/bin/env python3
"""Quick 500-hand validation of all 8 archetypes.

Run this BEFORE any multiseed research run to catch parameter issues.
Every archetype's VPIP, PFR, and AF must land within the expected range
for the smoke test to pass. Also checks Judge grievance accumulation,
Mirror opponent tracking, and chip conservation.

Usage:
    python3 smoke_test.py
    python3 smoke_test.py --hands 1000 --seed 137
"""

from __future__ import annotations

# Ensure repo root is on sys.path (this file lives in phase1/ or phase2/)
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))


import argparse
import sys

from engine.table import Table


def build_stage6():
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom
    from agents.predator import Predator
    from agents.mirror import Mirror
    from agents.judge import Judge

    return [
        Oracle(seat=0), Sentinel(seat=1), Firestorm(seat=2), Wall(seat=3),
        Phantom(seat=4), Predator(seat=5), Mirror(seat=6), Judge(seat=7),
    ]


#: Expected behavioral ranges per archetype. Tuned for 500-hand runs at
#: seed=42 but should hold across any reasonable seed. Ranges are
#: deliberately wide enough to tolerate Monte Carlo variance at 500 hands
#: while still catching gross parameter errors (the Phantom bug produced
#: VPIP 19.8% against a 30-50% target — well outside any sane range).
EXPECTED = {
    #                   VPIP range      PFR range       AF range
    "oracle":          ((18, 30),       (3, 12),        (0.5, 3.0)),
    "sentinel":        ((12, 24),       (2, 12),        (0.5, 3.5)),
    "firestorm":       ((42, 62),       (8, 20),        (0.6, 3.0)),
    "wall":            ((38, 62),       (0, 8),         (0.05, 0.5)),
    "phantom":         ((30, 50),       (5, 18),        (0.5, 3.0)),
    "predator":        ((14, 32),       (2, 10),        (0.4, 3.0)),
    "mirror":          ((12, 42),       (2, 12),        (0.3, 3.5)),
    "judge":           ((12, 24),       (2, 15),        (0.5, 4.0)),
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hands", type=int, default=500, help="Hands to play (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    args = parser.parse_args(argv)

    agents = build_stage6()
    table = Table(agents, seed=args.seed)

    for _ in range(args.hands):
        table.play_hand()

    fails = 0
    print("=" * 70)
    print(f"SMOKE TEST — {args.hands} hands, seed={args.seed}")
    print("=" * 70)

    for agent in agents:
        arch = agent.archetype
        vpip = agent.vpip() * 100
        pfr = agent.pfr() * 100
        af = agent.af()

        exp = EXPECTED.get(arch)
        if not exp:
            continue

        (vmin, vmax), (pmin, pmax), (amin, amax) = exp

        v_ok = vmin <= vpip <= vmax
        p_ok = pmin <= pfr <= pmax
        a_ok = amin <= af <= amax

        status = "PASS" if (v_ok and p_ok and a_ok) else "FAIL"
        if status == "FAIL":
            fails += 1

        flags = []
        if not v_ok:
            flags.append(f"VPIP {vpip:.1f}% not in [{vmin},{vmax}]")
        if not p_ok:
            flags.append(f"PFR {pfr:.1f}% not in [{pmin},{pmax}]")
        if not a_ok:
            flags.append(f"AF {af:.2f} not in [{amin},{amax}]")

        flag_str = " | ".join(flags) if flags else ""
        print(f"  {status} {arch:15s}  VPIP={vpip:5.1f}%  PFR={pfr:5.1f}%  AF={af:5.2f}"
              f"  {flag_str}")

    # Judge grievance check
    judge = agents[7]
    print(f"\n  Judge grievances after {args.hands} hands:")
    for seat in sorted(judge.grievance):
        trig = " TRIGGERED" if judge.triggered.get(seat) else ""
        trig_h = f" at hand {judge.trigger_hand[seat]}" if seat in judge.trigger_hand else ""
        print(f"    vs S{seat} ({agents[seat].archetype}): "
              f"grievance={judge.grievance[seat]}{trig}{trig_h}")
    if not judge.grievance:
        print(f"    (none — τ={judge.tau}, may need more hands)")

    # Mirror behavioral check
    mirror = agents[6]
    print(f"\n  Mirror observed opponent stats:")
    for seat in [1, 2, 3, 4]:  # Sentinel, Firestorm, Wall, Phantom
        stats = mirror.opponent_stats.get(seat, {})
        obs_br = stats.get("observed_br")
        obs_cr = stats.get("observed_cr")
        obs_vpip = stats.get("observed_vpip")
        arch_name = agents[seat].archetype
        if obs_br is not None:
            print(f"    vs {arch_name:12s}: obs_vpip={obs_vpip:.3f}  "
                  f"obs_br={obs_br:.3f}  obs_cr={obs_cr:.3f}")
        else:
            print(f"    vs {arch_name:12s}: (no data)")

    # Predator classification check
    predator = agents[5]
    print(f"\n  Predator posteriors (top archetype per target):")
    from trust import posterior_to_dict, TRUST_TYPE_LIST
    for seat in range(8):
        if seat == 5:
            continue
        post = predator.posteriors.get(seat)
        if post is not None:
            d = posterior_to_dict(post)
            top_arch = max(d, key=d.get)
            top_prob = d[top_arch]
            true_arch = agents[seat].archetype
            classified = "CLASSIFIED" if top_prob > 0.60 else ""
            print(f"    S{seat} ({true_arch:12s}): top={top_arch:<20} "
                  f"p={top_prob:.3f} {classified}")

    # Chip conservation
    total_chips = sum(a.stack for a in agents)
    total_rebuys = sum(a.rebuys for a in agents)
    expected_chips = 8 * 200 + total_rebuys * 200
    chip_ok = total_chips == expected_chips
    print(f"\n  Chip conservation: {'PASS' if chip_ok else 'FAIL'} "
          f"({total_chips} chips, {total_rebuys} rebuys, expected {expected_chips})")
    if not chip_ok:
        fails += 1

    print("=" * 70)
    if fails:
        print(f"RESULT: {fails} check(s) FAILED — DO NOT proceed to multiseed run")
        return 1
    print("RESULT: All archetypes in range — ready for multiseed run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
