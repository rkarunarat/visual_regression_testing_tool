"""Results page — summary and detailed comparison tabs."""
import pandas as pd
import streamlit as st

from ui.comparison_view import render_comparison_detail
from ui.deps import PLAYWRIGHT_DEVICE_MAP
from ui.export import export_results
from ui.session import request_nav
from utils import format_configured_viewport
from ui.theme import render_page_header


def _result_status(result):
    """Return display status and similarity for one result."""
    if result.get('is_skipped', False):
        return "Skipped", "N/A"
    if result['is_match']:
        return "Pass", f"{result['similarity_score']:.1f}"
    return "Fail", f"{result['similarity_score']:.1f}"


def _build_results_dataframe():
    """Build a display dataframe from session test results."""
    results_data = []
    for result in st.session_state.test_results:
        device_model = PLAYWRIGHT_DEVICE_MAP.get(result['device'], result['device'])
        status, similarity = _result_status(result)
        results_data.append({
            'Test Name': result['test_name'],
            'Browser': result['browser'],
            'Device': f"{result['device']} ({device_model})",
            'Viewport': format_configured_viewport(result),
            'Similarity (%)': similarity,
            'Status': status,
            'Staging URL': result['staging_url'],
            'Production URL': result['production_url'],
            'Skip Reason': result.get('skip_reason', '') if result.get('is_skipped', False) else '',
        })
    return pd.DataFrame(results_data)


def _render_test_results_tab():
    """Show aggregate metrics, filters, table, and export."""
    df = _build_results_dataframe()

    total_tests = len(df)
    passed_tests = sum(
        1 for r in st.session_state.test_results
        if r['is_match'] and not r.get('is_skipped', False)
    )
    failed_tests = sum(
        1 for r in st.session_state.test_results
        if not r['is_match'] and not r.get('is_skipped', False)
    )
    skipped_tests = sum(1 for r in st.session_state.test_results if r.get('is_skipped', False))

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tests", total_tests)
    with col2:
        st.metric("Passed", passed_tests)
    with col3:
        st.metric("Failed", failed_tests)
    with col4:
        st.metric("Skipped", skipped_tests)
    with col5:
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        st.metric("Pass Rate", f"{pass_rate:.1f}%")

    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Pass", "Fail", "Skipped"],
            help="Show only passing, failing, skipped, or all results",
        )
    with col2:
        browser_filter = st.selectbox(
            "Filter by Browser",
            ["All"] + list(set(df['Browser'])),
            help="Limit results to a specific browser",
        )
    with col3:
        device_filter = st.selectbox(
            "Filter by Device",
            ["All"] + list(set(df['Device'])),
            help="Limit results to a specific device type",
        )

    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    if browser_filter != "All":
        filtered_df = filtered_df[filtered_df['Browser'] == browser_filter]
    if device_filter != "All":
        filtered_df = filtered_df[filtered_df['Device'] == device_filter]

    if len(filtered_df) > 0:
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        if st.button("Export Results", help="Prepare a ZIP with CSV + images for download"):
            export_results(df)
    else:
        st.info("No results match the selected filters.")


def _render_detailed_comparison_tab():
    """Show per-test screenshot comparison views."""
    test_options = []
    for i, result in enumerate(st.session_state.test_results):
        label = f"{result['test_name']} - {result['browser']} ({result['device']})"
        test_options.append((label, i))

    selected_test = st.selectbox(
        "Select test for detailed comparison:",
        options=range(len(test_options)),
        format_func=lambda x: test_options[x][0],
    )

    if selected_test is not None:
        render_comparison_detail(selected_test)


def results_page():
    """Show results summary and detailed comparison in separate tabs."""
    render_page_header(
        "Results",
        "Review outcomes, export data, and inspect screenshots for individual tests.",
    )

    if not st.session_state.test_results:
        st.info("No test results yet. Configure URLs on **New Test** and run a comparison.")
        if st.button("Go to New Test"):
            request_nav("New Test")
            st.rerun()
        return

    tab_results, tab_comparison = st.tabs(["Test Results", "Detailed Comparison"])

    with tab_results:
        _render_test_results_tab()

    with tab_comparison:
        _render_detailed_comparison_tab()
