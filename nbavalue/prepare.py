"""Turn a raw NBA.com snapshot into one labelled row per player.

NBA.com column names appear only in the mappings below; everything after this step
uses our own snake_case names, so a renamed NBA.com field is a one-line fix here.
"""

from pathlib import Path

import pandas as pd

from nbavalue.checks import require_columns
from nbavalue.fetch import SEASON
from nbavalue.labels import DataLabel

PROCESSED_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "players.csv"
SOURCE = "NBA.com stats via nba_api"

# Base names come from nba_api's published schema for LeagueDashPlayerStats.
BASE_COLUMNS = {
    "PLAYER_ID": "player_id",
    "PLAYER_NAME": "player_name",
    "TEAM_ABBREVIATION": "team",
    "AGE": "age",
    "GP": "games_played",
    "MIN": "minutes",
    "PTS": "points",
    "FGM": "fgm",
    "FGA": "fga",
    "FG3M": "fg3m",
    "FG3A": "fg3a",
    "FTM": "ftm",
    "FTA": "fta",
    "OREB": "oreb",
    "DREB": "dreb",
    "REB": "rebounds",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
    "TOV": "turnovers",
}

# Not in nba_api's published schema: unconfirmed until the first real fetch (decisions O5).
ADVANCED_COLUMNS = {
    "PLAYER_ID": "player_id",
    "POSS": "possessions",
    "USG_PCT": "usg_pct",
    "AST_PCT": "ast_pct",
    "OREB_PCT": "oreb_pct",
    "DREB_PCT": "dreb_pct",
}

# Tables added in step 4a. Only counting stats are kept, so a traded player's rows (one per
# team) can be added up; rates are worked out later from the totals (nbavalue/analysis.py).
# All names confirmed by Nathan's fetch on 2026-10-26 (D28). For shots within 6 ft NBA.com
# sends FGM_LT_06/FGA_LT_06, not the D_FGM/D_FGA that nba_api's schema lists.
EXTRA_COLUMNS = {
    "hustle": {
        "PLAYER_ID": "player_id",
        "DEFLECTIONS": "deflections",
        "CONTESTED_SHOTS": "contested_shots",
        "SCREEN_ASSISTS": "screen_assists",
    },
    "rim_defense": {
        "CLOSE_DEF_PERSON_ID": "player_id",
        "FGM_LT_06": "rim_dfgm",
        "FGA_LT_06": "rim_dfga",
    },
    "pullup": {"PLAYER_ID": "player_id", "PULL_UP_FGM": "pullup_fgm", "PULL_UP_FGA": "pullup_fga"},
    "pnr_ball_handler": {"PLAYER_ID": "player_id", "POSS": "pnr_bh_poss", "PTS": "pnr_bh_pts"},
    "isolation": {"PLAYER_ID": "player_id", "POSS": "iso_poss", "PTS": "iso_pts"},
    "roll_man": {"PLAYER_ID": "player_id", "POSS": "roll_man_poss", "PTS": "roll_man_pts"},
    "putbacks": {"PLAYER_ID": "player_id", "POSS": "putback_poss", "PTS": "putback_pts"},
}

PLAYER_COLUMNS = [
    *BASE_COLUMNS.values(),
    *[col for col in ADVANCED_COLUMNS.values() if col != "player_id"],
    *[col for mapping in EXTRA_COLUMNS.values() for col in mapping.values() if col != "player_id"],
    "season",
    "fetched_on",
    "source",
    "data_label",
]


# NBA.com only lists players with at least this many possessions of a play type. The
# analysis ranks a blank as "fewer than 10" (D29), so every build re-checks the floor.
PLAY_TYPE_TABLES = {"pnr_ball_handler", "isolation", "roll_man", "putbacks"}
LISTING_FLOOR = 10


def check_listing_floor(raw: pd.DataFrame, name: str) -> None:
    """Stop if a play-type table lists a blank or fewer than LISTING_FLOOR possessions."""
    poss = pd.to_numeric(raw["POSS"], errors="coerce") if "POSS" in raw else None
    if poss is not None and (poss.isna() | (poss < LISTING_FLOOR)).any():
        raise ValueError(
            f"{name} lists a player with a blank or under {LISTING_FLOOR} possessions. "
            "NBA.com's listing rule may have changed, so blanks can no longer be read as "
            "'fewer than 10' (decision D29). Check the data before continuing."
        )


def _select(raw: pd.DataFrame, mapping: dict[str, str], name: str) -> pd.DataFrame:
    try:
        require_columns(raw, list(mapping), name)
    except ValueError as err:
        raise ValueError(f"{err}. Columns NBA.com sent: {', '.join(raw.columns)}") from err
    return raw[list(mapping)].rename(columns=mapping)


def clean_extra_table(raw: pd.DataFrame, mapping: dict[str, str], name: str) -> pd.DataFrame:
    """Keep the mapped counting stats and add up a traded player's rows into one.

    min_count=1: a value no row has stays missing instead of becoming 0.
    """
    return _select(raw, mapping, name).groupby("player_id", as_index=False).sum(min_count=1)


def clean_table(raw: pd.DataFrame, mapping: dict[str, str], name: str) -> pd.DataFrame:
    """Keep the mapped columns, rename them, and refuse duplicate players."""
    df = _select(raw, mapping, name)
    if not df["player_id"].is_unique:
        raise ValueError(f"{name} lists the same player more than once")
    return df


def build_player_table(snapshot: Path) -> pd.DataFrame:
    """Join every table of one snapshot into one labelled row per player."""
    base = clean_table(pd.read_csv(snapshot / "base.csv"), BASE_COLUMNS, "base.csv")
    advanced = clean_table(pd.read_csv(snapshot / "advanced.csv"), ADVANCED_COLUMNS, "advanced.csv")

    base_ids, advanced_ids = set(base["player_id"]), set(advanced["player_id"])
    if base_ids != advanced_ids:
        raise ValueError(
            f"base.csv and advanced.csv list different players "
            f"({len(base_ids - advanced_ids)} only in base, "
            f"{len(advanced_ids - base_ids)} only in advanced)"
        )

    players = base.merge(advanced, on="player_id", validate="one_to_one")

    # The extra tables leave out players with no plays of that kind. Those values stay
    # missing (never 0): the base table is the list of players.
    for table, mapping in EXTRA_COLUMNS.items():
        raw = pd.read_csv(snapshot / f"{table}.csv")
        if table in PLAY_TYPE_TABLES:
            check_listing_floor(raw, f"{table}.csv")
        extra = clean_extra_table(raw, mapping, f"{table}.csv")
        unknown = set(extra["player_id"]) - base_ids
        if unknown:
            raise ValueError(f"{table}.csv lists players that base.csv doesn't: {len(unknown)}")
        players = players.merge(extra, on="player_id", how="left", validate="one_to_one")

    players["season"] = SEASON
    players["fetched_on"] = snapshot.name
    players["source"] = SOURCE
    players["data_label"] = str(DataLabel.NBA_COM)
    return players[PLAYER_COLUMNS]


def write_player_table(players: pd.DataFrame, path: Path = PROCESSED_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    players.to_csv(path, index=False)
    return path
