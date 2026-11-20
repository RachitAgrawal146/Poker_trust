"""Summarise the R1 ledgers.

usage: python3 revision_experiments/analyze_r1.py DIR --out DIR/summary.json

DIR holds one <condition>.json per condition (written by collect_r1.py).
Everything is computed per seed first and then summarised across seeds;
the seed is the unit of replication. Win rates are in big blinds (2 chips)
per 100 hands.

Per condition and archetype: win rate, showdown and non-showdown win rate,
per-hand standard deviation, style statistics, the trust held about it.
Per condition: the trust-outcome association (Pearson and Spearman r over the
eight archetypes, per seed), the realised responses to each bettor, and how
often the response rule applied.

Contrasts against ``no_read`` are paired by seed (the same seed gives the
same seat order and the same starting random state in both conditions).
The primary contrast is the *cost of being read*: the win rate of archetype
X when the others apply the response rule to X's bets only, minus X's win
rate with all reading off. Holm adjustment covers the eight archetypes.

The bluff-rate sweep gives one seat (the Oracle's) a bluff rate of 0, 0.15,
0.33, 0.50 or 0.70 on every street and reports its win rate when nobody
reads and when the others apply the response rule to its bets.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy import stats as sps

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ARCH = ["oracle", "sentinel", "firestorm", "wall", "phantom", "predator", "mirror", "judge"]
BB = 2.0            # chips per big blind
BURN_IN = 500       # hands dropped before averaging trust over time
HONESTY = {         # archetype_params.HONESTY_SCORES via r1_agents.TRUST_TYPE
    "oracle": 1 - 0.330, "sentinel": 1 - 0.083, "firestorm": 1 - 0.625, "wall": 1 - 0.038,
    "phantom": 1 - 0.525, "predator": 1 - 0.213, "mirror": 1 - 0.088, "judge": 1 - 0.083,
}


def mean_ci(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = float(x.mean()) if n else float("nan")
    if n < 2:
        return {"n": n, "mean": m, "se": None, "sd": None, "ci95": None, "values": x.tolist()}
    sd = float(x.std(ddof=1))
    se = sd / math.sqrt(n)
    h = float(sps.t.ppf(0.975, n - 1)) * se
    return {"n": n, "mean": m, "se": se, "sd": sd, "ci95": [m - h, m + h], "values": x.tolist()}


def paired(x, y):
    """Summary of x - y across seeds, with a two-sided paired t-test."""
    d = np.asarray(x, dtype=float) - np.asarray(y, dtype=float)
    out = mean_ci(d)
    if out["se"] and out["se"] > 0:
        t = out["mean"] / out["se"]
        out["t"] = t
        out["p"] = float(2 * sps.t.sf(abs(t), len(d) - 1))
    else:
        out["t"], out["p"] = None, None
    return out


def holm(pvals):
    order = np.argsort(pvals)
    adj = np.empty(len(pvals))
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def per_seed(run):
    """Per-archetype quantities of one seed, indexed in ARCH order."""
    seat_of = {a: s for s, a in enumerate(run["seat_archetypes"])}
    hands = run["hands"]
    idx = [seat_of[a] for a in ARCH]
    net = np.array(run["net"], float)[idx]
    out = {
        "wr": net / hands * 100 / BB,
        "wr_sd": np.array(run["net_showdown"], float)[idx] / hands * 100 / BB,
        "wr_nsd": np.array(run["net_non_showdown"], float)[idx] / hands * 100 / BB,
        "hand_sd_bb": np.sqrt(np.array(run["sumsq"], float)[idx] / hands - (net / hands) ** 2) / BB,
        "showdowns_per100": np.array(run["n_showdown"], float)[idx] / hands * 100,
        "showdown_win_share": np.array(run["n_showdown_won"], float)[idx]
        / np.maximum(np.array(run["n_showdown"], float)[idx], 1),
        "uncontested_per100": np.array(run["n_uncontested_won"], float)[idx] / hands * 100,
        "rebuys": np.array(run["rebuys"], float)[idx],
        "final_stack": np.array(run["final_stack"], float)[idx],
    }
    st = [run["stats"][s] for s in idx]
    out["vpip"] = np.array([s["vpip_count"] / max(s["hands_dealt"], 1) for s in st])
    out["pfr"] = np.array([s["pfr_count"] / max(s["hands_dealt"], 1) for s in st])
    out["af"] = np.array([(s["bets"] + s["raises"]) / max(s["calls"], 1) for s in st])
    trust = np.array(run["trust"], float)[:, idx]            # [snapshot, archetype]
    first = min(BURN_IN // run["block"], max(len(trust) - 1, 0))
    out["trust"] = trust[first:].mean(axis=0)
    out["trust_final"] = trust[-1]
    out["top_correct_final"] = np.array(run["top_correct"], float)[-1, idx]
    out["true_type_prob"] = np.array(run["true_type_prob"], float)[first:, idx].mean(axis=0)
    blocks = np.array(run["block_net"], float)[:, idx]
    cum = np.cumsum(blocks, axis=0)
    n_h = (np.arange(len(blocks)) + 1)[:, None] * run["block"]
    out["running_wr"] = cum / n_h * 100 / BB                 # [block, archetype]
    return out


def assoc(x, y):
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan"), float("nan")
    return float(np.corrcoef(x, y)[0, 1]), float(sps.spearmanr(x, y)[0])


def summarise_r(vals):
    v = np.asarray([x for x in vals if not math.isnan(x)], float)
    s = mean_ci(v)
    s["sd_pop"] = float(v.std()) if len(v) else None
    s["n_positive"] = int((v > 0).sum())
    return s


def condition_summary(cond, runs):
    seeds = [r["seed"] for r in runs]
    ps = [per_seed(r) for r in runs]
    out = {"condition": cond, "config": runs[0]["config"], "seeds": seeds,
           "hands_per_seed": runs[0]["hands"], "starting_stack": runs[0]["starting_stack"],
           "git_sha": sorted({r["git_sha"] for r in runs}), "archetypes": {}}
    keys = ["wr", "wr_sd", "wr_nsd", "hand_sd_bb", "showdowns_per100", "showdown_win_share",
            "uncontested_per100", "rebuys", "final_stack", "vpip", "pfr", "af",
            "trust", "trust_final", "top_correct_final", "true_type_prob"]
    for ai, a in enumerate(ARCH):
        out["archetypes"][a] = {k: mean_ci([p[k][ai] for p in ps]) for k in keys}
        out["archetypes"][a]["honesty"] = HONESTY[a]
    # association over the eight archetypes, per seed
    rp, rs, rp_final, rp_stack, rp_noman = [], [], [], [], []
    keep = [i for i, a in enumerate(ARCH) if a != "firestorm"]
    for p in ps:
        a, b = assoc(p["trust"], p["wr"]); rp.append(a); rs.append(b)
        rp_final.append(assoc(p["trust_final"], p["wr"])[0])
        rp_stack.append(assoc(p["trust_final"], p["final_stack"])[0])
        rp_noman.append(assoc(p["trust"][keep], p["wr"][keep])[0])
    out["association"] = {
        "pearson_trust_winrate": summarise_r(rp),
        "spearman_trust_winrate": summarise_r(rs),
        "pearson_final_trust_winrate": summarise_r(rp_final),
        "pearson_final_trust_final_stack": summarise_r(rp_stack),
        "pearson_trust_winrate_without_firestorm": summarise_r(rp_noman),
    }
    # pooled realised behaviour
    resp = np.sum([np.array(r["resp"], float) for r in runs], axis=0)   # [resp, bettor, street, bucket, action]
    opn = np.sum([np.array(r["open"], float) for r in runs], axis=0)    # [arch, street, bucket, check/bet]
    f_n = np.sum([np.array(r["f_n"], float) for r in runs], axis=0)
    f_sum = np.sum([np.array(r["f_sum"], float) for r in runs], axis=0)
    facing = resp.sum()
    mw = resp[:, :, :, 1:, :]                                           # Medium and Weak responders
    by_bettor = mw.sum(axis=(0, 2, 3))                                  # [bettor, action]
    strong_by_bettor = resp[:, :, :, 0, :].sum(axis=(0, 2))
    out["responses"] = {
        "facing_bet_decisions": float(facing),
        "rule_eligible": float(f_n.sum()),
        "rule_changed": float(sum(r["f_changed"] for r in runs)),
        "share_changed_of_facing": float(sum(r["f_changed"] for r in runs) / facing) if facing else None,
        "mean_factor": float(f_sum.sum() / f_n.sum()) if f_n.sum() else None,
        "mean_factor_by_bettor": {a: (float(f_sum[i].sum() / f_n[i].sum()) if f_n[i].sum() else None)
                                  for i, a in enumerate(ARCH)},
        "mean_factor_by_street_bucket": {
            rnd: {b: (float(f_sum[:, ri, bi].sum() / f_n[:, ri, bi].sum()) if f_n[:, ri, bi].sum() else None)
                  for bi, b in enumerate(("Strong", "Medium", "Weak"))}
            for ri, rnd in enumerate(("preflop", "flop", "turn", "river"))},
        "fold_rate_medium_weak_by_bettor": {a: (float(by_bettor[i, 0] / by_bettor[i].sum()) if by_bettor[i].sum() else None)
                                            for i, a in enumerate(ARCH)},
        "fold_rate_strong_by_bettor": {a: (float(strong_by_bettor[i, 0] / strong_by_bettor[i].sum()) if strong_by_bettor[i].sum() else None)
                                       for i, a in enumerate(ARCH)},
        "fold_rate_medium_weak_overall": float(mw[..., 0].sum() / mw.sum()) if mw.sum() else None,
        "call_rate_medium_weak_overall": float(mw[..., 1].sum() / mw.sum()) if mw.sum() else None,
        "by_responder_bettor_fold_rate_medium_weak": {
            ARCH[i]: {ARCH[j]: (float(mw[i, j, :, :, 0].sum() / mw[i, j].sum()) if mw[i, j].sum() else None)
                      for j in range(len(ARCH))} for i in range(len(ARCH))},
    }
    bets = opn[..., 1]                                                  # [arch, street, bucket]
    opp = opn.sum(axis=-1)
    out["betting"] = {a: {
        "bet_rate_by_bucket": {b: (float(bets[i, :, bi].sum() / opp[i, :, bi].sum()) if opp[i, :, bi].sum() else None)
                               for bi, b in enumerate(("Strong", "Medium", "Weak"))},
        "share_of_bets_from_weak": float(bets[i, :, 2].sum() / bets[i].sum()) if bets[i].sum() else None,
        "share_of_bets_from_weak_postflop": float(bets[i, 1:, 2].sum() / bets[i, 1:].sum()) if bets[i, 1:].sum() else None,
        "bucket_share_when_first_to_act": {
            rnd: [float(x) for x in (opp[i, ri] / opp[i, ri].sum() if opp[i, ri].sum() else np.zeros(3))]
            for ri, rnd in enumerate(("preflop", "flop", "turn", "river"))},
    } for i, a in enumerate(ARCH)}
    out["noise_share"] = float(sum(r["noise_n"] for r in runs) / max(sum(r["decisions"] for r in runs), 1))
    out["hands_with_showdown_share"] = float(sum(r["hands_with_showdown"] for r in runs)
                                             / sum(r["hands"] for r in runs))
    # running win-rate estimate: mean and 95% interval across seeds at each block
    run_wr = np.stack([p["running_wr"] for p in ps])                    # [seed, block, arch]
    n = run_wr.shape[0]
    m = run_wr.mean(axis=0)
    h = (sps.t.ppf(0.975, n - 1) * run_wr.std(axis=0, ddof=1) / math.sqrt(n)) if n > 1 else np.zeros_like(m)
    step = max(1, run_wr.shape[1] // 50)
    sel = list(range(step - 1, run_wr.shape[1], step))
    out["running"] = {"hands": [int((i + 1) * runs[0]["block"]) for i in sel],
                      "mean": {a: m[sel, ai].tolist() for ai, a in enumerate(ARCH)},
                      "half_width": {a: np.asarray(h)[sel, ai].tolist() for ai, a in enumerate(ARCH)}}
    return out, {s: p for s, p in zip(seeds, ps)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    summaries, per = {}, {}
    for path in sorted(Path(a.dir).glob("*.json")):
        if path.name in ("summary.json", "manifest.json"):
            continue
        d = json.load(open(path))
        if "runs" not in d or not d["runs"]:
            continue
        summaries[d["condition"]], per[d["condition"]] = condition_summary(d["condition"], d["runs"])

    contrasts = {}
    base_name = {False: "no_read", True: "no_read_legacy"}
    for cond, s in summaries.items():
        base = base_name[bool(s["config"].get("legacy", False))]
        if cond == base or base not in per:
            continue
        common = [sd for sd in s["seeds"] if sd in per[base]]
        if len(common) < 2:
            continue
        c = {"baseline": base, "n_seeds": len(common), "delta_wr": {}}
        for ai, arch in enumerate(ARCH):
            c["delta_wr"][arch] = paired([per[cond][sd]["wr"][ai] for sd in common],
                                         [per[base][sd]["wr"][ai] for sd in common])
        d_trust = {arch: paired([per[cond][sd]["trust"][ai] for sd in common],
                                [per[base][sd]["trust"][ai] for sd in common])
                   for ai, arch in enumerate(ARCH)}
        c["delta_trust"] = d_trust
        contrasts[cond] = c

    # primary: cost of being read
    cost = {}
    for ai, arch in enumerate(ARCH):
        cond = f"read_target_{arch}_b10"
        if cond in contrasts:
            d = dict(contrasts[cond]["delta_wr"][arch])
            others = [contrasts[cond]["delta_wr"][o]["mean"] for o in ARCH if o != arch]
            d["mean_change_of_the_other_seven"] = float(np.mean(others))
            d["honesty"] = HONESTY[arch]
            cost[arch] = d
    primary = {"cost_of_being_read": cost}
    if len(cost) == len(ARCH):
        p = [cost[x]["p"] for x in ARCH]
        for x, adj in zip(ARCH, holm(p)):
            cost[x]["p_holm"] = adj
        h = np.array([HONESTY[x] for x in ARCH])
        m = np.array([cost[x]["mean"] for x in ARCH])
        slope, intercept = np.polyfit(h, m, 1)
        primary["cost_vs_honesty"] = {
            "pearson": float(np.corrcoef(h, m)[0, 1]),
            "spearman": float(sps.spearmanr(h, m)[0]),
            "slope_bb100_per_unit_honesty": float(slope), "intercept": float(intercept)}
        # per-seed slope, for an interval that respects the unit of replication
        seeds = contrasts["read_target_oracle_b10"]["delta_wr"]["oracle"]["n"]
        per_seed_slopes = []
        for k in range(seeds):
            mk = np.array([cost[x]["values"][k] for x in ARCH])
            per_seed_slopes.append(float(np.polyfit(h, mk, 1)[0]))
        primary["cost_vs_honesty"]["slope_per_seed"] = mean_ci(per_seed_slopes)

    # bluff-rate sweep: the Oracle seat with its bluff rate set to x on every street
    sweep = {}
    oi = ARCH.index("oracle")
    for br in (0.00, 0.15, 0.33, 0.50, 0.70):
        tag = f"sweep_br{int(round(br * 100)):02d}"
        off = "no_read" if br == 0.33 else tag + "_no_read"
        on = "read_target_oracle_b10" if br == 0.33 else tag + "_read"
        if off not in per or on not in per:
            continue
        common = [sd for sd in summaries[off]["seeds"] if sd in per[on]]
        wr_off = [per[off][sd]["wr"][oi] for sd in common]
        wr_on = [per[on][sd]["wr"][oi] for sd in common]
        sweep[f"{br:.2f}"] = {
            "bluff_rate": br, "condition_not_read": off, "condition_read": on,
            "win_rate_not_read": mean_ci(wr_off), "win_rate_read": mean_ci(wr_on),
            "cost_of_being_read": paired(wr_on, wr_off),
            "trust_not_read": mean_ci([per[off][sd]["trust"][oi] for sd in common]),
            "trust_read": mean_ci([per[on][sd]["trust"][oi] for sd in common]),
            "nonshowdown_not_read": mean_ci([per[off][sd]["wr_nsd"][oi] for sd in common]),
            "nonshowdown_read": mean_ci([per[on][sd]["wr_nsd"][oi] for sd in common]),
            "showdown_not_read": mean_ci([per[off][sd]["wr_sd"][oi] for sd in common]),
            "showdown_read": mean_ci([per[on][sd]["wr_sd"][oi] for sd in common]),
            "fold_rate_medium_weak_vs_focal_not_read": summaries[off]["responses"]["fold_rate_medium_weak_by_bettor"]["oracle"],
            "fold_rate_medium_weak_vs_focal_read": summaries[on]["responses"]["fold_rate_medium_weak_by_bettor"]["oracle"],
        }
    if len(sweep) >= 3:
        xs = np.array([v["bluff_rate"] for v in sweep.values()])
        n_seeds = min(v["win_rate_not_read"]["n"] for v in sweep.values())
        for key in ("win_rate_not_read", "win_rate_read"):
            slopes = [float(np.polyfit(xs, [v[key]["values"][k] for v in sweep.values()], 1)[0])
                      for k in range(n_seeds)]
            primary[f"sweep_slope_{key}_per_unit_bluff_rate"] = mean_ci(slopes)
    primary["bluff_rate_sweep"] = sweep

    json.dump({"unit": "big blinds (2 chips) per 100 hands", "burn_in_hands_for_trust": BURN_IN,
               "conditions": summaries, "contrasts_vs_no_read": contrasts, "primary": primary},
              open(a.out, "w"), indent=1)
    print(f"{len(summaries)} conditions summarised -> {a.out}")
    for cond, s in summaries.items():
        r = s["association"]["pearson_trust_winrate"]
        print(f"  {cond:28s} n={len(s['seeds']):2d}  r(trust, win rate) = {r['mean']:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
