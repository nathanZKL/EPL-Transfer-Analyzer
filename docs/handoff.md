# Handoff

A current snapshot for picking up work. Overwrite it at meaningful stopping points; don't append a diary.

**Last updated:** 2026-10-28

## Current objective

The MVP is complete (steps 1–6 merged, PRs #1–#8). This branch, `salaries-hoopshype-dataset`, only records how the real 2025-26 salaries were filled in (D36); the data itself stays on Nathan's machine.

## Done

- Real data on Nathan's machine: 582 players (fetched 2026-10-26), 378 with 500+ minutes.
- Salaries (D36, agreed 2026-10-27): `data/salaries/salaries_2025-26.csv` rebuilt from a third-party dataset of HoopsHype figures (`~/Downloads/player_salaries.csv`, stated as accessed 2026-07-07):
  - 583 players; source `HoopsHype`, `retrieved_on` 2026-07-07, link `https://www.hoopshype.com/salaries/players/<name-slug>/<HoopsHype id>/`.
  - 42 players with several 2025-26 rows (trades, waivers) got the sum; their team is the team of the bigger row (team only breaks ties between namesakes).
  - 10 rows with no HoopsHype id were left out (no link possible): Max Shulga, Alex Antetokounmpo, Chris Manon, Malachi Smith, Tyler Burton, Lucas Williamson, David Muoka, Lawson Lovering, Kyle Mangas, Hayden Gray.
  - The 20 earlier hand-entered rows are kept in `data/salaries/salaries_2025-26.backup.csv`.
  - `data/salaries/overrides.csv`: 14 nickname/spelling fixes (Yang Hansen, Nate Williams, Nic Claxton, Santi Aldama, Dennis Schröder, Herbert Jones, Ronald Holland II, Bub Carrington, Svi Mykhailiuk, Cam Whitmore, Yanic Konan Niederhäuser, David Jones Garcia, Trevon Scott, Nigel Hayes-Davis).
  - Import result before the Spotrac additions: 552 of 583 matched (14 by override); 362 of 378 ranked players had a salary. 30 NBA.com players had none: 8 left out for no HoopsHype id, 22 missing from the dataset's 2025-26 rows (16 of them ranked: Neemias Queta, Moussa Diabaté, Pelle Larsson, Jordan Goodwin, Brandon Williams, Javonte Green, Adem Bona, Bones Hyland, Landry Shamet, Craig Porter Jr., Gary Payton II, Dru Smith, Rob Dillingham, Anthony Gill, Thomas Bryant, Mohamed Diawara).
- The conversion was a one-off script in Claude's scratchpad, not added to the repo.

## Remaining

- Nathan reviews and merges the D36 docs PR.
- Done 2026-10-28: Nathan added the 22 missing players by hand from Spotrac (lines 585–606 of the salary file, `retrieved_on` 2026-10-28); all 22 matched by name. Import now: 574 of 605 matched (14 by override), 31 unmatched (no 2025-26 games), and all 378 ranked players have a salary. Only the 8 left-out small contracts (none ranked) have no salary.
- Optional: replace the Spotrac team/league page links with player pages (Gary Payton II, Rob Dillingham, Andre Jackson Jr. point to the league rankings page); Craig Porter Jr.'s link ends in `cap_total2`, possibly a typo.
- Optional: name who made the salary dataset in D36 if known.

## Known issues

- 31 salary rows stay unmatched: players NBA.com doesn't list because they played no 2025-26 games (e.g. Tyrese Haliburton, Kyrie Irving, Damian Lillard, Fred VanVleet), D22. They must not get overrides.
- The built HoopsHype links are unchecked: HoopsHype answered automated requests with 402, so Claude stopped after three tries.
- **No listed position** in real or mock data: NBA.com's league stats table doesn't return one.
- The value chart's hover details need a mouse; the "Chart as a table" expander has the same numbers for keyboard and screen-reader use.
- Screenshots must be retaken by hand when the screens change.
- Low-priority review notes (not fixed): duplicate override keys silently use the last one; `load_overrides` checks have no tests; duplicate salary rows that are both unmatched aren't flagged.
- Still open: O1 (salary site to scrape, if any; not needed while D36 holds) and O3 (final role weights, now possible with near-full salaries).

## Last verification (2026-10-27, macOS, Python 3.13 via uv, branch `salaries-hoopshype-dataset`)

| Check | Result |
| --- | --- |
| `pytest` | 157 passed (no code changed) |
| `ruff check .` / `ruff format --check .` | Clean |
| `python -m nbavalue.import_salaries` | 574 of 605 matched, 14 by override, 31 unmatched (2026-10-28) |

## Next concrete task

O3: tune the role weights in `config/roles.toml` now that rankings and value scores rest on real data.
