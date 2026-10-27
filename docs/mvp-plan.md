# MVP plan

Agreed with Nathan on 2026-10-23. The working copy of this plan lives in a shared doc; this file is the version the code follows. If they disagree, ask Nathan and update this file.

## The question the MVP answers

> Which NBA players best fit the role I'm looking for, and who gives the most of that role per dollar of salary?

A local Streamlit app built on NBA.com stats from the **2025-26** season, plus salaries imported from a CSV file with a source on every row.

Trades, salary-cap rules and a hosted website are **out of scope** for the MVP (see [Ideas for later](#ideas-for-later)).

## Data limitations (these shaped every feature)

| Limitation | What it means for the MVP |
| --- | --- |
| NBA.com stats are rich: box score, advanced, hustle, tracking and play types. | Roles such as rim protector or 3-and-D wing can be measured directly. |
| [NBA.com terms](https://www.nba.com/terms) allow personal, non-commercial use, require prominent attribution to NBA.com, and bar public republishing and database-style services without consent. | The app runs locally only and credits NBA.com. The repo holds code, never downloaded data. Public screenshots use mock data. |
| `nba_api` is an unofficial wrapper. NBA.com publishes no rate limits; heavy use is reported to cause temporary IP blocks. | Fetch once, cache locally, pause between requests. |
| [Basketball-Reference's data-use policy](https://www.sports-reference.com/data_use.html) says not to build tools from scraped data or use its content to prompt AI. | Not used. |
| Salaries are public facts, but Spotrac and HoopsHype don't state clear terms for bulk use (not verified). | Salaries come from a CSV with a source and date on every row, labelled "Reported salary". An optional scraper may fill it once the chosen site's terms and robots.txt are checked. |
| NBA positions (G, F, C) are loose. | Roles are not tied to a position. Percentiles are league-wide; listed position is shown for context. |
| The 2026-27 season had only just started when this was planned. | The MVP uses full 2025-26 data. |
| Salary-cap and trade rules are complex. | Not modelled. The app ranks fit and value, not trade legality. |
| The cloud environment used for development can't reach NBA.com or salary sites. | Development and tests use mock data. Real fetches run on Nathan's machine. |

## Essential features

1. **Labelled data snapshot.** One command fetches 2025-26 stats from NBA.com into dated local files; a salary CSV is imported alongside. A mock dataset with fictional players supports tests, offline demos and public screenshots. Every value is labelled `NBA.com, fetched on [date]`, `Reported salary, [source], [date]` or `Mock`.
2. **Per-100-possession stats and percentiles**, ranked league-wide, with a minimum-minutes filter.
3. **Role fit scores.** Every player gets a 0–100 score for every role, so one player can fit several. Roles are short lists of weighted stats in a config file.
4. **Value view.** For a chosen role, plot fit against salary and rank by fit percentile minus salary percentile. The value score is labelled as our own estimate, not a fact.
5. **Shortlist, comparison and method page.** Pick a role and filters (team to exclude, max salary, max age, min minutes), compare two or three players side by side, and read how the numbers are made.

### Starter roles

| Role | Stats used |
| --- | --- |
| Rim protector | Blocks, opponent FG% at the rim, defensive rebounds |
| 3-and-D wing | 3-point attempt rate, 3-point %, deflections, contested shots |
| Primary creator | Usage, assist %, pick-and-roll ball-handler possessions |
| Shot creator | Isolation and pull-up attempts, points per 100, efficiency on those plays |
| Interior big | Offensive and defensive rebound %, roll-man and putback efficiency |
| Connector | Assist-to-turnover ratio, screen assists, deflections |

Exact NBA.com field names are confirmed in step 2 against a real fetch.

## Done when

Written on 2026-10-24 from the agreed features above. **Confirmed by Nathan on 2026-10-26** (D24). Every feature also needs passing `pytest`, `ruff check .` and `ruff format --check .`, and tests that run on mock data only.

| Feature | Done when |
| --- | --- |
| 1. Labelled data snapshot | One documented command fetches 2025-26 NBA.com stats into dated files in `data/raw/`, reusing the cache on a second run and pausing between requests. A salary CSV in the agreed format imports and validates, failing loudly on missing columns or sources. Every row carries a label (`NBA.com` + fetch date, `Reported salary` + source and date, or `Mock`). Nathan has run the first real fetch on his machine. |
| 2. Per-100 stats and percentiles | Per-100-possession stats and league-wide percentiles are computed by tested functions. Players under the minimum-minutes cut are excluded from percentiles. Results on the mock dataset match hand-checked values. |
| 3. Role fit scores | All six starter roles are defined in `config/roles.toml`. Every qualifying player gets a 0–100 score for every role. Scores are labelled `Estimate`. Changing a weight in the config changes the ranking without code changes. |
| 4. Value view | For a chosen role, the app plots fit against salary and ranks by fit percentile minus salary percentile. Players without a salary are shown as missing, not dropped or guessed. The value score is labelled as our estimate. |
| 5. Shortlist, comparison, method page | The role and filters (exclude team, max salary, max age, min minutes) change the shortlist. Two or three players can be compared side by side. A method page explains the calculations and limits. Every screen with real stats credits NBA.com. |

## Architecture

See [architecture.md](architecture.md).

## Build steps

Six small pull requests, each reviewable and testable on its own.

1. **Skeleton** – project layout, dependencies, lint and test setup, mock dataset and mock salary file, README. ✅ done (PR #1, merged 2026-10-23)
2. **NBA.com data** – cached, rate-limited fetch for 2025-26, field checks, clean player table. Nathan runs the first real fetch. ✅ done (PR #2, 2026-10-24). Hustle, tracking and play-type tables are deferred to step 4.
3. **Salary import** – CSV format, validation, matching salaries to players. ✅ done (PR #3, 2026-10-25; review fixes D22–D23 in a follow-up PR): `python -m nbavalue.import_salaries` (D18–D23). The optional scraper waits on O1.
4. **Analysis** – split in two PRs (D24), tested on mock data:
   - **4a** – hustle, rim-defence, pull-up and play-type tables (7 more NBA.com requests), per-100 stats and league percentiles for players with 500+ minutes (D25): `nbavalue/analysis.py`.
   - **4b** – `config/roles.toml` (D26), role fit scores and value score.
5. **App** – shortlist, value chart and comparison screens.
6. **Method page and README polish** – method and limits, NBA.com attribution, mock-data screenshots.

## Open decisions

Tracked in [decisions.md](decisions.md#open): salary site, salary matching rule, role weights, minimum minutes, and a few smaller ones.

## Ideas for later

Not in the MVP. New ideas go here, not into the build steps, unless Nathan agrees.


| Idea | Data it needs | Data status |
| --- | --- | --- |
| Team needs view (which roles a roster lacks) | NBA.com stats only | Ready; first candidate after v1 |
| Current-season data with in-season refresh | Same NBA.com endpoints | Ready once enough games are played |
| Contract value (years left, total owed) | Contract lengths and options | Same terms question as salaries |
| Age curves and multi-season trends | Several NBA.com seasons | Available; mind the rate limits |
| Trade checker (salary matching, aprons) | CBA cap rules plus team payrolls | Rules public but complex; payroll data has the salary terms question |
| Injury status | NBA official injury reports | Published as reports, not clean data |
| Adjustable ranking filters: let the user change the 500-minute cut (D25) and the attempt minimums (D30) in the app, with the defaults shown | Nothing new: same data, recalculated | Ready; the thresholds are already single settings in `nbavalue/analysis.py` |
| Injury-prone flag: mark players who missed many games over recent seasons, labelled `Estimate` | Games played per season from NBA.com (several seasons); reasons for absences from injury reports | Games played: available, mind the rate limits. Reasons: not clean data, so a flag can't tell injury from rest, suspension or coach's decision |
| Salaried players with no 2025-26 games (D22): give them an ID and a "no stats" label | NBA.com's full player list (one extra request) | Not fetched yet |
| Hosted public website | Written permission from the NBA | Barred by NBA.com terms without consent |
