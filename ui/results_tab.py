"""Test results summary tab."""
import pandas as pd
import streamlit as st

from ui.deps import PLAYWRIGHT_DEVICE_MAP
from ui.export import export_results


def display_results_tab():
    """Show aggregate metrics and a filterable table of results."""
    st.header("Test Results")

    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return

    results_data = []
    for result in st.session_state.test_results:
        device_model = PLAYWRIGHT_DEVICE_MAP.get(result['device'], result['device'])

        if result.get('is_skipped', False):
            status = "Skipped"
            similarity = "N/A"
        elif result['is_match']:
            status = "Pass"
            similarity = f"{result['similarity_score']:.1f}"
        else:
            status = "Fail"
            similarity = f"{result['similarity_score']:.1f}"

        results_data.append({
            'Test Name': result['test_name'],
            'Browser': result['browser'],
            'Device': f"{result['device']} ({device_model})",
            'Viewport': f"{result.get('viewport_width', '?')}x{result.get('viewport_height', '?')}",
            'Similarity (%)': similarity,
            'Status': status,
            'Staging URL': result['staging_url'],
            'Production URL': result['production_url'],
            'Skip Reason': result.get('skip_reason', '') if result.get('is_skipped', False) else '',
        })

    df = pd.DataFrame(results_data)

    total_tests = len(results_data)
    passed_tests = sum(1 for r in st.session_state.test_results if r['is_match'] and not r.get('is_skipped', False))
    failed_tests = sum(1 for r in st.session_state.test_results if not r['is_match'] and not r.get('is_skipped', False))
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
        status_symbol = {"Pass": "Pass", "Fail": "Fail", "Skipped": "Skipped"}[status_filter]
        filtered_df = filtered_df[filtered_df['Status'] == status_symbol]
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
