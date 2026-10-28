import pytest

from nbavalue import mock_data, salaries
from nbavalue.labels import DataLabel


@pytest.fixture
def real_files(tmp_path):
    """Mock players and salaries written as if they were the real processed files, to test
    the real-data path without real data. Names stay fictional ('Mock ...')."""
    players = mock_data.load_players()
    players["data_label"] = str(DataLabel.NBA_COM)
    players["fetched_on"] = "2026-01-01"
    players.loc[0, ["iso_poss", "iso_pts"]] = None  # a player NBA.com's isolation table omits
    pay, _ = salaries.match_salaries(mock_data.load_salaries(), mock_data.load_players())
    pay["data_label"] = str(DataLabel.REPORTED_SALARY)
    players_path, salaries_path = tmp_path / "players.csv", tmp_path / "salaries.csv"
    players.to_csv(players_path, index=False)
    pay.to_csv(salaries_path, index=False)
    return players_path, salaries_path
