"""Quick 500-hand validation of ML agents against Phase 1 spec ranges.

Runs 8 ML agents for 500 hands and checks VPIP, PFR, AF against the
same EXPECTED ranges used in smoke_test.py for rule-based agents.

Usage::

    python -m ml.smoke_test_ml --modeldir ml/models_split/rf
    python -m ml.smoke_test_ml --modeldir ml/models_split/rf --hands 1000
"""

from __future__ import annotations

import argparse
import sys
import warnings

warnings.filterwarnings("ignore")

from agents.ml_agent import MLAgent
from engine.table import Table
from ml.feature_engineering import ARCHETYPES


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


def build_ml_agents(model_dir: str):
    agents = []
    for seat, archetype in enumerate(ARCHETYPES):
        agents.append(MLAgent(
            seat=seat,
            archetype=archetype,
            model_dir=model_dir,
        ))
    return agents


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modeldir", required=True, help="Path to model directory")
    parser.add_argument("--hands", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    agents = build_ml_agents(args.modeldir)
    table = Table(agents, seed=args.seed)

    for _ in range(args.hands):
        table.play_hand()

    fails = 0
    print("=" * 70)
    print(f"ML SMOKE TEST — {args.hands} hands, seed={args.seed}")
    print(f"Models: {args.modeldir}")
    print("=" * 70)

    for agent in agents:
        arch = agent._base_archetype
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

    # Prediction stats
    print(f"\n  Prediction stats:")
    for agent in agents:
        stats = agent.prediction_stats()
        print(f"    {agent._base_archetype:15s}: "
              f"{stats['predictions']} predictions, "
              f"{stats['fallbacks']} fallbacks ({stats['fallback_rate']:.1%})")

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
        print(f"RESULT: {fails} check(s) FAILED")
        return 1
    print("RESULT: All ML archetypes in spec range — ready for full run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
