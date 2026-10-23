import pandas as pd
import pytest

from nbavalue import mock_data
from nbavalue.labels import DataLabel

REAL_NBA_TEAMS = set(
    "ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM "
    "MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS".split()
)


@pytest.fixture
def players():
    return mock_data.load_players()


@pytest.fixture
def salaries():
    return mock_data.load_salaries()


def test_every_row_is_labelled_mock(players, salaries):
    assert (players["data_label"] == DataLabel.MOCK).all()
    assert (salaries["data_label"] == DataLabel.MOCK).all()


def test_players_are_obviously_fictional(players, salaries):
    assert players["player_name"].str.startswith("Mock ").all()
    assert salaries["player_name"].str.startswith("Mock ").all()
    assert not set(players["team"]) & REAL_NBA_TEAMS
    assert (players["season"] == "MOCK").all()


def test_player_ids_are_unique(players):
    assert players["player_id"].is_unique


def test_stats_are_plausible(players):
    stat_cols = "games_played minutes points rebounds assists steals blocks turnovers".split()
    stat_cols += ["fg3m", "fg3a"]
    assert (players[stat_cols] >= 0).all().all()
    assert (players["games_played"] <= 82).all()
    assert (players["minutes"] <= players["games_played"] * 48).all()
    assert (players["fg3m"] <= players["fg3a"]).all()


def test_every_salary_belongs_to_a_mock_player(players, salaries):
    player_keys = set(zip(players["player_name"], players["team"], strict=True))
    salary_keys = set(zip(salaries["player_name"], salaries["team"], strict=True))
    assert salary_keys <= player_keys
    assert (salaries["salary_usd"] > 0).all()


def test_missing_column_gives_clear_error():
    df = pd.DataFrame({"player_name": ["Mock X"]})
    with pytest.raises(ValueError, match="missing columns: team"):
        mock_data.require_columns(df, ["player_name", "team"], "example.csv")
