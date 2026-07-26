#!/usr/bin/env python3
"""Phase 3.1 replication at n=20 seeds — the paper's priority follow-up.

The manuscript's Limitations and Conclusion sections both name this as the
P0 experiment: the headline Phase 3.1 result (mean r = -0.094) rests on 5
seeds, and its 95% bootstrap CI [-0.32, +0.20] straddles zero. The paper is
careful about this — it claims attenuation, not abolition — but the claim
cannot be sharpened without more seeds. This script runs that experiment.

It is a thin driver over ``run_phase3_chat.run_one_seed``; the simulation
itself is unchanged, so a replication is comparable to the original by
construction. What this adds is the machinery a long, paid, interruptible
run needs:

* **Resume.** A 20-seed run is tens of thousands of API calls over many
  hours. If it dies at seed 17, restarting from zero wastes most of the
  spend. Seeds already complete in the target database are skipped, so
  re-invoking the same command resumes rather than restarts.
* **Dry run.** ``--dry-run`` exercises the whole path — roster
  construction, prompt assembly, engine, logging, r computation — against
  an offline mock client, with no API calls and no cost. Run this first.
* **Cost estimate.** Printed up front, with a confirmation prompt, derived
  from the measured per-call cost of the original runs.
* **Nested design.** The original 5 seeds are the first 5 of the 20, so
  the published result is a strict subset of the replication and the two
  are directly comparable.
* **``--emit-r-json``.** Writes the per-seed r values straight into the
  format ``analysis/r_data.py`` reads, so the CIs, figures and LaTeX
  tables all update from one regeneration with nothing hand-copied.

Typical use::

    # 1. Validate offline. No API calls, no spend.
    python3 phase3/run_phase31_replication.py --dry-run

    # 2. The real run (resumable — safe to re-invoke after an interruption).
    export ANTHROPIC_API_KEY=sk-...
    python3 phase3/run_phase31_replication.py \
        --db research_data/runs_phase31_n20.sqlite --hands 150

    # 3. Land the numbers.
    python3 phase3/run_phase31_replication.py \
        --db research_data/runs_phase31_n20.sqlite --emit-r-json
    python3 analysis/bootstrap_ci.py --csv > paper_resources/data/r_bootstrap_ci.csv
    python3 analysis/make_paper_figures.py && python3 analysis/make_paper_tables.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.sqlite_logger import SQLiteLogger  # noqa: E402
from phase3.run_phase3_chat import run_one_seed  # noqa: E402


# ---------------------------------------------------------------------------
# Seed set
# ---------------------------------------------------------------------------
# The first five are the published Phase 3.1 seeds, kept in place so the
# n=5 result is nested inside the n=20 result rather than being a separate
# experiment. The other fifteen were drawn once, deterministically, from
#
#     rng  = numpy.random.default_rng(20260726)
#     pool = [s for s in range(1, 100000) if s not in ORIGINAL_SEEDS]
#     extra = sorted(rng.choice(pool, size=15, replace=False))
#
# and then frozen here. Fixing the literal list rather than re-drawing at
# runtime matters for two reasons: numpy's generator stream is not
# guaranteed stable across releases, and a seed set chosen before any
# outcome is observed cannot be accused of being selected to favour a
# result. Do not edit this list to chase a number.
# ---------------------------------------------------------------------------

ORIGINAL_SEEDS: List[int] = [42, 137, 256, 512, 1024]
EXTRA_SEEDS: List[int] = [
    12666, 13927, 14942, 19277, 29004, 41939, 42908, 58556,
    69218, 70875, 72385, 73280, 77153, 86890, 99769,
]
REPLICATION_SEEDS: List[int] = ORIGINAL_SEEDS + EXTRA_SEEDS

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_DB = _REPO_ROOT / "research_data" / "runs_phase31_n20.sqlite"
R_JSON = _REPO_ROOT / "paper_resources" / "data" / "r_by_phase.json"
PHASE_KEY = "Phase 3.1 (LLM + reasoning)"

# Measured from the published runs: Phase 3.1 was 11,953 calls across
# 5 seeds x 150 hands for roughly $17, i.e. ~15.9 calls/hand and
# ~$0.00142/call. Used only for the up-front estimate.
CALLS_PER_HAND = 15.9
USD_PER_CALL = 0.00142


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------

def completed_seeds(db_path: Path, num_hands: int) -> Dict[int, int]:
    """Map ``seed -> run_id`` for seeds already fully played in ``db_path``.

    A run counts as complete only when the number of logged hands matches
    ``num_hands``. A seed interrupted midway is therefore *not* skipped —
    it is replayed into a fresh ``run_id``, and the partial rows are left
    in place rather than deleted (they are harmless: every downstream
    query selects an explicit ``run_id``, and silently destroying logged
    data on a resume would be the wrong default for a paid run).
    """
    if not db_path.exists():
        return {}
    out: Dict[int, int] = {}
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        try:
            rows = cur.execute("SELECT run_id, seed FROM runs").fetchall()
        except sqlite3.OperationalError:
            return {}          # schema not created yet
        for run_id, seed in rows:
            n = cur.execute(
                "SELECT COUNT(*) FROM hands WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if n >= num_hands:
                out[seed] = run_id      # last complete run for this seed wins
    finally:
        conn.close()
    return out


# ---------------------------------------------------------------------------
# Offline mock client for --dry-run
# ---------------------------------------------------------------------------

class _MockMessages:
    def __init__(self, owner: "MockClient") -> None:
        self._owner = owner

    def create(self, **kwargs: Any) -> Any:
        """Return a canned, schema-valid Phase 3.1 response."""
        self._owner.calls += 1

        class _Block:
            def __init__(self, text: str) -> None:
                self.text = text
                self.type = "text"

        class _Resp:
            def __init__(self, text: str) -> None:
                self.content = [_Block(text)]
                self.stop_reason = "end_turn"

        # Phase 3.1 format: brief reasoning, then a final ACTION: line.
        # CALL is legal in every position the engine can present, which
        # keeps the dry run exercising the parser rather than the
        # fallback path.
        return _Resp("Pot odds are acceptable and my read is unclear.\nACTION: CALL")


class MockClient:
    """Stands in for the Anthropic client. Makes no network calls."""

    def __init__(self) -> None:
        self.calls = 0
        self.messages = _MockMessages(self)


# ---------------------------------------------------------------------------
# r extraction
# ---------------------------------------------------------------------------

def per_seed_r(db_path: Path, seed_to_run: Dict[int, int]) -> Dict[int, float]:
    """Trust-profit Pearson r per seed, via the canonical definition.

    Delegates to ``analysis.compute_metrics.compute_trust_profit_correlation``
    rather than reimplementing it, so the replication's r is computed the
    same way as every published r in the ladder.
    """
    from analysis.compute_metrics import compute_trust_profit_correlation

    conn = sqlite3.connect(str(db_path))
    try:
        out: Dict[int, float] = {}
        for seed in sorted(seed_to_run, key=lambda s: REPLICATION_SEEDS.index(s)
                           if s in REPLICATION_SEEDS else 10**9):
            r, _, _ = compute_trust_profit_correlation(conn, seed_to_run[seed])
            out[seed] = float(r)
        return out
    finally:
        conn.close()


def emit_r_json(db_path: Path, num_hands: int, json_path: Path,
                dry_run: bool = False) -> int:
    """Rewrite the Phase 3.1 entry of ``r_by_phase.json`` from the database."""
    done = completed_seeds(db_path, num_hands)
    if not done:
        print(f"  no completed seeds in {db_path} at {num_hands} hands — nothing to emit")
        return 1

    rmap = per_seed_r(db_path, done)
    seeds = list(rmap.keys())
    rs = [rmap[s] for s in seeds]

    payload = json.loads(json_path.read_text())
    entry = payload["phases"][PHASE_KEY]
    old_n, old_r = len(entry["r"]), list(entry["r"])
    entry["seeds"] = seeds
    entry["r"] = [round(x, 3) for x in rs]
    entry["hands_per_seed"] = num_hands

    mean_old = sum(old_r) / len(old_r)
    mean_new = sum(rs) / len(rs)
    print(f"  {PHASE_KEY}")
    print(f"    n:      {old_n} -> {len(seeds)}")
    print(f"    mean r: {mean_old:+.3f} -> {mean_new:+.3f}")
    print(f"    r:      {[f'{x:+.3f}' for x in rs]}")

    if dry_run:
        print(f"  [dry-run] would write {json_path}")
        return 0

    backup = json_path.with_suffix(".json.bak")
    shutil.copy2(json_path, backup)
    json_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  wrote {json_path}  (previous version saved to {backup.name})")
    print("  next: python3 analysis/bootstrap_ci.py")
    return 0


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _estimate(num_seeds: int, num_hands: int) -> None:
    calls = num_seeds * num_hands * CALLS_PER_HAND
    usd = calls * USD_PER_CALL
    print(f"  seeds        : {num_seeds}")
    print(f"  hands/seed   : {num_hands}")
    print(f"  est. calls   : {calls:,.0f}")
    print(f"  est. cost    : ${usd:,.2f}  (at ~${USD_PER_CALL:.5f}/call)")
    print("  NOTE: an estimate from the published runs' measured rate, not a quote.")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(DEFAULT_DB), help="Target SQLite database.")
    p.add_argument("--hands", type=int, default=150,
                   help="Hands per seed. 150 matches the published Phase 3.1 "
                        "horizon (directly comparable); 500 matches Phase 3 and "
                        "additionally closes the hand-count asymmetry. Default: 150.")
    p.add_argument("--seeds", default=None,
                   help="Comma-separated seed override. Default: the frozen 20.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--provider", default="anthropic", choices=["anthropic", "ollama"])
    p.add_argument("--label", default="phase31-n20-replication")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate the full path offline with a mock client. "
                        "No API calls, no cost.")
    p.add_argument("--dry-run-hands", type=int, default=3,
                   help="Hands per seed during --dry-run (default: 3).")
    p.add_argument("--dry-run-seeds", type=int, default=2,
                   help="Seeds to exercise during --dry-run (default: 2).")
    p.add_argument("--emit-r-json", action="store_true",
                   help="Recompute per-seed r from --db and update r_by_phase.json.")
    p.add_argument("--yes", action="store_true",
                   help="Skip the cost confirmation prompt.")
    args = p.parse_args(argv)

    db_path = Path(args.db)
    seeds = ([int(s) for s in args.seeds.split(",") if s.strip()]
             if args.seeds else list(REPLICATION_SEEDS))

    if args.emit_r_json:
        print("Emitting r_by_phase.json from", db_path)
        return emit_r_json(db_path, args.hands, R_JSON)

    # ---------------- dry run ----------------
    if args.dry_run:
        seeds = seeds[:args.dry_run_seeds]
        num_hands = args.dry_run_hands
        db_path = Path("/tmp/phase31_dryrun.sqlite")
        if db_path.exists():
            db_path.unlink()
        print("=" * 68)
        print("DRY RUN — offline mock client, no API calls, no cost")
        print("=" * 68)
        print("Cost of the REAL run this validates:")
        _estimate(len(REPLICATION_SEEDS), args.hands)
        print()
    else:
        num_hands = args.hands
        print("=" * 68)
        print("PHASE 3.1 REPLICATION")
        print("=" * 68)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Work out what is left to do BEFORE pricing or building a client, so
    # that a resumed run is quoted for the seeds it will actually play
    # rather than for the whole set, and so that an already-finished run
    # exits cleanly without needing credentials.
    already = completed_seeds(db_path, num_hands)
    todo = [s for s in seeds if s not in already]
    if already:
        print(f"Resuming: {len(already)} seed(s) already complete "
              f"({sorted(already)}) — skipping.")
    if not todo:
        print("All seeds already complete. Nothing to run.")
        print("Run with --emit-r-json to land the numbers.")
        return 0
    print(f"To run: {len(todo)} seed(s): {todo}\n")

    if args.dry_run:
        client: Any = MockClient()
    else:
        _estimate(len(todo), num_hands)
        print()
        if args.provider == "anthropic":
            import os
            if not os.environ.get("ANTHROPIC_API_KEY"):
                print("ERROR: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
                print("       export ANTHROPIC_API_KEY=sk-... and retry, or use "
                      "--dry-run to validate offline.", file=sys.stderr)
                return 2
        if not args.yes:
            resp = input("Proceed and incur this cost? [y/N] ").strip().lower()
            if resp not in ("y", "yes"):
                print("Aborted.")
                return 1
        from phase3.llm_chat_agent import make_client
        client = make_client(args.provider, args.model)

    logger = SQLiteLogger(str(db_path))
    summaries: List[Dict[str, Any]] = []
    started = time.time()
    try:
        for i, seed in enumerate(todo, 1):
            print(f"[{i}/{len(todo)}] seed={seed}")
            summary = run_one_seed(
                seed=seed, num_hands=num_hands, client=client,
                model=args.model, provider=args.provider,
                logger=logger, label=args.label, phase31=True,
            )
            summaries.append(summary)
            if summary["chip_delta"] != 0:
                print(f"  !! CHIP CONSERVATION FAILURE: delta={summary['chip_delta']}. "
                      f"This run is contaminated — investigate before using the data.")
            print(f"  done: {summary['llm_calls']} calls, "
                  f"{summary['llm_failures']} failures\n")
    except KeyboardInterrupt:
        print("\nInterrupted. Completed seeds are saved; re-run the same "
              "command to resume where it stopped.")
        return 130
    finally:
        logger.close()

    elapsed = time.time() - started
    total_calls = sum(s["llm_calls"] for s in summaries)
    total_fail = sum(s["llm_failures"] for s in summaries)
    print("=" * 68)
    print(f"Completed {len(summaries)} seed(s) in {elapsed/60:.1f} min")
    print(f"  LLM calls   : {total_calls:,}")
    print(f"  failures    : {total_fail:,}")
    if not args.dry_run:
        print(f"  actual est. : ${total_calls * USD_PER_CALL:,.2f}")

    if args.dry_run:
        print()
        print("Validating r extraction...")
        done = completed_seeds(db_path, num_hands)
        rmap = per_seed_r(db_path, done)
        for seed, r in rmap.items():
            print(f"  seed {seed}: r = {r:+.3f}")
        print()
        print("Previewing the r_by_phase.json update (no write):")
        emit_r_json(db_path, num_hands, R_JSON, dry_run=True)
        print()
        print("DRY RUN OK — the full path works end to end.")
        print("The r values above are meaningless (the mock always calls);")
        print("what this proves is that the pipeline runs and lands its numbers.")
    else:
        print()
        print("Next: --emit-r-json, then bootstrap_ci.py / make_paper_*.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
