# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-27

## Current objective

MVP **step 5: the app** ([mvp-plan.md](mvp-plan.md#build-steps)), branch `step-5-app`. Built and tested; Nathan checks it on his real data, then the PR is opened.

## Done

- Steps 1–4 merged (PRs #1–#6). Real data on Nathan's machine: 582 players (fetched 2026-10-26), 378 with 500+ minutes, 19 salaries imported (16 of them ranked).
- Step 5 decisions agreed 2026-10-27: D32 sidebar switch real/mock, D33 Altair for the chart (Streamlit minimum raised to 1.66), D34 salary limit keeps players with no salary.
- `nbavalue/board.py` (no Streamlit code):
  - `load_real` reads `players.csv` with normal blank handling (the `keep_default_na` trap noted in step 4), checks labels and one fetch date, and refuses a salary file naming players the player table lacks (files from different runs). A missing salary file is allowed: every salary shows as missing.
  - `load_mock` matches the mock salaries with the existing `match_salaries`.
  - `build_board`: one row per player with a `ranked` flag (500+ minutes), salary and source, and per role `fit_<role>` and `value_<role>`. Value percentiles use the whole league, so filters never change a score.
  - `shortlist` (filters), `not_ranked_with_salary`, `compare` (Basics, Role fit, Stats as text, saying why a value or rank is missing).
- `app.py`: sidebar (data switch, role with its recipe, filters); tabs Shortlist, Value chart, Compare players; NBA.com credit or mock label on every tab; loading spinner, error message with the fix, empty-filter message, missing salary shown as a dash or "not in salary file". `.streamlit/config.toml` sets a muted blue accent and hides Streamlit's "Deploy" button (local app only); a small style block trims the empty band above the page and sidebar. The team filter shows full names from nba_api's built-in team list (no network request; unknown codes such as mock teams stay as codes).
- Checked in a browser at 1440×900 and 390×844 (keyboard: skip link, data switch, role select; phone: sidebar collapses, player and fit columns pinned/visible). Screenshots are kept locally in `.playwright-mcp/` (git-ignored: they show real data).
- Ideas for later: Google search API for salaries (not a way around Spotrac's terms; see the row).

## Remaining

- Nathan runs `streamlit run app.py` on his real data and looks it over; then open the step 5 PR.
- Step 6: method page (how the numbers are made, limits, NBA.com attribution), README polish (the opening pitch still says "trade analyzer", D1), mock-data screenshots.

## Known issues

- Only 19 salaries, so value scores are rough; the value tab warns when fewer than 30 ranked players have one.
- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- Players with no 2025-26 games (e.g. Tyrese Haliburton) aren't in NBA.com's table, so their salaries stay unmatched (D22).
- The value chart's hover details need a mouse; the "Chart as a table" expander has the same numbers for keyboard and screen-reader use.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.

## Last verification (2026-10-27, macOS, Python 3.13 via uv, branch `step-5-app`)

| Check | Result |
| --- | --- |
| `pytest` | 141 passed (all app tests use temporary files, never `data/processed/`) |
| PR #7 review (local, `.claude/reviews/pr-7-review.md`) | Approve; 3 low findings, all fixed: empty player file now says so, test counts updated, layout-style guard test added |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| App on real data (`streamlit run app.py`, Claude in a headless browser) | Shortlist, value chart, comparison render; mock switch works |

## Next concrete task

Nathan reviews the app on his real data, then the step 5 PR is opened.
