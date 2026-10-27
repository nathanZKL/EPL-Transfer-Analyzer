import numpy as np
import pandas as pd
import pytest

from nbavalue import analysis, mock_data


def players(**columns) -> pd.DataFrame:
    """Fictional players: every needed stat is 1 unless a test sets it."""
    n = len(next(iter(columns.values())))
    needed = [
        "possessions",
        *analysis.PER_100,
        *[col for pair in analysis.RATIOS.values() for col in pair],
        "dreb_pct",
        "usg_pct",
        "ast_pct",
        "oreb_pct",
    ]
    df = pd.DataFrame({col: [1.0] * n for col in needed})
    df["player_id"] = range(1, n + 1)
    df["minutes"] = 1000
    for col, values in columns.items():
        df[col] = values
    return df


def test_counting_stats_become_per_100_possessions():
    df = analysis.add_rates(players(blocks=[30], points=[450], possessions=[1500]))

    assert df.loc[0, "blocks_per100"] == pytest.approx(2.0)
    assert df.loc[0, "points_per100"] == pytest.approx(30.0)


def test_rates_come_from_season_totals():
    df = analysis.add_rates(
        players(fg3m=[40], fg3a=[100], fga=[400], iso_pts=[45], iso_poss=[50], rim_dfgm=[30])
    )

    assert df.loc[0, "fg3_pct"] == pytest.approx(0.4)
    assert df.loc[0, "fg3a_rate"] == pytest.approx(0.25)
    assert df.loc[0, "iso_ppp"] == pytest.approx(0.9)


def test_dividing_by_zero_or_missing_gives_missing_not_infinite():
    df = analysis.add_rates(players(turnovers=[0, 2], iso_poss=[np.nan, 4], iso_pts=[np.nan, 6]))

    assert pd.isna(df.loc[0, "ast_to_tov"])
    assert pd.isna(df.loc[0, "iso_ppp"])
    assert pd.isna(df.loc[0, "iso_poss_per100"])
    assert df.loc[1, "iso_ppp"] == pytest.approx(1.5)


def test_players_under_the_minutes_cut_are_not_ranked():
    df = players(blocks=[10, 20, 30, 99], minutes=[600, 700, 800, 499])

    ranked = analysis.percentiles(df)

    assert list(ranked["player_id"]) == [1, 2, 3]
    # The 499-minute player's 99 blocks don't push the others down.
    assert list(ranked["blocks_per100_pctile"].round(2)) == [33.33, 66.67, 100.0]


def test_minutes_cut_is_500_by_default():
    assert analysis.MIN_MINUTES == 500
    assert list(analysis.qualifying(players(minutes=[499, 500]))["minutes"]) == [500]


def test_lower_opponent_shooting_at_the_rim_ranks_higher():
    df = players(rim_dfgm=[50, 60, 70], rim_dfga=[100, 100, 100])

    ranked = analysis.percentiles(df)

    assert list(ranked["rim_dfg_pct_pctile"].round(2)) == [100.0, 66.67, 33.33]


def test_missing_stat_gets_no_percentile_and_others_rank_without_it():
    # E.g. a player the hustle table leaves out: unknown, so not ranked.
    df = players(deflections=[np.nan, 5, 10], possessions=[1000, 1000, 1000])

    ranked = analysis.percentiles(df)

    assert pd.isna(ranked.loc[0, "deflections_per100_pctile"])
    assert list(ranked["deflections_per100_pctile"][1:]) == [50.0, 100.0]


def test_mock_dataset_matches_hand_checked_values():
    mock = mock_data.load_players()
    rates = analysis.add_rates(mock).set_index("player_name")
    ranked = analysis.percentiles(mock).set_index("player_id")

    # Mock Cyrus Oakes: 148 blocks over 4310 possessions; 7 of 28 threes; 253 of 504 at the rim.
    assert rates.loc["Mock Cyrus Oakes", "blocks_per100"] == pytest.approx(3.434, abs=0.001)
    assert rates.loc["Mock Cyrus Oakes", "fg3_pct"] == pytest.approx(0.25)
    assert rates.loc["Mock Cyrus Oakes", "rim_dfg_pct"] == pytest.approx(0.502, abs=0.001)
    # 10th lowest blocks rate of the 12 mock players.
    assert ranked.loc[900003, "blocks_per100_pctile"] == pytest.approx(100 * 10 / 12)


def test_efficiency_on_too_few_attempts_gets_no_percentile():
    df = players(
        iso_poss=[24, 25, 50],
        iso_pts=[48, 20, 50],
        pullup_fga=[49, 50, 80],
        pullup_fgm=[49, 20, 40],
    )

    ranked = analysis.percentiles(df)

    # 24 isolations at 2.0 per play would top the league; under the 25 minimum it isn't ranked.
    assert pd.isna(ranked.loc[0, "iso_ppp_pctile"])
    assert list(ranked["iso_ppp_pctile"][1:]) == [50.0, 100.0]
    assert pd.isna(ranked.loc[0, "pullup_fg_pct_pctile"])
    assert list(ranked["pullup_fg_pct_pctile"][1:]) == [50.0, 100.0]


def test_minimum_attempts_are_25_plays_and_50_pullups():
    assert analysis.MIN_ATTEMPTS == {
        "iso_ppp": ("iso_poss", 25),
        "roll_man_ppp": ("roll_man_poss", 25),
        "putback_ppp": ("putback_poss", 25),
        "pullup_fg_pct": ("pullup_fga", 50),
    }


def test_play_type_volume_blank_ranks_tied_for_last():
    # NBA.com leaves out players with fewer than 10 isolations, so a blank is the fewest.
    df = players(iso_poss=[np.nan, np.nan, 20, 40], possessions=[1000] * 4)

    ranked = analysis.percentiles(df)

    # The two blanks share the bottom two places (ranks 1 and 2 of 4, averaged).
    assert list(ranked["iso_poss_per100_pctile"]) == [37.5, 37.5, 75.0, 100.0]
    # Their isolation efficiency is still unknown, so it isn't ranked.
    assert ranked["iso_ppp_pctile"][:2].isna().all()


def test_every_role_stat_gets_a_percentile_on_the_mock_dataset():
    ranked = analysis.percentiles(mock_data.load_players())

    assert list(ranked.columns) == ["player_id", *[f"{s}_pctile" for s in analysis.STATS]]
    assert len(ranked) == 12
    values = ranked.drop(columns="player_id")
    # Only efficiency below the attempt minimums may be blank.
    blank = values.columns[values.isna().any()]
    assert set(blank) <= {f"{s}_pctile" for s in analysis.MIN_ATTEMPTS}
    assert ((values > 0) & (values <= 100) | values.isna()).all().all()


def test_player_table_without_a_needed_column_is_refused():
    with pytest.raises(ValueError, match="missing columns: possessions"):
        analysis.add_rates(players(blocks=[1]).drop(columns="possessions"))
