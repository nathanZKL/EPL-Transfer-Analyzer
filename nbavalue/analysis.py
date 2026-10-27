"""Per-100-possession stats and league percentiles (MVP feature 2).

Works on the player table (`prepare.PLAYER_COLUMNS`). Missing values stay missing: a player
NBA.com leaves out of a table, or one who never attempted a shot type, gets no rate and no
percentile instead of a guessed 0.
"""

import numpy as np
import pandas as pd

from nbavalue.checks import require_columns

MIN_MINUTES = 500  # decision O4: fewer minutes and a player gets no percentiles

# Counting stats shown per 100 of the player's possessions: our column -> new column.
PER_100 = {
    "blocks": "blocks_per100",
    "deflections": "deflections_per100",
    "contested_shots": "contested_shots_per100",
    "screen_assists": "screen_assists_per100",
    "points": "points_per100",
    "pnr_bh_poss": "pnr_bh_poss_per100",
    "iso_poss": "iso_poss_per100",
    "pullup_fga": "pullup_fga_per100",
}

# Rates worked out from season totals: new column -> (top, bottom).
RATIOS = {
    "fg3a_rate": ("fg3a", "fga"),
    "fg3_pct": ("fg3m", "fg3a"),
    "ast_to_tov": ("assists", "turnovers"),
    "rim_dfg_pct": ("rim_dfgm", "rim_dfga"),
    "pullup_fg_pct": ("pullup_fgm", "pullup_fga"),
    "iso_ppp": ("iso_pts", "iso_poss"),
    "roll_man_ppp": ("roll_man_pts", "roll_man_poss"),
    "putback_ppp": ("putback_pts", "putback_poss"),
}

# The stats the roles are built from (step 4b reads `<stat>_pctile` for each of these).
STATS = [
    "blocks_per100",
    "dreb_pct",
    "rim_dfg_pct",
    "fg3a_rate",
    "fg3_pct",
    "deflections_per100",
    "contested_shots_per100",
    "usg_pct",
    "ast_pct",
    "pnr_bh_poss_per100",
    "iso_poss_per100",
    "pullup_fga_per100",
    "points_per100",
    "iso_ppp",
    "pullup_fg_pct",
    "oreb_pct",
    "roll_man_ppp",
    "putback_ppp",
    "ast_to_tov",
    "screen_assists_per100",
]

# Opponents shooting worse near a defender is good, so this percentile is flipped.
LOWER_IS_BETTER = {"rim_dfg_pct"}

# NBA.com's play-type tables only list players with 10+ possessions of that type
# (`prepare.check_listing_floor` re-checks this on every build), so a blank here means
# "fewer than 10", not "unknown". These blanks rank tied for last instead of left out (D29).
BLANK_MEANS_FEWER_THAN_10 = {"pnr_bh_poss_per100", "iso_poss_per100"}

# Efficiency on fewer attempts than this gets no percentile (D30): stat -> (attempts, minimum).
MIN_ATTEMPTS = {
    "iso_ppp": ("iso_poss", 25),
    "roll_man_ppp": ("roll_man_poss", 25),
    "putback_ppp": ("putback_poss", 25),
    "pullup_fg_pct": ("pullup_fga", 50),
}


def _divide(top: pd.Series, bottom: pd.Series) -> pd.Series:
    """top / bottom, missing (not infinite) when bottom is 0 or either side is missing."""
    return (top / bottom).replace([np.inf, -np.inf], np.nan)


def add_rates(players: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with the per-100 and ratio columns added."""
    require_columns(
        players, ["possessions", *PER_100, *[c for p in RATIOS.values() for c in p]], "player table"
    )
    df = players.copy()
    for stat, new in PER_100.items():
        df[new] = _divide(df[stat], df["possessions"]) * 100
    for new, (top, bottom) in RATIOS.items():
        df[new] = _divide(df[top], df[bottom])
    return df


def qualifying(players: pd.DataFrame, min_minutes: float = MIN_MINUTES) -> pd.DataFrame:
    """Players with enough minutes to be ranked."""
    require_columns(players, ["minutes"], "player table")
    return players[players["minutes"] >= min_minutes]


def percentiles(players: pd.DataFrame, min_minutes: float = MIN_MINUTES) -> pd.DataFrame:
    """League percentiles (0-100, higher is always better) for every stat in STATS.

    Only players with at least `min_minutes` are ranked, against each other. Returns
    `player_id` plus one `<stat>_pctile` column per stat. A missing stat, or efficiency on
    fewer than MIN_ATTEMPTS, gets no percentile; play-type volume blanks rank tied for last.
    """
    ranked = qualifying(add_rates(players), min_minutes)
    require_columns(ranked, ["player_id", *STATS], "player table")
    out = ranked[["player_id"]].reset_index(drop=True)
    for stat in STATS:
        values = ranked[stat]
        if stat in MIN_ATTEMPTS:
            attempts, minimum = MIN_ATTEMPTS[stat]
            values = values.where(ranked[attempts] >= minimum)
        blanks = "top" if stat in BLANK_MEANS_FEWER_THAN_10 else "keep"  # "top" = lowest ranks
        rank = values.reset_index(drop=True).rank(
            pct=True, ascending=stat not in LOWER_IS_BETTER, na_option=blanks
        )
        out[f"{stat}_pctile"] = rank * 100
    return out
