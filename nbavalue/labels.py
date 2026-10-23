"""Data labels. Every value shown in the app must carry one of these."""

from enum import StrEnum


class DataLabel(StrEnum):
    NBA_COM = "NBA.com"
    REPORTED_SALARY = "Reported salary"
    ESTIMATE = "Estimate"
    MOCK = "Mock"


MOCK_WARNING = (
    "MOCK DATA: every player, team and salary on this page is fictional. "
    "Nothing here is real NBA data."
)
