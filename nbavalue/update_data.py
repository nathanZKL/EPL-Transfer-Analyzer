"""Fetch NBA.com stats and rebuild data/processed/players.csv.

Run on your own machine with: python -m nbavalue.update_data [--refresh]
"""

import argparse
from pathlib import Path

import pandas as pd

from nbavalue import fetch, prepare


def main(
    argv: list[str] | None = None,
    client: fetch.Client = fetch.nba_api_client,
    raw_dir: Path = fetch.RAW_DIR,
    processed_path: Path = prepare.PROCESSED_PATH,
) -> Path:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="download again even if a saved snapshot exists",
    )
    args = parser.parse_args(argv)

    snapshot = fetch.fetch_all(client=client, raw_dir=raw_dir, refresh=args.refresh)
    print(f"Snapshot: {snapshot}")
    # Printed so the real NBA.com field names can be confirmed (decisions O5).
    for table in fetch.TABLES:
        columns = pd.read_csv(snapshot / f"{table}.csv", nrows=0).columns
        print(f"{table}.csv columns: {', '.join(columns)}")

    players = prepare.build_player_table(snapshot)
    path = prepare.write_player_table(players, processed_path)
    print(f"Wrote {len(players)} players to {path}")
    print("Data: NBA.com (personal, non-commercial use). Never commit data/raw or data/processed.")
    return path


if __name__ == "__main__":
    main()
