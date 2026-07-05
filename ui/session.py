"""Streamlit session state initialization."""
import streamlit as st

_NAV_MIGRATION = {
    "Run Tests": "New Test",
    "Manage Test Runs": "History",
}

NAV_OPTIONS = ("New Test", "Results", "History")


def request_nav(page):
    """Queue a navigation change for the next script run."""
    if page in NAV_OPTIONS:
        st.session_state.nav_request = page


def apply_nav_request():
    """Apply a queued navigation change before the nav widget renders."""
    if st.session_state.get("nav_request"):
        st.session_state.nav = st.session_state.pop("nav_request")
    elif st.session_state.nav not in NAV_OPTIONS:
        st.session_state.nav = "New Test"


def init_session_state():
    """Initialize default session state keys."""
    defaults = {
        'test_results': [],
        'current_test_id': None,
        'stop_testing': False,
        'test_running': False,
        'cleanup_needed': False,
        'nav': "New Test",
        'banner_message': None,
        'banner_type': "info",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.nav in _NAV_MIGRATION:
        st.session_state.nav = _NAV_MIGRATION[st.session_state.nav]
