# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-24

## Current objective

Plan and build MVP **step 3: salary import** ([mvp-plan.md](mvp-plan.md#build-steps)). Nothing for step 3 has been started.

## Done

- Step 1 skeleton (PR #1, 2026-10-23).
- Step 2 NBA.com data (PR #2, 2026-10-24):
  - `python -m nbavalue.update_data` fetches base + advanced 2025-26 tables (`nbavalue/fetch.py`), checks, maps and labels them (`nbavalue/prepare.py`), and writes `data/processed/players.csv`.
  - Nathan's first real fetch: 582 players; base and advanced column names confirmed.
  - Mock players now use exactly the real table's columns, enforced by a test (D17).
  - Setup uses `uv` (D16). Project knowledge docs are in place.

## Remaining

- Step 3: salary CSV format, validation, and matching salaries to NBA.com player IDs (needs O2). The scraper is optional and waits on O1.
- Step 4: add hustle, tracking and play-type tables (O5), `config/roles.yaml` (O6), per-100 stats, percentiles (O4), fit and value scores (O3).
- Steps 5–6 in the plan. Open questions are in [decisions.md](decisions.md#open).

## Known issues

- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one. Needs another endpoint if the app should show it.
- Mock `salaries.csv` still matches players by name + team, with no `player_id`. Step 3 decides the real salary format (O2).
- Real `age` and `minutes` arrive as decimals; mock values are whole numbers. Harmless so far.
- README opening pitch still says "trade analyzer" (D1); fix in step 6.

## Last verification (2026-10-24, macOS, Python 3.13.17 via uv)

| Check | Result |
| --- | --- |
| `pytest` | 20 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| Real fetch (`update_data`, Nathan's machine) | 582 players in both tables; all mapped columns present |

## Next concrete task

Write the step 3 plan for Nathan to approve:
- the salary CSV columns (start from mock `salaries.csv`: `source`, `source_url`, `retrieved_on` required for real rows);
- the matching rule (O2; proposed: normalised name + team, with a manual override file);
- how unmatched rows are reported.
