"""Check data/salaries/ and match each salary to an NBA.com player.

Run on your own machine with: python -m nbavalue.import_salaries
Needs data/processed/players.csv first (python -m nbavalue.update_data).
"""

import argparse
from pathlib import Path

import pandas as pd

from nbavalue import prepare, salaries


def main(
    argv: list[str] | None = None,
    salary_path: Path = salaries.SALARY_PATH,
    overrides_path: Path = salaries.OVERRIDES_PATH,
    players_path: Path = prepare.PROCESSED_PATH,
    processed_path: Path = salaries.PROCESSED_PATH,
    unmatched_path: Path = salaries.UNMATCHED_PATH,
) -> Path:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)

    if not players_path.exists():
        raise FileNotFoundError(
            f"No player table at {players_path}. Run python -m nbavalue.update_data first."
        )
    players = pd.read_csv(players_path, keep_default_na=False)
    salary_rows = salaries.load_salaries(salary_path)
    overrides = salaries.load_overrides(overrides_path)

    matched, unmatched = salaries.match_salaries(salary_rows, players, overrides)
    salaries.write_tables(matched, unmatched, processed_path, unmatched_path)

    by_override = (matched["matched_by"] == "override").sum()
    print(f"Matched {len(matched)} of {len(salary_rows)} salary rows ({by_override} by override).")
    if not unmatched.empty:
        print(f"{len(unmatched)} unmatched (also in {unmatched_path}):")
        for row in unmatched.itertuples():
            hint = f" Did you mean: {row.suggestions}?" if row.suggestions else ""
            print(f"  {row.player_name} ({row.team}): {row.reason}.{hint}")
        print(f"Fix a row by adding it to {overrides_path} with the right player_id.")
    without_salary = len(players) - len(matched)
    print(f"{without_salary} NBA.com players have no salary; they stay missing, never guessed.")
    print(f"Wrote {processed_path}. Never commit data/salaries or data/processed.")
    return processed_path


if __name__ == "__main__":
    main()
