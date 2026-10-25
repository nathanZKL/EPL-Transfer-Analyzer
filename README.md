# NBA-Player-Value-Analyzer
An NBA trade analyzer that evaluates potential trades and player acquisitions using player performance, team needs, roster fit, and contract value to help identify moves that make sense for each team.

> **Status: step 3 of 6.** The app still shows **mock data only**: fictional players, teams and salaries. Commands to fetch real NBA.com stats and import salaries exist, but the app doesn't read their output yet.

## What the first version (MVP) will do

Answer one question: *which NBA players best fit the role I'm looking for, and who gives the most of that role per dollar of salary?*

- Role fit scores (0–100) for six roles, such as rim protector and 3-and-D wing
- A value view: role fit against reported salary
- A shortlist with filters, and side-by-side player comparison

Trades, salary-cap rules and team-needs analysis are planned for after the MVP. The full plan, including what the data can and can't support, is in [docs/mvp-plan.md](docs/mvp-plan.md), and the data flow is in [docs/architecture.md](docs/architecture.md).

## Data and labels

Every value the app shows carries a label:

| Label | Meaning |
| --- | --- |
| `NBA.com` | Official stats from NBA.com, with the date fetched (coming in step 2) |
| `Reported salary` | A salary from a named public source, with its link and date (step 3) |
| `Estimate` | Something this app calculates, such as the value score (step 4) |
| `Mock` | Fictional data for testing and demos. See [data/mock/README.md](data/mock/README.md) |

Real data is downloaded to your own machine and is **never committed** to this repo (`data/raw/` and `data/processed/` are git-ignored). NBA.com's [terms](https://www.nba.com/terms) allow personal, non-commercial use with attribution, but not public republishing. (`data/salaries/` is git-ignored too.)

## Setup

You need [uv](https://docs.astral.sh/uv/), which downloads the right Python (3.13) for you. The project needs Python 3.11 or newer; an older system `python3` won't work.

```bash
# 1. Get the code
git clone https://github.com/nathanZKL/NBA-Player-Value-Analyzer.git
cd NBA-Player-Value-Analyzer

# 2. Create a virtual environment: a private folder of packages just for this project
uv venv --python 3.13 .venv

# 3. Turn it on (do this every time you open a new terminal)
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 4. Install the packages
uv pip install -r requirements-dev.txt
```

## Run the app

```bash
streamlit run app.py
```

Your browser opens at http://localhost:8501. You should see a yellow **MOCK DATA** warning above two tables of fictional players and salaries. Press `Ctrl+C` in the terminal to stop it.

## Fetch real NBA.com stats (optional, your own machine only)

```bash
python -m nbavalue.update_data
```

This downloads 2025-26 player stats from NBA.com into `data/raw/2025-26/<date>/` (two requests, a few seconds apart) and builds `data/processed/players.csv`. Running it again reuses the saved files; add `--refresh` to download again. Both folders are git-ignored: NBA.com's terms allow personal use but not republishing. The app doesn't read this file yet.

## Import salaries (optional, your own machine only)

Salaries come from a CSV you make yourself, with a source on every row. Fetch the NBA.com stats first, then:

1. Create `data/salaries/salaries_2025-26.csv` with these columns (the folder is git-ignored):

   ```csv
   player_name,team,season,salary_usd,source,source_url,retrieved_on,data_label
   Example Player,BOS,2025-26,12500000,Site name,https://example.com/page,2026-10-24,Reported salary
   ```

   `salary_usd` is whole dollars. `retrieved_on` is the date you read it (YYYY-MM-DD). Every row needs a source and link.
2. Run:

   ```bash
   python -m nbavalue.import_salaries
   ```

   It matches each row to an NBA.com player by name (accents, capitals, punctuation and Jr./III are ignored; the team only decides between players with the same name). It writes `data/processed/salaries.csv` and lists rows it couldn't match, with suggestions, in `data/processed/salary_unmatched.csv`.
3. For a row that didn't match (often a nickname), add it to `data/salaries/overrides.csv` with the player's NBA.com ID from the suggestions, and run the command again:

   ```csv
   player_name,team,player_id,note
   Nic Example,BKN,1234567,listed as Nicolas on NBA.com
   ```

Players without a salary are shown as missing, never guessed.

## Check the code

```bash
pytest              # run the tests
ruff check .        # look for common mistakes
ruff format .       # tidy the formatting
```

## Project layout

```
app.py               Streamlit app (the screen you see)
nbavalue/            Python code the app uses
  labels.py          The data labels above
  mock_data.py       Loads and checks the mock data
  fetch.py           Downloads NBA.com stats politely, with a cache
  prepare.py         Checks and labels them as one row per player
  update_data.py     The command that runs fetch + prepare
  salaries.py        Checks the salary CSV and matches it to players
  import_salaries.py The command that imports salaries
data/mock/           Fictional data, committed to the repo
tests/               Automated checks
docs/                Plan, architecture, decisions, handoff
CLAUDE.md            Instructions for Claude when working on this repo
```

No configuration or API keys are needed. NBA.com stats don't need a key, so there is no `.env` file yet.

## License

MIT. See [LICENSE](LICENSE).
