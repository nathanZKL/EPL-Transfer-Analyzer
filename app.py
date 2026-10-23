"""Streamlit entry point. Run with: streamlit run app.py"""

import streamlit as st

from nbavalue import mock_data
from nbavalue.labels import MOCK_WARNING

st.set_page_config(page_title="NBA Player Value Analyzer", layout="wide")

st.title("NBA Player Value Analyzer")
st.caption("Which players best fit the role you need, and who gives the most of it per dollar?")

st.warning(MOCK_WARNING)

st.subheader("Players (mock)")
st.dataframe(mock_data.load_players(), hide_index=True)

st.subheader("Salaries (mock)")
st.dataframe(mock_data.load_salaries(), hide_index=True)

st.info(
    "This is the project skeleton. Real NBA.com stats, salary import, role fit scores "
    "and the value chart arrive in the next steps (see docs/mvp-plan.md)."
)
