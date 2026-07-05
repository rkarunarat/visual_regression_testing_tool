"""Manage saved test runs and cleanup partial results."""
import logging
import shutil

import pandas as pd
import streamlit as st

from ui.deps import ResultManager
from ui.export import export_selected_runs

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
    """List runs, load/export/delete them, and clean up storage."""
    st.header("Manage Test Runs")

    result_manager = ResultManager()
    test_runs = result_manager.list_test_runs()

    if not test_runs:
        st.info("No test runs found.")
        return

    total_runs = len(test_runs)
    total_size = 0
    try:
        for run in test_runs:
            run_path = result_manager.results_dir / run['test_id']
            if run_path.exists():
                total_size += sum(f.stat().st_size for f in run_path.rglob('*') if f.is_file())
    except Exception:
        total_size = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Test Runs", total_runs)
    with col2:
        st.metric("Storage Used", f"{total_size / (1024*1024):.1f} MB")
    with col3:
        st.metric("Oldest Run", test_runs[-1]['test_id'][:8] if test_runs else "None")

    st.subheader("Storage Management")

    cleanup_col1, cleanup_col2 = st.columns(2)

    with cleanup_col1:
        days_to_keep = st.number_input(
            "Keep runs from last N days",
            min_value=1,
            max_value=365,
            value=30,
            help="Delete runs older than this many days",
        )
        if st.button("Clean Old Runs", key="clean_old_runs"):
            try:
                cleaned = result_manager.cleanup_old_results(days_to_keep)
                st.success(f"Cleaned up {cleaned} old test runs")
                st.rerun()
            except Exception as e:
                st.error(f"Error cleaning old runs: {e}")

    with cleanup_col2:
        confirm_delete = st.checkbox(
            "I understand this will delete all test results",
            key="confirm_delete_all",
        )
        if st.button("Delete All Runs", type="secondary", key="delete_all_runs"):
            if not confirm_delete:
                st.warning("Please confirm deletion by checking the box above.")
            else:
                try:
                    shutil.rmtree(result_manager.results_dir)
                    result_manager.results_dir.mkdir(exist_ok=True)
                    st.session_state.test_results = []
                    st.session_state.current_test_id = None
                    st.success("All test runs deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting runs: {e}")

    st.subheader("Existing Test Runs")

    if test_runs:
        run_data = []
        for run in test_runs:
            stats = result_manager.get_summary_stats(run['test_id'])
            logger.info(
                "Processing run %s: latest_timestamp=%s, stats=%s",
                run['test_id'], run['latest_timestamp'], stats,
            )

            latest_run_display = "N/A"
            if run['latest_timestamp']:
                try:
                    latest_run_display = run['latest_timestamp'][:19]
                except Exception as e:
                    logger.warning("Error formatting timestamp for %s: %s", run['test_id'], e)
                    latest_run_display = "N/A"

            run_data.append({
                'Test ID': run['test_id'],
                'Tests': run['result_count'],
                'Pass Rate': f"{stats.get('pass_rate', 0):.1f}%" if stats else "N/A",
                'Latest Run': latest_run_display,
                'Actions': run['test_id'],
            })

        df = pd.DataFrame(run_data)
        st.dataframe(df.drop('Actions', axis=1), use_container_width=True, hide_index=True)

        st.subheader("Select Test Run for Actions")
        if len(test_runs) > 0:
            selected_run_index = st.selectbox(
                "Choose a test run:",
                range(len(test_runs)),
                format_func=lambda x: (
                    f"{test_runs[x]['test_id']} ({test_runs[x]['result_count']} tests)"
                ),
            )

            selected_runs = [test_runs[selected_run_index]['test_id']]

            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if st.button("Load Results"):
                    try:
                        all_results = []
                        for run_id in selected_runs:
                            results = result_manager.load_test_results(run_id)
                            for result in results:
                                result['run_id'] = run_id
                                all_results.append(result)

                        if all_results:
                            st.session_state.test_results = all_results
                            st.session_state.current_test_id = selected_runs[0]
                            st.success(
                                f"Loaded {len(all_results)} results from test run {selected_runs[0]}",
                            )
                            st.info(
                                "Switch to 'Test Results' or 'Detailed Comparison' tabs "
                                "to view the loaded data",
                            )
                        else:
                            st.warning("No results found in selected test run")
                    except Exception as e:
                        st.error(f"Error loading results: {e}")

            with action_col2:
                if st.button("Export Run"):
                    export_selected_runs(selected_runs, result_manager)

            with action_col3:
                if f"delete_confirm_{selected_runs[0]}" not in st.session_state:
                    st.session_state[f"delete_confirm_{selected_runs[0]}"] = False

                if not st.session_state[f"delete_confirm_{selected_runs[0]}"]:
                    if st.button("Delete Run", type="secondary"):
                        st.session_state[f"delete_confirm_{selected_runs[0]}"] = True
                        st.rerun()
                else:
                    st.warning(f"Really delete test run: {selected_runs[0]}?")
                    col_confirm, col_cancel = st.columns(2)

                    with col_confirm:
                        if st.button("Yes, Delete", type="primary"):
                            try:
                                for run_id in selected_runs:
                                    result_manager.delete_test_run(run_id)
                                if st.session_state.get('current_test_id') in selected_runs:
                                    st.session_state.test_results = []
                                    st.session_state.current_test_id = None
                                st.success(f"Test run {selected_runs[0]} deleted successfully")
                                del st.session_state[f"delete_confirm_{selected_runs[0]}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting test run: {e}")

                    with col_cancel:
                        if st.button("Cancel"):
                            st.session_state[f"delete_confirm_{selected_runs[0]}"] = False
                            st.rerun()
        else:
            st.info("No test runs available for selection")
