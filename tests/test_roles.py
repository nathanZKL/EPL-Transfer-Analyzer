import math

import pandas as pd
import pytest

from nbavalue import roles
from nbavalue.labels import DataLabel
from nbavalue.roles import Role

NAN = float("nan")


def role_toml(tmp_path, text: str):
    path = tmp_path / "roles.toml"
    path.write_text(text)
    return path


def pctile_table(**columns) -> pd.DataFrame:
    """A fictional percentile table: Mock players 9001, 9002, ... plus the given stats."""
    count = len(next(iter(columns.values())))
    table = pd.DataFrame({"player_id": range(9001, 9001 + count)})
    table["player_name"] = [f"Mock Player {i}" for i in range(1, count + 1)]
    for stat, values in columns.items():
        table[roles.pctile_column(stat)] = values
    return table


# --- loading the config -------------------------------------------------------------------


def test_real_config_loads_all_six_starter_roles():
    loaded = roles.load_roles()
    assert set(loaded) == {
        "rim_protector",
        "three_and_d_wing",
        "primary_creator",
        "shot_creator",
        "interior_big",
        "connector",
    }
    for role in loaded.values():
        assert role.label
        assert set(role.weights) <= set(roles.KNOWN_STATS)


def test_real_config_scores_a_full_percentile_table():
    loaded = roles.load_roles()
    table = pctile_table(**{stat: [50.0, 90.0] for stat in roles.KNOWN_STATS})
    scores = roles.fit_scores(table, loaded)
    assert list(scores.columns) == ["player_id", *loaded, "data_label"]
    for key in loaded:
        assert scores[key].tolist() == pytest.approx([50.0, 90.0])


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[r]\nlabel = "R"\n[r.weights]\nmade_up_stat = 1\n', "role 'r' uses unknown stats"),
        ('[r]\nlabel = "R"\n[r.weights]\nblocks_per100 = 0\n', "role 'r': weight for"),
        ('[r]\nlabel = "R"\n[r.weights]\nblocks_per100 = -1\n', "role 'r': weight for"),
        ('[r]\nlabel = "R"\n[r.weights]\nblocks_per100 = "1"\n', "role 'r': weight for"),
        ('[r]\nlabel = "R"\n[r.weights]\nblocks_per100 = true\n', "role 'r': weight for"),
        ('[r]\nlabel = "R"\n[r.weights]\nblocks_per100 = nan\n', "role 'r': weight for"),
        ('[r]\nlabel = "R"\n[r.weights]\n', "role 'r' has no stats"),
        ('[r]\nlabel = "R"\n', "role 'r' has no stats"),
        ("[r]\n[r.weights]\nblocks_per100 = 1\n", "role 'r' is missing a label"),
        ('[r]\nlabel = " "\n[r.weights]\nblocks_per100 = 1\n', "role 'r' is missing a label"),
        ('[r]\nlabel = "R"\ncolour = "red"\n[r.weights]\nblocks_per100 = 1\n', "unknown keys"),
        ('r = "not a table"\n', "role 'r' must be a table"),
        ("", "defines no roles"),
    ],
)
def test_bad_config_is_refused(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        roles.load_roles(role_toml(tmp_path, text))


# --- fit scores ---------------------------------------------------------------------------


def test_fit_score_is_weighted_average_checked_by_hand():
    rim = Role("Rim protector", {"blocks_per100": 0.4, "rim_dfg_pct": 0.4, "dreb_pct": 0.2})
    other = Role("Two stats", {"blocks_per100": 3, "dreb_pct": 1})
    table = pctile_table(blocks_per100=[50.0, 80.0], rim_dfg_pct=[100.0, 0.0], dreb_pct=[0, 40])
    scores = roles.fit_scores(table, {"rim": rim, "other": other})
    # Player 9001: 0.4*50 + 0.4*100 + 0.2*0 = 60.  Player 9002: 0.4*80 + 0 + 0.2*40 = 40.
    assert scores["rim"].tolist() == pytest.approx([60.0, 40.0])
    # Weights don't need to add to 1: (3*50 + 1*0) / 4 = 37.5 and (3*80 + 1*40) / 4 = 70.
    assert scores["other"].tolist() == pytest.approx([37.5, 70.0])
    assert scores["player_id"].tolist() == [9001, 9002]


def test_missing_stat_gives_missing_score_only_for_roles_using_it():
    uses_it = Role("Uses blocks", {"blocks_per100": 1, "dreb_pct": 1})
    ignores_it = Role("Rebounds only", {"dreb_pct": 1})
    table = pctile_table(blocks_per100=[NAN, 60.0], dreb_pct=[80.0, 20.0])
    scores = roles.fit_scores(table, {"a": uses_it, "b": ignores_it})
    assert math.isnan(scores.loc[0, "a"])
    assert scores.loc[1, "a"] == pytest.approx(40.0)
    assert scores["b"].tolist() == pytest.approx([80.0, 20.0])
    assert len(scores) == 2  # the player is kept, not dropped


def test_fit_scores_are_labelled_estimates():
    table = pctile_table(blocks_per100=[10.0, 20.0])
    scores = roles.fit_scores(table, {"r": Role("R", {"blocks_per100": 1})})
    assert (scores["data_label"] == DataLabel.ESTIMATE).all()


def test_missing_pctile_column_is_refused():
    table = pctile_table(blocks_per100=[10.0])
    role = Role("R", {"blocks_per100": 1, "dreb_pct": 1})
    with pytest.raises(ValueError, match="missing columns: dreb_pct_pctile"):
        roles.fit_scores(table, {"r": role})


def test_duplicate_players_and_out_of_range_pctiles_are_refused():
    role = {"r": Role("R", {"blocks_per100": 1})}
    duplicated = pctile_table(blocks_per100=[10.0, 20.0]).assign(player_id=[9001, 9001])
    with pytest.raises(ValueError, match="duplicate player_id"):
        roles.fit_scores(duplicated, role)
    with pytest.raises(ValueError, match="outside 0-100 in: blocks_per100_pctile"):
        roles.fit_scores(pctile_table(blocks_per100=[10.0, 120.0]), role)


def test_changing_a_weight_in_the_config_changes_the_ranking(tmp_path):
    table = pctile_table(blocks_per100=[90.0, 30.0], dreb_pct=[10.0, 70.0])

    def leader(blocks_weight: int, dreb_weight: int) -> int:
        path = role_toml(
            tmp_path,
            f'[big]\nlabel = "Big"\n[big.weights]\n'
            f"blocks_per100 = {blocks_weight}\ndreb_pct = {dreb_weight}\n",
        )
        scores = roles.fit_scores(table, roles.load_roles(path))
        return int(scores.sort_values("big", ascending=False)["player_id"].iloc[0])

    # Blocks-heavy: 9001 = (3*90 + 10) / 4 = 70 beats 9002 = (3*30 + 70) / 4 = 40.
    assert leader(3, 1) == 9001
    # Rebound-heavy: 9001 = (90 + 3*10) / 4 = 30 loses to 9002 = (30 + 3*70) / 4 = 60.
    assert leader(1, 3) == 9002


# --- value scores -------------------------------------------------------------------------


def fit_table(scores: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": range(9001, 9001 + len(scores)),
            "big": scores,
            "data_label": str(DataLabel.ESTIMATE),
        }
    )


def salary_table(pairs: dict[int, int]) -> pd.DataFrame:
    """Fictional salaries in the import_salaries output shape (only the columns used)."""
    return pd.DataFrame(
        {
            "player_id": list(pairs),
            "salary_usd": list(pairs.values()),
            "data_label": str(DataLabel.MOCK),
        }
    )


def test_value_score_maths_checked_by_hand():
    # 9005 has no salary; 9006 has a salary but no fit score. Neither counts in the ranks.
    fit = fit_table([80.0, 60.0, 40.0, 20.0, 99.0, NAN])
    pay = salary_table(
        {9001: 40_000_000, 9002: 10_000_000, 9003: 30_000_000, 9004: 20_000_000, 9006: 1_000}
    )
    value = roles.value_scores(fit, pay, "big").set_index("player_id")

    # Among the four players with both: fit percentiles 100, 75, 50, 25;
    # salary percentiles 100, 25, 75, 50; value = fit minus salary.
    rated = value.loc[[9001, 9002, 9003, 9004]]
    assert rated["fit_pctile"].tolist() == pytest.approx([100, 75, 50, 25])
    assert rated["salary_pctile"].tolist() == pytest.approx([100, 25, 75, 50])
    assert rated["value_score"].tolist() == pytest.approx([0, 50, -25, -25])


def test_players_without_salary_or_fit_are_kept_as_missing():
    fit = fit_table([80.0, 60.0, 99.0, NAN])
    pay = salary_table({9001: 20_000_000, 9002: 10_000_000, 9004: 5_000_000})
    value = roles.value_scores(fit, pay, "big").set_index("player_id")

    assert list(value.index) == [9001, 9002, 9003, 9004]  # nobody dropped
    assert math.isnan(value.loc[9003, "salary_usd"])
    for player in (9003, 9004):
        for col in ("fit_pctile", "salary_pctile", "value_score"):
            assert math.isnan(value.loc[player, col])
    assert value.loc[9003, "fit_score"] == pytest.approx(99.0)  # fit itself is still shown


def test_value_scores_are_labelled_estimates():
    value = roles.value_scores(fit_table([50.0]), salary_table({9001: 1_000_000}), "big")
    assert (value["data_label"] == DataLabel.ESTIMATE).all()


@pytest.mark.parametrize(
    ("pay", "role", "message"),
    [
        (salary_table({9001: 1_000_000}), "not_a_role", "fit score table is missing columns"),
        (pd.DataFrame({"player_id": [9001]}), "big", "salary table is missing columns"),
        (salary_table({9001: 1_000_000}).assign(salary_usd="lots"), "big", "non-numeric"),
        (salary_table({9001: 0}), "big", "0 or less"),
        (
            pd.DataFrame({"player_id": [9001, 9001], "salary_usd": [1, 2]}),
            "big",
            "more than one salary",
        ),
    ],
)
def test_bad_value_inputs_are_refused(pay, role, message):
    with pytest.raises(ValueError, match=message):
        roles.value_scores(fit_table([50.0]), pay, role)
