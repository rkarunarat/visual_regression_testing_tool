"""New Test page — URLs and run configuration on one screen."""
import logging

import pandas as pd
import streamlit as st

from config import REGIONS
from result_manager import ResultManager
from ui.browsers import ensure_playwright_browsers_installed
from ui.deps import BROWSERS, DEVICES
from ui.manage_tab import cleanup_partial_results
from ui.test_runner import run_tests
from ui.session import request_nav
from ui.theme import render_page_header
from utils import validate_url_pairs

logger = logging.getLogger(__name__)


def _render_test_settings():
    """Collect browsers, devices, region, threshold, and wait time."""
    col1, col2 = st.columns(2)
    with col1:
        selected_browsers = st.multiselect(
            "Browsers",
            options=list(BROWSERS.keys()),
            default=["Chrome"],
            help="Choose browsers for testing",
        )
        selected_devices = st.multiselect(
            "Devices",
            options=list(DEVICES.keys()),
            default=["Desktop", "Mobile"],
            help="Choose device types for testing",
        )
    with col2:
        selected_region = st.selectbox(
            "Region",
            options=["Default"] + list(REGIONS.keys()),
            format_func=lambda x: (
                "Default (No region)" if x == "Default" else f"{REGIONS[x]['name']} ({x})"
            ),
            help="Geo-specific locale, timezone, and language headers",
        )
        if selected_region != "Default":
            region_info = REGIONS[selected_region]
            st.caption(
                f"{region_info['name']} · {region_info['timezone']} · {region_info['locale']}"
            )

        similarity_threshold = st.slider(
            "Similarity Threshold (%)",
            min_value=50,
            max_value=100,
            value=95,
            help="Minimum similarity percentage to consider images as matching",
        )
        wait_time = st.number_input(
            "Page Load Wait (seconds)",
            min_value=1,
            max_value=30,
            value=3,
            help="Time to wait for page to fully load (recommended: 3s for slower sites)",
        )

    return selected_browsers, selected_devices, selected_region, similarity_threshold, wait_time


def _collect_url_pairs():
    """Return URL pairs from manual entry or CSV upload."""
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "CSV Upload"],
        horizontal=True,
    )

    url_pairs = []

    if input_method == "Manual Entry":
        st.subheader("Add URL Pairs")

        if 'url_pairs_count' not in st.session_state:
            st.session_state.url_pairs_count = 1

        for i in range(st.session_state.url_pairs_count):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                staging_url = st.text_input(f"Staging URL {i+1}", key=f"staging_{i}")
            with col2:
                production_url = st.text_input(f"Production URL {i+1}", key=f"production_{i}")
            with col3:
                st.write("")
                if st.button("Remove", key=f"remove_{i}") and st.session_state.url_pairs_count > 1:
                    st.session_state.url_pairs_count -= 1
                    st.rerun()

            if staging_url and production_url:
                url_pairs.append({
                    'name': f"Test {i+1}",
                    'staging_url': staging_url,
                    'production_url': production_url,
                })

        col1, _ = st.columns([1, 4])
        with col1:
            if st.button("Add More URLs"):
                st.session_state.url_pairs_count += 1
                st.rerun()

    else:
        st.subheader("Upload CSV File")
        st.markdown("CSV should have columns: name, staging_url, production_url")

        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if all(col in df.columns for col in ['name', 'staging_url', 'production_url']):
                    url_pairs = df.to_dict('records')
                    st.success(f"Loaded {len(url_pairs)} URL pairs")
                    st.dataframe(df)
                else:
                    st.error("CSV must have columns: name, staging_url, production_url")
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")

    return url_pairs


def _handle_run_controls(
    url_pairs,
    selected_browsers,
    selected_devices,
    similarity_threshold,
    wait_time,
    selected_region,
):
    """Start, stop, and execute test runs."""
    col1, col2 = st.columns([2, 1])

    with col1:
        run_tests_clicked = st.button(
            "Run Visual Regression Tests",
            type="primary",
            disabled=st.session_state.test_running,
        )

        if run_tests_clicked and url_pairs:
            if not selected_browsers:
                st.error("Please select at least one browser")
                return
            if not selected_devices:
                st.error("Please select at least one device")
                return

            invalid_urls = validate_url_pairs(url_pairs)
            if invalid_urls:
                for name, field, url in invalid_urls:
                    st.error(f"Invalid {field.replace('_', ' ')} in '{name}': {url}")
                st.info("Only http/https URLs are allowed. Cloud metadata endpoints are blocked.")
                return

            logger.info("Starting visual regression tests...")
            logger.info(
                "Configuration: %s URLs, %s browsers, %s devices",
                len(url_pairs), len(selected_browsers), len(selected_devices),
            )
            logger.info("Settings: %s%% threshold, %ss wait time", similarity_threshold, wait_time)

            st.info("**Starting tests...** Initializing browsers and preparing test environment...")
            st.session_state.stop_testing = False
            st.session_state.test_running = True
            st.rerun()

    with col2:
        if st.session_state.test_running:
            if st.button("Stop Tests", help="Stop the current test run"):
                st.session_state.stop_testing = True
                st.session_state.cleanup_needed = True
                st.warning("Stopping tests...")

    if st.session_state.test_running and not st.session_state.get('tests_started', False):
        st.session_state.tests_started = True
        st.info("Starting visual regression tests...")
        run_tests(url_pairs, selected_browsers, selected_devices, similarity_threshold, wait_time, selected_region)
        st.session_state.tests_started = False
    elif st.session_state.test_running:
        st.info("Test is currently running...")

    if st.session_state.cleanup_needed:
        st.warning("Tests were stopped mid-process. What would you like to do with partial results?")
        cleanup_col1, cleanup_col2 = st.columns(2)

        with cleanup_col1:
            if st.button("Clean Up Partial Results"):
                cleanup_partial_results()
                st.session_state.cleanup_needed = False
                st.session_state.banner_message = "Partial results cleared. You can start a new test."
                st.session_state.banner_type = "success"
                st.rerun()

        with cleanup_col2:
            if st.button("Keep Partial Results"):
                try:
                    result_manager = ResultManager()
                    if st.session_state.current_test_id:
                        loaded = result_manager.load_test_results(st.session_state.current_test_id)
                        st.session_state.test_results = loaded
                        request_nav("Results")
                        st.session_state.banner_message = (
                            f"Loaded {len(loaded)} results from {st.session_state.current_test_id}. "
                            "Review them on the Results page."
                        )
                        st.session_state.banner_type = "success"
                    else:
                        st.session_state.banner_message = "No current test run found to load."
                        st.session_state.banner_type = "warning"
                except Exception as e:
                    st.session_state.banner_message = f"Error loading partial results: {e}"
                    st.session_state.banner_type = "error"
                finally:
                    st.session_state.cleanup_needed = False
                    st.session_state.test_running = False
                    st.session_state.tests_started = False
                    st.session_state.stop_testing = False
                    st.rerun()


def new_test_page():
    """Render the unified New Test configuration and run page."""
    render_page_header(
        "New Test",
        "Configure browsers, devices, and URLs, then launch a visual regression run.",
    )

    if not st.session_state.get("_pw_browsers_ready"):
        if st.button("Setup Browsers", type="primary"):
            ensure_playwright_browsers_installed()
            st.rerun()
        st.info("Browsers need to be set up before running tests. Click the button above.")
        return

    st.subheader("Test Settings")
    selected_browsers, selected_devices, selected_region, similarity_threshold, wait_time = (
        _render_test_settings()
    )

    st.divider()
    st.subheader("URL Pairs")
    url_pairs = _collect_url_pairs()

    st.divider()
    _handle_run_controls(
        url_pairs,
        selected_browsers,
        selected_devices,
        similarity_threshold,
        wait_time,
        selected_region,
    )
