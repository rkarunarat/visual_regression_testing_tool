"""Streamlit UI entry point for the Visual Regression Testing Tool."""
import logging
import warnings

import streamlit as st

from config import REGIONS
from ui.about_tab import about_tab
from ui.auth import require_auth
from ui.comparison_tab import detailed_comparison_tab
from ui.config_tab import configure_urls_tab
from ui.deps import BROWSERS, DEVICES, IMPORTS_OK
from ui.manage_tab import manage_test_runs_tab
from ui.results_tab import display_results_tab
from ui.session import init_session_state

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
    if not require_auth():
        return

    if not IMPORTS_OK:
        st.error("**Dependency Error**: Some required modules failed to import.")
        st.info(
            "This usually happens during the first deployment. "
            "Please wait a moment and refresh the page.",
        )
        st.stop()

    st.markdown("""
    <style>
    .stButton > button[kind="primary"] {
        background: #2E8B57;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #228B22;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔍 Visual Regression Testing Tool")
    st.markdown("Professional visual comparison across multiple browsers and devices")

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
        nav = st.radio("Navigation", ["Run Tests", "Manage Test Runs", "About"], index=0, key="nav")

    if nav == "Run Tests":
        with st.sidebar:
            st.header("⚙️ Test Configuration")
            selected_browsers = st.multiselect(
                "Select Browsers",
                options=list(BROWSERS.keys()),
                default=["Chrome"],
                help="Choose browsers for testing",
            )
            selected_devices = st.multiselect(
                "Select Devices",
                options=list(DEVICES.keys()),
                default=["Desktop", "Mobile"],
                help="Choose device types for testing",
            )
            selected_region = st.selectbox(
                "🌍 Select Region",
                options=["Default"] + list(REGIONS.keys()),
                format_func=lambda x: (
                    "Default (No region)" if x == "Default" else f"{REGIONS[x]['name']} ({x})"
                ),
                help="Choose region for geo-specific testing (affects locale, timezone, and language headers)",
            )
            if selected_region != "Default":
                region_info = REGIONS[selected_region]
                st.info(
                    f"**{region_info['name']}** - Timezone: {region_info['timezone']}, "
                    f"Locale: {region_info['locale']}",
                )
            st.subheader("🎯 Comparison Settings")
            similarity_threshold = st.slider(
                "Similarity Threshold (%)",
                min_value=50,
                max_value=100,
                value=95,
                help="Minimum similarity percentage to consider images as matching",
            )
            wait_time = st.number_input(
                "Page Load Wait Time (seconds)",
                min_value=1,
                max_value=30,
                value=3,
                help="Time to wait for page to fully load (recommended: 3s for slower sites)",
            )

        tab1, tab2, tab3 = st.tabs(["URL Configuration", "Test Results", "Detailed Comparison"])
        with tab1:
            configure_urls_tab(
                selected_browsers, selected_devices, similarity_threshold, wait_time, selected_region,
            )
        with tab2:
            display_results_tab()
        with tab3:
            detailed_comparison_tab()
    elif nav == "Manage Test Runs":
        manage_test_runs_tab()
    elif nav == "About":
        about_tab()

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center; opacity:0.8; font-size:13px;'>"
        "Made with ❤️ by Roshan Karunarathna</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
