# Architecture

How data moves through the MVP. Data flows one way, from the sources down to the app, and each step hands the next a plain CSV file. Decisions referenced as D# / O# are in [decisions.md](decisions.md).

## What exists today (MVP built: steps 1–6)

The app reads the real processed files when they exist (a sidebar switch shows the mock data instead, D32) and runs the whole analysis on them: percentiles, role fit scores and value scores. Nathan's real fetch (2026-10-26) has 582 players; 550 salaries are imported (HoopsHype figures, D36). Mock players use the same columns as the real table (D17), so every function takes either.

| Piece | File | Status |
| --- | --- | --- |
| Data labels | `nbavalue/labels.py` | ✅ Built |
| Shared column check | `nbavalue/checks.py` | ✅ Built (`require_columns`) |
| Mock data loader + validation | `nbavalue/mock_data.py` | ✅ Built (raises `ValueError` on missing columns or non-`Mock` rows) |
| NBA.com fetch | `nbavalue/fetch.py` | ✅ Built: 9 tables (base, advanced, hustle, rim defence, pull-ups, 4 play types), 3 s pause, snapshot reuse. All 9 run for real on 2026-10-26 (D28) |
| Prepare (field checks, mapping, labels) | `nbavalue/prepare.py` | ✅ Built: writes `data/processed/players.csv` with `NBA.com` label and `fetched_on` date. Extra tables keep counting stats only, check the play-type listing floor (D29), add up a traded player's rows, and leave players they omit as missing |
| Per-100 stats and percentiles | `nbavalue/analysis.py` | ✅ Built (step 4a): per-100 stats and ratios from season totals; 0–100 league percentiles among players with 500+ minutes (D25); opponent rim FG% flipped; missing stays missing, except play-type volume blanks (fewer than 10 possessions) rank tied for last (D29); efficiency needs 25 plays / 50 pull-ups (D30) / 150 threes (D31) |
| Command | `nbavalue/update_data.py` | ✅ Built: `python -m nbavalue.update_data [--refresh]` |
| Salary check and match | `nbavalue/salaries.py` | ✅ Built: validates the salary CSV, matches by normalised name with team as tie-break and an override file (D18–D21); digits-only salaries and no unused overrides (D23); players with no 2025-26 games stay unmatched (D22) |
| Salary command | `nbavalue/import_salaries.py` | ✅ Built: `python -m nbavalue.import_salaries` writes `data/processed/salaries.csv` and `salary_unmatched.csv`. Run on 583 real salaries (D36): 550 matched, 12 by override |
| Role recipes | `config/roles.toml` | ✅ Built (step 4b): six starter roles, each a list of stats with weights; Claude's starting guesses (D27), read with Python's built-in `tomllib` (no new dependency) |
| Fit and value scores | `nbavalue/roles.py` | ✅ Built (step 4b): `load_roles` checks the config loudly; `fit_scores` = weighted average of a player's stat percentiles per role (a stat with no percentile is left out and the other weights count for more, D29); `value_scores` = fit percentile minus salary percentile among players with both (D10). Both labelled `Estimate` |
| What the app shows | `nbavalue/board.py` | ✅ Built (step 5): loads real files (normal blank handling, label checks, refuses salaries from a different run) or the mock set; joins stats, salaries and scores into one row per player with a `ranked` flag (500+ minutes); filters the shortlist without changing scores (D34); builds the comparison text. No Streamlit code |
| Mock dataset | `data/mock/players.csv`, `data/mock/salaries.csv` | ✅ Built; players use the real table's columns (D17) |
| Streamlit app | `app.py`, `.streamlit/config.toml` | ✅ Built (step 5): sidebar (data switch D32, role, filters); tabs Shortlist, Value chart (Altair, D33) and Compare players; NBA.com credit or mock label on every tab; loading, empty, error and missing-data messages |
| Method page | `docs/method.md` | ✅ Built (step 6, D35): how every number is made, its limits, NBA.com attribution. Its recipes and cut-offs are checked against the code by `tests/test_method_doc.py` |
| Tests | `tests/` | ✅ 157 tests, including headless app runs on temporary files (never the real data folder) and a check that the app's layout style still matches this Streamlit version; fetch tests use `tests/fake_nba.py`, never the network |
| Everything else in the diagram | — | Planned |

## Technology stack

| Tool | Version | Role |
| --- | --- | --- |
| Python | 3.11+ required, verified on 3.13 | Language |
| pandas | `>=2.2,<3` (verified 2.3.3) | Tables |
| Streamlit | `>=1.66,<2` (verified 1.66.1) | Local web UI |
| Altair | `>=5,<7` (verified 6.3.0; comes with Streamlit) | Value chart (D33) |
| pytest, ruff | `pytest>=8,<9`, `ruff>=0.6` | Tests, lint and formatting (dev only) |
| `nba_api` | `>=1.12,<2` (verified 1.12.0) | NBA.com fetch |

## Data sources

| Source | Status | Label | Notes |
| --- | --- | --- | --- |
| Mock data (`data/mock/`) | ✅ In use | `Mock` | Fictional, committed. Tests, demos, public screenshots. |
| NBA.com stats via `nba_api`, 2025-26 | ✅ Base + advanced fetched on Nathan's machine (step 2) | `NBA.com` + fetch date | Personal, non-commercial use, with attribution. Never committed. Fetch runs on Nathan's machine only. |
| Salary CSV (`data/salaries/`, git-ignored) | ✅ Import built (step 3); the file is converted once from a dataset of HoopsHype figures (D36) | `Reported salary` + source, URL, date | An optional scraper could fill it later (site still open, O1). |
| Basketball-Reference | ❌ Not used | — | Terms forbid it (D4). |

## Data flow

Solid green boxes exist; dashed boxes are planned. Real data lives only on Nathan's machine.

```mermaid
flowchart TD
  NBA["NBA.com stats via nba_api<br/>(Nathan's machine only)"]
  SAL[("data/salaries/<br/>salary CSV + overrides, git-ignored")]
  SALM["nbavalue/salaries.py<br/>checks, name match (D18)"]
  STAB[("data/processed/salaries.csv<br/>+ salary_unmatched.csv")]
  FS["nbavalue/fetch.py<br/>cached, 3 s between requests"]
  RAW[("data/raw/<br/>dated snapshots, git-ignored")]
  MOCK[("data/mock/*.csv<br/>fictional, committed")]
  LOAD["nbavalue/mock_data.py<br/>column + label checks"]
  PREP["nbavalue/prepare.py<br/>field checks, labels"]
  TABLE[("data/processed/players.csv<br/>git-ignored")]
  ROLES["config/roles.toml<br/>role recipes (O3)"]
  ANA["nbavalue analysis + roles<br/>per-100, percentiles, fit, value"]
  BOARD["nbavalue/board.py<br/>load, join, filter, compare"]
  APP["app.py (Streamlit, local)"]

  NBA --> FS --> RAW --> PREP
  PREP --> TABLE --> BOARD
  SAL --> SALM --> STAB --> BOARD
  TABLE --> SALM
  ROLES --> ANA
  MOCK --> LOAD --> BOARD
  BOARD <--> ANA
  BOARD --> APP
  MOCK -.-> PREP

  classDef built fill:#d4edda,stroke:#2e7d32,color:#000
  class MOCK,LOAD,APP,FS,PREP,SALM built
  class NBA,RAW,TABLE,SAL,STAB built
  class ROLES,ANA,BOARD built
```

The app asks `board.py` for either the real files or the mock set (sidebar switch, D32). Because mock players share the real table's columns (D17), the same analysis runs on both.

## Planned components

| Component | What it does | Step |
| --- | --- | --- |
| `scrape_salaries` | Optional. Writes the same CSV format, only after the site's terms and robots.txt are checked (O1). | Later |

## Deliberately left out

A database, a backend API, cloud hosting, scheduled refreshes, Docker, user accounts and any extra caching layer (D2, D11).
