# research_data/MANIFEST.md

Where every simulation dataset lives, how it was produced, and how to
check it. Last updated 2026-10-13.

All databases use the schema in `data/schema.sql` (`runs`, `hands`,
`actions`, `showdowns`, `trust_snapshots`, `agent_stats`). Each `runs`
row records the seed, hands, a label and the git commit of the code that
produced it. `research_data/tools/check_dbs.py DIR --out FILE.json`
re-runs the integrity and shape checks below on any directory of
databases.

## 1. In this repository (Git LFS)

| File | Contents | Protocol | Checksum (LFS oid = SHA-256) |
|---|---|---|---|
| `runs_v3.sqlite.part_00`, `runs_v3.sqlite.part_01` | Phase 1 rule-based, Stage 6 roster. Reassemble with `cat research_data/runs_v3.sqlite.part_* > runs_v3.sqlite` | 20 seeds x 25,000 hands (500,000 hands). Seeds 42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432. Described in `phase1/phase1_report.md` | part_00 `5e3c45911658a689ad52732c22cfda460680c2d1d2feb4c5508243358d1e5372` (1,572,864,000 B); part_01 `8fa25c3ddca5ef93445e4e282c09430efbc8a336e8a0fd631413fbe178d7e4d9` (915,365,888 B) |
| `runs_phase3_long.sqlite` | Phase 3, LLM personality agents, no reasoning scaffolds | claude-haiku-4-5, SDK default temperature (1.0; produced before the temperature-0 pin of 2026-05-22, see `paper_resources/notes/methods_disclosures.md`). 5 seeds (42, 137, 256, 512, 1024) x 500 hands; 43,943 LLM calls. Scorecard: `reports/phase3_long_scorecard.txt` | `b4de2f0de59057c336b56af8d31997ea55788798f81a12edc81ce4dbb604579a` (12,201,984 B) |

All three LFS objects were confirmed to resolve on the LFS server on
2026-10-13 (batch API returns a download action for each).

## 2. GitHub Release `data-r0`

Release `data-r0` (tag on `3e87700`), created by
`.github/workflows/archive-data.yml`. Files were copied unchanged from
Actions artifacts that expire after 90 days. Download with
`curl -sSfL -O https://github.com/RachitAgrawal146/Poker_trust/releases/download/data-r0/<asset>`.

| Asset | Contents | Protocol | SHA-256 |
|---|---|---|---|
| `phase31_n20_r0.tar.gz` | Phase 3.1, LLM agents with chain-of-thought, memory and notes (arm `full`). 20 databases, one seed each, in folders `db-full-<seed>/` | claude-haiku-4-5-20251001, temperature 0. 150 hands per seed. Seeds 42, 137, 256, 512, 1024, 12666, 13927, 14942, 19277, 29004, 41939, 42908, 58556, 69218, 70875, 72385, 73280, 77153, 86890, 99769. Driver `phase3/run_phase31_replication.py`; workflow run 30788234686 ("Paper experiments", 3 Aug 2026), code at `92e1b64` (matches `runs.git_sha` in every file). Run label `phase31-repl-full` | `d6626d38da83c9fe64a5171db241832703aea14caf341b7749c34e280687169a` |
| `ablation_r0.tar.gz` | Phase 3.1 leave-one-out scaffold ablation. Folders `abl-no-cot-<seed>/` (5 seeds: 42, 137, 256, 512, 1024; label `phase31-repl-memory+notes`) and `abl-no-memory-<seed>/` (3 seeds: 256, 512, 1024; label `phase31-repl-cot+notes`). No `no-notes` databases exist | claude-haiku-4-5-20251001, temperature 0, 150 hands per seed. Workflow run 30874382486 ("Run ablation", 4 Aug 2026), code at `28f3fd1`. **The `no-memory` databases are contaminated by API errors (credit exhausted from 04:33:58Z) and must not be analysed**; see the README in the archive and commit `0b43ea5` | `abec0b3ffcaa2e8ddff4925e6c32a2508d27b89cb053f3f37675b10c94435e1a` |
| `phase31_n20_source.json`, `ablation_source.json` | Per-database SHA-256, size, `PRAGMA integrity_check`, `runs` rows and row counts, taken from the artifact before packing | | in `SHA256SUMS` |
| `SHA256SUMS` | Checksums of the four assets above | | |

Copies of the checks are in `research_data/checks/`. At creation every
database passed `PRAGMA integrity_check`; each Phase 3.1 n=20 database
holds exactly 150 hands, as does every ablation database. A separate job
downloaded the Release, verified `SHA256SUMS`, re-opened every database
and matched every per-file SHA-256 to the source checks
(`research_data/checks/verify_run_*.json`).

Aggregates derived from these databases:
`paper_resources/data/phase31_n20_stats.json` and the
"Phase 3.1 (LLM + reasoning)" and "Phase 3.1 ablation (no-cot)" entries
of `paper_resources/data/r_by_phase.json`.

## 3. Referenced elsewhere but not in this repository

These databases are named in reports and notes but are not tracked in
git, LFS or a Release. Only their derived aggregates (scorecards in
`reports/`, `paper_resources/data/r_by_phase.json`) are in the
repository.

| File named in the docs | Contents | Where the aggregates are |
|---|---|---|
| `runs_phase1_long.sqlite` | Phase 1, 5 seeds (42, 137, 256, 512, 1024) x 10,000 hands | `r_by_phase.json` "Phase 1 (frozen rules)" |
| `runs_phase2_long.sqlite` | Phase 2 bounded hill-climbing, same seeds and hands | `r_by_phase.json` "Phase 2 (bounded HC)" |
| `runs_phase2_unbounded.sqlite`, `runs_phase2_unbounded_aggressive.sqlite` | Phase 2 unbounded hill-climbing (weak and aggressive), same seeds and hands | `reports/phase2_unbounded_scorecard*.txt`; `r_by_phase.json` "Phase 2*" entries |
| `runs_phase31_long.sqlite` | Phase 3.1, 5 seeds x 150 hands, SDK default temperature (1.0); 11,953 LLM calls. Superseded by the n=20 temperature-0 run in `data-r0`. `phase3/phase3_report.md` describes it as LFS-tracked; it is not | `reports/phase31_long_scorecard.txt` (UTF-16 text) |

The rule-based datasets in this table can be regenerated from the code;
when they are, they will be added to a Release and listed here.
