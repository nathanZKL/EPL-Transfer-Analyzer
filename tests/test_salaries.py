import pandas as pd
import pytest

from nbavalue import import_salaries, mock_data, salaries
from nbavalue.labels import DataLabel

# Fictional players in the shape of the real NBA.com table; matching only needs these columns.
PLAYERS = pd.DataFrame(
    {
        "player_id": [1, 2, 3, 4],
        "player_name": ["Mock Zoë Ruiz Jr.", "Mock Kai Bell", "Mock Kai Bell", "Mock Theo Lund"],
        "team": ["MVM", "MVM", "FTF", "SPS"],
        "data_label": [str(DataLabel.NBA_COM)] * 4,
    }
)


def salary_rows(*rows: tuple[str, str], **changes) -> pd.DataFrame:
    """Valid 'Reported salary' rows for (name, team) pairs, with optional column changes."""
    df = pd.DataFrame(
        {
            "player_name": [name for name, _ in rows],
            "team": [team for _, team in rows],
            "season": "2025-26",
            "salary_usd": "10000000",
            "source": "Example salary site",
            "source_url": "https://example.com/salaries",
            "retrieved_on": "2026-10-24",
            "data_label": str(DataLabel.REPORTED_SALARY),
        }
    )
    for col, value in changes.items():
        df[col] = value
    return df


def overrides(*rows: tuple[str, str, int]) -> pd.DataFrame:
    return pd.DataFrame(
        [(name, team, player_id, "") for name, team, player_id in rows],
        columns=salaries.OVERRIDE_COLUMNS,
    )


def match(salary_df, override_df=None):
    return salaries.match_salaries(salaries.validate_salaries(salary_df), PLAYERS, override_df)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Nikola Jokić", "nikola jokic"),
        ("Jaren Jackson Jr.", "jaren jackson"),
        ("Gary Trent Jr", "gary trent"),
        ("Marvin Bagley III", "marvin bagley"),
        ("P.J. Washington", "pj washington"),
        ("De'Aaron Fox", "deaaron fox"),
        ("Karl-Anthony Towns", "karl anthony towns"),
        ("  Kai   BELL ", "kai bell"),
    ],
)
def test_normalise_name(raw, expected):
    assert salaries.normalise_name(raw) == expected


def test_every_mock_salary_matches_a_mock_player():
    players = mock_data.load_players()
    matched, unmatched = salaries.match_salaries(
        salaries.validate_salaries(mock_data.load_salaries()), players
    )

    assert unmatched.empty
    assert len(matched) == 12
    assert list(matched.columns) == salaries.MATCHED_COLUMNS
    named = players.set_index("player_name")["player_id"]
    assert (matched["player_id"] == matched["player_name"].map(named)).all()


def test_name_matches_even_when_the_team_differs():
    # A traded player, or a site writing a different team code, still matches.
    matched, unmatched = match(salary_rows(("Mock Zoe Ruiz", "GS")))

    assert unmatched.empty
    assert matched.loc[0, "player_id"] == 1
    assert matched.loc[0, "matched_by"] == "name"


def test_team_breaks_a_tie_between_players_with_the_same_name():
    matched, _ = match(salary_rows(("Mock Kai Bell", "ftf")))

    assert matched.loc[0, "player_id"] == 3
    assert matched.loc[0, "matched_by"] == "name + team"


def test_shared_name_without_a_team_match_is_reported_not_guessed():
    matched, unmatched = match(salary_rows(("Mock Kai Bell", "SPS")))

    assert matched.empty
    assert "share this name" in unmatched.loc[0, "reason"]
    assert unmatched.loc[0, "suggestions"] == "Mock Kai Bell (MVM, 2); Mock Kai Bell (FTF, 3)"


def test_unknown_name_is_reported_with_suggestions():
    matched, unmatched = match(salary_rows(("Mock Teo Lund", "SPS"), ("Mock Kai Bell", "MVM")))

    assert list(matched["player_id"]) == [2]
    assert list(unmatched.columns) == salaries.UNMATCHED_COLUMNS
    assert "no NBA.com player" in unmatched.loc[0, "reason"]
    # Every fake name starts with "Mock ", so other close names may follow the best one.
    assert unmatched.loc[0, "suggestions"].startswith("Mock Theo Lund (SPS, 4)")


def test_override_beats_the_automatic_match():
    matched, unmatched = match(
        salary_rows(("Mock Teo Lund", "SPS"), ("Mock Kai Bell", "SPS")),
        overrides(("Mock Teo Lund", "sps", 4), ("Mock Kai Bell", "SPS", 3)),
    )

    assert unmatched.empty
    assert list(matched["player_id"]) == [4, 3]
    assert (matched["matched_by"] == "override").all()


def test_override_with_an_unknown_player_id_is_refused():
    with pytest.raises(ValueError, match="aren't in the player table: 99"):
        match(salary_rows(("Mock Kai Bell", "SPS")), overrides(("Mock Kai Bell", "SPS", 99)))


def test_override_that_matches_no_salary_row_is_refused():
    # The salary file says GS, the override says GSW: the override would silently do nothing.
    with pytest.raises(ValueError, match=r"match no salary row.*: Mock Kai Bell \(GSW\)"):
        match(salary_rows(("Mock Kai Bell", "GS")), overrides(("Mock Kai Bell", "GSW", 3)))


def test_two_salaries_for_one_player_are_refused():
    with pytest.raises(ValueError, match="same player: Mock Zoe Ruiz, Mock Zoë Ruiz Jr."):
        match(salary_rows(("Mock Zoë Ruiz Jr.", "MVM"), ("Mock Zoe Ruiz", "FTF")))


def test_mock_salaries_are_not_matched_against_real_players():
    with pytest.raises(ValueError, match="only be matched against 'Mock' players"):
        salaries.match_salaries(salaries.validate_salaries(mock_data.load_salaries()), PLAYERS)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"source_url": ""}, "real salaries need a source_url"),
        ({"source": " "}, "real salaries need a source"),
        ({"retrieved_on": "24/10/2026"}, "retrieved_on must be a YYYY-MM-DD date"),
        ({"salary_usd": "12.5"}, "salary_usd must be a whole number above 0"),
        ({"salary_usd": "0"}, "salary_usd must be a whole number above 0"),
        ({"salary_usd": ""}, "salary_usd must be a whole number above 0"),
        ({"salary_usd": "5.52E+07"}, "salary_usd must be a whole number above 0"),
        ({"salary_usd": "12,500,000"}, "salary_usd must be a whole number above 0"),
        ({"salary_usd": "12500000.0"}, "salary_usd must be a whole number above 0"),
        ({"season": "2024-25"}, "season must be 2025-26"),
        ({"team": ""}, "team is blank"),
        ({"data_label": "Estimate"}, "data_label must be 'Reported salary' or 'Mock'"),
    ],
)
def test_bad_salary_rows_are_refused_with_line_numbers(changes, message):
    df = salary_rows(("Mock Kai Bell", "MVM"), ("Mock Theo Lund", "SPS"))
    for col, value in changes.items():
        df.loc[1, col] = value

    with pytest.raises(ValueError, match=f"{message}.*lines 3"):
        salaries.validate_salaries(df)


def test_file_mixing_real_and_mock_rows_is_refused():
    df = salary_rows(("Mock Kai Bell", "MVM"), ("Mock Theo Lund", "SPS"))
    df.loc[1, "data_label"] = str(DataLabel.MOCK)

    with pytest.raises(ValueError, match="mixes"):
        salaries.validate_salaries(df)


def test_missing_salary_column_is_refused():
    with pytest.raises(ValueError, match="missing columns: source_url"):
        salaries.validate_salaries(salary_rows(("Mock Kai Bell", "MVM")).drop(columns="source_url"))


def test_import_salaries_runs_end_to_end(tmp_path, capsys):
    folder = tmp_path / "salaries"
    folder.mkdir()
    salary_rows(("Mock Zoe Ruiz", "MVM"), ("Mock Teo Lund", "SPS"), ("Mock Kai Bell", "X")).to_csv(
        folder / "salaries.csv", index=False
    )
    overrides(("Mock Kai Bell", "X", 2)).to_csv(folder / "overrides.csv", index=False)
    PLAYERS.to_csv(tmp_path / "players.csv", index=False)
    out = tmp_path / "processed" / "salaries.csv"
    unmatched_out = tmp_path / "processed" / "salary_unmatched.csv"

    path = import_salaries.main(
        [],
        salary_path=folder / "salaries.csv",
        overrides_path=folder / "overrides.csv",
        players_path=tmp_path / "players.csv",
        processed_path=out,
        unmatched_path=unmatched_out,
    )

    assert path == out
    assert list(pd.read_csv(out)["player_id"]) == [1, 2]
    assert list(pd.read_csv(unmatched_out)["player_name"]) == ["Mock Teo Lund"]
    printed = capsys.readouterr().out
    assert "Matched 2 of 3 salary rows (1 by override)" in printed
    assert "Did you mean: Mock Theo Lund (SPS, 4)" in printed
    assert "2 NBA.com players have no salary" in printed


def test_import_salaries_without_players_says_what_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="nbavalue.update_data"):
        import_salaries.main([], players_path=tmp_path / "missing.csv")
