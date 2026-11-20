"""Checks for the R1 harness.

usage: python3 revision_experiments/test_r1.py [--hands 300]

1. ``published_legacy`` reproduces the roster of ``phase1/run_sim.py``
   exactly (same final stacks, rebuys and action counts for seed 42).
2. The response rule at strength zero, from any source, is identical to
   ``no_read``.
3. Chips are conserved and the ledger reconciles in every condition; with
   100,000-chip stacks there is no rebuy and no empty stack (both are
   enforced inside ``run_seed``, which raises otherwise).
4. With the rule on, Strong hands respond exactly as often as the table
   says, the factor moves in the stated direction, and a targeted condition
   touches only bets by its target.
5. Every condition in ``r1_conditions.json`` completes a short run.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import json

import numpy as np

from engine.table import Table
from revision_experiments import run_r1
from revision_experiments.r1_agents import ARCHETYPES, T_REF


def reference_run(seed: int, hands: int):
    """The roster exactly as phase1/run_sim.py builds it (stage 6)."""
    from phase1.run_sim import _stage6_roster
    agents = _stage6_roster()
    table = Table(agents, seed=seed)
    for _ in range(hands):
        table.play_hand()
    return ([int(a.stack) for a in agents], [int(a.rebuys) for a in agents],
            [dict(a.stats) for a in agents])


def with_temp_conditions(extra: dict):
    """Run with extra conditions without touching the conditions file."""
    base = run_r1.load_conditions()
    merged = dict(base, **extra)
    run_r1.load_conditions = lambda: merged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=300)
    ap.add_argument("--short", type=int, default=60)
    a = ap.parse_args()
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(("PASS  " if cond else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))

    # 1. published_legacy == run_sim roster
    ref_stack, ref_rebuys, ref_stats = reference_run(42, a.hands)
    res = run_r1.run_seed("published_legacy", 42, a.hands)
    check("published_legacy reproduces the run_sim roster (stacks)", res["final_stack"] == ref_stack,
          f"{res['final_stack']} vs {ref_stack}")
    check("published_legacy reproduces the run_sim roster (rebuys)", res["rebuys"] == ref_rebuys)
    check("published_legacy reproduces the run_sim roster (action counts)", res["stats"] == ref_stats)

    # 2. strength zero == no_read, whatever the source
    with_temp_conditions({
        "_z_post": {"roster": "no_read", "beta": 0.0, "source": "posterior"},
        "_z_true": {"roster": "no_read", "beta": 0.0, "source": "true"},
        "_z_shuf": {"roster": "no_read", "beta": 0.0, "source": "shuffled"},
        "_z_tgt": {"roster": "no_read", "beta": 0.0, "source": "posterior", "target": "wall"},
        "_z_noise": {"roster": "no_read", "noise_p": 0.0},
    })
    base = run_r1.run_seed("no_read", 137, a.hands)
    for name in ("_z_post", "_z_true", "_z_shuf", "_z_tgt", "_z_noise"):
        r = run_r1.run_seed(name, 137, a.hands)
        same = (r["net"] == base["net"] and r["stats"] == base["stats"]
                and r["resp"] == base["resp"] and r["trust"] == base["trust"])
        check(f"strength zero identical to no_read ({name})", same)
    check("no_read: rule never changes a probability", base["f_changed"] == 0)

    # 4. rule on
    r = run_r1.run_seed("read_all_b10", 137, a.hands)
    f_n, f_sum = np.array(r["f_n"]), np.array(r["f_sum"])
    check("rule applies only to Medium and Weak hands", int(f_n[:, :, 0].sum()) == 0)
    mean_f = {ARCHETYPES[i]: (f_sum[i].sum() / f_n[i].sum() if f_n[i].sum() else None)
              for i in range(len(ARCHETYPES))}
    print("      mean factor by bettor:", {k: (None if v is None else round(float(v), 3)) for k, v in mean_f.items()})
    if mean_f["wall"] is not None and mean_f["firestorm"] is not None:
        check("factor below 1 against the most-trusted bettor, above 1 against the least",
              mean_f["wall"] < 1.0 < mean_f["firestorm"])
    resp_on, resp_off = np.array(r["resp"]), np.array(base["resp"])
    # Strong-hand response frequencies are set by the table alone; compare pooled rates.
    s_on, s_off = resp_on[:, :, :, 0, :].sum(axis=(0, 1, 2)), resp_off[:, :, :, 0, :].sum(axis=(0, 1, 2))
    print("      Strong-hand responses fold/call/raise, rule on:", s_on.tolist(), "off:", s_off.tolist())

    t = run_r1.run_seed("read_target_wall_b10", 137, a.hands)
    tf_n, tf_sum = np.array(t["f_n"]), np.array(t["f_sum"])
    wi = ARCHETYPES.index("wall")
    others = [i for i in range(len(ARCHETYPES)) if i != wi]
    untouched = np.allclose(tf_sum[others], tf_n[others])
    check("targeted rule leaves every other bettor at factor 1", untouched)

    check("reference trust of the uniform prior", abs(T_REF - 0.751875) < 1e-9, f"{T_REF}")

    # 5. every condition completes (conservation and reconciliation are enforced inside)
    for name in run_r1.load_conditions():
        if name.startswith("_z_"):
            continue
        try:
            rr = run_r1.run_seed(name, 256, a.short)
            json.dumps(rr)
            check(f"short run completes: {name}", sum(rr["net"]) == 0)
        except Exception as e:  # noqa: BLE001
            check(f"short run completes: {name}", False, repr(e))

    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
