"""One runner for every R1 rule-based condition.

usage:
  python3 revision_experiments/run_r1.py --condition no_read \
      --seeds 42,137,256,512 --hands 10000 --procs 4 --out out/

Writes one JSON file per seed, ``<out>/<condition>_seed<seed>.json``, holding
a per-seat ledger rather than a hand-by-hand database:

* net chips per seat (total, in hands where the seat reached showdown, in
  hands where it did not), the sum of squared per-hand results, and the net
  per block of 100 hands;
* mean trust held about each seat by the other seven, every 100 hands;
* counts of folds, calls and raises when facing a bet, by responder,
  bettor, street and the responder's hand bucket;
* counts of bets and checks when no bet is pending, by street and bucket;
* how often the response rule applied and the factor it used.

Conditions are defined in ``r1_conditions.json``. The default protocol is a
100,000-chip stack (no seat can go broke, so there are no rebuys, all-ins or
side pots) and a seat order permuted per seed. ``legacy`` conditions use the
200-chip stack with rebuys and the fixed seat order of the earlier runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import json
import multiprocessing as mp
import subprocess
import time

import numpy as np

from engine.table import Table
from revision_experiments.r1_agents import (
    ARCHETYPES, BUCKETS, RESPONSES, ROUNDS, T_REF, TRUST_TYPE, build_roster,
)
from trust import TRUST_TYPE_LIST

CONDITIONS_FILE = Path(__file__).with_name("r1_conditions.json")
BLOCK = 100
DEEP_STACK = 100_000
LEGACY_STACK = 200


def load_conditions() -> dict:
    return json.load(open(CONDITIONS_FILE))["conditions"]


def seat_order(seed: int, mode: str):
    if mode == "fixed":
        return list(ARCHETYPES)
    perm = np.random.default_rng([seed, 9001]).permutation(len(ARCHETYPES))
    return [ARCHETYPES[int(i)] for i in perm]


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def run_seed(condition: str, seed: int, hands: int) -> dict:
    cfg = load_conditions()[condition]
    legacy = bool(cfg.get("legacy", False))
    order = seat_order(seed, "fixed" if legacy else "permuted")
    agents, ctx = build_roster(cfg, order, seed)
    stack0 = LEGACY_STACK if legacy else DEEP_STACK
    for a in agents:
        a.stack = stack0
        a.rebuys = 0
    table = Table(agents, seed=seed)
    n = len(agents)
    type_idx = [TRUST_TYPE_LIST.index(TRUST_TYPE[a]) for a in order]

    net = np.zeros(n, dtype=np.int64)
    net_sd = np.zeros(n, dtype=np.int64)       # hands in which the seat reached showdown
    net_nsd = np.zeros(n, dtype=np.int64)
    sumsq = np.zeros(n, dtype=np.int64)
    n_sd = np.zeros(n, dtype=np.int64)
    n_sd_won = np.zeros(n, dtype=np.int64)
    n_uncontested = np.zeros(n, dtype=np.int64)  # pots won without showdown
    blocks, block = [], np.zeros(n, dtype=np.int64)
    trust_snap, top_correct_snap, top_prob_snap = [], [], []
    hands_with_showdown = 0
    min_stack = stack0
    started = time.time()

    for h in range(1, hands + 1):
        ctx.new_hand()
        # Rebuys are applied inside play_hand, before the hand's own snapshot.
        table.play_hand()
        hand = table.last_hand
        delta = np.array([hand.stack_after_hand[s] - hand.stack_before_hand[s]
                          for s in range(n)], dtype=np.int64)
        if int(delta.sum()) != 0:
            raise RuntimeError(f"chips not conserved in hand {h}: {delta.tolist()}")
        min_stack = min(min_stack, min(hand.stack_after_hand.values()))
        reached = np.zeros(n, dtype=bool)
        if hand.showdown_data is not None:
            hands_with_showdown += 1
            for e in hand.showdown_data:
                reached[e["seat"]] = True
                n_sd[e["seat"]] += 1
                if e["won"]:
                    n_sd_won[e["seat"]] += 1
        else:
            n_uncontested[hand._walkover_winner] += 1
        net += delta
        net_sd += np.where(reached, delta, 0)
        net_nsd += np.where(reached, 0, delta)
        sumsq += delta * delta
        block += delta
        if h % BLOCK == 0:
            blocks.append(block.tolist())
            block = np.zeros(n, dtype=np.int64)
            t_row, c_row, p_row = [], [], []
            for j in range(n):
                ts, correct, probs = [], 0, []
                for i in range(n):
                    if i == j:
                        continue
                    ts.append(agents[i].trust_score(j))
                    post = agents[i].posteriors.get(j)
                    if post is not None:
                        correct += int(int(np.argmax(post)) == type_idx[j])
                        probs.append(float(post[type_idx[j]]))
                t_row.append(float(np.mean(ts)))
                c_row.append(correct / (n - 1))
                p_row.append(float(np.mean(probs)) if probs else 0.0)
            trust_snap.append(t_row)
            top_correct_snap.append(c_row)
            top_prob_snap.append(p_row)

    stats = [dict(a.stats) for a in agents]
    rebuys = [int(a.rebuys) for a in agents]
    final = [int(a.stack) for a in agents]
    expect = [stack0 * (1 + r) + int(x) for r, x in zip(rebuys, net)]
    if final != expect:
        raise RuntimeError(f"ledger does not reconcile: {final} vs {expect}")
    if not legacy and (sum(rebuys) != 0 or min_stack <= 0):
        raise RuntimeError("deep-stack run saw a rebuy or an empty stack")

    return {
        "condition": condition, "config": cfg, "seed": seed, "hands": hands,
        "git_sha": _git_sha(), "seconds": round(time.time() - started, 1),
        "starting_stack": stack0, "seat_archetypes": order, "t_ref": T_REF,
        "net": net.tolist(), "net_showdown": net_sd.tolist(),
        "net_non_showdown": net_nsd.tolist(), "sumsq": sumsq.tolist(),
        "n_showdown": n_sd.tolist(), "n_showdown_won": n_sd_won.tolist(),
        "n_uncontested_won": n_uncontested.tolist(),
        "hands_with_showdown": hands_with_showdown,
        "rebuys": rebuys, "final_stack": final, "min_stack": int(min_stack),
        "stats": stats, "block": BLOCK, "block_net": blocks,
        "trust": trust_snap, "top_correct": top_correct_snap,
        "true_type_prob": top_prob_snap,
        "axes": {"archetypes": ARCHETYPES, "rounds": list(ROUNDS),
                 "buckets": list(BUCKETS), "responses": list(RESPONSES)},
        "resp": ctx.resp.tolist(), "open": ctx.open.tolist(),
        "f_n": ctx.f_n.tolist(), "f_sum": ctx.f_sum.tolist(),
        "f_changed": int(ctx.f_changed), "noise_n": int(ctx.noise_n),
        "decisions": int(ctx.decisions),
    }


def _job(args):
    condition, seed, hands, out = args
    res = run_seed(condition, seed, hands)
    path = Path(out) / f"{condition}_seed{seed}.json"
    json.dump(res, open(path, "w"))
    return (seed, res["seconds"], round(hands / max(res["seconds"], 1e-9), 2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", required=True)
    ap.add_argument("--seeds", required=True, help="comma-separated")
    ap.add_argument("--hands", type=int, required=True)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.condition not in load_conditions():
        raise SystemExit(f"unknown condition {a.condition!r}")
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    Path(a.out).mkdir(parents=True, exist_ok=True)
    jobs = [(a.condition, s, a.hands, a.out) for s in seeds]
    if a.procs > 1 and len(jobs) > 1:
        with mp.Pool(min(a.procs, len(jobs))) as pool:
            done = pool.map(_job, jobs, chunksize=1)
    else:
        done = [_job(j) for j in jobs]
    for seed, secs, rate in done:
        print(f"{a.condition} seed {seed}: {a.hands} hands in {secs}s ({rate} hands/s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
