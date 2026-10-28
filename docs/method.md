# Method: how the numbers are made

This page explains every number the app shows, step by step, and what those numbers can't tell you. Fit and value scores are **our own estimates**, not facts and not NBA ratings.

A test (`tests/test_method_doc.py`) checks the role recipes and cut-offs on this page against the code and `config/roles.toml`, so this page fails the tests if the two disagree.

## The question

*Which players best fit the role I'm looking for, and who gives the most of that role per dollar of salary?*

The app answers it in five steps: collect stats, turn them into rates, rank players against the league, combine the ranks into a fit score per role, and compare fit with salary.

## 1. Where the data comes from

| Source | What it gives | Label in the app |
| --- | --- | --- |
| NBA.com stats, 2025-26 regular season, via the unofficial [`nba_api`](https://github.com/swar/nba_api) package | All player stats below, with the date they were fetched | `NBA.com` |
| A salary CSV you build yourself, one source and link per row | Each player's reported 2025-26 salary | `Reported salary` |
| This app's calculations | Fit scores and value scores | `Estimate` |
| `data/mock/` | Twelve fictional players for tests, demos and the screenshots in the README | `Mock` |

The fetch makes nine requests to NBA.com, a few seconds apart, and saves the answers so it doesn't ask again:

| NBA.com table | Stats used |
| --- | --- |
| Player box score totals | Points, blocks, threes made and attempted, all shots attempted, assists, turnovers, minutes, age |
| Player advanced stats | Possessions, usage %, assist %, offensive and defensive rebound % |
| Hustle stats | Deflections, contested shots, screen assists |
| Defence within 6 feet | Shots opponents made and attempted near the rim with the player as closest defender |
| Pull-up shooting | Pull-up shots made and attempted |
| Play types: pick-and-roll ball handler, isolation, roll man, putbacks | Plays and points of each type |

A player traded mid-season appears once per team in the hustle, defence, pull-up and play-type tables; the app adds those rows up. Rates are worked out afterwards from the season totals, never averaged from per-team rates.

Nothing is filled in. A player missing from a table, or a salary that isn't in your file, stays missing and is shown as a dash or "missing".

## 2. Rates

Raw totals favour players who play a lot, so counting stats are turned into rates:

- **Per 100 possessions:** blocks, deflections, contested shots, screen assists, points, pick-and-roll ball-handler plays, isolation plays and pull-up shots are divided by the player's own possessions and multiplied by 100.
- **Ratios from season totals:** share of shots that are threes, 3-point %, assists per turnover, opponent FG% within 6 ft, pull-up FG%, and points per isolation, roll-man and putback play.
- **Already rates on NBA.com:** usage %, assist %, offensive and defensive rebound %.

## 3. Who is ranked

Only players with at least **500 minutes** are ranked. Below that, a few good or bad games swing the numbers too much. Players under the cut still appear in the data with their salary, but get no percentiles, fit or value score.

## 4. Percentiles

Each stat is turned into a **percentile from 0 to 100** among ranked players: 90 means the player is ahead of about 90% of them. Higher is always better; for opponent FG% within 6 ft, where lower is better for the defender, the order is flipped.

Two rules keep thin samples honest:

- **Minimum attempts for efficiency stats.** On a handful of tries a player can top the league by luck, so below these numbers the stat gets no percentile (it is treated as missing, see step 5):

  | Stat | Minimum attempts |
  | --- | --- |
  | Points per isolation play | 25 |
  | Points per roll-man play | 25 |
  | Points per putback | 25 |
  | Pull-up FG% | 50 |
  | 3-point % | 150 |

- **Play-type volume.** NBA.com only lists a player in a play-type table once they have **10** or more plays of that type. A blank for pick-and-roll ball-handler or isolation plays per 100 therefore means "fewer than 10", which is known to be low, so those blanks rank tied for last instead of being left out.

## 5. Role fit score (0–100)

Each role is a recipe: a few stats and how much each counts. A player's fit score is the **weighted average of their percentiles** for those stats.

If a stat has no percentile for a player (too few attempts, or missing from NBA.com), it is left out of that player's average and the other stats count for more. Nothing is guessed. Only a player with none of the role's stats gets no fit score.

The recipes live in `config/roles.toml`. The weights are starting guesses, not tuned results; change a weight there and the rankings change, no code needed. Weights are relative: 0.4 counts twice as much as 0.2.

| Role | Stats and weights |
| --- | --- |
| Rim protector | Blocks per 100 possessions **0.4** · Opponent FG% within 6 ft (lower is better) **0.4** · Defensive rebound % **0.2** |
| 3-and-D wing | Share of shots that are threes **0.25** · 3-point % **0.3** · Deflections per 100 **0.2** · Contested shots per 100 **0.25** |
| Primary creator | Usage % **0.3** · Assist % **0.4** · Pick-and-roll ball-handler plays per 100 **0.3** |
| Shot creator | Isolation plays per 100 **0.2** · Pull-up shots per 100 **0.2** · Points per 100 **0.25** · Points per isolation play **0.2** · Pull-up FG% **0.15** |
| Interior big | Offensive rebound % **0.3** · Defensive rebound % **0.3** · Points per roll-man play **0.2** · Points per putback **0.2** |
| Connector | Assists per turnover **0.4** · Screen assists per 100 **0.3** · Deflections per 100 **0.3** |

**Example.** A player in the 90th percentile for blocks, the 70th for opponent FG% within 6 ft and the 50th for defensive rebound % has a rim-protector fit of 0.4 × 90 + 0.4 × 70 + 0.2 × 50 = **74**.

## 6. Value score (−100 to +100)

For the chosen role, among ranked players who have both a fit score and a salary:

**value = fit percentile − salary percentile**

- A player in the 80th percentile for fit but only the 30th for salary scores **+50**: much more of the role than their pay suggests.
- A player in the 60th percentile for fit and the 90th for salary scores **−30**.

Players with no salary keep their fit score but get no value score. In the value chart, blue dots are good value and orange dots poor value.

Filters in the sidebar (teams, salary, age, minutes) only hide players. They never change anyone's scores, because every percentile is worked out against the whole league first.

## Limits

- **One season.** Everything is 2025-26 regular-season stats. Injuries, role changes and form within or after that season aren't seen.
- **Stats can't see everything.** Much of defence (positioning, communication, help rotations) isn't in any of these tables. A role score measures what the recipe measures, nothing more.
- **The recipes are guesses.** The weights are starting values chosen before seeing real rankings and still need tuning.
- **No positions.** NBA.com's league stats table doesn't list a position, so the app can't filter by one.
- **Value depends on your salary file.** Salary percentiles are worked out only among players with a salary, so adding salaries moves everyone's value score. With fewer than **30** ranked players priced, the app warns that value scores are rough.
- **Value isn't dollars.** It compares ranks, not money: +50 doesn't mean a player is worth a certain amount more.
- **Players who didn't play are missing.** NBA.com only lists players with at least one 2025-26 game, so a player who missed the whole season has no stats and their salary can't be matched.
- **Unofficial access.** `nba_api` reads NBA.com's own stats pages; it isn't an official NBA service and could change or break.

## Attribution and terms

Player statistics are from **[NBA.com](https://www.nba.com/stats)**, fetched with `nba_api`. This is a personal, non-commercial fan project, not affiliated with or endorsed by the NBA. NBA.com's [terms](https://www.nba.com/terms) allow personal use with attribution but not republishing, so this repository contains code only: the stats are downloaded to your own machine and never committed. The app credits NBA.com, with the fetch date, on every screen that shows real stats.

Salaries come from whatever public source you list in your own salary file; each row carries its source, link and date, and the app shows them.
