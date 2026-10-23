from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_runs_and_shows_mock_warning():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)

    assert not app.exception
    assert any("MOCK DATA" in w.value for w in app.warning)
    assert len(app.dataframe) == 2
