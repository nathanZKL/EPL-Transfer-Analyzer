# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-26

## Current objective

MVP **step 4: analysis**, split into two PRs (D24; [mvp-plan.md](mvp-plan.md#build-steps)).
- **4a** (PR #5, branch `step-4a-stats`): ready for Nathan to merge. Real fetch done, field names confirmed (D28).
- **4b** (branch `step-4b-roles`, stacked on 4a): `config/roles.toml`, `nbavalue/roles.py` (fit and value scores), plus D29 (missing stats) and D30 (minimum attempts) in `analysis.py` and `roles.py`. PR opened against main; it shows 4a's commits too until PR #5 merges.

## Done

- Steps 1–3 merged (PRs #1–#4). Step 3: salary import with name matching and overrides (D18–D23). Nathan's first real import (2026-10-26): 19 of 20 rows matched; Tyrese Haliburton unmatched as expected (no 2025-26 games, D22).
- Decisions agreed 2026-10-26/27: D29 missing stats in role scores, D30 minimum attempts, D31 150 threes for 3P%; step split and "Done when" confirmed (D24), 500-minute cut (D25), `config/roles.toml` with `tomllib` (D26), starting weights are Claude's guesses (D27).
- Step 4a code:
  - `fetch.TABLES` has 9 tables; each names its endpoint (`players`, `hustle`, `defense`, `tracking`, `play_type`). An old 2-table snapshot counts as incomplete, so the next run downloads all 9.
  - `prepare.EXTRA_COLUMNS` keeps counting stats only, adds up a traded player's rows, and left-joins onto the base table so omitted players stay missing. An extra table listing a player base.csv lacks stops the build.
  - `analysis.py`: `add_rates`, `qualifying`, `percentiles` (returns `player_id` + `<stat>_pctile` for the 20 stats in `analysis.STATS`; the contract 4b consumes).
  - Mock players gained the 15 new columns (fictional values).
- Real fetch, 2026-10-26 (9 tables, 582 players, 378 with 500+ minutes). Findings:
  - Hustle, rim defence and pull-ups list each player once. Play types list traded players once per team (PnR ball handler 28, isolation 17, roll man 3), added up as designed.
  - Play-type tables only list players with **10+ possessions** of that type (minimum is exactly 10 in all four). So a missing play-type value means "fewer than 10", not "unknown".
  - Missing among the 378 qualifying players: isolation 125, roll man 129, putbacks 93, PnR ball handler 90, 3P% 10 (no attempts), pull-up FG% 4.
  - Small samples: under 25 attempts for isolation 72, roll man 107, putbacks 111, pull-ups 93 of the players with a value; rim defence 0 (min 32).

## Remaining

- Merge PR #5, then 4b's PR.
- Step 5: show the 3 salaried players under 500 minutes as "not ranked", not hidden (PR #6 review).
- Steps 5–6 in the plan.

## Known issues

- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- Players with no 2025-26 games (e.g. Tyrese Haliburton) aren't in NBA.com's table, so their salaries stay unmatched (D22). Fix later via NBA.com's full player list ("Ideas for later").
- Only 19 real salaries so far, so salary percentiles (4b) are rough until the salary file covers most of the league.
- Step 5: load the real `players.csv` with normal NaN handling. `import_salaries` reads it with `keep_default_na=False`, which turns stat columns with blanks into text; fine for the import (id, name, team only) but `analysis.add_rates` would fail on it.
- README opening pitch still says "trade analyzer" (D1); fix in step 6.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.

## Last verification (2026-10-26, macOS, Python 3.13.17 via uv, branch `step-4a-stats`)

| Check | Result |
| --- | --- |
| `pytest` | 107 passed (branch `step-4b-roles`) |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| Real fetch (`update_data --refresh`, Nathan) | 9 tables, 582 players, all fields mapped |

## Next concrete task

Nathan merges PR #5, then reviews and merges the 4b PR. Then step 5 (app screens).
