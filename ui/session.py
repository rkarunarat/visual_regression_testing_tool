"""Streamlit session state initialization."""
import streamlit as st


def init_session_state():
    """Initialize default session state keys."""
    defaults = {
        'test_results': [],
        'current_test_id': None,
        'stop_testing': False,
        'test_running': False,
        'cleanup_needed': False,
        'nav': "Run Tests",
        'banner_message': None,
        'banner_type': "info",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
