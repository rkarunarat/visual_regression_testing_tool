"""Detailed side-by-side comparison tab — backward-compatible wrapper."""
import streamlit as st

from ui.comparison_view import render_comparison_detail
from ui.theme import render_page_header


def detailed_comparison_tab():
    """Provide side-by-side, overlay, and diff visualizations per test."""
    render_page_header(
        "Detailed Comparison",
        "Inspect screenshots side-by-side, overlay views, and visual diffs.",
    )

    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return

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
