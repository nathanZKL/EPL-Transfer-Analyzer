# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-24

## Current objective

Finish MVP **step 3: salary import** ([mvp-plan.md](mvp-plan.md#build-steps)). The code is built on branch `step-3-salary-import` (PR open). What's left is Nathan's first real import and merging.

## Done

- Step 1 skeleton (PR #1, 2026-10-23).
- Step 2 NBA.com data (PR #2, 2026-10-24): `python -m nbavalue.update_data` writes `data/processed/players.csv` (first real run: 582 players).
- Step 3 code (2026-10-24, plan approved by Nathan):
  - `nbavalue/salaries.py` validates the salary CSV (columns, labels, season, whole-dollar salary, source/URL/date on real rows, with CSV line numbers in errors) and matches rows to `player_id` by normalised name, using the team only to break ties (D18), plus `data/salaries/overrides.csv` (D19).
  - `python -m nbavalue.import_salaries` writes `data/processed/salaries.csv` and `salary_unmatched.csv` with suggestions (D21). `data/salaries/` is git-ignored (D20).
  - Check on the real player table: all 582 normalised names are distinct, so the tie-break isn't needed for 2025-26.
  - README has a "how to fill in your salary file" section.

## Remaining

- Step 3: Nathan builds a small real `data/salaries/salaries_2025-26.csv` (even 20 rows), runs the import, checks the unmatched report, then merges the PR. The scraper waits on O1.
- Step 4: add hustle, tracking and play-type tables (O5), `config/roles.yaml` (O6), per-100 stats, percentiles (O4), fit and value scores (O3). Analysis joins `players.csv` with `salaries.csv` on `player_id`.
- Steps 5–6 in the plan. Open questions are in [decisions.md](decisions.md#open).

## Known issues

- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- The import hasn't been run on real salaries yet; nickname mismatches are expected and fixed with overrides.
- Mock `salaries.csv` has no `player_id`; that's by design, since it goes through the same name matching as a real file.
- Real `age` and `minutes` arrive as decimals; mock values are whole numbers. Harmless so far.
- README opening pitch still says "trade analyzer" (D1); fix in step 6.

## Last verification (2026-10-24, macOS, Python 3.13.17 via uv)

| Check | Result |
| --- | --- |
| `pytest` | 50 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| `git check-ignore data/salaries/x.csv` | Ignored |
| Real import (`import_salaries`, Nathan's machine) | Not run yet: no real salary file |

## Next concrete task

Nathan: create `data/salaries/salaries_2025-26.csv` by hand (format in the README), run `python -m nbavalue.import_salaries`, and share the summary lines (not the data). Then merge step 3 and plan step 4.
