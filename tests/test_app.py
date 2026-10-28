"""Headless runs of the app. Every test points the app at temporary files, so it never reads
real data that may sit in data/processed/ on Nathan's machine."""

import re
from pathlib import Path

import pandas as pd
import pytest
import streamlit
from streamlit.testing.v1 import AppTest

from nbavalue import board

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"
TABS = ["Shortlist", "Value chart", "Compare players"]


def run_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
    assert not app.exception
    return app


def texts(elements) -> list[str]:
    return [element.value for element in elements]


@pytest.fixture
def no_real_data(tmp_path, monkeypatch):
    monkeypatch.setattr(board, "PLAYERS_PATH", tmp_path / "players.csv")
    monkeypatch.setattr(board, "SALARIES_PATH", tmp_path / "salaries.csv")


@pytest.fixture
def real_data(real_files, monkeypatch):
    players_path, salaries_path = real_files
    monkeypatch.setattr(board, "PLAYERS_PATH", players_path)
    monkeypatch.setattr(board, "SALARIES_PATH", salaries_path)
    return real_files


def test_without_real_data_the_app_shows_labelled_mock_data(no_real_data):
    app = run_app()
    assert any("MOCK DATA" in text for text in texts(app.warning))
    assert app.sidebar.radio[0].value.startswith("Mock") and app.sidebar.radio[0].disabled
    assert [tab.label for tab in app.tabs] == TABS
    for tab in app.tabs:  # every screen says the data is fictional
        assert any("fictional" in text for text in texts(tab.caption))


def test_real_data_credits_nba_com_on_every_screen_and_shows_no_mock_warning(real_data):
    app = run_app()
    assert not any("MOCK DATA" in text for text in texts(app.warning))
    assert any("fetched 2026-01-01" in text for text in texts(app.markdown))
    for tab in app.tabs:
        assert any("Stats: NBA.com" in text for text in texts(tab.caption))


def test_shortlist_and_comparison_tables_appear(real_data):
    app = run_app()
    shortlist, _, compare = app.tabs
    assert len(shortlist.dataframe) >= 1
    assert len(compare.dataframe) == 3  # basics, role fit, stats for the two default players


def test_filters_that_match_nobody_explain_what_to_loosen(no_real_data):
    app = run_app()
    minutes = next(s for s in app.sidebar.slider if s.label == "Min minutes played")
    age = next(s for s in app.sidebar.slider if s.label == "Max age")
    minutes.set_value(minutes.max)
    age.set_value(age.min).run(timeout=60)
    assert any("No players match these filters" in text for text in texts(app.tabs[0].info))


def test_without_a_salary_file_the_value_chart_says_how_to_import(real_data):
    real_data[1].unlink()
    app = run_app()
    assert any("No salaries imported yet" in text for text in texts(app.tabs[1].warning))
    assert any("no salary filter" in text for text in texts(app.sidebar.caption))


def test_layout_style_targets_elements_this_streamlit_version_has():
    """app.py trims Streamlit's top whitespace through its internal `data-testid` names. If an
    upgrade renames one, the style silently stops working; this test catches that instead."""
    ids = set(re.findall(r"data-testid='(\w+)'", APP_PATH.read_text()))
    bundle = Path(streamlit.__file__).parent / "static"
    code = "".join(path.read_text(errors="ignore") for path in bundle.rglob("*.js"))
    assert ids, "app.py no longer styles any Streamlit element; remove this test"
    assert {name for name in ids if name not in code} == set()


def test_a_broken_data_file_shows_an_error_instead_of_crashing(real_data):
    players_path = real_data[0]
    pd.read_csv(players_path).drop(columns=["minutes"]).to_csv(players_path, index=False)
    app = run_app()
    assert any("Couldn't load the data" in text for text in texts(app.error))
    assert not app.tabs
