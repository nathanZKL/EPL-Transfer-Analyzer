# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-24

## Current objective

Start MVP **step 2: NBA.com data**: a cached, rate-limited fetch of 2025-26 stats, field checks, and a clean player table ([mvp-plan.md](mvp-plan.md#build-steps)).

## Done

- Step 1 skeleton merged (PR #1, 2026-10-23): layout, `requirements*.txt`, `pyproject.toml`, data labels, labelled mock dataset with validation, Streamlit skeleton, 7 tests, README.
- Project knowledge docs (2026-10-24): `CLAUDE.md`, `docs/decisions.md`, `docs/handoff.md`. `docs/architecture.md` now separates built from planned. `docs/mvp-plan.md` has proposed done criteria. No application code changed.

## Remaining

Steps 2–6 in [mvp-plan.md](mvp-plan.md#build-steps). Open questions are in [decisions.md](decisions.md#open).

## Known issues

- **Default `python3` on Nathan's Mac is 3.9.6.** A venv built from it installs the packages, but tests fail with `ImportError: cannot import name 'StrEnum'`. Use Python 3.11+ (O7).
- **README pitch is out of date.** The opening line calls the project a trade analyzer; trades are out of MVP scope (D1).
- Mock columns are a first draft. They lack the hustle, tracking and play-type stats the starter roles need, and must be updated once step 2 confirms real field names.
- `nba_api` is not yet in `requirements.txt` (expected in step 2).

## Last verification (2026-10-24, macOS, Python 3.13.17 via `uv`, run in a throwaway venv)

| Check | Result |
| --- | --- |
| `pip install -r requirements-dev.txt` | OK (Streamlit 1.66.1, pandas 2.3.3) |
| `pytest` | 7 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 12 files already formatted |
| `streamlit run app.py` (headless) | Server started, `/_stcore/health` returned `ok` |
| Same install on Python 3.9.6 | Tests fail at import (`StrEnum`) |

## Next concrete task

1. Nathan picks a way to get Python 3.11+ (O7) and recreates `.venv`.
2. Branch for step 2. Add `nba_api` to `requirements.txt` (part of the agreed plan) and write `fetch_stats` with caching and pauses. Unit-test it against saved mock responses, not live NBA.com.
3. Nathan runs the first real fetch locally. Record the confirmed field names (O5) and update the mock columns to match.
