"""Download 2025-26 player stats from NBA.com into dated, git-ignored snapshots.

Politeness rules (CLAUDE.md): reuse what is already downloaded, pause between requests,
and only ever run on Nathan's machine. Tests pass in a fake client instead of NBA.com.
"""

import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd

SEASON = "2025-26"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PAUSE_SECONDS = 3

# Each table is one request to NBA.com's league-wide player stats endpoint.
TABLES = {
    "base": {"measure_type_detailed_defense": "Base"},
    "advanced": {"measure_type_detailed_defense": "Advanced"},
}

Client = Callable[[dict], pd.DataFrame]


def nba_api_client(params: dict) -> pd.DataFrame:
    """Fetch one table of regular-season season totals for every player from NBA.com."""
    from nba_api.stats.endpoints import leaguedashplayerstats  # imported here: network code

    endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        season_type_all_star="Regular Season",
        per_mode_detailed="Totals",
        timeout=60,
        **params,
    )
    return endpoint.get_data_frames()[0]


def snapshot_dir(fetched_on: date, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / SEASON / fetched_on.isoformat()


def latest_snapshot(raw_dir: Path = RAW_DIR) -> Path | None:
    """The newest snapshot folder that holds every table, or None if there isn't one."""
    season_dir = raw_dir / SEASON
    if not season_dir.is_dir():
        return None
    complete = [
        d
        for d in season_dir.iterdir()
        if d.is_dir() and all((d / f"{table}.csv").exists() for table in TABLES)
    ]
    return max(complete, default=None)


def fetch_all(
    client: Client = nba_api_client,
    raw_dir: Path = RAW_DIR,
    today: date | None = None,
    refresh: bool = False,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    """Make sure a complete snapshot exists and return its folder.

    Reuses the newest complete snapshot unless refresh is True. Otherwise downloads
    into today's folder, skipping tables already saved there, so an interrupted run
    can be resumed without repeating requests.
    """
    if not refresh:
        existing = latest_snapshot(raw_dir)
        if existing is not None:
            return existing

    target = snapshot_dir(today or date.today(), raw_dir)
    target.mkdir(parents=True, exist_ok=True)
    requests_made = 0
    for table, params in TABLES.items():
        path = target / f"{table}.csv"
        if path.exists() and not refresh:
            continue
        if requests_made:
            sleep(PAUSE_SECONDS)
        df = client(params)
        requests_made += 1
        if df.empty:
            raise ValueError(f"NBA.com returned no rows for the {table} table")
        df.to_csv(path, index=False)
    return target
