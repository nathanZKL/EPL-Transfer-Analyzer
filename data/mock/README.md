# Mock data: fictional players, not real

Everything in this folder is **made up**. The players, teams (MVM, FTF, SPS) and salaries do not exist. Every name starts with `Mock` and every row has `data_label = Mock`, so it can never be mistaken for real NBA data.

It exists so that:

- tests run without the internet,
- the app can be demoed offline,
- screenshots for the public repo don't republish NBA.com data (which its terms don't allow).

`players.csv` uses exactly the same columns as the real `data/processed/players.csv` (`nbavalue/prepare.py`'s `PLAYER_COLUMNS`), and a test enforces it. The numbers are invented but internally consistent: points = 2 × FGM + 3PM + FTM, and offensive + defensive rebounds = total rebounds. Percentages are decimals from 0 to 1, as NBA.com sends them.

| File | One row per | Notes |
| --- | --- | --- |
| `players.csv` | player | Season totals. `season` is `MOCK`, `source` is `Mock`, `fetched_on` is blank. No listed position (the real table has none either). |
| `salaries.csv` | player salary | Same format as a real salary file (`nbavalue/salaries.py`'s `SALARY_COLUMNS`): `source`, `source_url` and `retrieved_on` are required for real rows and blank here. Tests check that every row matches a mock player by name. |
