"""Input checks shared by every data loader."""

import pandas as pd


def require_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    """Stop with a clear message if a table is missing any expected column."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(missing)}")
