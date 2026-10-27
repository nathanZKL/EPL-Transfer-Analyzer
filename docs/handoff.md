# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-26

## Current objective

Close out MVP **step 3: salary import** ([mvp-plan.md](mvp-plan.md#build-steps)). The code is merged (PR #3). Branch `step-3-followups` carries the review fixes (D22, D23) and these doc updates. What's left is merging it and Nathan's first real import.

## Done

- Step 1 skeleton (PR #1, 2026-10-23).
- Step 2 NBA.com data (PR #2, 2026-10-24): `python -m nbavalue.update_data` writes `data/processed/players.csv` (first real run: 582 players).
- Step 3 salary import (PR #3, merged 2026-10-25):
  - `nbavalue/salaries.py` validates the salary CSV (columns, labels, season, whole-dollar salary, source/URL/date on real rows, with CSV line numbers in errors) and matches rows to `player_id` by normalised name, using the team only to break ties (D18), plus `data/salaries/overrides.csv` (D19).
  - `python -m nbavalue.import_salaries` writes `data/processed/salaries.csv` and `salary_unmatched.csv` with suggestions (D21). `data/salaries/` is git-ignored (D20).
  - All 582 real normalised names are distinct, so the tie-break isn't needed for 2025-26.
- Step 3 follow-ups (branch `step-3-followups`, 2026-10-26, from the PR #3 review):
  - `salary_usd` must be plain digits, so Excel's `5.52E+07` can't sneak in a rounded salary (D23).
  - An override that fits no salary row stops the import (D23).
  - The unmatched message, import output and README explain that players with no 2025-26 games stay unmatched (D22). Fetching NBA.com's full player list is in "Ideas for later".
- Nathan's `data/salaries/salaries_2025-26.csv` has 20 hand-copied Spotrac rows (2025-26 cap hits). All pass validation; a read-only check found no misspelled names.

## Remaining

- Merge `step-3-followups`.
- Nathan runs `python -m nbavalue.import_salaries` and shares the summary lines (not the data). Expected: 19 of 20 matched; Tyrese Haliburton unmatched (no 2025-26 games, D22).
- Before step 4, Nathan answers O4 (minimum minutes, suggested 500), O6 (roles config: TOML recommended, no new dependency) and confirms the "Done when" table in the plan. O3 weights can start as guesses.
- Step 4: add hustle, tracking and play-type tables (O5), roles config (O6), per-100 stats, percentiles (O4), fit and value scores (O3). Analysis joins `players.csv` with `salaries.csv` on `player_id`.
- Steps 5–6 in the plan. Open questions are in [decisions.md](decisions.md#open).

## Known issues

- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- Players with no 2025-26 games (e.g. Tyrese Haliburton) aren't in NBA.com's table, so their salaries always stay unmatched (D22). Fix later via NBA.com's full player list (plan, "Ideas for later").
- Mock `salaries.csv` has no `player_id`; that's by design, since it goes through the same name matching as a real file.
- Real `age` and `minutes` arrive as decimals; mock values are whole numbers. Harmless so far.
- README opening pitch still says "trade analyzer" (D1); fix in step 6.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.

## Last verification (2026-10-26, macOS, Python 3.13.17 via uv)

| Check | Result |
| --- | --- |
| `pytest` | 54 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| Real salary file validation (`load_salaries`) | 20 rows valid |
| Real import (`import_salaries`, Nathan's machine) | Not run yet |

## Next concrete task

Merge `step-3-followups`, then Nathan runs `python -m nbavalue.import_salaries` and pastes the summary. Then answer O4/O6, confirm "Done when", and plan step 4.
