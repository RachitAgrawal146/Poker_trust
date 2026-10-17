"""Win-rate ledger: net chips per hand and seat, reconciled to the stack ledger.

Runbook step B1. Replaces final-stack scoring, which ignores rebuys.

Definitions
-----------
* Net chips of a seat in a hand = chips won from the pot minus chips put in.
  Blinds are not rows in ``actions``: the small blind (``hands.sb_seat``) is
  charged 1 chip; the big blind is charged ``final_pot - sum(action amounts)
  - 1``, which is 2 except when a one-chip stack posts 1.
* A seat "reached showdown" in a hand if it has a row in ``showdowns`` for
  that hand (player-level definition, not "the hand had a showdown").
* Win rate = net chips per 100 hands. ``BB_CHIPS`` gives the display unit
  (big blind = 2 chips); the unit used in the paper is fixed in C0.

Reconciliation (hard check)
---------------------------
For every run: each hand's row sums to zero, and each seat's column sums to
``final_stack - 200 * (1 + rebuys)``.

Intervals
---------
With 10 or more seeds per archetype: a t-interval and a percentile bootstrap
over seeds. With fewer: a moving-block bootstrap over hands within each seed
(block length ``BLOCK``), seeds pooled.

usage:
  python3 analysis/winrate.py DB [DB ...] --out FILE.json [--label NAME]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from typing import Dict, List, Tuple

import numpy as np

STARTING_STACK = 200
BB_CHIPS = 2
BLOCK = 100
N_BOOT = 2000


def per_hand_net(conn: sqlite3.Connection, run_id: int, n_seats: int = 8
                 ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (hand_ids, net[H, seats], reached_showdown[H, seats])."""
    cur = conn.cursor()
    hands = cur.execute(
        "SELECT hand_id, final_pot, had_showdown, walkover_winner, sb_seat, bb_seat "
        "FROM hands WHERE run_id=? ORDER BY hand_id", (run_id,)).fetchall()
    idx = {h[0]: i for i, h in enumerate(hands)}
    net = np.zeros((len(hands), n_seats), dtype=np.int64)
    put_in = np.zeros(len(hands), dtype=np.int64)
    sd = np.zeros((len(hands), n_seats), dtype=bool)
    for hid, seat, amt in cur.execute(
            "SELECT hand_id, seat, SUM(amount) FROM actions WHERE run_id=? "
            "AND action_type IN ('call','bet','raise') GROUP BY hand_id, seat", (run_id,)):
        net[idx[hid], seat] -= amt
        put_in[idx[hid]] += amt
    for hid, pot, had_sd, winner, sb, bb in hands:
        i = idx[hid]
        net[i, sb] -= 1
        net[i, bb] -= pot - put_in[i] - 1
        if not had_sd and winner is not None:
            net[i, winner] += pot
    for hid, seat, won in cur.execute(
            "SELECT hand_id, seat, pot_won FROM showdowns WHERE run_id=?", (run_id,)):
        net[idx[hid], seat] += won
        sd[idx[hid], seat] = True
    return np.array([h[0] for h in hands]), net, sd


class ReconciliationError(AssertionError):
    pass


def reconcile(conn: sqlite3.Connection, run_id: int, net: np.ndarray) -> Dict:
    """Hard check against the stack ledger. Raises ReconciliationError."""
    row_sums = net.sum(axis=1)
    bad_rows = int(np.count_nonzero(row_sums))
    stats = conn.execute(
        "SELECT seat, final_stack, rebuys FROM agent_stats WHERE run_id=? ORDER BY seat",
        (run_id,)).fetchall()
    col = net.sum(axis=0)
    seat_err = {int(seat): int(col[seat] - (fs - STARTING_STACK * (1 + rb)))
                for seat, fs, rb in stats}
    max_err = max(abs(v) for v in seat_err.values())
    if bad_rows or max_err:
        raise ReconciliationError(
            f"run {run_id}: {bad_rows} hands do not sum to zero; seat errors {seat_err}")
    return {"hands_not_zero_sum": bad_rows, "max_seat_error": max_err}


def _block_bootstrap_mean(series: List[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    """Bootstrap distribution of the mean per-hand value, blocks within seeds."""
    # Circular blocks (Politis and Romano 1992): every hand is equally likely
    # to be drawn, so the bootstrap is centred on the sample mean.
    out = np.empty(N_BOOT)
    for b in range(N_BOOT):
        tot, n = 0.0, 0
        for x in series:
            H = len(x)
            L = min(BLOCK, max(1, H // 5))
            k = int(np.ceil(H / L))
            starts = rng.integers(0, H, size=k)
            take = (starts[:, None] + np.arange(L)[None, :]) % H
            sample = x[take.ravel()[:H]]
            tot += sample.sum(); n += len(sample)
        out[b] = tot / n
    return out


def summarise(runs: List[Dict], seed: int = 20261017) -> Dict:
    """Per-archetype outcomes pooled over runs (one run = one seed)."""
    rng = np.random.default_rng(seed)
    by_arch: Dict[str, Dict[str, list]] = {}
    for r in runs:
        for seat, arch in enumerate(r["archetypes"]):
            d = by_arch.setdefault(arch, {"x": [], "sd": [], "seed_rate": [], "net": []})
            x = r["net"][:, seat].astype(float)
            d["x"].append(x)
            d["sd"].append(r["reached_sd"][:, seat])
            d["seed_rate"].append(100.0 * x.mean())
            d["net"].append(float(x.sum()))
    out = {}
    for arch, d in sorted(by_arch.items()):
        allx = np.concatenate(d["x"]); allsd = np.concatenate(d["sd"])
        n_seeds = len(d["x"])
        rate = 100.0 * allx.mean()
        rec = {
            "n_seeds": n_seeds, "hands": int(len(allx)),
            "net_chips_total": float(allx.sum()),
            "net_chips_per_seed": float(np.mean(d["net"])),
            "win_rate_chips_per_100": rate,
            "win_rate_bb_per_100": rate / BB_CHIPS,
            "showdown_net_chips_per_seed": float(allx[allsd].sum() / n_seeds),
            "non_showdown_net_chips_per_seed": float(allx[~allsd].sum() / n_seeds),
            "showdowns_per_seed": float(allsd.sum() / n_seeds),
            "per_hand_sd_chips": float(allx.std()),
            "seed_win_rates_chips_per_100": d["seed_rate"],
        }
        if n_seeds >= 10:
            sr = np.array(d["seed_rate"])
            se = sr.std(ddof=1) / np.sqrt(n_seeds)
            from scipy import stats as _st  # scipy only needed here
            t = _st.t.ppf(0.975, n_seeds - 1)
            boot = rng.choice(sr, size=(N_BOOT, n_seeds), replace=True).mean(axis=1)
            rec.update({"interval_method": "seeds",
                        "se_across_seeds_chips_per_100": float(se),
                        "ci95_t_chips_per_100": [float(sr.mean() - t * se), float(sr.mean() + t * se)],
                        "ci95_boot_chips_per_100": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]})
        else:
            boot = 100.0 * _block_bootstrap_mean(d["x"], rng)
            rec.update({"interval_method": f"circular block bootstrap within seeds, block=min({BLOCK}, hands//5)",
                        "ci95_boot_chips_per_100": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]})
        out[arch] = rec
    return out


def load_runs(paths: List[str]) -> List[Dict]:
    runs = []
    for p in paths:
        conn = sqlite3.connect(p)
        for run_id, seed, label in conn.execute("SELECT run_id, seed, label FROM runs ORDER BY run_id"):
            n_seats = conn.execute("SELECT COUNT(*) FROM agent_stats WHERE run_id=?", (run_id,)).fetchone()[0]
            hand_ids, net, sd = per_hand_net(conn, run_id, n_seats)
            check = reconcile(conn, run_id, net)
            arch = [a for (a,) in conn.execute(
                "SELECT archetype FROM agent_stats WHERE run_id=? ORDER BY seat", (run_id,))]
            runs.append({"file": os.path.basename(p), "run_id": run_id, "seed": seed, "label": label,
                         "archetypes": arch, "net": net, "reached_sd": sd, "reconcile": check})
    return runs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dbs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default=None)
    a = ap.parse_args(argv)
    runs = load_runs(a.dbs)
    result = {
        "label": a.label, "n_runs": len(runs),
        "runs": [{k: r[k] for k in ("file", "run_id", "seed", "label", "reconcile")} for r in runs],
        "archetypes": summarise(runs),
        "units": {"chips_per_bb": BB_CHIPS, "starting_stack": STARTING_STACK},
    }
    json.dump(result, open(a.out, "w"), indent=1)
    print(f"{len(runs)} runs reconciled exactly; per-archetype outcomes -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
