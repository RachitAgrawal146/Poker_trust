"""Numbers, tables and figures for the revised paper, generated from the R1
ledgers. Nothing in the paper is typed from these by hand.

  python3 gen_results.py REPO PAPER

Reads  <repo>/research_data/r1/full/summary.json (+ no_read.json for the
horizon analysis) and <paper>/generated/static.json.
Writes <paper>/generated/numbers.tex, tab_*.tex, macros_list.txt and
<paper>/figures/fig_*.pdf.
"""
import json, math, os, sys
import numpy as np
from scipy import stats as sps
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo, paper = sys.argv[1], sys.argv[2]
GEN, FIG = os.path.join(paper, "generated"), os.path.join(paper, "figures")
os.makedirs(GEN, exist_ok=True); os.makedirs(FIG, exist_ok=True)
R1 = os.path.join(repo, "research_data/r1/full")
S = json.load(open(os.path.join(R1, "summary.json")))
C, CON, PRI = S["conditions"], S["contrasts_vs_no_read"], S["primary"]
static = json.load(open(os.path.join(GEN, "static.json")))
ARCH = ["oracle", "sentinel", "firestorm", "wall", "phantom", "predator", "mirror", "judge"]
TAG = {"oracle": "Bal", "sentinel": "Tag", "firestorm": "Man", "wall": "Sta", "phantom": "Blf",
       "predator": "Exp", "mirror": "Mim", "judge": "Grd"}
DISP = static["display"]
CODE = {"oracle": "Oracle", "sentinel": "Sentinel", "firestorm": "Firestorm", "wall": "Wall",
        "phantom": "Phantom", "predator": "Predator", "mirror": "Mirror", "judge": "Judge"}
H = static["non_bluff_rate"]
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1f1f1e", "#6b6a64", "#d9d8d2"

macros = {}
def sg(x, d=1):
    s = f"{x:+.{d}f}"
    if float(s) == 0: return f"{0:.{d}f}"
    return s.replace("-", "$-$").replace("+", "$+$")
def us(x, d=1): return f"{x:.{d}f}"
def M(name, val):
    assert name.isalpha(), name
    assert name not in macros, name
    macros[name] = str(val)
def tci(vals):
    v = np.asarray(vals, float); n = len(v); m = v.mean(); se = v.std(ddof=1) / math.sqrt(n)
    h = sps.t.ppf(0.975, n - 1) * se
    return m, se, m - h, m + h
def pdiff(c1, c2, a):
    return tci(np.array(C[c1]["archetypes"][a]["wr"]["values"]) - np.array(C[c2]["archetypes"][a]["wr"]["values"]))
def pfmt(p):
    return "$<$0.001" if p < 0.001 else (f"{p:.3f}" if p < 0.1 else f"{p:.2f}")

# ---------------------------------------------------------------- per-condition macros
CT = {"no_read": "NR", "published": "PB", "no_read_legacy": "NRL", "published_legacy": "PBL",
      "read_all_b05": "RAh", "read_all_b10": "RA", "read_all_b20": "RAd", "read_true_b10": "RT",
      "shuffled_b10": "SH", "loose_matched_b10": "LM", "noise_005": "NzF", "noise_010": "NzT"}
for c, t in CT.items():
    r = C[c]["association"]["pearson_trust_winrate"]
    M(t + "R", sg(r["mean"], 2)); M(t + "RLo", sg(r["ci95"][0], 2)); M(t + "RHi", sg(r["ci95"][1], 2))
    M(t + "RPos", r["n_positive"]); M(t + "Rho", sg(C[c]["association"]["spearman_trust_winrate"]["mean"], 2))
    for a in ARCH:
        w = C[c]["archetypes"][a]["wr"]
        M(t + TAG[a] + "Wr", sg(w["mean"])); M(t + TAG[a] + "Se", us(w["se"]))
nr = C["no_read"]
for a in ARCH:
    x = nr["archetypes"][a]; b = nr["betting"][a]
    M("NR" + TAG[a] + "Sd", sg(x["wr_sd"]["mean"])); M("NR" + TAG[a] + "Nsd", sg(x["wr_nsd"]["mean"]))
    M("NR" + TAG[a] + "Unc", us(x["uncontested_per100"]["mean"])); M("NR" + TAG[a] + "Sdn", us(x["showdowns_per100"]["mean"]))
    M("NR" + TAG[a] + "Trust", us(x["trust"]["mean"], 2)); M("NR" + TAG[a] + "Vpip", us(100 * x["vpip"]["mean"], 0))
    M("NR" + TAG[a] + "WeakShare", us(100 * b["share_of_bets_from_weak"], 0))
    M("NR" + TAG[a] + "WeakSharePost", us(100 * b["share_of_bets_from_weak_postflop"], 0))
    M("NR" + TAG[a] + "HandSd", us(x["hand_sd_bb"]["mean"], 1))
nm = nr["association"]["pearson_trust_winrate_without_firestorm"]
M("NRNoManR", sg(nm["mean"], 2)); M("NRNoManRLo", sg(nm["ci95"][0], 2)); M("NRNoManRHi", sg(nm["ci95"][1], 2))
M("NRFoldAll", us(100 * nr["responses"]["fold_rate_medium_weak_overall"], 0))
M("NRShowdownShare", us(100 * nr["hands_with_showdown_share"], 0))
M("NRGap", us(nr["archetypes"]["firestorm"]["wr"]["mean"] - nr["archetypes"]["wall"]["wr"]["mean"], 0))
sds = [nr["archetypes"][a]["hand_sd_bb"]["mean"] for a in ARCH]
M("NRHandSdMin", us(min(sds))); M("NRHandSdMax", us(max(sds)))
ses = [nr["archetypes"][a]["wr"]["se"] for a in ARCH]
M("NRSeMin", us(min(ses))); M("NRSeMax", us(max(ses)))
fs = nr["association"]["pearson_final_trust_final_stack"]
for c, t in (("no_read_legacy", "NRL"), ("published_legacy", "PBL")):
    M(t + "RStack", sg(C[c]["association"]["pearson_final_trust_final_stack"]["mean"], 2))
    M(t + "StaRebuys", us(C[c]["archetypes"]["wall"]["rebuys"]["mean"], 0))
ra = C["read_all_b10"]["responses"]
M("RAMeanFactor", us(ra["mean_factor"], 2)); M("RAShareChanged", us(100 * ra["share_changed_of_facing"], 0))
M("RAFoldAll", us(100 * ra["fold_rate_medium_weak_overall"], 0))
M("LMFoldAll", us(100 * C["loose_matched_b10"]["responses"]["fold_rate_medium_weak_overall"], 0))
M("LMMeanFactor", us(C["loose_matched_b10"]["responses"]["mean_factor"], 2))
M("SHFoldAll", us(100 * C["shuffled_b10"]["responses"]["fold_rate_medium_weak_overall"], 0))

# r differences (paired by seed)
def rdiff(c1, c2):
    k = "pearson_trust_winrate"
    return tci(np.array(C[c1]["association"][k]["values"]) - np.array(C[c2]["association"][k]["values"]))
for c, t in (("published", "PB"), ("read_all_b10", "RA"), ("loose_matched_b10", "LM"), ("shuffled_b10", "SH"),
             ("noise_010", "NzT"), ("read_true_b10", "RT")):
    m, se, lo, hi = rdiff(c, "no_read")
    M("Rdiff" + t, sg(m, 3)); M("Rdiff" + t + "Lo", sg(lo, 3)); M("Rdiff" + t + "Hi", sg(hi, 3))
m, se, lo, hi = rdiff("read_all_b10", "loose_matched_b10")
M("RdiffRAvsLM", sg(m, 3)); M("RdiffRAvsLMLo", sg(lo, 3)); M("RdiffRAvsLMHi", sg(hi, 3))

# win-rate contrasts (paired by seed)
for name, c1, c2 in (("RAvsNR", "read_all_b10", "no_read"), ("RAdvsNR", "read_all_b20", "no_read"),
                     ("RAvsLM", "read_all_b10", "loose_matched_b10"), ("RTvsRA", "read_true_b10", "read_all_b10"),
                     ("NzTvsNR", "noise_010", "no_read"), ("PBvsNR", "published", "no_read"),
                     ("NRLvsNR", "no_read_legacy", "no_read")):
    for a in ARCH:
        m, se, lo, hi = pdiff(c1, c2, a)
        M(name + TAG[a], sg(m)); M(name + TAG[a] + "Lo", sg(lo)); M(name + TAG[a] + "Hi", sg(hi))
mx = max(abs(pdiff("published", "no_read", a)[0]) for a in ARCH)
M("PBvsNRMaxAbs", us(mx)); M("NRLvsNRMaxAbs", us(max(abs(pdiff("no_read_legacy", "no_read", a)[0]) for a in ARCH)))

# ---------------------------------------------------------------- cost of being read
cost = PRI["cost_of_being_read"]
exact = PRI.get("cost_of_being_read_exact_posthoc", {})
have_exact = len(exact) == len(ARCH)
for a in ARCH:
    d = cost[a]; t = TAG[a]
    M("Cost" + t, sg(d["mean"])); M("Cost" + t + "Lo", sg(d["ci95"][0])); M("Cost" + t + "Hi", sg(d["ci95"][1]))
    M("Cost" + t + "Holm", pfmt(d["p_holm"]))
    M("Fold" + t + "Off", us(100 * nr["responses"]["fold_rate_medium_weak_by_bettor"][a], 0))
    cn = C[f"read_target_{a}_b10"]["responses"]
    M("Fold" + t + "On", us(100 * cn["fold_rate_medium_weak_by_bettor"][a], 0))
    M("Factor" + t, us(cn["mean_factor_by_bettor"][a], 2))
    if have_exact:
        e = exact[a]
        M("Exact" + t, sg(e["mean"])); M("Exact" + t + "Lo", sg(e["ci95"][0])); M("Exact" + t + "Hi", sg(e["ci95"][1]))
        M("Exact" + t + "Holm", pfmt(e["p_holm"]))
        M("FoldExact" + t, us(100 * C[f"read_target_{a}_true_b10"]["responses"]["fold_rate_medium_weak_by_bettor"][a], 0))
sl = PRI["cost_vs_honesty"]["slope_per_seed"]
M("CostSlope", sg(sl["mean"])); M("CostSlopeLo", sg(sl["ci95"][0])); M("CostSlopeHi", sg(sl["ci95"][1]))
lows = [cost[a]["ci95"][0] for a in ("sentinel", "wall", "mirror", "judge")]
M("CostLowBluffWorstLo", us(abs(min(lows))))
M("CostSevenWorstLo", us(abs(min(cost[a]["ci95"][0] for a in ARCH if a != "phantom"))))
M("CostBlfAbs", us(abs(cost["phantom"]["mean"])))
M("CostMaxHalfWidth", us(max((cost[a]["ci95"][1] - cost[a]["ci95"][0]) / 2 for a in ARCH)))
M("CostMinHalfWidth", us(min((cost[a]["ci95"][1] - cost[a]["ci95"][0]) / 2 for a in ARCH)))
if have_exact:
    tight = [abs(exact[a]["mean"]) for a in ("sentinel", "mirror", "judge")]
    M("ExactTightMin", us(min(tight))); M("ExactTightMax", us(max(tight)))
    M("ExactBlfAbs", us(abs(exact["phantom"]["mean"])))
    M("ExactTightShareOfGap", us(100 * max(tight) / (nr["archetypes"]["firestorm"]["wr"]["mean"] - nr["archetypes"]["wall"]["wr"]["mean"]), 0))
    for a in ARCH:
        d_ = exact[a]["exact_minus_inferred"]
        M("ExactVsInf" + TAG[a], sg(d_["mean"])); M("ExactVsInf" + TAG[a] + "Lo", sg(d_["ci95"][0])); M("ExactVsInf" + TAG[a] + "Hi", sg(d_["ci95"][1]))
    es = PRI["exact_cost_vs_honesty_slope_per_seed"]
    M("ExactSlope", sg(es["mean"])); M("ExactSlopeLo", sg(es["ci95"][0])); M("ExactSlopeHi", sg(es["ci95"][1]))
tm = C["read_target_firestorm_b10"]["archetypes"]["firestorm"]
M("TgtManSd", sg(tm["wr_sd"]["mean"])); M("TgtManNsd", sg(tm["wr_nsd"]["mean"]))
M("TgtManUnc", us(tm["uncontested_per100"]["mean"]))

# ---------------------------------------------------------------- bluff-rate sweep
SW = PRI["bluff_rate_sweep"]
WORD = {"0.00": "Zero", "0.15": "Fifteen", "0.33": "ThirtyThree", "0.50": "Fifty", "0.70": "Seventy"}
for k, v in SW.items():
    w = WORD[k]
    M("Sw" + w + "Off", sg(v["win_rate_not_read"]["mean"])); M("Sw" + w + "OffSe", us(v["win_rate_not_read"]["se"]))
    M("Sw" + w + "On", sg(v["win_rate_read"]["mean"])); M("Sw" + w + "OnSe", us(v["win_rate_read"]["se"]))
    c_ = v["cost_of_being_read"]
    M("Sw" + w + "Cost", sg(c_["mean"])); M("Sw" + w + "CostLo", sg(c_["ci95"][0])); M("Sw" + w + "CostHi", sg(c_["ci95"][1]))
    M("Sw" + w + "Trust", us(v["trust_read"]["mean"], 2))
    M("Sw" + w + "FoldOn", us(100 * v["fold_rate_medium_weak_vs_focal_read"], 0))
    M("Sw" + w + "NsdOff", sg(v["nonshowdown_not_read"]["mean"])); M("Sw" + w + "NsdOn", sg(v["nonshowdown_read"]["mean"]))
for key, nm_ in (("sweep_slope_win_rate_not_read_per_unit_bluff_rate", "SwSlopeOff"), ("sweep_slope_win_rate_read_per_unit_bluff_rate", "SwSlopeOn")):
    M(nm_, sg(PRI[key]["mean"])); M(nm_ + "Lo", sg(PRI[key]["ci95"][0])); M(nm_ + "Hi", sg(PRI[key]["ci95"][1]))
xs = np.array([v["bluff_rate"] for v in SW.values()])
dsl = [np.polyfit(xs, [v["win_rate_read"]["values"][k] for v in SW.values()], 1)[0]
       - np.polyfit(xs, [v["win_rate_not_read"]["values"][k] for v in SW.values()], 1)[0] for k in range(20)]
m, se, lo, hi = tci(dsl)
M("SwSlopeDiff", sg(m)); M("SwSlopeDiffLo", sg(lo)); M("SwSlopeDiffHi", sg(hi)); M("SwSlopeDiffP", pfmt(2 * sps.t.sf(abs(m / se), 19)))

# ---------------------------------------------------------------- horizon analysis (no_read ledgers)
runs = json.load(open(os.path.join(R1, "no_read.json")))["runs"]
def horizon(runs):
    out = []
    for r in runs:
        idx = [r["seat_archetypes"].index(a) for a in ARCH]
        cum = np.cumsum(np.array(r["block_net"], float)[:, idx], axis=0)
        tr = np.array(r["trust"], float)[:, idx]
        n = (np.arange(len(cum)) + 1) * r["block"]
        wr = cum / n[:, None] * 100 / 2
        out.append((n, wr, np.array([np.corrcoef(tr[k], wr[k])[0, 1] for k in range(len(n))])))
    return out
hz = horizon(runs)
nh = hz[0][0]
rmat = np.stack([h[2] for h in hz])            # [seed, block]
wmat = np.stack([h[1] for h in hz])            # [seed, block, arch]
r_mean, r_sd = rmat.mean(0), rmat.std(0, ddof=1)
hw = sps.t.ppf(0.975, len(hz) - 1) * wmat.std(0, ddof=1) / math.sqrt(len(hz))   # [block, arch]
def at(n): return int(np.where(nh == n)[0][0])
for n, w in ((100, "Hundred"), (200, "TwoHundred"), (500, "FiveHundred"), (10000, "TenK")):
    k = at(n)
    M("Hor" + w + "R", sg(r_mean[k], 2)); M("Hor" + w + "RSd", us(r_sd[k], 2))
    M("Hor" + w + "RPos", int((rmat[:, k] > 0).sum()))
    M("Hor" + w + "HwMin", us(hw[k].min(), 1)); M("Hor" + w + "HwMax", us(hw[k].max(), 1))

open(os.path.join(GEN, "numbers.tex"), "w").write(
    "% generated by scripts/gen_results.py from research_data/r1/full; do not edit\n"
    + "\n".join(f"\\newcommand{{\\num{k}}}{{{v}}}" for k, v in macros.items()) + "\n"
    + f"\\newif\\ifhaveexact\\haveexact{'true' if have_exact else 'false'}\n")
open(os.path.join(GEN, "macros_list.txt"), "w").write("\n".join(f"\\num{k} = {v}" for k, v in macros.items()) + "\n")

# ---------------------------------------------------------------- tables
ORDER = sorted(ARCH, key=lambda a: H[a])       # by non-bluff rate, ascending
mp = static["mean_params"]
rows = []
for a in ARCH:
    x = nr["archetypes"][a]
    rows.append(" & ".join([
        DISP[a], CODE[a], us(mp[a]["br"], 2), us(mp[a]["vbr"], 2), us(mp[a]["weak_call"], 2), us(H[a], 2),
        us(x["trust"]["mean"], 2), us(100 * x["vpip"]["mean"], 0), us(100 * x["pfr"]["mean"], 0), us(x["af"]["mean"], 2),
        us(x["showdowns_per100"]["mean"], 1), us(x["uncontested_per100"]["mean"], 1),
        f"{sg(x['wr']['mean'])} ({us(x['wr']['se'])})", sg(x["wr_sd"]["mean"]), sg(x["wr_nsd"]["mean"])]) + r" \\")
open(os.path.join(GEN, "tab_archetypes.tex"), "w").write(
    "\\begin{tabular}{llccccccccccccc}\n\\toprule\n"
    " & & \\multicolumn{4}{c}{Table (mean over streets)} & \\multicolumn{6}{c}{Realised, no reading} & \\multicolumn{3}{c}{Win rate, no reading (bb/100)} \\\\\n"
    "\\cmidrule(lr){3-6}\\cmidrule(lr){7-12}\\cmidrule(lr){13-15}\n"
    "Archetype & Code name & $b$ & $v$ & $c_W$ & $h$ & Trust & VPIP & PFR & AF & SD/100 & Unc./100 & Total (SE) & Showdown & Non-showdown \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

rows = []
for a in ORDER:
    d = cost[a]; cn = C[f"read_target_{a}_b10"]["responses"]
    cells = [DISP[a], us(H[a], 2), us(nr["archetypes"][a]["trust"]["mean"], 2), us(cn["mean_factor_by_bettor"][a], 2),
             us(100 * nr["responses"]["fold_rate_medium_weak_by_bettor"][a], 0) + r" $\to$ " + us(100 * cn["fold_rate_medium_weak_by_bettor"][a], 0),
             f"{sg(d['mean'])} [{sg(d['ci95'][0])}, {sg(d['ci95'][1])}]", pfmt(d["p_holm"])]
    if have_exact:
        e = exact[a]
        cells += [us(100 * C[f"read_target_{a}_true_b10"]["responses"]["fold_rate_medium_weak_by_bettor"][a], 0),
                  f"{sg(e['mean'])} [{sg(e['ci95'][0])}, {sg(e['ci95'][1])}]", pfmt(e["p_holm"])]
    rows.append(" & ".join(cells) + r" \\")
head = ("\\begin{tabular}{lcccccc" + ("ccc" if have_exact else "") + "}\n\\toprule\n"
        " & & & \\multicolumn{4}{c}{Read through the posterior (pre-specified)}"
        + (" & \\multicolumn{3}{c}{Read exactly (post hoc)}" if have_exact else "") + " \\\\\n"
        "\\cmidrule(lr){4-7}" + ("\\cmidrule(lr){8-10}" if have_exact else "") + "\n"
        "Archetype & $h$ & Trust & Factor $f$ & Fold \\% & Cost [95\\% interval] & Holm $p$"
        + (" & Fold \\% & Cost [95\\% interval] & Holm $p$" if have_exact else "") + " \\\\\n\\midrule\n")
open(os.path.join(GEN, "tab_cost.tex"), "w").write(head + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# supplement: win rate by condition
SUPC = [("no_read", "No reading"), ("published", "Original roster"), ("no_read_legacy", "No reading, earlier protocol"),
        ("published_legacy", "Original roster, earlier protocol"), ("read_all_b05", "Read all, $\\beta=0.5$"),
        ("read_all_b10", "Read all, $\\beta=1$"), ("read_all_b20", "Read all, $\\beta=2$"), ("read_true_b10", "Read all, exact types"),
        ("shuffled_b10", "Placebo (random seat)"), ("loose_matched_b10", "Matched loosening"),
        ("noise_005", "Noise 0.05"), ("noise_010", "Noise 0.10")]
rows = []
for c, lab in SUPC:
    r = C[c]["association"]["pearson_trust_winrate"]
    rows.append(" & ".join([lab] + [f"{sg(C[c]['archetypes'][a]['wr']['mean'])} ({us(C[c]['archetypes'][a]['wr']['se'])})" for a in ARCH]
                           + [f"{sg(r['mean'], 2)} [{sg(r['ci95'][0], 2)}, {sg(r['ci95'][1], 2)}]",
                              sg(C[c]["association"]["spearman_trust_winrate"]["mean"], 2)]) + r" \\")
open(os.path.join(GEN, "tab_by_condition.tex"), "w").write(
    "\\begin{tabular}{l" + "c" * 10 + "}\n\\toprule\nCondition & " + " & ".join(
        DISP[a].replace("Tight-aggressive", "TAG").replace("Calling station", "Station") for a in ARCH)
    + " & Pearson $r$ [95\\%] & Spearman \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
rows = []
for a in ARCH:
    cells = [DISP[a]]
    for c in [f"read_target_{x}_b10" for x in ARCH]:
        m, se, lo, hi = pdiff(c, "no_read", a)
        cells.append(sg(m))
    rows.append(" & ".join(cells) + r" \\")
open(os.path.join(GEN, "tab_target_matrix.tex"), "w").write(
    "\\begin{tabular}{l" + "c" * 8 + "}\n\\toprule\n & \\multicolumn{8}{c}{Archetype whose bets are read} \\\\\n\\cmidrule(lr){2-9}\nChange in win rate of & "
    + " & ".join(DISP[a].replace("Tight-aggressive", "TAG").replace("Calling station", "Station") for a in ARCH)
    + " \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
rows = []
for k, v in SW.items():
    c_ = v["cost_of_being_read"]
    rows.append(" & ".join([k, us(1 - float(k), 2), us(v["trust_read"]["mean"], 2),
                            f"{sg(v['win_rate_not_read']['mean'])} ({us(v['win_rate_not_read']['se'])})",
                            f"{sg(v['win_rate_read']['mean'])} ({us(v['win_rate_read']['se'])})",
                            f"{sg(c_['mean'])} [{sg(c_['ci95'][0])}, {sg(c_['ci95'][1])}]",
                            us(100 * v["fold_rate_medium_weak_vs_focal_not_read"], 0) + r" $\to$ " + us(100 * v["fold_rate_medium_weak_vs_focal_read"], 0),
                            sg(v["nonshowdown_not_read"]["mean"]) + r" $\to$ " + sg(v["nonshowdown_read"]["mean"])]) + r" \\")
open(os.path.join(GEN, "tab_sweep.tex"), "w").write(
    "\\begin{tabular}{cccccccc}\n\\toprule\nBluff rate & True non-bluff rate & Trust when read & Win rate, not read (SE) & Win rate, read (SE) & "
    "Cost of being read [95\\%] & Fold \\% against its bets & Non-showdown win rate \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- figures
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.linewidth": 0.6, "axes.edgecolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
                     "axes.labelcolor": INK, "pdf.fonttype": 42, "legend.frameon": False})
def base(ax, zero=True, axis="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=axis, color=GRID, lw=0.5); ax.set_axisbelow(True)
    if zero: (ax.axvline if axis == "x" else ax.axhline)(0, color=MUTED, lw=0.7)
def err(ax, x, y, lo, hi, color, marker, label, horizontal=True, filled=True):
    kw = dict(color=color, marker=marker, ms=4.2, lw=0, elinewidth=1.0, capsize=0, label=label,
              mfc=color if filled else "white", mec=color, mew=1.0)
    if horizontal: ax.errorbar(x, y, xerr=[np.array(x) - np.array(lo), np.array(hi) - np.array(x)], **kw)
    else: ax.errorbar(x, y, yerr=[np.array(y) - np.array(lo), np.array(hi) - np.array(y)], **kw)

# Fig 1: win rate by archetype, no reading vs first-submission roster
fig, ax = plt.subplots(figsize=(3.45, 2.5))
order = sorted(ARCH, key=lambda a: nr["archetypes"][a]["wr"]["mean"])
yy = np.arange(len(order))
for c, col, mk, lab, off, fl in (("no_read", BLUE, "o", "No reading", 0.14, True), ("published", ORANGE, "s", "Original roster", -0.14, False)):
    w = [C[c]["archetypes"][a]["wr"] for a in order]
    err(ax, [x["mean"] for x in w], yy + off, [x["ci95"][0] for x in w], [x["ci95"][1] for x in w], col, mk, lab, filled=fl)
ax.set_yticks(yy); ax.set_yticklabels([DISP[a] for a in order]); ax.set_xlabel("Win rate (bb/100)")
base(ax); ax.legend(loc="upper left", fontsize=7, handletextpad=0.2)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(FIG, "fig_winrate.pdf")); plt.close(fig)

# Fig 2: cost of being read, archetypes ordered by non-bluff rate
fig, ax = plt.subplots(figsize=(3.45, 2.6))
yy = np.arange(len(ORDER))
d = [cost[a] for a in ORDER]
err(ax, [x["mean"] for x in d], yy + (0.14 if have_exact else 0), [x["ci95"][0] for x in d], [x["ci95"][1] for x in d],
    BLUE, "o", "Posterior (pre-specified)")
if have_exact:
    e = [exact[a] for a in ORDER]
    err(ax, [x["mean"] for x in e], yy - 0.14, [x["ci95"][0] for x in e], [x["ci95"][1] for x in e],
        ORANGE, "s", "Exact (post hoc)", filled=False)
ax.set_yticks(yy); ax.set_yticklabels([f"{DISP[a]} ({H[a]:.2f})" for a in ORDER])
ax.set_xlabel("Cost of being read (bb/100)"); ax.set_ylabel("Archetype (non-bluff rate $h$)")
base(ax)
if have_exact: ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), fontsize=7, handletextpad=0.2, ncol=2, columnspacing=1.0)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(FIG, "fig_cost.pdf")); plt.close(fig)

# Fig 3: bluff-rate sweep
fig, ax = plt.subplots(figsize=(3.45, 2.3))
bx = [v["bluff_rate"] for v in SW.values()]
for key, col, mk, lab, fl, dx in (("win_rate_not_read", BLUE, "o", "Not read", True, -0.006), ("win_rate_read", ORANGE, "s", "Read by the other seven", False, 0.006)):
    w = [v[key] for v in SW.values()]
    ax.plot(np.array(bx) + dx, [x["mean"] for x in w], color=col, lw=1.2)
    err(ax, np.array(bx) + dx, [x["mean"] for x in w], [x["ci95"][0] for x in w], [x["ci95"][1] for x in w], col, mk, lab, horizontal=False, filled=fl)
ax.set_xticks(bx); ax.set_xlabel("Bluff rate of the focal seat (all streets)"); ax.set_ylabel("Its win rate (bb/100)")
base(ax, axis="y"); ax.legend(loc="upper left", fontsize=7, handletextpad=0.2)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(FIG, "fig_sweep.pdf")); plt.close(fig)

# Fig 4: association by condition
fig, ax = plt.subplots(figsize=(3.45, 2.6))
rowsr = [(lab.replace("$\\beta=", "strength ").replace("$", ""), C[c]["association"]["pearson_trust_winrate"]) for c, lab in SUPC if "legacy" not in c][::-1]
yy = np.arange(len(rowsr))
err(ax, [r["mean"] for _, r in rowsr], yy, [r["ci95"][0] for _, r in rowsr], [r["ci95"][1] for _, r in rowsr], BLUE, "o", None)
ax.axvline(C["no_read"]["association"]["pearson_trust_winrate"]["mean"], color=MUTED, lw=0.7, ls=(0, (3, 2)))
ax.set_yticks(yy); ax.set_yticklabels([l for l, _ in rowsr]); ax.set_xlabel("Correlation between\ntrust and win rate")
base(ax, zero=False); ax.set_xlim(-0.82, -0.48)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(FIG, "fig_assoc.pdf")); plt.close(fig)

# Fig S1: horizon, two panels with separate axes
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.4))
ax = axs[0]
ax.fill_between(nh, r_mean - r_sd, r_mean + r_sd, color=BLUE, alpha=0.18, lw=0)
ax.plot(nh, r_mean, color=BLUE, lw=1.3)
ax.set_xscale("log"); ax.set_xlabel("Hands played per seed"); ax.set_ylabel("Correlation between trust\nand win rate (mean $\\pm$ SD)")
base(ax, axis="y")
ax = axs[1]
ax.plot(nh, hw.max(axis=1), color=BLUE, lw=1.3); ax.plot(nh, hw.min(axis=1), color=ORANGE, lw=1.3)
ax.text(nh[3], hw.max(axis=1)[3] * 1.12, "widest archetype", color=INK, fontsize=7)
ax.text(nh[0], hw.min(axis=1)[0] * 0.55, "narrowest archetype", color=INK, fontsize=7)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Hands played per seed")
ax.set_ylabel("Half-width of the 95% interval\nof a win rate (bb/100, 20 seeds)")
ax.set_yticks([1, 2, 5, 10, 20]); ax.set_yticklabels(["1", "2", "5", "10", "20"]); ax.minorticks_off()
ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=GRID, lw=0.5); ax.set_axisbelow(True)
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(FIG, "fig_horizon.pdf")); plt.close(fig)

print(len(macros), "macros; exact post hoc data:", have_exact)
