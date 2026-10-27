"""Role fit scores and value scores (MVP feature 3 and 4).

Reads role recipes from config/roles.toml, turns a league percentile table into a 0-100 fit
score per role, and compares fit with salary (decision D10). Both scores are our own
estimates, labelled `Estimate`. Missing inputs give missing scores; nothing is guessed.

The percentile table comes from the analysis step: a `player_id` column plus one
`<stat>_pctile` column (0-100, higher is better, NaN when missing) per stat in KNOWN_STATS.
"""

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from nbavalue.checks import require_columns
from nbavalue.labels import DataLabel

ROOT = Path(__file__).resolve().parent.parent
ROLES_PATH = ROOT / "config" / "roles.toml"

# Every stat the percentile table provides. Role recipes may only use these.
KNOWN_STATS = (
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
)
PCTILE_SUFFIX = "_pctile"
ROLE_KEYS = {"label", "weights"}


@dataclass(frozen=True)
class Role:
    label: str
    weights: dict[str, float]  # stat name -> positive weight


def pctile_column(stat: str) -> str:
    return f"{stat}{PCTILE_SUFFIX}"


def _check_role(key: str, raw: object) -> Role:
    """Return a checked Role; raise ValueError naming the role on any problem."""
    if not isinstance(raw, dict):
        raise ValueError(f"role '{key}' must be a table with a label and weights")
    unknown_keys = set(raw) - ROLE_KEYS
    if unknown_keys:
        raise ValueError(f"role '{key}' has unknown keys: {', '.join(sorted(unknown_keys))}")
    label = raw.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"role '{key}' is missing a label")
    weights = raw.get("weights")
    if not isinstance(weights, dict) or not weights:
        raise ValueError(f"role '{key}' has no stats")
    unknown_stats = [stat for stat in weights if stat not in KNOWN_STATS]
    if unknown_stats:
        raise ValueError(f"role '{key}' uses unknown stats: {', '.join(unknown_stats)}")
    for stat, weight in weights.items():
        # bool is a kind of int in Python, so `true` must be refused explicitly.
        is_number = isinstance(weight, int | float) and not isinstance(weight, bool)
        if not is_number or not math.isfinite(weight) or weight <= 0:
            raise ValueError(
                f"role '{key}': weight for {stat} must be a number above 0, got {weight!r}"
            )
    return Role(label=label.strip(), weights={stat: float(w) for stat, w in weights.items()})


def load_roles(path: Path = ROLES_PATH) -> dict[str, Role]:
    """Read and check the role recipes. Raises ValueError on any problem."""
    with open(path, "rb") as file:
        raw = tomllib.load(file)
    if not raw:
        raise ValueError(f"{path} defines no roles")
    return {key: _check_role(key, value) for key, value in raw.items()}


def fit_scores(pctiles: pd.DataFrame, roles: dict[str, Role]) -> pd.DataFrame:
    """One 0-100 fit score column per role: the weighted average of its stat percentiles.

    A player missing any of a role's stats gets a missing score for that role (open question
    O9); it is never filled in. Output: `player_id`, one column per role key, `data_label`.
    """
    needed = sorted({pctile_column(stat) for role in roles.values() for stat in role.weights})
    require_columns(pctiles, ["player_id", *needed], "percentile table")
    if pctiles["player_id"].duplicated().any():
        raise ValueError("percentile table has duplicate player_id values")
    values = pctiles[needed]
    out_of_range = values.notna() & ((values < 0) | (values > 100))
    if out_of_range.any().any():
        bad = ", ".join(values.columns[out_of_range.any()])
        raise ValueError(f"percentile table has values outside 0-100 in: {bad}")

    scores = pd.DataFrame({"player_id": pctiles["player_id"]})
    for key, role in roles.items():
        weights = pd.Series({pctile_column(stat): w for stat, w in role.weights.items()})
        weighted = pctiles[weights.index].mul(weights, axis=1).sum(axis=1, skipna=False)
        scores[key] = weighted / weights.sum()
    scores["data_label"] = str(DataLabel.ESTIMATE)
    return scores.reset_index(drop=True)


def _percentile(values: pd.Series) -> pd.Series:
    """Percentile rank 0-100: the share of players at or below this value (ties averaged)."""
    return values.rank(method="average", pct=True) * 100


def value_scores(fit: pd.DataFrame, salaries: pd.DataFrame, role: str) -> pd.DataFrame:
    """Value for one role = fit percentile minus salary percentile (decision D10).

    Both percentiles are taken among the players who have a fit score for this role and a
    salary. Every player in `fit` is kept; those without a fit score or a salary get missing
    percentiles and a missing value score. `salaries` is the import_salaries output
    (`player_id`, `salary_usd`). Output columns: `player_id`, `fit_score`, `salary_usd`,
    `fit_pctile`, `salary_pctile`, `value_score`, `data_label`.
    """
    require_columns(fit, ["player_id", role], "fit score table")
    require_columns(salaries, ["player_id", "salary_usd"], "salary table")
    if salaries["player_id"].duplicated().any():
        raise ValueError("salary table has more than one salary for a player_id")
    pay = salaries[["player_id", "salary_usd"]].copy()
    try:
        pay["salary_usd"] = pd.to_numeric(pay["salary_usd"])
    except (TypeError, ValueError) as err:
        raise ValueError(f"salary table has a non-numeric salary_usd: {err}") from err
    if (pay["salary_usd"] <= 0).any():
        raise ValueError("salary table has a salary_usd of 0 or less")

    table = fit[["player_id", role]].rename(columns={role: "fit_score"})
    table = table.merge(pay, on="player_id", how="left", validate="one_to_one")
    both = table["fit_score"].notna() & table["salary_usd"].notna()
    table["fit_pctile"] = _percentile(table.loc[both, "fit_score"])
    table["salary_pctile"] = _percentile(table.loc[both, "salary_usd"])
    table["value_score"] = table["fit_pctile"] - table["salary_pctile"]
    table["data_label"] = str(DataLabel.ESTIMATE)
    return table
