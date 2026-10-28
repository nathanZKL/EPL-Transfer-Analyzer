import dataclasses
import math

import pandas as pd
import pytest

from nbavalue import analysis, board, roles

ROLES = roles.load_roles()


@pytest.fixture
def mock():
    return board.load_mock()


def without_salary(data, name):
    ids = data.players.loc[data.players["player_name"] == name, "player_id"]
    return dataclasses.replace(data, salaries=data.salaries[~data.salaries["player_id"].isin(ids)])


def with_minutes(data, name, minutes):
    players = data.players.copy()
    players.loc[players["player_name"] == name, "minutes"] = minutes
    return dataclasses.replace(data, players=players)


def test_mock_dataset_is_labelled_mock_and_every_salary_matches(mock):
    assert mock.is_mock and mock.season == "MOCK"
    assert len(mock.salaries) == len(mock.players) == 12
    assert list(mock.salaries.columns) == ["player_id", *board.SALARY_INFO]


def test_board_has_one_row_per_player_with_fit_and_value_for_every_role(mock):
    table = board.build_board(mock, ROLES)
    assert len(table) == len(mock.players) and table["player_id"].is_unique
    for key in ROLES:
        assert table[board.fit_column(key)].between(0, 100).all()
        assert table[board.value_column(key)].notna().all()


def test_player_under_the_minutes_cut_is_kept_but_not_ranked(mock):
    data = with_minutes(mock, "Mock Avery Stone", analysis.MIN_MINUTES - 1)
    row = board.build_board(data, ROLES).set_index("player_name").loc["Mock Avery Stone"]
    assert not row["ranked"]
    assert math.isnan(row[board.fit_column("connector")])
    assert math.isnan(row[board.value_column("connector")])
    assert row["salary_usd"] == 38_500_000  # the salary is still shown


def test_player_without_salary_keeps_a_fit_score_and_a_missing_value(mock):
    data = without_salary(mock, "Mock Bruno Vale")
    row = board.build_board(data, ROLES).set_index("player_name").loc["Mock Bruno Vale"]
    assert row["ranked"] and not math.isnan(row[board.fit_column("connector")])
    assert math.isnan(row["salary_usd"]) and math.isnan(row[board.value_column("connector")])


def test_shortlist_is_best_fit_first_and_only_ranked_players(mock):
    data = with_minutes(mock, "Mock Avery Stone", 100)
    listed = board.shortlist(board.build_board(data, ROLES), "rim_protector")
    assert "Mock Avery Stone" not in set(listed["player_name"])
    assert listed["fit_score"].is_monotonic_decreasing
    assert len(listed) == 11


def test_filters_leave_out_teams_older_players_and_low_minutes(mock):
    table = board.build_board(mock, ROLES)
    listed = board.shortlist(
        table, "connector", board.Filters(exclude_teams=("MVM",), max_age=30, min_minutes=2000)
    )
    assert not listed.empty
    assert "MVM" not in set(listed["team"])
    assert (listed["age"] <= 30).all() and (listed["minutes"] >= 2000).all()


def test_salary_limit_keeps_players_whose_salary_is_missing(mock):
    table = board.build_board(without_salary(mock, "Mock Elio Marsh"), ROLES)  # no salary now
    listed = board.shortlist(table, "connector", board.Filters(max_salary=10_000_000))
    assert "Mock Elio Marsh" in set(listed["player_name"])
    assert (listed["salary_usd"].dropna() <= 10_000_000).all()
    assert "Mock Ira Bishop" not in set(listed["player_name"])  # $41.0M


def test_filters_never_change_a_players_scores(mock):
    table = board.build_board(mock, ROLES)
    everyone = board.shortlist(table, "shot_creator").set_index("player_id")
    some = board.shortlist(table, "shot_creator", board.Filters(exclude_teams=("FTF", "SPS")))
    for row in some.itertuples():
        assert row.value_score == everyone.at[row.player_id, "value_score"]


def test_not_ranked_with_salary_lists_salaried_players_under_the_cut(mock):
    data = with_minutes(mock, "Mock Harlan Cole", 120)
    unranked = board.not_ranked_with_salary(board.build_board(data, ROLES))
    assert list(unranked["player_name"]) == ["Mock Harlan Cole"]


def test_real_files_load_with_blank_stats_as_missing_numbers(real_files):
    data = board.load_real(*real_files)
    assert not data.is_mock and data.fetched_on == "2026-01-01" and data.salary_file_found
    assert data.players["iso_poss"].dtype == float and data.players["iso_poss"].isna().sum() == 1
    assert len(board.build_board(data, ROLES)) == 12


def test_missing_salary_file_means_no_salaries_not_an_error(real_files, tmp_path):
    data = board.load_real(real_files[0], tmp_path / "not_there.csv")
    assert not data.salary_file_found and data.salaries.empty
    table = board.build_board(data, ROLES)
    assert table["salary_usd"].isna().all() and table[board.value_column("connector")].isna().all()
    assert board.salary_range(table) is None


def test_missing_player_table_says_which_command_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="update_data"):
        board.load_real(tmp_path / "players.csv", tmp_path / "salaries.csv")


def test_empty_player_table_says_so_and_how_to_fix_it(real_files):
    players_path, salaries_path = real_files
    pd.read_csv(players_path).head(0).to_csv(players_path, index=False)
    with pytest.raises(ValueError, match="has no players.*update_data --refresh"):
        board.load_real(players_path, salaries_path)


def test_salaries_from_a_different_run_are_refused(real_files):
    players_path, salaries_path = real_files
    pay = pd.read_csv(salaries_path)
    pay.loc[0, "player_id"] = 123
    pay.to_csv(salaries_path, index=False)
    with pytest.raises(ValueError, match="import_salaries"):
        board.load_real(players_path, salaries_path)


def test_real_files_with_wrong_labels_are_refused(real_files):
    players_path, salaries_path = real_files
    players = pd.read_csv(players_path)
    players.loc[0, "data_label"] = "Mock"
    players.to_csv(players_path, index=False)
    with pytest.raises(ValueError, match="not labelled 'NBA.com'"):
        board.load_real(players_path, salaries_path)


def test_compare_gives_basics_role_fit_and_stats_per_player(mock):
    table = board.build_board(mock, ROLES)
    ids = list(mock.players["player_id"][:3])
    tables = board.compare(mock, table, ids, ROLES)
    assert list(tables) == ["Basics", "Role fit", "Stats"]
    names = [board.player_label(row) for _, row in mock.players.head(3).iterrows()]
    for part in tables.values():
        assert list(part.columns[1:]) == names
    assert len(tables["Role fit"]) == len(ROLES)
    assert len(tables["Stats"]) == len(analysis.STATS)
    salary_row = tables["Basics"].set_index("Measure").loc["Salary"]
    assert salary_row.iloc[0] == "$38,500,000"  # Mock Avery Stone


def test_compare_refuses_players_who_are_not_ranked(mock):
    data = with_minutes(mock, "Mock Avery Stone", 10)
    table = board.build_board(data, ROLES)
    with pytest.raises(ValueError, match="ranked"):
        board.compare(data, table, list(mock.players["player_id"][:2]), ROLES)


def test_stat_cells_say_why_a_value_or_rank_is_missing():
    nan = float("nan")
    assert board._stat_cell("blocks_per100", 3.43, 83.2) == "3.4 · 83rd percentile"
    assert board._stat_cell("fg3_pct", 0.391, nan) == "39.1% · too few attempts to rank"
    assert board._stat_cell("iso_poss_per100", nan, 12) == "under 10 plays · 12th percentile"
    assert board._stat_cell("putback_ppp", nan, nan) == "missing"


def test_every_role_stat_has_a_display_name():
    assert list(board.STAT_DISPLAY) == analysis.STATS


@pytest.mark.parametrize(
    ("number", "text"),
    [
        (1, "1st"),
        (2, "2nd"),
        (3, "3rd"),
        (11, "11th"),
        (12.4, "12th"),
        (21, "21st"),
        (100, "100th"),
    ],
)
def test_ordinal(number, text):
    assert board.ordinal(number) == text


def test_team_codes_get_full_names_and_unknown_codes_stay_as_codes():
    assert board.team_names(["BOS", "MVM"]) == {"BOS": "Boston Celtics", "MVM": "MVM"}


def test_salary_source_leaves_out_blank_parts():
    row = {"salary_usd": 1_000_000, "source": "Site", "retrieved_on": "2026-10-24"}
    assert board.salary_source(pd.Series(row)) == "Site, 2026-10-24"
    assert board.salary_source(pd.Series({**row, "source": "Mock", "retrieved_on": ""})) == "Mock"
    assert board.salary_source(pd.Series({**row, "retrieved_on": float("nan")})) == "Site"
    assert board.salary_source(pd.Series({**row, "salary_usd": float("nan")})) == (
        "not in the salary file"
    )


def test_missing_salary_is_written_as_missing():
    assert board.format_salary(float("nan")) == "missing"
    assert board.format_salary(55_224_526) == "$55,224,526"
