"""Single source of truth for the per-seed trust-profit ``r`` ladder.

Before this module existed the per-seed ``r`` values were hardcoded twice —
once in ``analysis/bootstrap_ci.py`` and once in
``analysis/make_paper_figures.py`` — with a docstring in each asking the
next maintainer to "update both modules in lockstep". That is a drift
hazard, and it is the single biggest obstacle to landing a re-run (for
example the n=20 Phase 3.1 replication the paper's Limitations section
calls for): a re-run means editing two Python files by hand and hoping the
figures, the tables and the confidence intervals all end up quoting the
same numbers.

The values now live in ``paper_resources/data/r_by_phase.json``. This
module loads them and exposes them under the names the existing analysis
scripts already use, so the rest of the pipeline is unchanged.

**Seed counts are derived, never assumed.** Every consumer reads ``n``
from ``len(r)``, so a phase re-run at 20 seeds flows through the CIs,
figures and tables without touching any source file. Seed counts may
differ between phases — a 20-seed Phase 3.1 alongside a 5-seed Phase 1 is
a valid, and expected, configuration.

Usage::

    from analysis.r_data import load_r_data
    data = load_r_data()                     # canonical committed values
    data = load_r_data("my_rerun.json")      # a re-run's output

To land a re-run, regenerate the JSON (see
``phase3/run_phase31_replication.py --emit-r-json``) and re-run the figure
and table scripts. No Python edits required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_JSON = _REPO_ROOT / "paper_resources" / "data" / "r_by_phase.json"


class PhaseR:
    """Per-seed ``r`` values for one phase, plus its display metadata."""

    __slots__ = ("name", "short", "ladder", "hands_per_seed", "seeds", "r")

    def __init__(
        self,
        name: str,
        short: str,
        ladder: bool,
        hands_per_seed: int,
        seeds: Sequence[int],
        r: Sequence[float],
    ) -> None:
        if len(seeds) != len(r):
            raise ValueError(
                f"phase {name!r}: {len(seeds)} seeds but {len(r)} r values — "
                "these must correspond one-to-one"
            )
        if not r:
            raise ValueError(f"phase {name!r}: no r values")
        self.name = name
        self.short = short
        self.ladder = bool(ladder)
        self.hands_per_seed = int(hands_per_seed)
        self.seeds = list(seeds)
        self.r = [float(x) for x in r]

    @property
    def n(self) -> int:
        """Number of seeds. Derived — never assume 5."""
        return len(self.r)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"PhaseR({self.name!r}, n={self.n})"


class RData:
    """All phases, in file order."""

    def __init__(self, phases: Dict[str, PhaseR], source: Path) -> None:
        self.phases = phases
        self.source = source

    def __iter__(self):
        return iter(self.phases.values())

    def __getitem__(self, key: str) -> PhaseR:
        return self.phases[key]

    def ladder_phases(self) -> List[PhaseR]:
        """Only the phases that form the headline ladder (excludes Phase 2*)."""
        return [p for p in self.phases.values() if p.ladder]

    def r_by_phase(self, short_keys: bool = False) -> Dict[str, List[float]]:
        """``{phase_name: [r, ...]}`` — the legacy dict shape."""
        key = (lambda p: p.short) if short_keys else (lambda p: p.name)
        return {key(p): p.r for p in self.phases.values()}


def load_r_data(path: "str | Path | None" = None) -> RData:
    """Load per-seed r values. Defaults to the canonical committed JSON."""
    src = Path(path) if path is not None else CANONICAL_JSON
    raw = json.loads(src.read_text())
    phases: Dict[str, PhaseR] = {}
    for name, spec in raw["phases"].items():
        phases[name] = PhaseR(
            name=name,
            short=spec.get("short", name),
            ladder=spec.get("ladder", True),
            hands_per_seed=spec.get("hands_per_seed", 0),
            seeds=spec["seeds"],
            r=spec["r"],
        )
    return RData(phases, src)


# ---------------------------------------------------------------------------
# Legacy module-level names, kept so existing importers keep working.
#
# ``make_paper_tables.py`` does ``from make_paper_figures import R_BY_PHASE,
# SEEDS, ...``; ``make_paper_figures`` now re-exports these from here.
#
# NOTE: ``SEEDS`` is the seed list of the *first ladder phase*. It is only
# meaningful when every phase shares one seed list. Code that must be
# correct under mixed seed counts should use ``phase.seeds`` instead —
# see the guard in ``bootstrap_ci.render_per_seed_table``.
# ---------------------------------------------------------------------------

_DATA = load_r_data()

R_BY_PHASE: Dict[str, List[float]] = {
    p.short: p.r for p in _DATA.ladder_phases()
}
SEEDS: List[int] = _DATA.ladder_phases()[0].seeds
P2_UNBOUNDED_R_AGGRESSIVE: List[float] = _DATA["Phase 2* (unbounded HC, aggr.)"].r
P2_UNBOUNDED_R_WEAK: List[float] = _DATA["Phase 2* (unbounded HC, weak)"].r
P2_UNBOUNDED_R: List[float] = P2_UNBOUNDED_R_AGGRESSIVE  # canonical
PHASE_ORDER: List[str] = list(R_BY_PHASE.keys())


def uniform_seeds(data: "RData | None" = None) -> bool:
    """True when every phase shares an identical seed list."""
    d = data if data is not None else _DATA
    seed_lists = [tuple(p.seeds) for p in d]
    return len(set(seed_lists)) <= 1
