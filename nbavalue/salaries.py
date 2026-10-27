"""Check a salary CSV and match each row to an NBA.com player (decision D18).

Matching uses the normalised name; the team only breaks ties, because traded players
and different team codes (GS vs GSW) make teams unreliable across sites. A row that
can't be matched with certainty is reported for a human, never guessed.
"""

import difflib
import re
import unicodedata
from pathlib import Path

import pandas as pd

from nbavalue.checks import require_columns
from nbavalue.fetch import SEASON
from nbavalue.labels import DataLabel

ROOT = Path(__file__).resolve().parent.parent
SALARY_DIR = ROOT / "data" / "salaries"
SALARY_PATH = SALARY_DIR / f"salaries_{SEASON}.csv"
OVERRIDES_PATH = SALARY_DIR / "overrides.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "salaries.csv"
UNMATCHED_PATH = ROOT / "data" / "processed" / "salary_unmatched.csv"

SALARY_COLUMNS = [
    "player_name",
    "team",
    "season",
    "salary_usd",
    "source",
    "source_url",
    "retrieved_on",
    "data_label",
]
OVERRIDE_COLUMNS = ["player_name", "team", "player_id", "note"]
MATCHED_COLUMNS = ["player_id", *SALARY_COLUMNS, "matched_by"]
UNMATCHED_COLUMNS = [*SALARY_COLUMNS, "reason", "suggestions"]

# Each salary label may only be matched against players carrying the paired label.
PLAYER_LABEL_FOR = {DataLabel.REPORTED_SALARY: DataLabel.NBA_COM, DataLabel.MOCK: DataLabel.MOCK}
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalise_name(name: str) -> str:
    """'Jaren Jackson Jr.' -> 'jaren jackson', 'Nikola Jokić' -> 'nikola jokic'.

    Letters with no plain-ASCII form (such as ø) are dropped; use an override for those.
    """
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"['.]", "", text)  # P.J. -> pj, De'Aaron -> deaaron
    words = re.sub(r"[^a-z0-9]+", " ", text).split()  # Karl-Anthony -> karl anthony
    return " ".join(word for word in words if word not in SUFFIXES)


def _is_blank(column: pd.Series) -> pd.Series:
    return column.astype(str).str.strip() == ""


def _refuse_rows(df: pd.DataFrame, bad: pd.Series, name: str, problem: str) -> None:
    """Raise naming the CSV lines (header is line 1) where `bad` is true."""
    if bad.any():
        lines = ", ".join(str(i + 2) for i in df.index[bad])
        raise ValueError(f"{name}: {problem} (lines {lines})")


def validate_salaries(df: pd.DataFrame, name: str = "salary file") -> pd.DataFrame:
    """Return a checked copy with whole-dollar salaries; raise ValueError on any problem."""
    require_columns(df, SALARY_COLUMNS, name)
    if df.empty:
        raise ValueError(f"{name} has no rows")
    df = df[SALARY_COLUMNS].reset_index(drop=True)

    allowed = f"data_label must be '{DataLabel.REPORTED_SALARY}' or '{DataLabel.MOCK}'"
    _refuse_rows(df, ~df["data_label"].isin(list(PLAYER_LABEL_FOR)), name, allowed)
    labels = set(df["data_label"])
    if len(labels) > 1:
        raise ValueError(f"{name} mixes '{DataLabel.REPORTED_SALARY}' and '{DataLabel.MOCK}' rows")
    is_mock = labels == {DataLabel.MOCK}

    for col in ["player_name", "team"]:
        _refuse_rows(df, _is_blank(df[col]), name, f"{col} is blank")
    season = "MOCK" if is_mock else SEASON
    _refuse_rows(df, df["season"].astype(str) != season, name, f"season must be {season}")

    # Digits only: Excel can save 55224526 as 5.52E+07, which would read back rounded.
    digits = df["salary_usd"].astype(str).str.strip().str.fullmatch(r"\d+")
    salary = pd.to_numeric(df["salary_usd"].where(digits), errors="coerce")
    problem = "salary_usd must be a whole number above 0, digits only (no $, commas or 1.2E+07)"
    _refuse_rows(df, ~(digits & (salary > 0)), name, problem)
    df["salary_usd"] = salary.astype("int64")

    if not is_mock:
        for col in ["source", "source_url", "retrieved_on"]:
            _refuse_rows(df, _is_blank(df[col]), name, f"real salaries need a {col}")
        dates = pd.to_datetime(df["retrieved_on"], format="%Y-%m-%d", errors="coerce")
        _refuse_rows(df, dates.isna(), name, "retrieved_on must be a YYYY-MM-DD date")
    return df


def load_salaries(path: Path = SALARY_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"No salary file at {path}. See the README section 'Import salaries'."
        )
    return validate_salaries(pd.read_csv(path, dtype=str, keep_default_na=False), path.name)


def load_overrides(path: Path = OVERRIDES_PATH) -> pd.DataFrame:
    """The override file is optional; a missing file means no overrides."""
    if not path.exists():
        return pd.DataFrame(columns=OVERRIDE_COLUMNS)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    require_columns(df, OVERRIDE_COLUMNS, path.name)
    for col in ["player_name", "team"]:
        _refuse_rows(df, _is_blank(df[col]), path.name, f"{col} is blank")
    ids = pd.to_numeric(df["player_id"], errors="coerce")
    _refuse_rows(df, ids.isna() | (ids % 1 != 0), path.name, "player_id must be a whole number")
    df["player_id"] = ids.astype("int64")
    return df


def _key(name: str, team: str) -> tuple[str, str]:
    return normalise_name(name), team.strip().upper()


def match_salaries(
    salaries: pd.DataFrame, players: pd.DataFrame, overrides: pd.DataFrame | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split checked salary rows into (matched, unmatched).

    Matched rows gain `player_id` and `matched_by` (override, name, or name + team).
    Unmatched rows gain a `reason` and up to three `suggestions` to copy into overrides.
    """
    require_columns(players, ["player_id", "player_name", "team", "data_label"], "player table")
    wanted = PLAYER_LABEL_FOR[DataLabel(salaries["data_label"].iloc[0])]
    if set(players["data_label"]) != {wanted}:
        raise ValueError(f"These salaries can only be matched against '{wanted}' players")
    if overrides is None:
        overrides = pd.DataFrame(columns=OVERRIDE_COLUMNS)

    unknown_ids = set(overrides["player_id"]) - set(players["player_id"])
    if unknown_ids:
        ids = ", ".join(str(i) for i in sorted(unknown_ids))
        raise ValueError(f"Overrides name player_ids that aren't in the player table: {ids}")
    forced = {_key(row.player_name, row.team): row.player_id for row in overrides.itertuples()}

    by_name: dict[str, list] = {}
    for player in players.itertuples():
        by_name.setdefault(normalise_name(player.player_name), []).append(player)

    matched, unmatched, used = [], [], set()
    for row in salaries.to_dict("records"):
        name_key, team = _key(row["player_name"], row["team"])
        candidates = by_name.get(name_key, [])
        same_team = [p for p in candidates if p.team.upper() == team]
        if (name_key, team) in forced:
            used.add((name_key, team))
            matched.append({**row, "player_id": forced[name_key, team], "matched_by": "override"})
        elif len(candidates) == 1:
            matched.append({**row, "player_id": candidates[0].player_id, "matched_by": "name"})
        elif len(same_team) == 1:
            matched.append(
                {**row, "player_id": same_team[0].player_id, "matched_by": "name + team"}
            )
        else:
            if candidates:
                reason = "several NBA.com players share this name; add an override"
                close = [name_key]
            else:
                reason = (
                    "no NBA.com player with this name: check the spelling, or the player "
                    "played no 2025-26 games (then leave it unmatched, never override)"
                )
                close = difflib.get_close_matches(name_key, list(by_name), n=3, cutoff=0.6)
            options = [p for key in close for p in by_name[key]][:3]
            suggestions = "; ".join(f"{p.player_name} ({p.team}, {p.player_id})" for p in options)
            unmatched.append({**row, "reason": reason, "suggestions": suggestions})

    # An override that fits no salary row is almost always a typo or a different team code.
    unused = [
        f"{row.player_name} ({row.team})"
        for row in overrides.itertuples()
        if _key(row.player_name, row.team) not in used
    ]
    if unused:
        raise ValueError(
            "Overrides that match no salary row (the name and team must be written as in the "
            f"salary file): {', '.join(unused)}"
        )

    matched = pd.DataFrame(matched, columns=MATCHED_COLUMNS)
    twice = matched["player_id"].duplicated(keep=False)
    if twice.any():
        names = ", ".join(sorted(set(matched.loc[twice, "player_name"])))
        raise ValueError(f"More than one salary row matches the same player: {names}")
    return matched, pd.DataFrame(unmatched, columns=UNMATCHED_COLUMNS)


def write_tables(
    matched: pd.DataFrame,
    unmatched: pd.DataFrame,
    processed_path: Path = PROCESSED_PATH,
    unmatched_path: Path = UNMATCHED_PATH,
) -> None:
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    unmatched_path.parent.mkdir(parents=True, exist_ok=True)
    matched.to_csv(processed_path, index=False)
    unmatched.to_csv(unmatched_path, index=False)
