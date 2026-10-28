"""docs/method.md types its numbers by hand; these checks fail when the code or
config/roles.toml changes and the method page doesn't."""

import re
from pathlib import Path

import pytest

from nbavalue import analysis, board, prepare, roles

ROOT = Path(__file__).resolve().parent.parent
METHOD = (ROOT / "docs" / "method.md").read_text()
FIX = "update docs/method.md to match"


@pytest.mark.parametrize("key", list(roles.load_roles()))
def test_role_recipe_matches_the_config(key):
    role = roles.load_roles()[key]
    stats = " · ".join(f"{board.STAT_DISPLAY[s][0]} **{w:g}**" for s, w in role.weights.items())
    assert f"| {role.label} | {stats} |" in METHOD, f"recipe for {role.label}: {FIX}"


def test_method_lists_every_role_and_no_others():
    rows = [line for line in METHOD.splitlines() if line.startswith("| ") and " **" in line]
    assert len(rows) == len(roles.load_roles()), FIX


def test_minutes_cut_matches_the_code():
    assert f"at least **{analysis.MIN_MINUTES} minutes**" in METHOD, FIX


@pytest.mark.parametrize("stat", list(analysis.MIN_ATTEMPTS))
def test_minimum_attempts_match_the_code(stat):
    minimum = analysis.MIN_ATTEMPTS[stat][1]
    assert f"| {board.STAT_DISPLAY[stat][0]} | {minimum} |" in METHOD, f"{stat}: {FIX}"


def test_play_type_listing_floor_matches_the_code():
    assert f"**{prepare.LISTING_FLOOR}** or more plays" in METHOD, FIX


def test_few_salaries_warning_matches_the_app():
    # Read from the source: importing app.py would start the Streamlit page.
    few = re.search(r"^FEW_SALARIES = (\d+)", (ROOT / "app.py").read_text(), re.MULTILINE)
    assert few and f"fewer than **{few[1]}** ranked players" in METHOD, FIX
