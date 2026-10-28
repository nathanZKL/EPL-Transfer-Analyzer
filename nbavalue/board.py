"""Everything the app shows, as plain tables (MVP features 4 and 5).

Loads one dataset (real NBA.com stats plus imported salaries, or the fictional mock set),
joins stats, salaries and role scores into one row per player (the "board"), and filters it
into a shortlist. No Streamlit code here: app.py only displays these tables.

Missing stays missing: a player without a salary keeps a blank salary and value score, and a
player under the minutes cut keeps blank fit scores and is marked as not ranked.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from nba_api.stats.static import teams as nba_teams

from nbavalue import analysis, mock_data, prepare, roles, salaries
from nbavalue.checks import require_columns
from nbavalue.labels import DataLabel

PLAYERS_PATH = prepare.PROCESSED_PATH
SALARIES_PATH = salaries.PROCESSED_PATH
SALARY_INFO = ["salary_usd", "source", "source_url", "retrieved_on"]
PLAYER_INFO = ["player_id", "player_name", "team", "age", "games_played", "minutes"]

# How each role stat is named and written in the comparison: stat -> (label, format).
STAT_DISPLAY = {
    "blocks_per100": ("Blocks per 100 possessions", "{:.1f}"),
    "dreb_pct": ("Defensive rebound %", "{:.1%}"),
    "rim_dfg_pct": ("Opponent FG% within 6 ft (lower is better)", "{:.1%}"),
    "fg3a_rate": ("Share of shots that are threes", "{:.1%}"),
    "fg3_pct": ("3-point %", "{:.1%}"),
    "deflections_per100": ("Deflections per 100", "{:.1f}"),
    "contested_shots_per100": ("Contested shots per 100", "{:.1f}"),
    "usg_pct": ("Usage %", "{:.1%}"),
    "ast_pct": ("Assist %", "{:.1%}"),
    "pnr_bh_poss_per100": ("Pick-and-roll ball-handler plays per 100", "{:.1f}"),
    "iso_poss_per100": ("Isolation plays per 100", "{:.1f}"),
    "pullup_fga_per100": ("Pull-up shots per 100", "{:.1f}"),
    "points_per100": ("Points per 100", "{:.1f}"),
    "iso_ppp": ("Points per isolation play", "{:.2f}"),
    "pullup_fg_pct": ("Pull-up FG%", "{:.1%}"),
    "oreb_pct": ("Offensive rebound %", "{:.1%}"),
    "roll_man_ppp": ("Points per roll-man play", "{:.2f}"),
    "putback_ppp": ("Points per putback", "{:.2f}"),
    "ast_to_tov": ("Assists per turnover", "{:.2f}"),
    "screen_assists_per100": ("Screen assists per 100", "{:.1f}"),
}


@dataclass(frozen=True)
class Dataset:
    players: pd.DataFrame  # prepare.PLAYER_COLUMNS, numbers as numbers
    salaries: pd.DataFrame  # player_id + SALARY_INFO, one row per salaried player
    is_mock: bool
    season: str
    fetched_on: str  # "" for mock data
    salary_file_found: bool


@dataclass(frozen=True)
class Filters:
    exclude_teams: tuple[str, ...] = ()
    max_salary: float | None = None  # players with no salary are kept: unknown is not cheap
    max_age: float | None = None
    min_minutes: float = analysis.MIN_MINUTES


def real_data_available(players_path: Path | None = None) -> bool:
    return (players_path or PLAYERS_PATH).exists()


def _salary_info(pay: pd.DataFrame) -> pd.DataFrame:
    return pay[["player_id", *SALARY_INFO]].astype({"player_id": "int64", "salary_usd": "int64"})


def _only_label(df: pd.DataFrame, label: DataLabel, name: str) -> None:
    if not (df["data_label"] == label).all():
        raise ValueError(f"{name} has rows not labelled '{label}'")


def load_real(players_path: Path | None = None, salaries_path: Path | None = None) -> Dataset:
    """Read the processed NBA.com table and the imported salaries. Raises ValueError on problems."""
    players_path = players_path or PLAYERS_PATH
    salaries_path = salaries_path or SALARIES_PATH
    if not players_path.exists():
        raise FileNotFoundError(
            f"No player table at {players_path}. Run python -m nbavalue.update_data first."
        )
    # Normal blank handling, so a blank stat is a missing number rather than text.
    players = pd.read_csv(players_path)
    require_columns(players, prepare.PLAYER_COLUMNS, players_path.name)
    if players.empty:
        raise ValueError(
            f"{players_path.name} has no players. Run python -m nbavalue.update_data --refresh."
        )
    _only_label(players, DataLabel.NBA_COM, players_path.name)
    fetched = players["fetched_on"].astype(str).unique()
    if len(fetched) != 1:
        raise ValueError(f"{players_path.name} mixes several fetch dates")

    found = salaries_path.exists()
    if found:
        pay = pd.read_csv(salaries_path, keep_default_na=False)
        require_columns(pay, salaries.MATCHED_COLUMNS, salaries_path.name)
        _only_label(pay, DataLabel.REPORTED_SALARY, salaries_path.name)
        unknown = set(pay["player_id"].astype("int64")) - set(players["player_id"])
        if unknown:
            raise ValueError(
                f"{salaries_path.name} names {len(unknown)} players that {players_path.name} "
                "doesn't, so the two files come from different runs. "
                "Run python -m nbavalue.import_salaries again."
            )
    else:
        pay = pd.DataFrame(columns=salaries.MATCHED_COLUMNS)
    return Dataset(players, _salary_info(pay), False, prepare.SEASON, str(fetched[0]), found)


def load_mock() -> Dataset:
    """The fictional mock players with their mock salaries matched by name."""
    players = mock_data.load_players()
    matched, unmatched = salaries.match_salaries(mock_data.load_salaries(), players)
    if not unmatched.empty:
        raise ValueError("data/mock/salaries.csv has rows that match no mock player")
    return Dataset(players, _salary_info(matched), True, "MOCK", "", True)


def fit_column(role: str) -> str:
    return f"fit_{role}"


def value_column(role: str) -> str:
    return f"value_{role}"


def build_board(data: Dataset, role_defs: dict[str, roles.Role]) -> pd.DataFrame:
    """One row per player: basics, salary (blank if none), a ranked flag, and per role a fit
    score and a value score. Value percentiles use every ranked, salaried player in the league,
    so filtering the shortlist later never changes a player's score.
    """
    fit = roles.fit_scores(analysis.percentiles(data.players), role_defs)
    board = data.players[PLAYER_INFO].copy()
    board["ranked"] = board["minutes"] >= analysis.MIN_MINUTES
    board = board.merge(data.salaries, on="player_id", how="left", validate="one_to_one")
    for key in role_defs:
        value = roles.value_scores(fit, data.salaries, key)
        value = value[["player_id", "fit_score", "value_score"]].rename(
            columns={"fit_score": fit_column(key), "value_score": value_column(key)}
        )
        board = board.merge(value, on="player_id", how="left", validate="one_to_one")
    return board


def shortlist(board: pd.DataFrame, role: str, filters: Filters | None = None) -> pd.DataFrame:
    """Ranked players for one role, best fit first, after the filters.

    Only ranked players appear (the others have no fit score). Under a salary limit a player
    with no salary is kept, because a missing salary is unknown, not low; likewise for age.
    Columns: PLAYER_INFO, `fit_score`, `value_score`, SALARY_INFO.
    """
    filters = filters or Filters()
    fit, value = fit_column(role), value_column(role)
    require_columns(board, [*PLAYER_INFO, "ranked", fit, value, *SALARY_INFO], "board")
    keep = board["ranked"] & (board["minutes"] >= filters.min_minutes)
    keep &= ~board["team"].isin(filters.exclude_teams)
    if filters.max_salary is not None:
        keep &= board["salary_usd"].isna() | (board["salary_usd"] <= filters.max_salary)
    if filters.max_age is not None:
        keep &= board["age"].isna() | (board["age"] <= filters.max_age)
    out = board[keep].rename(columns={fit: "fit_score", value: "value_score"})
    out = out.sort_values(["fit_score", "player_name"], ascending=[False, True], na_position="last")
    return out[[*PLAYER_INFO, "fit_score", "value_score", *SALARY_INFO]].reset_index(drop=True)


def not_ranked_with_salary(board: pd.DataFrame) -> pd.DataFrame:
    """Salaried players under the minutes cut: they have no fit or value score."""
    rows = board[~board["ranked"] & board["salary_usd"].notna()]
    return rows[["player_name", "team", "minutes", "salary_usd"]].sort_values("player_name")


def team_names(codes) -> dict[str, str]:
    """Full name for each team code, from the NBA team list built into nba_api (no network
    request). A code it doesn't know, such as a mock team, stays as its code."""
    known = {team["abbreviation"]: team["full_name"] for team in nba_teams.get_teams()}
    return {code: known.get(code, code) for code in codes}


def salary_range(board: pd.DataFrame) -> tuple[float, float] | None:
    """Lowest and highest salary on the board, or None when nobody has one."""
    known = board["salary_usd"].dropna()
    if known.empty:
        return None
    return float(known.min()), float(known.max())


def format_salary(amount: float) -> str:
    return "missing" if pd.isna(amount) else f"${amount:,.0f}"


def ordinal(number: float) -> str:
    n = int(round(number))
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _stat_cell(stat: str, value: float, pctile: float) -> str:
    """e.g. '3.4 · 83rd percentile'. Says why when there is no value or no percentile."""
    if pd.isna(value):
        if stat in analysis.BLANK_MEANS_FEWER_THAN_10 and not pd.isna(pctile):
            return f"under 10 plays · {ordinal(pctile)} percentile"
        return "missing"
    shown = STAT_DISPLAY[stat][1].format(value)
    if pd.isna(pctile):
        return f"{shown} · too few attempts to rank"
    return f"{shown} · {ordinal(pctile)} percentile"


def player_label(row: pd.Series) -> str:
    return f"{row['player_name']} ({row['team']})"


def salary_source(row: pd.Series) -> str:
    """'Site, date' for a salary; blank parts (mock salaries have no date) are left out."""
    if pd.isna(row["salary_usd"]):
        return "not in the salary file"
    parts = [row["source"], row["retrieved_on"]]
    return ", ".join(str(part) for part in parts if pd.notna(part) and str(part).strip())


def compare(
    data: Dataset, board: pd.DataFrame, player_ids: list[int], role_defs: dict[str, roles.Role]
) -> dict[str, pd.DataFrame]:
    """Side-by-side tables for a few ranked players, as text ready to show.

    Returns {"Basics", "Role fit", "Stats"}: each has a first column naming the measure and
    one column per player, in the order of `player_ids`.
    """
    rows = board.set_index("player_id").loc[player_ids].reset_index()
    if not rows["ranked"].all():
        raise ValueError("Only ranked players can be compared: the others have no scores")
    names = [player_label(row) for _, row in rows.iterrows()]
    rates = analysis.add_rates(data.players).set_index("player_id")
    pctiles = analysis.percentiles(data.players).set_index("player_id")

    def table(measure: str, cells: dict[str, list[str]]) -> pd.DataFrame:
        records = [[label, *values] for label, values in cells.items()]
        return pd.DataFrame(records, columns=[measure, *names])

    basics = {
        "Team": list(rows["team"]),
        "Age": [f"{age:.0f}" for age in rows["age"]],
        "Minutes": [f"{minutes:,.0f}" for minutes in rows["minutes"]],
        "Salary": [format_salary(amount) for amount in rows["salary_usd"]],
        "Salary source": [salary_source(row) for _, row in rows.iterrows()],
    }
    fits = {
        role.label: ["missing" if pd.isna(v) else f"{v:.0f}" for v in rows[fit_column(key)]]
        for key, role in role_defs.items()
    }
    stats = {
        STAT_DISPLAY[stat][0]: [
            _stat_cell(stat, rates.at[pid, stat], pctiles.at[pid, f"{stat}_pctile"])
            for pid in player_ids
        ]
        for stat in analysis.STATS
    }
    return {
        "Basics": table("Measure", basics),
        "Role fit": table("Role (our estimate, 0-100)", fits),
        "Stats": table("Stat (rank among ranked players)", stats),
    }
