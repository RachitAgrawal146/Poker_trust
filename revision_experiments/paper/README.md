# Exhibit generators

These scripts write every number, table and figure of the R1 manuscript from
data in this repository. `REPO` is the root of this repository and `PAPER`
the manuscript folder (it must contain `generated/` and `figures/`).

    python3 gen_static.py  REPO PAPER/generated   # tables that come from the code alone
    python3 gen_legacy.py  REPO PAPER/generated   # earlier datasets under win rate (research_data/checks/b2/)
    python3 gen_results.py REPO PAPER             # R1 conditions (research_data/r1/full/)

`gen_results.py` reads `research_data/r1/full/summary.json`, written by
`revision_experiments/analyze_r1.py`, and the `no_read` ledgers.
