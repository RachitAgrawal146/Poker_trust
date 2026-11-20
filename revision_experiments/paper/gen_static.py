"""Tables that come from the code alone (no results): archetype tables, the
exploiter's table, the list of conditions. Run from anywhere:
  python3 gen_static.py REPO PAPER/generated
"""
import json, sys, os
repo, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)
from archetype_params import ARCHETYPE_PARAMS as P, PREDATOR_EXPLOIT as X, HONESTY_SCORES as H
os.makedirs(out, exist_ok=True)
NAME = {"oracle": "Balanced", "sentinel": "Tight-aggressive", "firestorm": "Maniac", "wall": "Calling station",
        "phantom": "Bluffer", "predator_baseline": "Exploiter (baseline)", "mirror_default": "Mimic (default)",
        "judge_cooperative": "Grudger (cooperative)", "judge_retaliatory": "Grudger (retaliatory)",
        "predator": "Exploiter", "mirror": "Mimic", "judge": "Grudger"}
ST = ["preflop", "flop", "turn", "river"]
def f(x): return f"{x:.2f}"
rows = []
for k in ["oracle", "sentinel", "firestorm", "wall", "phantom", "predator_baseline", "mirror_default",
          "judge_cooperative", "judge_retaliatory"]:
    for i, s in enumerate(ST):
        p = P[k][s]
        lead = (r"\multirow{4}{*}{" + NAME[k] + "}") if i == 0 else ""
        rows.append(" & ".join([lead, s, f(p["br"]), f(p["mbr"]), f(p["vbr"]), f(p["strong_raise"]), f(p["strong_call"]),
                                f(p["med_raise"]), f(p["cr"]), f(p["weak_call"])]) + r" \\")
    rows.append(r"\midrule")
rows = rows[:-1]
open(os.path.join(out, "tab_archetype_params.tex"), "w").write(
    "\\begin{tabular}{llcccccccc}\n\\toprule\n"
    " & & \\multicolumn{3}{c}{No bet pending: bet} & \\multicolumn{5}{c}{Facing a bet} \\\\\n"
    "\\cmidrule(lr){3-5}\\cmidrule(lr){6-10}\n"
    "Table & Street & $b$ (Weak) & $m$ (Medium) & $v$ (Strong) & $r_S$ & $c_S$ & $r_M$ & $c_M$ & $c_W$ \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
rows = []
for k in ["oracle", "sentinel", "firestorm", "wall", "phantom", "predator_baseline", "mirror_default", "judge_cooperative"]:
    for i, s in enumerate(ST):
        p = X[k][s]
        lead = (r"\multirow{4}{*}{" + NAME[k].split(" (")[0] + "}") if i == 0 else ""
        rows.append(" & ".join([lead, s, f(p["br"]), f(p["mbr"]), f(p["vbr"]), f(p["cr"])]) + r" \\")
    rows.append(r"\midrule")
rows = rows[:-1]
open(os.path.join(out, "tab_exploit.tex"), "w").write(
    "\\begin{tabular}{llcccc}\n\\toprule\nOpponent classified as & Street & $b$ & $m$ & $v$ & $c_M$ \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
hon = {a: H[t] for a, t in [("oracle","oracle"),("sentinel","sentinel"),("firestorm","firestorm"),("wall","wall"),
                            ("phantom","phantom"),("predator","predator_baseline"),("mirror","mirror_default"),("judge","judge_cooperative")]}
json.dump({"non_bluff_rate": hon, "display": {k: NAME[k] for k in ["oracle","sentinel","firestorm","wall","phantom","predator","mirror","judge"]},
           "mean_params": {a: {m: sum(P[t][s][m] for s in ST)/4 for m in ("br","mbr","vbr","cr","weak_call","strong_raise","med_raise")}
                           for a, t in [("oracle","oracle"),("sentinel","sentinel"),("firestorm","firestorm"),("wall","wall"),
                                        ("phantom","phantom"),("predator","predator_baseline"),("mirror","mirror_default"),("judge","judge_cooperative")]}},
          open(os.path.join(out, "static.json"), "w"), indent=1)
print("static tables written")
