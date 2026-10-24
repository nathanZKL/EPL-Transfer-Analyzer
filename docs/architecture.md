# Architecture

How data moves through the MVP. Data flows one way, from the sources down to the app, and each step hands the next a plain CSV file. Decisions referenced as D# / O# are in [decisions.md](decisions.md).

## What exists today (step 2 in progress)

The app still reads only the committed mock CSVs. The NBA.com fetch and prepare code exists and is tested with fake responses, but has not yet run against real NBA.com, and the app doesn't read its output yet.

| Piece | File | Status |
| --- | --- | --- |
| Data labels | `nbavalue/labels.py` | ✅ Built |
| Shared column check | `nbavalue/checks.py` | ✅ Built (`require_columns`) |
| Mock data loader + validation | `nbavalue/mock_data.py` | ✅ Built (raises `ValueError` on missing columns or non-`Mock` rows) |
| NBA.com fetch | `nbavalue/fetch.py` | ✅ Built, untested against real NBA.com: base + advanced tables, 3 s pause, snapshot reuse |
| Prepare (field checks, mapping, labels) | `nbavalue/prepare.py` | ✅ Built: writes `data/processed/players.csv` with `NBA.com` label and `fetched_on` date |
| Command | `nbavalue/update_data.py` | ✅ Built: `python -m nbavalue.update_data [--refresh]` |
| Mock dataset | `data/mock/players.csv`, `data/mock/salaries.csv` | ✅ Built (columns are a first draft) |
| Streamlit app | `app.py` | ✅ Skeleton only: mock warning and two tables |
| Tests | `tests/` | ✅ 18 tests, including a headless app smoke test; fetch tests use `tests/fake_nba.py`, never the network |
| Everything else in the diagram | — | Planned |

## Technology stack

| Tool | Version | Role |
| --- | --- | --- |
| Python | 3.11+ required, verified on 3.13 | Language |
| pandas | `>=2.2,<3` (verified 2.3.3) | Tables |
| Streamlit | `>=1.40,<2` (verified 1.66.1) | Local web UI |
| pytest, ruff | `pytest>=8,<9`, `ruff>=0.6` | Tests, lint and formatting (dev only) |
| `nba_api` | `>=1.12,<2` (verified 1.12.0) | NBA.com fetch |

## Data sources

| Source | Status | Label | Notes |
| --- | --- | --- | --- |
| Mock data (`data/mock/`) | ✅ In use | `Mock` | Fictional, committed. Tests, demos, public screenshots. |
| NBA.com stats via `nba_api`, 2025-26 | Code built, first real fetch pending (step 2) | `NBA.com` + fetch date | Personal, non-commercial use, with attribution. Never committed. Fetch runs on Nathan's machine only. |
| Salary CSV | Planned (step 3) | `Reported salary` + source, URL, date | Hand-built or from an optional scraper (site still open, O1). |
| Basketball-Reference | ❌ Not used | — | Terms forbid it (D4). |

## Data flow

Solid green boxes exist as code; dashed boxes are planned or hold data that hasn't been fetched yet.

```mermaid
flowchart TD
  NBA["NBA.com stats via nba_api<br/>(Nathan's machine only)"]
  SAL["Salary CSV<br/>hand-built or optional scraper (O1)"]
  FS["nbavalue/fetch.py<br/>cached, 3 s between requests"]
  RAW[("data/raw/<br/>dated snapshots, git-ignored")]
  MOCK[("data/mock/*.csv<br/>fictional, committed")]
  LOAD["nbavalue/mock_data.py<br/>column + label checks"]
  PREP["nbavalue/prepare.py<br/>field checks, labels<br/>(salary match in step 3, O2)"]
  TABLE[("data/processed/players.csv<br/>git-ignored")]
  ROLES["config/roles.yaml<br/>role recipes (O3, O6)"]
  ANA["nbavalue analysis<br/>per-100, percentiles, fit, value"]
  APP["app.py (Streamlit, local)"]

  NBA --> FS --> RAW --> PREP
  SAL --> PREP
  PREP --> TABLE --> ANA --> APP
  ROLES --> ANA
  MOCK --> LOAD --> APP
  MOCK -.-> PREP

  classDef built fill:#d4edda,stroke:#2e7d32,color:#000
  classDef planned fill:#fff,stroke:#888,stroke-dasharray:5 5,color:#000
  class MOCK,LOAD,APP,FS,PREP built
  class NBA,SAL,RAW,TABLE,ROLES,ANA planned
```

Today the app reads mock data directly through `mock_data.py`. Once steps 2 to 4 land, mock data is meant to go through the same prepare and analysis path as real data. Exactly how is decided in step 2.

## Planned components

| Component | What it does | Step |
| --- | --- | --- |
| Hustle, tracking, play-type tables | More `fetch.TABLES` entries and mappings, added once real base/advanced output has been seen. | 2 follow-up or 4 |
| Salary import / match | Reads the salary CSV, joins each row to an NBA.com player ID. Unmatched rows are listed for a human, never silently dropped. | 3 |
| `scrape_salaries` | Optional. Writes the same CSV format, only after the site's terms and robots.txt are checked. | 3 |
| `data/processed/players.csv` | One row per player, rebuilt from raw files. Git-ignored. | 2–3 |
| `config/roles.yaml` | Six role recipes (stats and weights), editable without code changes. | 4 |
| Analysis library | Pure functions: per-100 stats, league percentiles with a minimum-minutes cut, role fit (0–100), value score. Most heavily tested part. | 4 |
| App screens | Shortlist, value chart, comparison, method page. Credits NBA.com on every screen with real stats. | 5–6 |

## Deliberately left out

A database, a backend API, cloud hosting, scheduled refreshes, Docker, user accounts and any extra caching layer (D2, D11).
