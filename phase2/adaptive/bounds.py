"""
Per-archetype parameter bounds for Phase 2 adaptive hill-climbing.

Every archetype's mutable parameter vector lives inside an
archetype-shaped box. The hill-climber clamps perturbations to
``(lo, hi)`` for each (archetype, round, metric). Bounds preserve
identity: Wall's ``br`` (bluff rate) never leaves the [0.00, 0.05]
neighborhood, so optimization can't turn Wall into Firestorm.

Design rules (per the redesign spec):

  * Tight archetypes (Sentinel, Wall) — Phase 1 value +/- 10-15 %
  * Moderate archetypes (Oracle, Predator, Mirror, Judge cooperative)
    — Phase 1 value +/- 20-30 %
  * Loose archetypes (Firestorm, Phantom, Judge retaliatory) — Phase 1
    value +/- 30-40 %
  * Identity-locked metrics (Wall.br, Wall.strong_raise, Wall.med_raise,
    Sentinel.br) — clamped near zero or near one
  * Every Phase 1 starting value must lie strictly inside its bound box

Structure mirrors ``archetype_params.ARCHETYPE_PARAMS`` exactly so the
HillClimber can index by ``(round, metric)`` without translation. Judge
gets two bound sets (pre/post trigger), keyed under
``ARCHETYPE_BOUNDS["judge"]`` as ``"pre_trigger"`` and
``"post_trigger"``.

Predator and Mirror in Phase 2 lose their adaptive modifiers (the
PREDATOR_EXPLOIT lookup and the per-opponent-mirror copy mechanism).
They optimize their baseline param vectors only -- documented limitation.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from typing import Dict, Tuple

from archetype_params import ARCHETYPE_PARAMS

__all__ = [
    "ARCHETYPE_BOUNDS",
    "make_unbounded_bounds",
    "verify_bounds_cover_initial_values",
]


Bound = Tuple[float, float]
RoundBounds = Dict[str, Bound]
ArchetypeBounds = Dict[str, RoundBounds]


# ---------------------------------------------------------------------------
# THE ORACLE -- Nash equilibrium reference, moderate freedom (~+/-25%)
# ---------------------------------------------------------------------------
_ORACLE: ArchetypeBounds = {
    "preflop": {
        "br":           (0.20, 0.45),
        "vbr":          (0.80, 1.00),
        "cr":           (0.20, 0.50),
        "mbr":          (0.35, 0.65),
        "strong_raise": (0.45, 0.75),
        "strong_call":  (0.20, 0.50),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.02, 0.20),
        "weak_call":    (0.05, 0.25),
    },
    "flop": {
        "br":           (0.20, 0.45),
        "vbr":          (0.78, 0.98),
        "cr":           (0.20, 0.50),
        "mbr":          (0.30, 0.60),
        "strong_raise": (0.45, 0.75),
        "strong_call":  (0.20, 0.50),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.02, 0.20),
        "weak_call":    (0.05, 0.25),
    },
    "turn": {
        "br":           (0.20, 0.45),
        "vbr":          (0.72, 0.96),
        "cr":           (0.20, 0.50),
        "mbr":          (0.25, 0.55),
        "strong_raise": (0.40, 0.70),
        "strong_call":  (0.25, 0.50),
        "strong_fold":  (0.02, 0.18),
        "med_raise":    (0.02, 0.20),
        "weak_call":    (0.04, 0.22),
    },
    "river": {
        "br":           (0.20, 0.45),
        "vbr":          (0.65, 0.94),
        "cr":           (0.20, 0.50),
        "mbr":          (0.20, 0.50),
        "strong_raise": (0.35, 0.65),
        "strong_call":  (0.25, 0.55),
        "strong_fold":  (0.02, 0.20),
        "med_raise":    (0.02, 0.20),
        "weak_call":    (0.03, 0.20),
    },
}


# ---------------------------------------------------------------------------
# THE SENTINEL -- TAG. Tight bounds (~+/-10%). Identity = low BR.
# ---------------------------------------------------------------------------
_SENTINEL: ArchetypeBounds = {
    "preflop": {
        "br":           (0.02, 0.18),
        "vbr":          (0.85, 1.00),
        "cr":           (0.25, 0.50),
        "mbr":          (0.18, 0.38),
        "strong_raise": (0.50, 0.78),
        "strong_call":  (0.20, 0.40),
        "strong_fold":  (0.02, 0.12),
        "med_raise":    (0.00, 0.12),
        "weak_call":    (0.02, 0.18),
    },
    "flop": {
        "br":           (0.02, 0.18),
        "vbr":          (0.80, 1.00),
        "cr":           (0.20, 0.45),
        "mbr":          (0.15, 0.35),
        "strong_raise": (0.45, 0.72),
        "strong_call":  (0.25, 0.45),
        "strong_fold":  (0.02, 0.12),
        "med_raise":    (0.00, 0.12),
        "weak_call":    (0.02, 0.16),
    },
    "turn": {
        "br":           (0.02, 0.16),
        "vbr":          (0.80, 1.00),
        "cr":           (0.18, 0.40),
        "mbr":          (0.10, 0.30),
        "strong_raise": (0.42, 0.68),
        "strong_call":  (0.28, 0.48),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.00, 0.10),
        "weak_call":    (0.02, 0.14),
    },
    "river": {
        "br":           (0.00, 0.14),
        "vbr":          (0.75, 0.98),
        "cr":           (0.15, 0.38),
        "mbr":          (0.06, 0.25),
        "strong_raise": (0.38, 0.62),
        "strong_call":  (0.30, 0.50),
        "strong_fold":  (0.02, 0.18),
        "med_raise":    (0.00, 0.08),
        "weak_call":    (0.00, 0.10),
    },
}


# ---------------------------------------------------------------------------
# THE FIRESTORM -- Maniac. Wide bounds (~+/-35%). Identity = high BR floor.
# ---------------------------------------------------------------------------
_FIRESTORM: ArchetypeBounds = {
    "preflop": {
        "br":           (0.40, 0.95),
        "vbr":          (0.85, 1.00),
        "cr":           (0.45, 0.90),
        "mbr":          (0.55, 0.95),
        "strong_raise": (0.55, 0.92),
        "strong_call":  (0.10, 0.40),
        "strong_fold":  (0.00, 0.10),
        "med_raise":    (0.10, 0.45),
        "weak_call":    (0.20, 0.60),
    },
    "flop": {
        "br":           (0.40, 0.92),
        "vbr":          (0.80, 1.00),
        "cr":           (0.40, 0.85),
        "mbr":          (0.50, 0.92),
        "strong_raise": (0.50, 0.88),
        "strong_call":  (0.15, 0.45),
        "strong_fold":  (0.00, 0.12),
        "med_raise":    (0.10, 0.40),
        "weak_call":    (0.18, 0.55),
    },
    "turn": {
        "br":           (0.35, 0.88),
        "vbr":          (0.75, 1.00),
        "cr":           (0.35, 0.82),
        "mbr":          (0.45, 0.90),
        "strong_raise": (0.45, 0.85),
        "strong_call":  (0.18, 0.48),
        "strong_fold":  (0.00, 0.15),
        "med_raise":    (0.08, 0.38),
        "weak_call":    (0.15, 0.50),
    },
    "river": {
        "br":           (0.30, 0.85),
        "vbr":          (0.72, 0.98),
        "cr":           (0.30, 0.78),
        "mbr":          (0.40, 0.85),
        "strong_raise": (0.40, 0.80),
        "strong_call":  (0.20, 0.50),
        "strong_fold":  (0.00, 0.18),
        "med_raise":    (0.05, 0.35),
        "weak_call":    (0.10, 0.45),
    },
}


# ---------------------------------------------------------------------------
# THE WALL -- Calling station. Identity-locked. Ultra-narrow on br/raises.
# ---------------------------------------------------------------------------
_WALL: ArchetypeBounds = {
    "preflop": {
        "br":           (0.00, 0.05),    # NEVER bluffs
        "vbr":          (0.40, 0.75),
        "cr":           (0.65, 0.95),    # calls
        "mbr":          (0.05, 0.22),
        "strong_raise": (0.00, 0.20),    # rarely raises even with strong
        "strong_call":  (0.65, 0.95),
        "strong_fold":  (0.02, 0.18),
        "med_raise":    (0.00, 0.05),    # rarely raises
        "weak_call":    (0.30, 0.70),
    },
    "flop": {
        "br":           (0.00, 0.05),
        "vbr":          (0.35, 0.70),
        "cr":           (0.60, 0.92),
        "mbr":          (0.04, 0.20),
        "strong_raise": (0.00, 0.20),
        "strong_call":  (0.65, 0.95),
        "strong_fold":  (0.02, 0.20),
        "med_raise":    (0.00, 0.05),
        "weak_call":    (0.28, 0.65),
    },
    "turn": {
        "br":           (0.00, 0.04),
        "vbr":          (0.30, 0.65),
        "cr":           (0.55, 0.90),
        "mbr":          (0.03, 0.18),
        "strong_raise": (0.00, 0.18),
        "strong_call":  (0.65, 0.95),
        "strong_fold":  (0.02, 0.20),
        "med_raise":    (0.00, 0.04),
        "weak_call":    (0.22, 0.55),
    },
    "river": {
        "br":           (0.00, 0.04),
        "vbr":          (0.25, 0.60),
        "cr":           (0.50, 0.85),
        "mbr":          (0.02, 0.15),
        "strong_raise": (0.00, 0.15),
        "strong_call":  (0.65, 0.95),
        "strong_fold":  (0.02, 0.20),
        "med_raise":    (0.00, 0.04),
        "weak_call":    (0.20, 0.50),
    },
}


# ---------------------------------------------------------------------------
# THE PHANTOM -- Deceiver. Wide bounds (~+/-30%) on bluff/value mix.
# ---------------------------------------------------------------------------
_PHANTOM: ArchetypeBounds = {
    "preflop": {
        "br":           (0.35, 0.85),
        "vbr":          (0.45, 0.85),
        "cr":           (0.10, 0.45),
        "mbr":          (0.30, 0.75),
        "strong_raise": (0.20, 0.60),
        "strong_call":  (0.25, 0.65),
        "strong_fold":  (0.05, 0.30),
        "med_raise":    (0.02, 0.20),
        "weak_call":    (0.18, 0.55),
    },
    "flop": {
        "br":           (0.30, 0.80),
        "vbr":          (0.40, 0.80),
        "cr":           (0.08, 0.40),
        "mbr":          (0.28, 0.70),
        "strong_raise": (0.18, 0.55),
        "strong_call":  (0.25, 0.65),
        "strong_fold":  (0.08, 0.35),
        "med_raise":    (0.02, 0.18),
        "weak_call":    (0.15, 0.50),
    },
    "turn": {
        "br":           (0.25, 0.75),
        "vbr":          (0.35, 0.75),
        "cr":           (0.05, 0.35),
        "mbr":          (0.25, 0.65),
        "strong_raise": (0.15, 0.50),
        "strong_call":  (0.25, 0.65),
        "strong_fold":  (0.10, 0.40),
        "med_raise":    (0.02, 0.15),
        "weak_call":    (0.10, 0.40),
    },
    "river": {
        "br":           (0.20, 0.70),
        "vbr":          (0.30, 0.70),
        "cr":           (0.05, 0.30),
        "mbr":          (0.20, 0.60),
        "strong_raise": (0.10, 0.45),
        "strong_call":  (0.25, 0.65),
        "strong_fold":  (0.15, 0.45),
        "med_raise":    (0.02, 0.12),
        "weak_call":    (0.05, 0.30),
    },
}


# ---------------------------------------------------------------------------
# THE PREDATOR -- baseline-only in Phase 2 (no per-opponent exploit blend).
# Moderate bounds (~+/-25%).
# ---------------------------------------------------------------------------
_PREDATOR: ArchetypeBounds = {
    "preflop": {
        "br":           (0.10, 0.40),
        "vbr":          (0.75, 1.00),
        "cr":           (0.20, 0.50),
        "mbr":          (0.25, 0.55),
        "strong_raise": (0.45, 0.75),
        "strong_call":  (0.20, 0.50),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.02, 0.18),
        "weak_call":    (0.04, 0.22),
    },
    "flop": {
        "br":           (0.10, 0.40),
        "vbr":          (0.70, 0.98),
        "cr":           (0.20, 0.50),
        "mbr":          (0.20, 0.50),
        "strong_raise": (0.40, 0.70),
        "strong_call":  (0.25, 0.50),
        "strong_fold":  (0.02, 0.18),
        "med_raise":    (0.02, 0.18),
        "weak_call":    (0.03, 0.20),
    },
    "turn": {
        "br":           (0.08, 0.36),
        "vbr":          (0.65, 0.95),
        "cr":           (0.18, 0.45),
        "mbr":          (0.18, 0.45),
        "strong_raise": (0.35, 0.65),
        "strong_call":  (0.25, 0.55),
        "strong_fold":  (0.04, 0.20),
        "med_raise":    (0.02, 0.15),
        "weak_call":    (0.02, 0.18),
    },
    "river": {
        "br":           (0.06, 0.32),
        "vbr":          (0.65, 0.95),
        "cr":           (0.18, 0.45),
        "mbr":          (0.12, 0.40),
        "strong_raise": (0.30, 0.60),
        "strong_call":  (0.28, 0.55),
        "strong_fold":  (0.05, 0.25),
        "med_raise":    (0.02, 0.12),
        "weak_call":    (0.02, 0.15),
    },
}


# ---------------------------------------------------------------------------
# THE MIRROR -- baseline-only in Phase 2 (no opponent-copy mechanism).
# Moderate bounds (~+/-25%).
# ---------------------------------------------------------------------------
_MIRROR: ArchetypeBounds = {
    "preflop": {
        "br":           (0.03, 0.25),
        "vbr":          (0.75, 1.00),
        "cr":           (0.22, 0.52),
        "mbr":          (0.18, 0.42),
        "strong_raise": (0.45, 0.78),
        "strong_call":  (0.20, 0.45),
        "strong_fold":  (0.02, 0.12),
        "med_raise":    (0.02, 0.15),
        "weak_call":    (0.03, 0.20),
    },
    "flop": {
        "br":           (0.02, 0.22),
        "vbr":          (0.70, 1.00),
        "cr":           (0.20, 0.48),
        "mbr":          (0.15, 0.35),
        "strong_raise": (0.42, 0.72),
        "strong_call":  (0.25, 0.48),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.02, 0.15),
        "weak_call":    (0.02, 0.18),
    },
    "turn": {
        "br":           (0.02, 0.20),
        "vbr":          (0.70, 1.00),
        "cr":           (0.18, 0.42),
        "mbr":          (0.10, 0.30),
        "strong_raise": (0.38, 0.68),
        "strong_call":  (0.28, 0.50),
        "strong_fold":  (0.04, 0.18),
        "med_raise":    (0.01, 0.12),
        "weak_call":    (0.02, 0.15),
    },
    "river": {
        "br":           (0.00, 0.18),
        "vbr":          (0.65, 0.95),
        "cr":           (0.15, 0.38),
        "mbr":          (0.06, 0.25),
        "strong_raise": (0.32, 0.62),
        "strong_call":  (0.30, 0.55),
        "strong_fold":  (0.04, 0.20),
        "med_raise":    (0.01, 0.10),
        "weak_call":    (0.01, 0.12),
    },
}


# ---------------------------------------------------------------------------
# THE JUDGE (cooperative state) -- TAG-shaped, moderate bounds.
# ---------------------------------------------------------------------------
_JUDGE_COOPERATIVE: ArchetypeBounds = {
    "preflop": {
        "br":           (0.02, 0.18),
        "vbr":          (0.85, 1.00),
        "cr":           (0.25, 0.50),
        "mbr":          (0.18, 0.40),
        "strong_raise": (0.50, 0.78),
        "strong_call":  (0.20, 0.40),
        "strong_fold":  (0.02, 0.12),
        "med_raise":    (0.00, 0.12),
        "weak_call":    (0.02, 0.18),
    },
    "flop": {
        "br":           (0.02, 0.18),
        "vbr":          (0.80, 1.00),
        "cr":           (0.20, 0.45),
        "mbr":          (0.15, 0.35),
        "strong_raise": (0.45, 0.72),
        "strong_call":  (0.25, 0.45),
        "strong_fold":  (0.02, 0.12),
        "med_raise":    (0.00, 0.12),
        "weak_call":    (0.02, 0.16),
    },
    "turn": {
        "br":           (0.02, 0.16),
        "vbr":          (0.80, 1.00),
        "cr":           (0.18, 0.40),
        "mbr":          (0.10, 0.30),
        "strong_raise": (0.42, 0.68),
        "strong_call":  (0.28, 0.48),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.00, 0.10),
        "weak_call":    (0.02, 0.14),
    },
    "river": {
        "br":           (0.00, 0.14),
        "vbr":          (0.75, 0.98),
        "cr":           (0.15, 0.38),
        "mbr":          (0.06, 0.25),
        "strong_raise": (0.38, 0.62),
        "strong_call":  (0.30, 0.50),
        "strong_fold":  (0.02, 0.18),
        "med_raise":    (0.00, 0.08),
        "weak_call":    (0.00, 0.10),
    },
}


# ---------------------------------------------------------------------------
# THE JUDGE (retaliatory state) -- aggressive, wide bounds.
# ---------------------------------------------------------------------------
_JUDGE_RETALIATORY: ArchetypeBounds = {
    "preflop": {
        "br":           (0.40, 0.92),
        "vbr":          (0.85, 1.00),
        "cr":           (0.05, 0.28),
        "mbr":          (0.45, 0.88),
        "strong_raise": (0.50, 0.88),
        "strong_call":  (0.10, 0.40),
        "strong_fold":  (0.00, 0.12),
        "med_raise":    (0.08, 0.35),
        "weak_call":    (0.00, 0.12),
    },
    "flop": {
        "br":           (0.35, 0.88),
        "vbr":          (0.80, 1.00),
        "cr":           (0.04, 0.25),
        "mbr":          (0.40, 0.85),
        "strong_raise": (0.45, 0.85),
        "strong_call":  (0.12, 0.42),
        "strong_fold":  (0.02, 0.15),
        "med_raise":    (0.05, 0.30),
        "weak_call":    (0.00, 0.10),
    },
    "turn": {
        "br":           (0.30, 0.82),
        "vbr":          (0.78, 1.00),
        "cr":           (0.02, 0.22),
        "mbr":          (0.35, 0.80),
        "strong_raise": (0.42, 0.80),
        "strong_call":  (0.15, 0.45),
        "strong_fold":  (0.04, 0.18),
        "med_raise":    (0.04, 0.25),
        "weak_call":    (0.00, 0.08),
    },
    "river": {
        "br":           (0.25, 0.78),
        "vbr":          (0.72, 0.98),
        "cr":           (0.02, 0.18),
        "mbr":          (0.30, 0.75),
        "strong_raise": (0.40, 0.75),
        "strong_call":  (0.18, 0.45),
        "strong_fold":  (0.04, 0.22),
        "med_raise":    (0.03, 0.22),
        "weak_call":    (0.00, 0.06),
    },
}


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------
ARCHETYPE_BOUNDS: Dict[str, object] = {
    "oracle":            _ORACLE,
    "sentinel":          _SENTINEL,
    "firestorm":         _FIRESTORM,
    "wall":              _WALL,
    "phantom":           _PHANTOM,
    "predator_baseline": _PREDATOR,
    "mirror_default":    _MIRROR,
    "judge": {
        "pre_trigger":  _JUDGE_COOPERATIVE,
        "post_trigger": _JUDGE_RETALIATORY,
    },
}


# ---------------------------------------------------------------------------
# Verifier -- used by the runner before any hand is played.
# ---------------------------------------------------------------------------

_ROUNDS = ("preflop", "flop", "turn", "river")
_REQUIRED_KEYS = (
    "br", "vbr", "cr", "mbr",
    "strong_raise", "strong_call", "strong_fold",
    "med_raise", "weak_call",
)


def _check_archetype(name: str, params_key: str, bounds: ArchetypeBounds) -> None:
    initial = ARCHETYPE_PARAMS[params_key]
    for round_name in _ROUNDS:
        if round_name not in bounds:
            raise ValueError(f"{name}: missing bounds for round {round_name!r}")
        round_bounds = bounds[round_name]
        round_initial = initial[round_name]
        for key in _REQUIRED_KEYS:
            if key not in round_bounds:
                raise ValueError(
                    f"{name}.{round_name}.{key}: missing bound entry"
                )
            lo, hi = round_bounds[key]
            if not (0.0 <= lo <= hi <= 1.0):
                raise ValueError(
                    f"{name}.{round_name}.{key}: invalid bound ({lo}, {hi})"
                )
            v = round_initial[key]
            if not (lo <= v <= hi):
                raise ValueError(
                    f"{name}.{round_name}.{key}: initial value {v} "
                    f"outside bounds ({lo}, {hi})"
                )


def verify_bounds_cover_initial_values() -> None:
    """Raise ``ValueError`` if any bound box doesn't enclose the Phase 1
    starting value, or if any required (round, metric) key is missing.

    Called once at runner startup; cheap and worth it."""
    _check_archetype("oracle",            "oracle",            _ORACLE)
    _check_archetype("sentinel",          "sentinel",          _SENTINEL)
    _check_archetype("firestorm",         "firestorm",         _FIRESTORM)
    _check_archetype("wall",              "wall",              _WALL)
    _check_archetype("phantom",           "phantom",           _PHANTOM)
    _check_archetype("predator_baseline", "predator_baseline", _PREDATOR)
    _check_archetype("mirror_default",    "mirror_default",    _MIRROR)
    _check_archetype("judge_cooperative", "judge_cooperative", _JUDGE_COOPERATIVE)
    _check_archetype("judge_retaliatory", "judge_retaliatory", _JUDGE_RETALIATORY)


# ---------------------------------------------------------------------------
# Unbounded variant — every (round, metric) collapses to the full [0, 1]
# probability range. Used by run_adaptive.py --unbounded for the
# "convergence-without-personality" experiment.
# ---------------------------------------------------------------------------

def make_unbounded_bounds() -> Dict[str, object]:
    """Return a bounds registry shaped exactly like ``ARCHETYPE_BOUNDS``
    but with every ``(lo, hi)`` collapsed to ``(0.0, 1.0)``.

    Identity-locking metrics (Wall.br, Sentinel.br, etc.) lose their
    floors and ceilings — every archetype is free to drift toward any
    point in the legal probability space. Phase 1 starting values are
    preserved on each agent so all eight begin from their canonical
    personalities; the hill-climber decides whether to stay, drift, or
    converge.
    """
    free: Bound = (0.0, 1.0)
    free_round: RoundBounds = {key: free for key in _REQUIRED_KEYS}
    free_archetype: ArchetypeBounds = {
        round_name: dict(free_round) for round_name in _ROUNDS
    }

    def _fresh() -> ArchetypeBounds:
        return {round_name: dict(free_round) for round_name in _ROUNDS}

    return {
        "oracle":            _fresh(),
        "sentinel":          _fresh(),
        "firestorm":         _fresh(),
        "wall":              _fresh(),
        "phantom":           _fresh(),
        "predator_baseline": _fresh(),
        "mirror_default":    _fresh(),
        "judge": {
            "pre_trigger":  _fresh(),
            "post_trigger": _fresh(),
        },
    }


if __name__ == "__main__":
    verify_bounds_cover_initial_values()
    print("ARCHETYPE_BOUNDS: all 9 archetypes pass coverage checks.")
