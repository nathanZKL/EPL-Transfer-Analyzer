"""Fake NBA.com responses for tests. Players are fictional, like the mock dataset."""

import pandas as pd

from nbavalue.prepare import ADVANCED_COLUMNS, BASE_COLUMNS

PLAYERS = [(900101, "Mock Casey Reed", "MVM"), (900102, "Mock Dana Holt", "FTF")]


def fake_table(params: dict) -> pd.DataFrame:
    """Return a tiny table with every mapped column, plus one NBA.com column we don't use."""
    mapping = (
        BASE_COLUMNS if params["measure_type_detailed_defense"] == "Base" else ADVANCED_COLUMNS
    )
    rows = []
    for player_id, name, team in PLAYERS:
        row = {col: 1 for col in mapping}
        row |= {"PLAYER_ID": player_id, "UNUSED_FIELD": 0}
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
