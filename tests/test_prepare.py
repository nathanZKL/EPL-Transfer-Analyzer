import pandas as pd
import pytest

from nbavalue import fetch, prepare, update_data
from nbavalue.labels import DataLabel
from tests.fake_nba import FakeClient, fake_table

BASE = fetch.TABLES["base"]
ADVANCED = fetch.TABLES["advanced"]
ISOLATION = fetch.TABLES["isolation"]


@pytest.fixture
def snapshot(tmp_path):
    folder = tmp_path / "2026-10-24"
    folder.mkdir()
    for table, params in fetch.TABLES.items():
        fake_table(params).to_csv(folder / f"{table}.csv", index=False)
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


def test_traded_player_rows_are_added_up(snapshot):
    # Play-type tables list a traded player once per team.
    iso = fake_table(ISOLATION)
    second_team = iso.head(1).assign(POSS=4, PTS=6)
    pd.concat([iso, second_team]).to_csv(snapshot / "isolation.csv", index=False)

    players = prepare.build_player_table(snapshot).set_index("player_id")

    assert players.loc[900101, "iso_poss"] == 1 + 4
    assert players.loc[900101, "iso_pts"] == 1 + 6
    assert players.loc[900102, "iso_poss"] == 1


def test_blank_values_stay_missing_when_rows_are_added_up(snapshot):
    # A blank cell must never turn into a 0 (CLAUDE.md rule 1).
    iso = fake_table(ISOLATION).astype({"POSS": float, "PTS": float})
    iso.loc[0, ["POSS", "PTS"]] = None
    pd.concat([iso, iso.head(1)]).to_csv(snapshot / "isolation.csv", index=False)

    players = prepare.build_player_table(snapshot).set_index("player_id")

    assert pd.isna(players.loc[900101, "iso_poss"])
    assert pd.isna(players.loc[900101, "iso_pts"])
    assert players.loc[900102, "iso_poss"] == 1


def test_player_missing_from_an_extra_table_stays_missing(snapshot):
    fake_table(ISOLATION).tail(1).to_csv(snapshot / "isolation.csv", index=False)

    players = prepare.build_player_table(snapshot).set_index("player_id")

    assert pd.isna(players.loc[900101, "iso_poss"])
    assert pd.isna(players.loc[900101, "iso_pts"])
    assert players.loc[900102, "iso_poss"] == 1
    assert len(players) == 2


def test_extra_table_with_an_unknown_player_is_refused(snapshot):
    iso = fake_table(ISOLATION)
    pd.concat([iso, iso.head(1).assign(PLAYER_ID=999)]).to_csv(
        snapshot / "isolation.csv", index=False
    )

    with pytest.raises(ValueError, match="isolation.csv lists players that base.csv doesn't: 1"):
        prepare.build_player_table(snapshot)


def test_rim_defence_uses_its_own_player_id_column(snapshot):
    fake_table(fetch.TABLES["rim_defense"]).drop(columns="CLOSE_DEF_PERSON_ID").to_csv(
        snapshot / "rim_defense.csv", index=False
    )

    with pytest.raises(ValueError, match="rim_defense.csv is missing columns: CLOSE_DEF_PERSON_ID"):
        prepare.build_player_table(snapshot)


def test_update_data_runs_end_to_end_without_network(tmp_path, capsys):
    out = tmp_path / "processed" / "players.csv"
    path = update_data.main([], client=FakeClient(), raw_dir=tmp_path / "raw", processed_path=out)

    assert path == out
    assert len(pd.read_csv(out)) == 2
    assert "UNUSED_FIELD" in capsys.readouterr().out
