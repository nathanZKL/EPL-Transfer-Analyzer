import pandas as pd
import pytest

from nbavalue import prepare, update_data
from nbavalue.labels import DataLabel
from tests.fake_nba import FakeClient, fake_table

BASE = {"measure_type_detailed_defense": "Base"}
ADVANCED = {"measure_type_detailed_defense": "Advanced"}


@pytest.fixture
def snapshot(tmp_path):
    folder = tmp_path / "2026-10-24"
    folder.mkdir()
    fake_table(BASE).to_csv(folder / "base.csv", index=False)
    fake_table(ADVANCED).to_csv(folder / "advanced.csv", index=False)
    return folder


def test_player_table_has_our_columns_and_labels(snapshot):
    players = prepare.build_player_table(snapshot)

    assert list(players.columns) == prepare.PLAYER_COLUMNS
    assert len(players) == 2
    assert (players["data_label"] == DataLabel.NBA_COM).all()
    assert (players["fetched_on"] == "2026-10-24").all()
    assert (players["season"] == "2025-26").all()
    assert (players["source"] == prepare.SOURCE).all()


def test_missing_nba_field_names_it_and_lists_what_arrived(snapshot):
    fake_table(ADVANCED).drop(columns="POSS").to_csv(snapshot / "advanced.csv", index=False)

    with pytest.raises(ValueError, match="advanced.csv is missing columns: POSS.*sent: PLAYER_ID"):
        prepare.build_player_table(snapshot)


def test_duplicate_player_is_refused(snapshot):
    base = fake_table(BASE)
    pd.concat([base, base.head(1)]).to_csv(snapshot / "base.csv", index=False)

    with pytest.raises(ValueError, match="same player more than once"):
        prepare.build_player_table(snapshot)


def test_tables_with_different_players_are_refused(snapshot):
    fake_table(ADVANCED).head(1).to_csv(snapshot / "advanced.csv", index=False)

    with pytest.raises(ValueError, match="1 only in base, 0 only in advanced"):
        prepare.build_player_table(snapshot)


def test_update_data_runs_end_to_end_without_network(tmp_path, capsys):
    out = tmp_path / "processed" / "players.csv"
    path = update_data.main([], client=FakeClient(), raw_dir=tmp_path / "raw", processed_path=out)

    assert path == out
    assert len(pd.read_csv(out)) == 2
    assert "UNUSED_FIELD" in capsys.readouterr().out
