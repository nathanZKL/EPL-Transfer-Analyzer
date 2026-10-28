"""Streamlit entry point. Run with: streamlit run app.py

Only displays things: every number comes from nbavalue/board.py.
"""

import math

import altair as alt
import pandas as pd
import streamlit as st

from nbavalue import analysis, board, roles
from nbavalue.labels import MOCK_WARNING

FEW_SALARIES = 30  # below this many salaried players, warn that value scores are rough

st.set_page_config(page_title="NBA Player Value Analyzer", layout="wide")
# Streamlit leaves a tall empty band above the page and the sidebar; trim both. Its toolbar
# strip is made see-through so the title can sit under it (only the small menu button is
# there, see .streamlit/config.toml); phones keep room for the sidebar's open button. The
# data-testid names are Streamlit internals; tests/test_app.py fails if an upgrade drops one.
st.markdown(
    """<style>
    [data-testid='stHeader'] {background: transparent;}
    [data-testid='stMainBlockContainer'] {padding-top: 1.5rem;}
    [data-testid='stMainBlockContainer'] h1 {padding-top: 0;}
    @media (max-width: 640px) {[data-testid='stMainBlockContainer'] {padding-top: 3rem;}}
    [data-testid='stSidebarHeader'] {height: 2.5rem; margin-bottom: 0;}
    [data-testid='stSidebarUserContent'] {padding-top: 0;}
    </style>""",
    unsafe_allow_html=True,
)


def file_stamps() -> tuple[tuple[str, float], ...]:
    """Each input file with its last-change time (0 if absent), so the cache below reloads
    when a data file or the role recipes change."""
    paths = (board.PLAYERS_PATH, board.SALARIES_PATH, roles.ROLES_PATH)
    return tuple((str(path), path.stat().st_mtime if path.exists() else 0.0) for path in paths)


@st.cache_data(show_spinner=False)
def load(use_mock: bool, stamps: tuple[tuple[str, float], ...]):
    """Load once per data choice and set of file stamps."""
    data = board.load_mock() if use_mock else board.load_real()
    role_defs = roles.load_roles()
    return data, role_defs, board.build_board(data, role_defs)


def credit(data: board.Dataset) -> None:
    if data.is_mock:
        st.caption("Mock data: every player, team and salary is fictional, made up for testing.")
    else:
        st.caption(
            f"Stats: NBA.com, {data.season} season, fetched {data.fetched_on}. Used for "
            "personal, non-commercial analysis. Salaries: reported figures, source shown per "
            "player. Fit and value scores are our own estimates, not facts."
        )


def recipe(role: roles.Role) -> str:
    total = sum(role.weights.values())
    parts = [
        f"{board.STAT_DISPLAY[stat][0]} {weight / total:.0%}"
        for stat, weight in sorted(role.weights.items(), key=lambda item: -item[1])
    ]
    return "Built from: " + ", ".join(parts) + "."


def sidebar_filters(players: pd.DataFrame) -> board.Filters:
    ranked = players[players["ranked"]]
    st.header("Filters")
    names = board.team_names(ranked["team"].unique())
    exclude = st.multiselect(
        "Leave out teams",
        sorted(names, key=names.get),  # alphabetical by full name; the filter still uses codes
        format_func=names.get,
        placeholder="All teams included",
    )

    salaries = board.salary_range(players)
    max_salary = None
    if salaries is None:
        st.caption("No salaries loaded, so there's no salary filter.")
    else:
        top = math.ceil(salaries[1] / 1e6)
        limit = st.slider(
            "Max salary ($ millions)",
            0,
            top,
            top,
            format="$%dM",
            help="Players with no reported salary stay in the list, shown as missing.",
        )
        max_salary = None if limit >= top else limit * 1e6

    youngest, oldest = int(ranked["age"].min()), int(ranked["age"].max())
    age = st.slider("Max age", youngest, oldest, oldest)
    most = math.ceil(ranked["minutes"].max() / 100) * 100
    minutes = st.slider(
        "Min minutes played",
        analysis.MIN_MINUTES,
        most,
        analysis.MIN_MINUTES,
        step=50,
        help=f"Players under {analysis.MIN_MINUTES} minutes aren't ranked at all.",
    )
    return board.Filters(
        exclude_teams=tuple(exclude),
        max_salary=max_salary,
        max_age=None if age >= oldest else age,
        min_minutes=minutes,
    )


def salary_column() -> st.column_config.NumberColumn:
    """Salaries in millions stay readable in a narrow column and still sort as numbers."""
    return st.column_config.NumberColumn(
        "Salary", format="$%.1fM", help="Salary this season, in millions of dollars."
    )


def in_millions(table: pd.DataFrame) -> pd.DataFrame:
    return table.assign(salary_m=table["salary_usd"] / 1e6)


def not_ranked_note(players: pd.DataFrame) -> None:
    unranked = in_millions(board.not_ranked_with_salary(players))
    if unranked.empty:
        return
    title = (
        f"{len(unranked)} players with a salary aren't ranked (under {analysis.MIN_MINUTES} min)"
    )
    with st.expander(title):
        st.dataframe(
            unranked,
            hide_index=True,
            column_order=["player_name", "team", "minutes", "salary_m"],
            column_config={
                "player_name": "Player",
                "team": "Team",
                "minutes": st.column_config.NumberColumn("Minutes", format="%.0f"),
                "salary_m": salary_column(),
            },
        )


def shortlist_tab(data, players, listed, role_label) -> None:
    ranked = int(players["ranked"].sum())
    st.subheader(f"Best fits: {role_label}")
    st.caption(f"{len(listed)} of {ranked} ranked players match the filters, best fit first.")
    if listed.empty:
        st.info(
            "No players match these filters. Raise the age or salary limit, lower the minutes, "
            "or include more teams."
        )
    else:
        table = in_millions(listed).assign(
            rank=range(1, len(listed) + 1),
            salary_source=[board.salary_source(row) for _, row in listed.iterrows()],
            source_url=listed["source_url"].replace("", None),
        )
        st.caption("A dash means the value is missing, never guessed.")
        st.dataframe(
            table,
            hide_index=True,
            placeholder="—",
            column_order=[
                # The answer first (fit, value, salary), so it shows on a phone screen too.
                "rank",
                "player_name",
                "fit_score",
                "value_score",
                "salary_m",
                "team",
                "age",
                "minutes",
                "salary_source",
                "source_url",
            ],
            column_config={
                "rank": st.column_config.NumberColumn("#", width=40, pinned=True),
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "team": "Team",
                "age": st.column_config.NumberColumn("Age", format="%.0f"),
                "minutes": st.column_config.NumberColumn("Minutes", format="%.0f"),
                "fit_score": st.column_config.ProgressColumn(
                    "Fit (estimate)",
                    min_value=0,
                    max_value=100,
                    format="%.0f",
                    help="0-100: weighted average of this role's stat percentiles. Our estimate.",
                ),
                "value_score": st.column_config.NumberColumn(
                    "Value (estimate)",
                    format="%+.0f",
                    help="Fit percentile minus salary percentile. Above 0: more of the role "
                    "than the salary suggests. Missing when there's no salary.",
                ),
                "salary_m": salary_column(),
                "salary_source": "Salary source",
                "source_url": st.column_config.LinkColumn("Link", display_text="open"),
            },
        )
    not_ranked_note(players)
    credit(data)


def value_chart(plotted: pd.DataFrame, role_label: str, salary_title: str) -> alt.LayerChart:
    edge = max(plotted["value_score"].abs().max(), 1)
    base = alt.Chart(plotted).encode(
        x=alt.X("salary_usd:Q", title=salary_title, axis=alt.Axis(format="$.2s")),
        y=alt.Y(
            "fit_score:Q", title=f"{role_label} fit (estimate)", scale=alt.Scale(domain=[0, 100])
        ),
    )
    dots = base.mark_circle(size=110, opacity=0.95, stroke="#4b5563", strokeWidth=0.8).encode(
        color=alt.Color(
            "value_score:Q",
            title="Value (estimate)",
            scale=alt.Scale(scheme="blueorange", domain=[-edge, edge], reverse=True),
        ),
        tooltip=[
            alt.Tooltip("player_name:N", title="Player"),
            alt.Tooltip("team:N", title="Team"),
            alt.Tooltip("salary_usd:Q", title="Salary", format="$,.0f"),
            alt.Tooltip("fit_score:Q", title="Fit (estimate)", format=".0f"),
            alt.Tooltip("value_score:Q", title="Value (estimate)", format="+.0f"),
            alt.Tooltip("source:N", title="Salary source"),
            alt.Tooltip("retrieved_on:N", title="Salary retrieved"),
        ],
    )
    labels = (
        base.transform_filter(
            alt.FieldOneOfPredicate(
                "player_id", list(plotted.nlargest(5, "value_score")["player_id"])
            )
        )
        .mark_text(align="left", dx=8, fontSize=11)
        .encode(text="player_name:N")
    )
    return (dots + labels).properties(height=440)


def value_tab(data, players, listed, role_label) -> None:
    st.subheader(f"Fit vs salary: {role_label}")
    salaried_ranked = int((players["ranked"] & players["salary_usd"].notna()).sum())
    plotted = listed.dropna(subset=["salary_usd", "fit_score", "value_score"])
    if not data.salary_file_found:
        st.warning(
            "No salaries imported yet, so there's nothing to plot. Add rows to "
            "data/salaries/, then run `python -m nbavalue.import_salaries`. "
            "Fit scores in the shortlist still work."
        )
    elif plotted.empty:
        st.info(
            "None of the players in the current shortlist has a salary. Loosen the filters, "
            "or add their salaries to the salary file."
        )
    else:
        salary_title = "Salary (mock)" if data.is_mock else "Reported salary"
        st.altair_chart(value_chart(plotted, role_label, salary_title), width="stretch")
        st.caption(
            "Higher up = fits the role better. Further left = cheaper. Blue dots give more of "
            "the role than their salary suggests, orange dots less; the five best values are "
            f"named. Value = fit percentile minus salary percentile among the {salaried_ranked} "
            "ranked players with a salary. Our estimate."
        )
        if salaried_ranked < FEW_SALARIES:
            st.warning(
                f"Only {salaried_ranked} ranked players have a salary, so value scores are "
                "rough and will move as you add salaries."
            )
        with st.expander("Chart as a table"):
            st.dataframe(
                in_millions(plotted).sort_values("value_score", ascending=False),
                hide_index=True,
                column_order=["player_name", "team", "salary_m", "fit_score", "value_score"],
                column_config={
                    "player_name": "Player",
                    "team": "Team",
                    "salary_m": salary_column(),
                    "fit_score": st.column_config.NumberColumn("Fit (estimate)", format="%.0f"),
                    "value_score": st.column_config.NumberColumn(
                        "Value (estimate)", format="%+.0f"
                    ),
                },
            )

    missing = listed[listed["salary_usd"].isna()]
    if not missing.empty:
        with st.expander(f"Not on the chart: {len(missing)} players in this list have no salary"):
            best = missing.head(10)  # the shortlist is sorted best fit first
            st.write(
                "Best fits without a salary (worth adding to your salary file): "
                + ", ".join(board.player_label(row) for _, row in best.iterrows())
                + ("." if len(missing) <= 10 else f", and {len(missing) - 10} more.")
            )
    not_ranked_note(players)
    credit(data)


def compare_tab(data, players, listed, role_defs, role) -> None:
    st.subheader("Compare players")
    ranked = players[players["ranked"]].sort_values("player_name")
    labels = {row["player_id"]: board.player_label(row) for _, row in ranked.iterrows()}
    # Start with the top two of the shortlist; after that, keep the user's picks when the
    # role or filters change. One key per dataset, since mock and real ids differ.
    key = "compare_mock" if data.is_mock else "compare_real"
    if key not in st.session_state:
        st.session_state[key] = list(listed["player_id"].head(2))
    picked = st.multiselect(
        "Players to compare (two or three)",
        list(labels),
        key=key,
        format_func=labels.get,
        max_selections=3,
        placeholder="Type a name",
        help=f"Any ranked player ({analysis.MIN_MINUTES}+ minutes), whatever the filters.",
    )
    if len(picked) < 2:
        st.info("Pick at least two players to compare them side by side.")
        credit(data)
        return

    ordered = {role: role_defs[role], **role_defs}  # the chosen role first
    tables = board.compare(data, players, picked, ordered)
    for title, table in tables.items():
        st.markdown(f"**{title}**")
        st.dataframe(
            table,
            hide_index=True,
            height=36 * (len(table) + 1) + 2,
            column_config={table.columns[0]: st.column_config.TextColumn(pinned=True)},
        )
    st.caption(
        "Percentiles rank each player against every player with "
        f"{analysis.MIN_MINUTES}+ minutes. 'Too few attempts' means the stat exists but the "
        "sample is too small to rank (decision D30)."
    )
    credit(data)


real_available = board.real_data_available()
with st.sidebar:
    st.header("Data")
    choice = st.radio(
        "Show",
        ["Real: NBA.com stats", "Mock: fictional players"],
        index=0 if real_available else 1,
        disabled=not real_available,
    )
    if not real_available:
        st.caption(
            "No real data on this computer yet. Run `python -m nbavalue.update_data`, "
            "then `python -m nbavalue.import_salaries`."
        )
use_mock = not real_available or choice.startswith("Mock")

st.title("NBA Player Value Analyzer")
st.caption("Which players best fit the role you need, and who gives the most of it per dollar?")

try:
    with st.spinner("Loading stats and working out role scores..."):
        data, role_defs, players = load(use_mock, file_stamps())
except (ValueError, FileNotFoundError) as err:
    st.error(f"Couldn't load the data. {err}")
    if not use_mock:
        st.info("Fix the file named above and reload, or switch to mock data in the sidebar.")
    st.stop()

if data.is_mock:
    st.warning(MOCK_WARNING)
    st.markdown(f"**Mock season** · {len(players)} fictional players")
else:
    salaried = int(players["salary_usd"].notna().sum())
    st.markdown(
        f"**Season {data.season}** · NBA.com stats fetched {data.fetched_on} · "
        f"{salaried} of {len(players)} players have a reported salary"
    )

with st.sidebar:
    st.header("Role")
    role = st.selectbox(
        "Role you're looking for", list(role_defs), format_func=lambda key: role_defs[key].label
    )
    st.caption(recipe(role_defs[role]))
    filters = sidebar_filters(players)

role_label = role_defs[role].label
listed = board.shortlist(players, role, filters)
shortlist_view, value_view, compare_view = st.tabs(["Shortlist", "Value chart", "Compare players"])
with shortlist_view:
    shortlist_tab(data, players, listed, role_label)
with value_view:
    value_tab(data, players, listed, role_label)
with compare_view:
    compare_tab(data, players, listed, role_defs, role)
