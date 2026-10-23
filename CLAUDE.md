# CLAUDE.md

Guidance for Claude when working in this repository.

## Project purpose

NBA Player Value Analyzer: a local Streamlit app that answers *"Which NBA players best fit the role I'm looking for, and who gives the most of that role per dollar of salary?"* It is a fan project, a learning project, and a public portfolio piece for the owner, Nathan (GitHub `nathanZKL`).

- **Plan (source of truth for scope):** [docs/mvp-plan.md](docs/mvp-plan.md)
- **Architecture and data flow:** [docs/architecture.md](docs/architecture.md)

Current status: step 1 of 6 (skeleton) is done. The app runs on mock data only.

## Working with Nathan

- Nathan is a beginner. Explain important decisions in plain language, with the tradeoff, before or alongside the change.
- Keep the MVP small. Do not add features, dependencies or infrastructure beyond the current build step without asking. Ideas go in the "Ideas for later" table in the plan.
- One build step = one small pull request.
- Check data limitations before proposing a feature that depends on data.

## Data-integrity rules (non-negotiable)

1. **Never invent statistics or salaries.** If data is unavailable, say so in the app and the docs.
2. **Label every value** with one of `NBA.com`, `Reported salary`, `Estimate`, `Mock` (`nbavalue/labels.py`). Real values also carry their source and date.
3. **Mock data must be obviously fictional:** names start with `Mock `, teams are not real NBA abbreviations, `season` is `MOCK`, `data_label` is `Mock`. Tests enforce this.
4. **Never commit real data.** `data/raw/` and `data/processed/` are git-ignored. NBA.com terms allow personal, non-commercial use with prominent attribution, and forbid public republishing.
5. **Credit NBA.com** on every screen that shows real stats.
6. **Don't use Basketball-Reference** (its terms forbid tools built on scraped data and using content to prompt AI).
7. **Salary scraping** is optional, personal-use only, and only from a site whose terms and robots.txt Nathan has checked. Scraped salaries are labelled `Reported salary` with the site, URL and date.
8. **Fetch politely:** cache results, pause between requests, never hammer NBA.com.
9. Estimates (fit scores, value scores) are labelled as our own estimates, never presented as facts.

## Conventions

- Python 3.11+ (tested on 3.13), pandas, Streamlit, pytest, ruff.
- Dependencies: `requirements.txt` (runtime) and `requirements-dev.txt` (adds test/lint tools). Tool settings are in `pyproject.toml`. No packaging or build step.
- Code: analysis logic lives in `nbavalue/` as plain functions with no Streamlit code; `app.py` only displays things.
- Data passes between steps as CSV files. No database, server, scheduler or Docker in the MVP.
- Validate inputs loudly: missing columns or unlabelled rows raise a clear `ValueError` rather than being silently fixed.
- Line length 100; ruff rules E, F, I, B, UP.

## Commands (verified 2026-10-23 on Python 3.13)

```bash
python3 -m venv .venv && source .venv/bin/activate   # one-time setup
pip install -r requirements-dev.txt                  # install
streamlit run app.py                                 # run the app (http://localhost:8501)
pytest                                               # tests, including a headless app smoke test
ruff check .                                         # lint
ruff format --check .                                # formatting check (use `ruff format .` to fix)
```

There is no build step. Run `pytest`, `ruff check .` and `ruff format --check .` before every commit.

## Environment notes

- The cloud development environment cannot reach NBA.com, Basketball-Reference, Spotrac or HoopsHype. Build and test with mock data there; real fetches run on Nathan's machine.
- No secrets or API keys are needed. If one is ever needed, add `.env.example` with placeholder values only; `.env` is git-ignored.
