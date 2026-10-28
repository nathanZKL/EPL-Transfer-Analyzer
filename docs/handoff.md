# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-27

## Current objective

MVP **step 6: method page and README polish** ([mvp-plan.md](mvp-plan.md#build-steps)), branch `step-6-method-readme`. Built and tested; Nathan reviews, then the PR is opened. With it the MVP is complete.

## Done

- Steps 1–5 merged (PRs #1–#7). Real data on Nathan's machine: 582 players (fetched 2026-10-26), 378 with 500+ minutes, 19 salaries imported (16 of them ranked).
- Step 6 decision agreed 2026-10-27: D35 method page as Markdown (`docs/method.md`), three committed mock-data screenshots in `docs/images/`.
- `docs/method.md`: data sources (the nine NBA.com tables), rates, the 500-minute cut, percentiles and the minimum-attempts table, role recipes with a worked example, the value score, limits, NBA.com attribution and terms.
- `tests/test_method_doc.py` checks the page's role recipes, minutes cut, minimum attempts, play-type listing floor and the "fewer than 30 salaries" warning against the code; changing a weight in `config/roles.toml` without updating the page fails a test (checked).
- README rewritten: the opening said "trade analyzer" (D1); it now states the role/value question, MVP status, the three screenshots, attribution and a link to the method page.
- Screenshots taken at 1440×900 with the sidebar switch on mock data (checked: only `Mock` players, teams and salaries visible).
- Fix found while taking them: the shortlist's Salary source column showed "Mock," with a trailing comma (mock salaries have no date). `board.salary_source` (was `_salary_source`) now leaves out blank parts and the shortlist uses it, so both screens word it the same.

## Remaining

- Nathan reviews `docs/method.md`, the README and the screenshots; then open the step 6 PR.
- Not done, needs Nathan's OK: the GitHub repository description describes a different project ("evaluating Premier League transfer targets..."). It is changed on GitHub (`gh repo edit --description`), not in the code.

## Known issues

- Only 19 salaries, so value scores are rough; the value tab warns when fewer than 30 ranked players have one.
- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- Players with no 2025-26 games (e.g. Tyrese Haliburton) aren't in NBA.com's table, so their salaries stay unmatched (D22).
- The value chart's hover details need a mouse; the "Chart as a table" expander has the same numbers for keyboard and screen-reader use.
- Screenshots must be retaken by hand when the screens change.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.
- Still open: O1 (salary site to scrape, if any) and O3 (final role weights).

## Last verification (2026-10-27, macOS, Python 3.13 via uv, branch `step-6-method-readme`)

| Check | Result |
| --- | --- |
| `pytest` | 157 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Clean |
| App on mock data (`streamlit run app.py`, Claude in a headless browser) | Shortlist, value chart and comparison render; Salary source reads "Mock" |

## Next concrete task

Nathan reviews step 6, then the PR is opened. After that the MVP is done; the next work would come from O3 (tuning role weights on real rankings) or the plan's "Ideas for later".
