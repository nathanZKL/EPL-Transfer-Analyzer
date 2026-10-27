# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-26

## Current objective

MVP **step 4: analysis**, split into two PRs (D24; [mvp-plan.md](mvp-plan.md#build-steps)).
- **4a** (branch `step-4a-stats`, PR open): 7 more NBA.com tables, per-100 stats and league percentiles in `nbavalue/analysis.py`. Waiting on Nathan's `python -m nbavalue.update_data --refresh` to confirm the new field names (O5), then merge.
- **4b** (branch `step-4b-roles`, built and committed locally in a worktree, not pushed): `config/roles.toml`, `nbavalue/roles.py` with fit and value scores. Rebase onto main after 4a merges, then open its PR.

## Done

- Steps 1–3 merged (PRs #1–#4). Step 3: salary import with name matching and overrides (D18–D23). Nathan's first real import (2026-10-26): 19 of 20 rows matched; Tyrese Haliburton unmatched as expected (no 2025-26 games, D22).
- Decisions agreed 2026-10-26: step split and "Done when" confirmed (D24), 500-minute cut (D25), `config/roles.toml` with `tomllib` (D26), starting weights are Claude's guesses (D27).
- Step 4a code:
  - `fetch.TABLES` has 9 tables; each names its endpoint (`players`, `hustle`, `defense`, `tracking`, `play_type`). An old 2-table snapshot counts as incomplete, so the next run downloads all 9.
  - `prepare.EXTRA_COLUMNS` keeps counting stats only, adds up a traded player's rows, and left-joins onto the base table so omitted players stay missing. An extra table listing a player base.csv lacks stops the build.
  - `analysis.py`: `add_rates`, `qualifying`, `percentiles` (returns `player_id` + `<stat>_pctile` for the 20 stats in `analysis.STATS`; the contract 4b consumes).
  - Mock players gained the 15 new columns (fictional values).

## Remaining

- Nathan runs `update_data --refresh`. If a pull-up or play-type column name is wrong, the error lists what NBA.com sent; fix the mapping in `prepare.EXTRA_COLUMNS` (one line).
- Then check, on real data: how many 500+ minute players are missing from each play-type table (feeds O9 in 4b), and whether hustle/rim-defence tables ever list a traded player twice.
- Merge 4a, rebase 4b, reconcile docs (4b numbered its open question O9; 4b's architecture rows and test count will conflict with 4a's), open 4b's PR.
- Steps 5–6 in the plan.

## Known issues

- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- Players with no 2025-26 games (e.g. Tyrese Haliburton) aren't in NBA.com's table, so their salaries stay unmatched (D22). Fix later via NBA.com's full player list ("Ideas for later").
- Only 19 real salaries so far, so salary percentiles (4b) are rough until the salary file covers most of the league.
- Nathan's current `data/processed/players.csv` predates 4a and lacks the new columns until he refreshes.
- Step 5: load the real `players.csv` with normal NaN handling. `import_salaries` reads it with `keep_default_na=False`, which turns stat columns with blanks into text; fine for the import (id, name, team only) but `analysis.add_rates` would fail on it.
- Efficiency stats (`iso_ppp`, `roll_man_ppp`, `putback_ppp`, `pullup_fg_pct`, `rim_dfg_pct`) are ranked even on 1–2 attempts. Nathan chose to decide a per-stat minimum after seeing real data (PR #5 review).
- README opening pitch still says "trade analyzer" (D1); fix in step 6.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.

## Last verification (2026-10-26, macOS, Python 3.13.17 via uv, branch `step-4a-stats`)

| Check | Result |
| --- | --- |
| `pytest` | 71 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| Real fetch of the 7 new tables | Not run yet |

## Next concrete task

Nathan: `python -m nbavalue.update_data --refresh`, then paste the printed `*.csv columns:` lines for the new tables (and any error). Then merge 4a.
