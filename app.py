"""Streamlit UI entry point for the Visual Regression Testing Tool."""
import logging
import warnings

import streamlit as st

from ui.about_tab import about_tab
from ui.auth import require_auth
from ui.deps import IMPORTS_OK
from ui.history_page import history_page
from ui.new_test_page import new_test_page
from ui.results_page import results_page
from ui.session import apply_nav_request, init_session_state, NAV_OPTIONS
from ui.theme import (
    inject_global_styles,
    render_footer,
    render_hero,
    sidebar_divider,
    sidebar_label,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")

st.set_page_config(
    page_title="Visual Regression Testing Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()


def main():
    """Render the Streamlit app and orchestrate navigation and actions."""
    apply_nav_request()
    inject_global_styles()

    if not require_auth():
        return

    if not IMPORTS_OK:
        st.error("**Dependency Error**: Some required modules failed to import.")
        st.info(
            "This usually happens during the first deployment. "
            "Please wait a moment and refresh the page.",
        )
        st.stop()

    render_hero()

    if st.session_state.banner_message:
        if st.session_state.banner_type == "success":
            st.success(st.session_state.banner_message)
        elif st.session_state.banner_type == "warning":
            st.warning(st.session_state.banner_message)
        elif st.session_state.banner_type == "error":
            st.error(st.session_state.banner_message)
        else:
            st.info(st.session_state.banner_message)
        st.session_state.banner_message = None

    with st.sidebar:
        sidebar_label("Navigation")
        nav = st.radio(
            "Navigation",
            list(NAV_OPTIONS),
            key="nav",
            label_visibility="collapsed",
        )

        sidebar_divider()
        if st.button("About", use_container_width=True):
            st.session_state.show_about = True

    if st.session_state.get("show_about"):
        about_tab()
        if st.button("Back to app"):
            st.session_state.show_about = False
            st.rerun()
    elif nav == "New Test":
        new_test_page()
    elif nav == "Results":
        results_page()
    elif nav == "History":
        history_page()

    render_footer()


if __name__ == "__main__":
    main()
