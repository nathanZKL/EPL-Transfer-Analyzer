from datetime import date

import pandas as pd
import pytest

from nbavalue import fetch
from tests.fake_nba import FakeClient

DAY_1 = date(2026, 10, 24)
DAY_2 = date(2026, 10, 25)


@pytest.fixture
def client():
    return FakeClient()


@pytest.fixture
def pauses():
    return []


def run(client, raw_dir, pauses, today=DAY_1, refresh=False):
    return fetch.fetch_all(
        client=client, raw_dir=raw_dir, today=today, refresh=refresh, sleep=pauses.append
    )


def test_first_run_saves_every_table_in_a_dated_folder(client, tmp_path, pauses):
    snapshot = run(client, tmp_path, pauses)

    assert snapshot == tmp_path / "2025-26" / "2026-10-24"
    for table in fetch.TABLES:
        assert not pd.read_csv(snapshot / f"{table}.csv").empty
    assert len(client.calls) == len(fetch.TABLES)


def test_pauses_between_requests_but_not_before_the_first(client, tmp_path, pauses):
    run(client, tmp_path, pauses)

    assert pauses == [fetch.PAUSE_SECONDS] * (len(fetch.TABLES) - 1)


def test_second_run_reuses_the_saved_snapshot(client, tmp_path, pauses):
    first = run(client, tmp_path, pauses, today=DAY_1)
    second = run(client, tmp_path, pauses, today=DAY_2)

    assert second == first
    assert len(client.calls) == len(fetch.TABLES)


def test_refresh_downloads_a_new_snapshot(client, tmp_path, pauses):
    run(client, tmp_path, pauses, today=DAY_1)
    second = run(client, tmp_path, pauses, today=DAY_2, refresh=True)

    assert second.name == "2026-10-25"
    assert len(client.calls) == 2 * len(fetch.TABLES)
    assert fetch.latest_snapshot(tmp_path) == second


def test_interrupted_run_resumes_without_repeating_requests(client, tmp_path, pauses):
    folder = fetch.snapshot_dir(DAY_1, tmp_path)
    folder.mkdir(parents=True)
    pd.DataFrame({"PLAYER_ID": [1]}).to_csv(folder / "base.csv", index=False)

    run(client, tmp_path, pauses)

    assert client.calls == [fetch.TABLES[t] for t in fetch.TABLES if t != "base"]
    assert pauses == [fetch.PAUSE_SECONDS] * (len(fetch.TABLES) - 2)


def test_snapshot_from_before_the_extra_tables_is_not_reused(client, tmp_path, pauses):
    # A step-2 snapshot holds only base and advanced, so the next run downloads everything.
    old = fetch.snapshot_dir(DAY_1, tmp_path)
    old.mkdir(parents=True)
    for table in ["base", "advanced"]:
        pd.DataFrame({"PLAYER_ID": [1]}).to_csv(old / f"{table}.csv", index=False)

    snapshot = run(client, tmp_path, pauses, today=DAY_2)

    assert snapshot.name == "2026-10-25"
    assert len(client.calls) == len(fetch.TABLES)


def test_every_table_names_a_known_endpoint():
    assert {params["endpoint"] for params in fetch.TABLES.values()} == {
        "players",
        "hustle",
        "defense",
        "tracking",
        "play_type",
    }


def test_empty_response_stops_with_clear_error(tmp_path, pauses):
    with pytest.raises(ValueError, match="no rows for the base table"):
        run(lambda params: pd.DataFrame(), tmp_path, pauses)
