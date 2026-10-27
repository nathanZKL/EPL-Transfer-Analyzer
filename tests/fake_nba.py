"""Fake NBA.com responses for tests. Players are fictional, like the mock dataset."""

import pandas as pd

from nbavalue.fetch import TABLES
from nbavalue.prepare import ADVANCED_COLUMNS, BASE_COLUMNS, EXTRA_COLUMNS

PLAYERS = [(900101, "Mock Casey Reed", "MVM"), (900102, "Mock Dana Holt", "FTF")]
MAPPINGS = {"base": BASE_COLUMNS, "advanced": ADVANCED_COLUMNS, **EXTRA_COLUMNS}


def table_name(params: dict) -> str:
    return next(name for name, settings in TABLES.items() if settings == params)


def fake_table(params: dict) -> pd.DataFrame:
    """Return a tiny table with every mapped column, plus one NBA.com column we don't use."""
    mapping = MAPPINGS[table_name(params)]
    id_column = next(col for col, ours in mapping.items() if ours == "player_id")
    rows = []
    for player_id, name, team in PLAYERS:
        row = {col: 1 for col in mapping}
        row |= {id_column: player_id, "UNUSED_FIELD": 0}
        if "PLAYER_NAME" in mapping:
            row |= {"PLAYER_NAME": name, "TEAM_ABBREVIATION": team}
        rows.append(row)
    return pd.DataFrame(rows)


class FakeClient:
    """Records every request so tests can check nothing extra hit NBA.com."""

    def __init__(self):
        self.calls: list[dict] = []

    def __call__(self, params: dict) -> pd.DataFrame:
        self.calls.append(params)
        return fake_table(params)
