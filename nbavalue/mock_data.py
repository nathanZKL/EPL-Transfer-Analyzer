"""Load the fictional mock dataset in data/mock/ and check it is well formed."""

from pathlib import Path

import pandas as pd

from nbavalue.checks import require_columns
from nbavalue.labels import DataLabel

MOCK_DIR = Path(__file__).resolve().parent.parent / "data" / "mock"

PLAYER_COLUMNS = [
    "player_id",
    "player_name",
    "team",
    "position",
    "age",
    "season",
    "games_played",
    "minutes",
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "fg3m",
    "fg3a",
    "data_label",
]

SALARY_COLUMNS = [
    "player_name",
    "team",
    "season",
    "salary_usd",
    "source",
    "source_url",
    "retrieved_on",
    "data_label",
]


def _load(filename: str, required: list[str]) -> pd.DataFrame:
    df = pd.read_csv(MOCK_DIR / filename, keep_default_na=False)
    require_columns(df, required, filename)
    if not (df["data_label"] == DataLabel.MOCK).all():
        raise ValueError(f"{filename} contains rows not labelled '{DataLabel.MOCK}'")
    return df


def load_players() -> pd.DataFrame:
    return _load("players.csv", PLAYER_COLUMNS)


def load_salaries() -> pd.DataFrame:
    return _load("salaries.csv", SALARY_COLUMNS)
