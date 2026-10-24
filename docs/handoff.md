# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-24

## Current objective

Finish MVP **step 2: NBA.com data** on branch `step-2-nba-data` ([mvp-plan.md](mvp-plan.md#build-steps)). The code is built and tested offline; the first real fetch is next.

## Done

- Step 1 skeleton merged (PR #1, 2026-10-23).
- Project knowledge docs: `CLAUDE.md`, `docs/decisions.md`, `docs/handoff.md`, done criteria in `docs/mvp-plan.md` (first commit on the step 2 branch).
- Step 2 code (approved plan, D15/D16):
  - `nbavalue/fetch.py`: base + advanced tables from NBA.com's league player stats, 3 s pause, dated snapshots in `data/raw/2025-26/<date>/`, reuses the newest snapshot unless `--refresh`, resumes interrupted runs.
  - `nbavalue/prepare.py`: field checks (errors list the columns NBA.com actually sent), one mapping from NBA.com to our column names, labels every row `NBA.com` with `fetched_on`, `source`, `season`; writes `data/processed/players.csv`.
  - `nbavalue/update_data.py`: `python -m nbavalue.update_data`.
  - `require_columns` moved to `nbavalue/checks.py` (no behaviour change).
  - `nba_api>=1.12,<2` added to `requirements.txt`. Setup switched to `uv`.

## Remaining

- **Step 2:** first real fetch (Nathan); confirm advanced field names (O5); decide O8 and update the mock columns to the real schema; merge the PR.
- Steps 3–6 in [mvp-plan.md](mvp-plan.md#build-steps). Open questions in [decisions.md](decisions.md#open).

## Known issues

- **Advanced column names are unconfirmed** (`POSS`, `USG_PCT`, `AST_PCT`, `OREB_PCT`, `DREB_PCT`). If they're wrong, `update_data` stops with an error that lists the real columns; fix the mapping in `nbavalue/prepare.py`.
- The prepared table has **no listed position**: the league stats endpoint doesn't return one. Needs another endpoint later.
- Mock columns are still the step 1 draft and don't match the prepared table (O8). They lack possessions, FGA, FTA and offensive rebounds, so per-100 stats can't be tested on them yet.
- README opening pitch still says "trade analyzer" (D1); fix in step 6.

## Last verification (2026-10-24, macOS, Python 3.13.17 via uv, nba_api 1.12.0)

| Check | Result |
| --- | --- |
| `pytest` | 18 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| `nba_api` call arguments | Checked offline against the library's signature and parameter values |
| Real NBA.com fetch | **Not run** |

## Next concrete task

1. Nathan runs `python -m nbavalue.update_data` and shares the printed column lists (no data values needed).
2. Fix any advanced field names in `prepare.py`, then agree O8 and update `data/mock/` and its tests to the prepared table's columns.
3. Merge step 2, then plan step 3 (salary import).
