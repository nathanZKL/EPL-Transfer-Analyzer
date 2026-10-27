# CLAUDE.md

Guidance for Claude when working in this repository.

## Project purpose

NBA Player Value Analyzer: a local Streamlit app that answers *"Which NBA players best fit the role I'm looking for, and who gives the most of that role per dollar of salary?"* It is a fan project, a learning project, and a public portfolio piece for the owner, Nathan (GitHub `nathanZKL`).

**MVP boundaries:** 2025-26 NBA.com stats plus a sourced salary CSV; six role fit scores; a fit-vs-salary value view; a shortlist, comparison and method page. **Out:** trades, salary-cap rules, team needs, hosting, databases. Ideas go in the plan's "Ideas for later" table.

Current status: steps 1 (skeleton) and 2 (NBA.com fetch) are merged; step 3 (salary import) is merged; step 4 is split into 4a (stats and percentiles) and 4b (roles and scores). The app still shows mock data only. See the handoff for what's next.

## Project docs: read before working

| Doc | Read it for |
| --- | --- |
| [docs/handoff.md](docs/handoff.md) | Current objective, known issues, next task. **Start here.** |
| [docs/mvp-plan.md](docs/mvp-plan.md) | Scope, features, done criteria, build steps (source of truth for scope) |
| [docs/architecture.md](docs/architecture.md) | Stack, data sources, data flow, built vs planned |
| [docs/decisions.md](docs/decisions.md) | Agreed decisions with reasons, and open questions |

Keep them current in the same pull request as the change:
- Scope or done criteria change → `mvp-plan.md`. Components, data sources or flow change → `architecture.md`. A decision is made, changed or opened → `decisions.md`. Commands change → this file and the README.
- Overwrite `handoff.md` at meaningful stopping points (end of a build step, or before stopping mid-step). It is a snapshot, not a diary.
- Don't record decisions Nathan hasn't agreed to; list them as open.

## Working with Nathan

- Nathan is a beginner. Explain important decisions in plain language, with the tradeoff, before or alongside the change.
- Keep the MVP small. Do not add features, dependencies or infrastructure beyond the current build step without asking.
- One build step = one small pull request.
- Check data limitations before proposing a feature that depends on data.

## Data-integrity rules (non-negotiable)

1. **Never invent statistics or salaries.** If data is unavailable, say so in the app and the docs. Show missing values as missing; never fill or guess them.
2. **Label every value** with one of `NBA.com`, `Reported salary`, `Estimate`, `Mock` (`nbavalue/labels.py`). Real values also carry their source and date.
3. **Mock data must be obviously fictional:** names start with `Mock `, teams are not real NBA abbreviations, `season` is `MOCK`, `data_label` is `Mock`. Tests enforce this.
4. **Never commit real data.** `data/raw/` and `data/processed/` are git-ignored. NBA.com terms allow personal, non-commercial use with prominent attribution, and forbid public republishing.
5. **Credit NBA.com** on every screen that shows real stats.
6. **Don't use Basketball-Reference** (its terms forbid tools built on scraped data and using content to prompt AI).
7. **Salary scraping** is optional, personal-use only, and only from a site whose terms and robots.txt Nathan has checked. Scraped salaries are labelled `Reported salary` with the site, URL and date.
8. **Fetch politely:** cache results, pause between requests, never hammer NBA.com.
9. **Estimates** (fit scores, value scores) are labelled as our own estimates, never presented as facts.

## Conventions

- Python 3.11+ (tested on 3.13), pandas, Streamlit, pytest, ruff.
- Dependencies: `requirements.txt` (runtime) and `requirements-dev.txt` (adds test/lint tools). Tool settings are in `pyproject.toml`. No packaging or build step.
- Code: analysis logic lives in `nbavalue/` as plain functions with no Streamlit code; `app.py` only displays things.
- Data passes between steps as CSV files. No database, server, scheduler or Docker in the MVP.
- Validate inputs loudly: missing columns or unlabelled rows raise a clear `ValueError` rather than being silently fixed.
- Tests use mock data only; never call NBA.com or salary sites from tests.
- Line length 100; ruff rules E, F, I, B, UP.

## Commands (verified 2026-10-24 on macOS, Python 3.13 via uv)

```bash
uv venv --python 3.13 .venv && source .venv/bin/activate   # one-time setup (uv, decision D16)
uv pip install -r requirements-dev.txt               # install
streamlit run app.py                                 # run the app (http://localhost:8501)
python -m nbavalue.update_data                       # fetch NBA.com stats (Nathan's machine only)
python -m nbavalue.import_salaries                   # match data/salaries/ to players (after update_data)
pytest                                               # tests, including a headless app smoke test
ruff check .                                         # lint
ruff format --check .                                # formatting check (use `ruff format .` to fix)
```

There is no build step. Run `pytest`, `ruff check .` and `ruff format --check .` before every commit.

Don't use the Mac's default `python3` (3.9.6): it fails at import (`StrEnum`). `update_data` reuses the newest saved snapshot; `--refresh` downloads again. First real run: 2026-10-24, 582 players.

## Environment notes

- The cloud development environment cannot reach NBA.com, Basketball-Reference, Spotrac or HoopsHype. Build and test with mock data there; real fetches run on Nathan's machine.
- No secrets or API keys are needed. If one is ever needed, add `.env.example` with placeholder values only; `.env` is git-ignored.
