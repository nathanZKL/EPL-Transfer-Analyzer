# Mock data: fictional players, not real

Everything in this folder is **made up**. The players, teams (MVM, FTF, SPS) and salaries do not exist. Every name starts with `Mock` and every row has `data_label = Mock`, so it can never be mistaken for real NBA data.

It exists so that:

- tests run without the internet,
- the app can be demoed offline,
- screenshots for the public repo don't republish NBA.com data (which its terms don't allow).

The columns are a first draft. Step 2 confirms the real NBA.com field names, and these files will be updated to match.

| File | One row per | Notes |
| --- | --- | --- |
| `players.csv` | player | Season totals. `season` is `MOCK`. |
| `salaries.csv` | player salary | Same format a real salary file will use: `source`, `source_url` and `retrieved_on` are required for real rows and blank here. |
