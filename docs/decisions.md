# Decisions

Significant choices for this project, why they were made, and what they cost. Newest first within each section. Add a row when a decision is made or changed; don't delete old ones, mark them **Replaced** and link the new one.

Source for the 2026-10-23 entries: the MVP plan agreed with Nathan that day ([mvp-plan.md](mvp-plan.md)) and the step 1 pull request (#1).

## Agreed

| # | Decision | Why | Tradeoff |
| --- | --- | --- | --- |
| D1 | **The MVP answers one question:** which players best fit a role, and who gives the most of it per dollar. Trades, salary-cap rules, team needs and hosting are out. (2026-10-23) | Keeps the first version small enough to finish and explain. | The repo name and README pitch ("trade analyzer") promise more than v1 does. |
| D2 | **Local Streamlit app only, no hosted site.** (2026-10-23) | NBA.com terms allow personal, non-commercial use and forbid public republishing. | It can't be shared as a live link; the public portfolio shows code and mock-data screenshots. |
| D3 | **Stats come from NBA.com via `nba_api`, 2025-26 season.** (2026-10-23) | Rich stats (hustle, tracking, play types) that can measure roles directly. 2026-27 had barely started. | `nba_api` is unofficial and has no published rate limits; fetches must be cached and slow. Data is a season old. |
| D4 | **No Basketball-Reference.** (2026-10-23) | Its data-use policy forbids tools built on scraped data and using content to prompt AI. | Loses an easy, familiar source. |
| D5 | **Salaries come from a CSV, with a source, URL and date on every row, labelled `Reported salary`.** An optional scraper may fill it later. (2026-10-23) | Salaries are public facts, but the salary sites' terms for bulk use are unclear. | Building or updating the CSV can be manual work. |
| D6 | **Every value carries a label:** `NBA.com`, `Reported salary`, `Estimate` or `Mock` (`nbavalue/labels.py`). Fit and value scores are labelled as our own estimates. (2026-10-23) | Never mislead a reader about where a number came from. | Every table needs a label column and validation. |
| D7 | **Mock data is obviously fictional** (`Mock ` names, fake team codes, season `MOCK`) and enforced by tests. (2026-10-23) | Lets tests, offline demos and public screenshots run without republishing real data. | Mock columns are a first draft and must be updated once real NBA.com fields are confirmed. |
| D8 | **Real data is never committed.** `data/raw/` and `data/processed/` are git-ignored. (2026-10-23) | NBA.com terms. | Anyone cloning the repo must run the fetch themselves. |
| D9 | **Roles are not tied to positions; percentiles are league-wide** with a minimum-minutes cut. (2026-10-23) | NBA positions (G, F, C) are loose. | A guard and a centre are compared on the same scale for every role. |
| D10 | **Value score = role-fit percentile minus salary percentile.** (2026-10-23) | Simple and easy to explain to a fan. | Ignores contract length and cap context. |
| D11 | **Steps hand each other plain CSV files.** No database, backend, scheduler, Docker or extra cache layer. (2026-10-23) | About 500 players fit easily in pandas; fewer moving parts for a beginner. | No history or querying beyond what pandas does; files must be rebuilt by hand. |
| D12 | **Stack:** Python 3.11+, pandas, Streamlit, pytest, ruff. Dependencies in `requirements*.txt`, tool settings in `pyproject.toml`, no packaging. (2026-10-23) | Common, beginner-friendly tools. | `StrEnum` in `labels.py` needs 3.11+; older interpreters fail at import. |
| D13 | **Analysis logic lives in `nbavalue/` as plain functions; `app.py` only displays.** (2026-10-23) | Logic can be tested without the UI. | Slightly more files than one script. |
| D14 | **Six build steps, one small pull request each.** (2026-10-23) | Reviewable, learnable chunks. | Slower to reach a usable app with real data. |

## Open

| # | Question | Current assumption | Blocks | Who decides |
| --- | --- | --- | --- | --- |
| O1 | **Which salary site, if any, to scrape:** Spotrac or HoopsHype. | Fallback is a hand-built CSV. Nathan is checking terms and robots.txt. | Step 3 scraper (not the CSV import) | Nathan |
| O2 | **Salary-to-player matching rule.** | Normalised name plus team, with a small manual override file. | Step 3 | Nathan, in step 3 PR |
| O3 | **Role weights.** | Starting guesses in `config/roles.yaml`, tuned once real rankings exist. | Step 4 tuning | Nathan |
| O4 | **Minimum minutes for percentiles.** | 500 minutes. | Step 4 | Nathan |
| O5 | **Exact NBA.com field names for each role stat.** | To be confirmed against a real fetch. | Steps 2 and 4 | Confirmed from data in step 2 |
| O6 | **Parser for `config/roles.yaml`.** YAML needs a new dependency (e.g. PyYAML), which isn't in `requirements.txt` yet. | Not discussed. | Step 4 | Nathan (new dependencies need approval) |
| O7 | **How to get Python 3.11+ on Nathan's Mac.** The default `python3` is 3.9.6. `uv` is installed and works (see CLAUDE.md). | Not discussed. | Local setup | Nathan |
