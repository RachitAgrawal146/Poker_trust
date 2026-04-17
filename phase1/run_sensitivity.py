"""Stage 11 / 12 scaffold — trust-model sensitivity sweeps.

The Bayesian posterior has three hyper-parameters that can meaningfully move
the archetype-identification curve: ``lambda_decay`` (the forgetting rate),
``epsilon_noise`` (trembling-hand smoothing), and ``third_party_weight``
(the exponent on observations made after the observer folded). This CLI
sweeps one of them across several values, re-runs the simulation with the
Stage-5 canonical roster, and writes a long-format CSV with the
end-of-run mean trust, mean entropy, and per-archetype identification rate
for every (value, seed) combination.

Usage
-----
::

    python3 run_sensitivity.py --param lambda --values 0.90,0.95,0.98,1.0 \\
        --hands 500 --seeds 42,137 --outdir runs/sensitivity/

``--param`` must be one of ``lambda`` / ``epsilon`` / ``tpw`` (short for
``third_party_weight``). The output CSV is named after the parameter —
``lambda_sweep.csv``, ``epsilon_sweep.csv``, or ``tpw_sweep.csv``.

Config plumbing
---------------
``trust.bayesian_model`` caches the config values at *module load* (see the
``_LAMBDA`` / ``_EPS`` / ``_TPW`` module-level floats). A live sweep has to
patch both ``config.TRUST`` AND those cached module constants, then restore
both at exit via a ``try / finally`` block — the module stays importable in
its original state for anything else that runs in the same process (tests,
notebooks).
"""

from __future__ import annotations

# Ensure repo root is on sys.path (this file lives in phase1/ or phase2/)
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))


import argparse
import csv
import os
import sys
from typing import Dict, List, Tuple


# Map the short CLI name to the config.TRUST key AND the cached module
# constant on ``trust.bayesian_model``. We drive both in lock-step.
_PARAM_MAP = {
    "lambda":  ("lambda_decay",       "_LAMBDA"),
    "epsilon": ("epsilon_noise",      "_EPS"),
    "tpw":     ("third_party_weight", "_TPW"),
}

# Fixed true archetypes per seat. Keyed by stage because Stage 5 fills
# seats 5-7 with Oracle stand-ins (which would triple-dip if we tracked
# them) while Stage 6 uses the full 8-archetype roster.
_TRACKED_SEATS_BY_STAGE: Dict[int, List[Tuple[int, str]]] = {
    5: [
        (1, "sentinel"),
        (2, "firestorm"),
        (3, "wall"),
        (4, "phantom"),
    ],
    6: [
        (1, "sentinel"),
        (2, "firestorm"),
        (3, "wall"),
        (4, "phantom"),
        (5, "predator_baseline"),
        (6, "mirror_default"),
        (7, "judge_cooperative"),
    ],
}

# Output columns (long-format: one row per (param, value, seed)).
# Stage 5 rosters leave the adaptive columns at 0; Stage 6 populates them.
_SWEEP_HEADER = [
    "param",
    "value",
    "seed",
    "stage",
    "mean_trust",
    "mean_entropy",
    "sentinel_id_rate",
    "firestorm_id_rate",
    "wall_id_rate",
    "phantom_id_rate",
    "predator_id_rate",
    "mirror_id_rate",
    "judge_id_rate",
]


# =============================================================================
# Agent roster: stage-aware builder (matches run_multiseed.build_agents).
# =============================================================================
def build_agents(stage: int = 6):
    """Return a fresh 8-seat roster for the requested stage.

    Stage 5 is retained for reproducing older sweeps; Stage 6 is the
    canonical default and measures adaptive-agent identification rates
    alongside the 4 static archetypes.
    """
    from agents.oracle import Oracle
    from agents.sentinel import Sentinel
    from agents.firestorm import Firestorm
    from agents.wall import Wall
    from agents.phantom import Phantom

    base = [
        Oracle(seat=0),
        Sentinel(seat=1),
        Firestorm(seat=2),
        Wall(seat=3),
        Phantom(seat=4),
    ]

    if stage == 5:
        return base + [
            Oracle(seat=5, name="Oracle-5"),
            Oracle(seat=6, name="Oracle-6"),
            Oracle(seat=7, name="Oracle-7"),
        ]
    if stage == 6:
        from agents.predator import Predator
        from agents.mirror import Mirror
        from agents.judge import Judge

        return base + [
            Predator(seat=5),
            Mirror(seat=6),
            Judge(seat=7),
        ]
    raise ValueError(
        f"run_sensitivity supports stage 5 and 6, got {stage}"
    )


# =============================================================================
# Measurement: run one (value, seed) cell and compute aggregate metrics.
# =============================================================================
def _run_cell(seed: int, num_hands: int, stage: int = 6) -> Dict[str, float]:
    """Play ``num_hands`` hands with a fresh roster and return aggregate
    metrics for the sweep: mean_trust, mean_entropy, and per-archetype
    identification rates. Adaptive-agent columns are populated only when
    ``stage >= 6`` (they stay at 0.0 for Stage 5 for schema stability)."""
    from engine.table import Table
    from trust import TRUST_TYPE_LIST

    agents = build_agents(stage=stage)
    table = Table(agents, seed=seed)
    for _ in range(num_hands):
        table.play_hand()

    # Mean trust / entropy across all (observer, target) pairs.
    trust_sum = 0.0
    entropy_sum = 0.0
    pair_count = 0
    for obs in agents:
        for target in range(len(agents)):
            if target == obs.seat:
                continue
            trust_sum += float(obs.trust_score(target))
            entropy_sum += float(obs.entropy(target))
            pair_count += 1
    mean_trust = trust_sum / pair_count if pair_count else 0.0
    mean_entropy = entropy_sum / pair_count if pair_count else 0.0

    # Per-archetype identification rate: average posterior mass assigned to
    # the target's TRUE archetype, across all observers for that target.
    id_rates: Dict[str, float] = {}
    arch_idx = {a: i for i, a in enumerate(TRUST_TYPE_LIST)}
    tracked = _TRACKED_SEATS_BY_STAGE[stage]
    for target_seat, true_arch in tracked:
        idx = arch_idx[true_arch]
        vals: List[float] = []
        for obs in agents:
            if obs.seat == target_seat:
                continue
            post = obs.posteriors.get(target_seat)
            if post is None:
                continue
            vals.append(float(post[idx]))
        id_rates[true_arch] = sum(vals) / len(vals) if vals else 0.0

    return {
        "mean_trust": mean_trust,
        "mean_entropy": mean_entropy,
        "sentinel_id_rate":  id_rates.get("sentinel", 0.0),
        "firestorm_id_rate": id_rates.get("firestorm", 0.0),
        "wall_id_rate":      id_rates.get("wall", 0.0),
        "phantom_id_rate":   id_rates.get("phantom", 0.0),
        "predator_id_rate":  id_rates.get("predator_baseline", 0.0),
        "mirror_id_rate":    id_rates.get("mirror_default", 0.0),
        "judge_id_rate":     id_rates.get("judge_cooperative", 0.0),
    }


# =============================================================================
# Config patching — done in lock-step between config.TRUST and the cached
# constants inside ``trust.bayesian_model``. Both must change because
# ``update_posterior`` reads the cached floats, not the live dict.
# =============================================================================
def _apply_override(param: str, value: float) -> None:
    import config
    import trust.bayesian_model as bm

    cfg_key, mod_attr = _PARAM_MAP[param]
    config.TRUST[cfg_key] = float(value)
    setattr(bm, mod_attr, float(value))


def _snapshot_params() -> Tuple[dict, Dict[str, float]]:
    """Capture the current config.TRUST + cached module constants so the
    try/finally in ``run`` can restore them verbatim."""
    import config
    import trust.bayesian_model as bm

    cfg_copy = dict(config.TRUST)
    mod_copy = {attr: float(getattr(bm, attr)) for _, attr in _PARAM_MAP.values()}
    return cfg_copy, mod_copy


def _restore_params(cfg_copy: dict, mod_copy: Dict[str, float]) -> None:
    import config
    import trust.bayesian_model as bm

    config.TRUST.clear()
    config.TRUST.update(cfg_copy)
    for attr, val in mod_copy.items():
        setattr(bm, attr, val)


# =============================================================================
# Orchestration + CLI
# =============================================================================
def run(
    param: str,
    values: List[float],
    seeds: List[int],
    num_hands: int,
    outdir: str,
    stage: int = 6,
) -> str:
    """Execute the sweep and write ``<param>_sweep.csv``. Returns the path.

    Restores ``config.TRUST`` and the cached ``trust.bayesian_model``
    constants even if one cell raises — all the real work runs inside a
    try/finally."""
    if param not in _PARAM_MAP:
        raise ValueError(
            f"Unknown --param {param!r}. Valid: {sorted(_PARAM_MAP)}"
        )
    if stage not in _TRACKED_SEATS_BY_STAGE:
        raise ValueError(
            f"Unknown --stage {stage}. Valid: {sorted(_TRACKED_SEATS_BY_STAGE)}"
        )

    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, f"{param}_sweep.csv")

    cfg_copy, mod_copy = _snapshot_params()
    summary_rows: List[dict] = []
    try:
        with open(out_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(_SWEEP_HEADER)
            for value in values:
                _apply_override(param, value)
                for seed in seeds:
                    metrics = _run_cell(seed, num_hands, stage=stage)
                    row = [
                        param,
                        f"{value:.6f}",
                        seed,
                        stage,
                        f"{metrics['mean_trust']:.6f}",
                        f"{metrics['mean_entropy']:.6f}",
                        f"{metrics['sentinel_id_rate']:.6f}",
                        f"{metrics['firestorm_id_rate']:.6f}",
                        f"{metrics['wall_id_rate']:.6f}",
                        f"{metrics['phantom_id_rate']:.6f}",
                        f"{metrics['predator_id_rate']:.6f}",
                        f"{metrics['mirror_id_rate']:.6f}",
                        f"{metrics['judge_id_rate']:.6f}",
                    ]
                    writer.writerow(row)
                    summary_rows.append({
                        "value": value,
                        "seed": seed,
                        **metrics,
                    })
    finally:
        _restore_params(cfg_copy, mod_copy)

    # Console summary — mean/std across seeds for each value.
    print(
        f"Sensitivity sweep: param={param}, "
        f"values={values}, seeds={seeds}, hands={num_hands} → {out_path}"
    )
    print(
        f"  {'value':>8}  {'seed':>6}  {'mean_trust':>11}  {'mean_H':>7}  "
        f"{'sent':>6}  {'fire':>6}  {'wall':>6}  {'phan':>6}"
    )
    for r in summary_rows:
        print(
            f"  {r['value']:>8.4f}  {r['seed']:>6d}  "
            f"{r['mean_trust']:>11.4f}  {r['mean_entropy']:>7.4f}  "
            f"{r['sentinel_id_rate']:>6.3f}  {r['firestorm_id_rate']:>6.3f}  "
            f"{r['wall_id_rate']:>6.3f}  {r['phantom_id_rate']:>6.3f}"
        )

    return out_path


def _parse_csv_floats(s: str) -> List[float]:
    return [float(x) for x in s.split(",") if x.strip()]


def _parse_csv_ints(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 12 scaffold — trust-model parameter sweep."
    )
    parser.add_argument(
        "--param", required=True, choices=sorted(_PARAM_MAP),
        help="Which trust-model hyper-parameter to vary.",
    )
    parser.add_argument(
        "--values", required=True,
        help="Comma-separated values to sweep through (e.g. 0.90,0.95,0.98).",
    )
    parser.add_argument(
        "--seeds", default="42,137",
        help="Comma-separated RNG seeds per cell (default: 42,137).",
    )
    parser.add_argument(
        "--hands", type=int, default=500,
        help="Hands per (value, seed) cell (default: 500).",
    )
    parser.add_argument(
        "--outdir", default="runs/sensitivity/",
        help="Output directory (default: runs/sensitivity/).",
    )
    parser.add_argument(
        "--stage", type=int, default=6, choices=[5, 6],
        help="Stage roster to use (default: 6). Stage 6 populates the "
             "predator/mirror/judge id-rate columns; Stage 5 leaves them 0.",
    )
    args = parser.parse_args(argv)

    values = _parse_csv_floats(args.values)
    seeds = _parse_csv_ints(args.seeds)
    if not values:
        parser.error("--values must contain at least one float")
    if not seeds:
        parser.error("--seeds must contain at least one integer")

    run(args.param, values, seeds, args.hands, args.outdir, stage=args.stage)
    return 0


if __name__ == "__main__":
    sys.exit(main())
