"""Manage saved test runs and cleanup partial results."""
import logging

import streamlit as st

from ui.deps import ResultManager

logger = logging.getLogger(__name__)


def cleanup_partial_results():
    """Remove partially saved run directories and reset session state."""
    try:
        result_manager = ResultManager()
        if st.session_state.current_test_id:
            result_manager.delete_test_run(st.session_state.current_test_id)
            st.session_state.current_test_id = None
            st.session_state.test_results = []

        st.session_state.test_running = False
        st.session_state.tests_started = False
        st.session_state.stop_testing = False
        st.session_state.cleanup_needed = False
    except Exception as e:
        st.error(f"Error cleaning up partial results: {e}")


def manage_test_runs_tab():
    """Backward-compatible entry point for the History page."""
    from ui.history_page import history_page

    history_page()
