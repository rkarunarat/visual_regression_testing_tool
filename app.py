import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
import os
import base64
from io import BytesIO
import zipfile

from browser_automation import BrowserManager
from image_comparison import ImageComparator
from result_manager import ResultManager
from config import BROWSERS, DEVICES, VIEWPORT_CONFIGS
from utils import create_download_link
import shutil

# Page configuration
st.set_page_config(
    page_title="Visual Regression Testing Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'current_test_id' not in st.session_state:
    st.session_state.current_test_id = None
if 'browser_manager' not in st.session_state:
    st.session_state.browser_manager = None
if 'stop_testing' not in st.session_state:
    st.session_state.stop_testing = False
if 'test_running' not in st.session_state:
    st.session_state.test_running = False
if 'cleanup_needed' not in st.session_state:
    st.session_state.cleanup_needed = False

def initialize_browser_manager():
    """Initialize browser manager if not already done"""
    if st.session_state.browser_manager is None:
        st.session_state.browser_manager = BrowserManager()

def main():
    # Custom CSS for modern dark green theme
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: #1E3A3A;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E8B57;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #2E8B57;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .stButton > button {
        background: #2E8B57;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: #228B22;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(46, 139, 87, 0.3);
    }
    .stop-button {
        background: #DC143C !important;
    }
    .stop-button:hover {
        background: #B22222 !important;
    }
    .sidebar .stSelectbox > div > div {
        background-color: #1E3A3A;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; font-size: 2.5rem;">🔍 Visual Regression Testing Tool</h1>
        <p style="margin:0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Professional visual comparison across multiple browsers and devices
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for configuration
    with st.sidebar:
        st.markdown("""
        <div style="background: #1E3A3A; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h2 style="color: #2E8B57; margin: 0; font-size: 1.5rem;">⚙️ Test Configuration</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Browser selection
        selected_browsers = st.multiselect(
            "Select Browsers",
            options=list(BROWSERS.keys()),
            default=["Chrome", "Firefox"],
            help="Choose browsers for testing"
        )
        
        # Device selection
        selected_devices = st.multiselect(
            "Select Devices",
            options=list(DEVICES.keys()),
            default=["Desktop", "Mobile"],
            help="Choose device types for testing"
        )
        
        # Comparison settings
        st.markdown("""
        <div style="background: #1E3A3A; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h3 style="color: #2E8B57; margin: 0 0 1rem 0;">🎯 Comparison Settings</h3>
        </div>
        """, unsafe_allow_html=True)
        similarity_threshold = st.slider(
            "Similarity Threshold (%)",
            min_value=50,
            max_value=100,
            value=95,
            help="Minimum similarity percentage to consider images as matching"
        )
        
        wait_time = st.number_input(
            "Page Load Wait Time (seconds)",
            min_value=1,
            max_value=30,
            value=3,
            help="Time to wait for page to fully load"
        )

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["URL Configuration", "Test Results", "Detailed Comparison", "Manage Test Runs"])
    
    with tab1:
        configure_urls_tab(selected_browsers, selected_devices, similarity_threshold, wait_time)
    
    with tab2:
        display_results_tab()
    
    with tab3:
        detailed_comparison_tab()
    
    with tab4:
        manage_test_runs_tab()

def configure_urls_tab(selected_browsers, selected_devices, similarity_threshold, wait_time):
    st.header("URL Configuration")
    
    # URL input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "CSV Upload"],
        horizontal=True
    )
    
    url_pairs = []
    
    if input_method == "Manual Entry":
        st.subheader("Add URL Pairs")
        
        # Dynamic URL pair input
        if 'url_pairs_count' not in st.session_state:
            st.session_state.url_pairs_count = 1
        
        for i in range(st.session_state.url_pairs_count):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                staging_url = st.text_input(f"Staging URL {i+1}", key=f"staging_{i}")
            with col2:
                production_url = st.text_input(f"Production URL {i+1}", key=f"production_{i}")
            with col3:
                st.write("") # Spacer
                if st.button("Remove", key=f"remove_{i}") and st.session_state.url_pairs_count > 1:
                    st.session_state.url_pairs_count -= 1
                    st.rerun()
            
            if staging_url and production_url:
                url_pairs.append({
                    'name': f"Test {i+1}",
                    'staging_url': staging_url,
                    'production_url': production_url
                })
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Add More URLs"):
                st.session_state.url_pairs_count += 1
                st.rerun()
    
    else:  # CSV Upload
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
    
    # Run/Stop test controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not st.session_state.test_running:
            if st.button("Run Visual Regression Tests", type="primary") and url_pairs:
                if not selected_browsers:
                    st.error("Please select at least one browser")
                    return
                if not selected_devices:
                    st.error("Please select at least one device")
                    return
                
                st.session_state.stop_testing = False
                st.session_state.test_running = True
                run_tests(url_pairs, selected_browsers, selected_devices, similarity_threshold, wait_time)
        else:
            st.info("⏳ Test is currently running...")
    
    with col2:
        if st.session_state.test_running:
            st.markdown('<style>.stop-btn button {background: #DC143C !important;}</style>', unsafe_allow_html=True)
            if st.button("🛑 Stop Tests", key="stop_btn", help="Stop the current test run"):
                st.session_state.stop_testing = True
                st.session_state.cleanup_needed = True
                st.warning("⚠️ Stopping tests...")
    
    # Cleanup dialog
    if st.session_state.cleanup_needed:
        st.warning("Tests were stopped mid-process. What would you like to do with partial results?")
        cleanup_col1, cleanup_col2 = st.columns(2)
        
        with cleanup_col1:
            if st.button("🗑️ Clean Up Partial Results"):
                cleanup_partial_results()
                st.session_state.cleanup_needed = False
                st.success("Partial results cleaned up!")
        
        with cleanup_col2:
            if st.button("💾 Keep Partial Results"):
                st.session_state.cleanup_needed = False
                st.info("Partial results preserved.")

def run_tests(url_pairs, browsers, devices, similarity_threshold, wait_time):
    """Run visual regression tests"""
    initialize_browser_manager()
    
    # Create progress indicators
    total_tests = len(url_pairs) * len(browsers) * len(devices)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Add timing info
    start_time = datetime.now()
    timing_text = st.empty()
    current_test = 0
    
    # Initialize result manager
    result_manager = ResultManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_test_id = test_id
    
    # Create results container
    results = []
    
    try:
        for url_pair in url_pairs:
            for browser in browsers:
                for device in devices:
                    # Check for stop signal
                    if st.session_state.stop_testing:
                        status_text.text("🛑 Tests stopped by user")
                        st.session_state.test_running = False
                        return
                    
                    current_test += 1
                    progress = current_test / total_tests
                    progress_bar.progress(progress)
                    
                    # Show detailed status
                    elapsed = (datetime.now() - start_time).total_seconds()
                    avg_time = elapsed / current_test if current_test > 0 else 0
                    remaining = (total_tests - current_test) * avg_time
                    
                    status_text.text(f"Testing {url_pair['name']} on {browser} ({device})... ({current_test}/{total_tests})")
                    timing_text.text(f"⏱️ Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")
                    
                    # Run the actual test
                    result = asyncio.run(run_single_test(
                        url_pair, browser, device, similarity_threshold, wait_time
                    ))
                    
                    if result:
                        results.append(result)
                        result_manager.save_result(test_id, result)
        
        # Store results in session state
        st.session_state.test_results = results
        
        progress_bar.progress(1.0)
        total_time = (datetime.now() - start_time).total_seconds()
        status_text.text("Tests completed!")
        timing_text.text(f"✅ Total time: {total_time:.1f}s")
        st.success(f"Completed {len(results)} tests successfully in {total_time:.1f} seconds!")
        
        # Show quick summary
        if results:
            passed = sum(1 for r in results if r['is_match'])
            failed = len(results) - passed
            st.info(f"📊 Results: {passed} passed, {failed} failed | Average similarity: {sum(r['similarity_score'] for r in results)/len(results):.1f}%")
        
    except Exception as e:
        st.error(f"Error during testing: {str(e)}")
    finally:
        # Reset test state
        st.session_state.test_running = False
        # Cleanup browser manager
        if st.session_state.browser_manager:
            asyncio.run(st.session_state.browser_manager.cleanup())

async def run_single_test(url_pair, browser, device, similarity_threshold, wait_time):
    """Run a single visual regression test"""
    try:
        browser_manager = st.session_state.browser_manager
        
        # Get viewport configuration
        viewport = VIEWPORT_CONFIGS[device]
        
        # Take screenshots
        staging_screenshot = await browser_manager.take_screenshot(
            url_pair['staging_url'], browser, viewport, wait_time
        )
        
        production_screenshot = await browser_manager.take_screenshot(
            url_pair['production_url'], browser, viewport, wait_time
        )
        
        if not staging_screenshot or not production_screenshot:
            return None
        
        # Compare images
        comparator = ImageComparator()
        comparison_result = comparator.compare_images(
            staging_screenshot, production_screenshot, similarity_threshold
        )
        
        # Create result object
        result = {
            'test_name': url_pair['name'],
            'browser': browser,
            'device': device,
            'staging_url': url_pair['staging_url'],
            'production_url': url_pair['production_url'],
            'similarity_score': comparison_result['similarity_score'],
            'is_match': comparison_result['is_match'],
            'staging_screenshot': staging_screenshot,
            'production_screenshot': production_screenshot,
            'diff_image': comparison_result['diff_image'],
            'timestamp': datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        st.error(f"Error in test {url_pair['name']} ({browser}, {device}): {str(e)}")
        return None

def display_results_tab():
    st.header("Test Results")
    
    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return
    
    # Create results DataFrame
    results_data = []
    for result in st.session_state.test_results:
        results_data.append({
            'Test Name': result['test_name'],
            'Browser': result['browser'],
            'Device': result['device'],
            'Similarity (%)': f"{result['similarity_score']:.1f}",
            'Status': "✅ Pass" if result['is_match'] else "❌ Fail",
            'Staging URL': result['staging_url'],
            'Production URL': result['production_url']
        })
    
    df = pd.DataFrame(results_data)
    
    # Summary statistics
    total_tests = len(results_data)
    passed_tests = sum(1 for r in st.session_state.test_results if r['is_match'])
    failed_tests = total_tests - passed_tests
    
    # Modern metrics display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2E8B57; margin: 0;">📊 Total Tests</h3>
            <h2 style="margin: 0.5rem 0 0 0; color: #FAFAFA;">{total_tests}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2E8B57; margin: 0;">✅ Passed</h3>
            <h2 style="margin: 0.5rem 0 0 0; color: #32CD32;">{passed_tests}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2E8B57; margin: 0;">❌ Failed</h3>
            <h2 style="margin: 0.5rem 0 0 0; color: #FF6B6B;">{failed_tests}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        color = "#32CD32" if pass_rate >= 80 else "#FFD700" if pass_rate >= 60 else "#FF6B6B"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2E8B57; margin: 0;">📈 Pass Rate</h3>
            <h2 style="margin: 0.5rem 0 0 0; color: {color};">{pass_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pass", "Fail"])
    with col2:
        browser_filter = st.selectbox("Filter by Browser", ["All"] + list(set(df['Browser'])))
    with col3:
        device_filter = st.selectbox("Filter by Device", ["All"] + list(set(df['Device'])))
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter != "All":
        status_symbol = "✅ Pass" if status_filter == "Pass" else "❌ Fail"
        filtered_df = filtered_df[filtered_df['Status'] == status_symbol]
    if browser_filter != "All":
        filtered_df = filtered_df[filtered_df['Browser'] == browser_filter]
    if device_filter != "All":
        filtered_df = filtered_df[filtered_df['Device'] == device_filter]
    
    # Display results table with selection
    if len(filtered_df) > 0:
        selected_rows = st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Export functionality
        if st.button("Export Results"):
            export_results(df)
    else:
        st.info("No results match the selected filters.")

def detailed_comparison_tab():
    st.header("Detailed Comparison")
    
    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return
    
    # Test selection
    test_options = []
    for i, result in enumerate(st.session_state.test_results):
        label = f"{result['test_name']} - {result['browser']} ({result['device']})"
        test_options.append((label, i))
    
    selected_test = st.selectbox(
        "Select test for detailed comparison:",
        options=range(len(test_options)),
        format_func=lambda x: test_options[x][0]
    )
    
    if selected_test is not None:
        result = st.session_state.test_results[selected_test]
        
        # Test information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Similarity Score", f"{result['similarity_score']:.1f}%")
        with col2:
            st.metric("Status", "Pass" if result['is_match'] else "Fail")
        with col3:
            st.metric("Browser/Device", f"{result['browser']} / {result['device']}")
        
        # Comparison mode selection
        comparison_mode = st.radio(
            "Comparison Mode:",
            ["Side by Side", "Overlay", "Difference Only"],
            horizontal=True
        )
        
        # Display images based on mode
        if comparison_mode == "Side by Side":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Staging")
                st.image(result['staging_screenshot'], use_column_width=True)
                st.caption(result['staging_url'])
            with col2:
                st.subheader("Production")
                st.image(result['production_screenshot'], use_column_width=True)
                st.caption(result['production_url'])
        
        elif comparison_mode == "Overlay":
            st.subheader("Overlay Comparison")
            opacity = st.slider("Staging Opacity", 0.0, 1.0, 0.5, 0.1)
            
            # Create overlay image
            comparator = ImageComparator()
            overlay_image = comparator.create_overlay(
                result['staging_screenshot'],
                result['production_screenshot'],
                opacity
            )
            st.image(overlay_image, use_column_width=True)
        
        elif comparison_mode == "Difference Only":
            st.subheader("Visual Differences")
            if result['diff_image']:
                st.image(result['diff_image'], use_column_width=True)
                st.caption("Red areas indicate differences between staging and production")
            else:
                st.info("No differences detected")

def cleanup_partial_results():
    """Clean up partial test results from interrupted tests"""
    try:
        result_manager = ResultManager()
        if st.session_state.current_test_id:
            result_manager.delete_test_run(st.session_state.current_test_id)
            st.session_state.current_test_id = None
            st.session_state.test_results = []
    except Exception as e:
        st.error(f"Error cleaning up partial results: {e}")

def manage_test_runs_tab():
    """Tab for managing old test runs and storage"""
    st.header("📁 Manage Test Runs")
    
    result_manager = ResultManager()
    test_runs = result_manager.list_test_runs()
    
    if not test_runs:
        st.info("No test runs found.")
        return
    
    # Summary stats
    total_runs = len(test_runs)
    total_size = 0
    try:
        for run in test_runs:
            run_path = result_manager.results_dir / run['test_id']
            if run_path.exists():
                total_size += sum(f.stat().st_size for f in run_path.rglob('*') if f.is_file())
    except:
        total_size = 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Test Runs", total_runs)
    with col2:
        st.metric("Storage Used", f"{total_size / (1024*1024):.1f} MB")
    with col3:
        st.metric("Oldest Run", test_runs[-1]['test_id'][:8] if test_runs else "None")
    
    # Cleanup options
    st.subheader("🧹 Storage Management")
    
    cleanup_col1, cleanup_col2 = st.columns(2)
    
    with cleanup_col1:
        days_to_keep = st.number_input("Keep runs from last N days", min_value=1, max_value=365, value=30)
        if st.button("🗓️ Clean Old Runs"):
            cleaned = result_manager.cleanup_old_results(days_to_keep)
            st.success(f"Cleaned up {cleaned} old test runs")
            st.rerun()
    
    with cleanup_col2:
        if st.button("🗑️ Delete All Runs", type="secondary"):
            if st.checkbox("I understand this will delete all test results"):
                try:
                    shutil.rmtree(result_manager.results_dir)
                    result_manager.results_dir.mkdir(exist_ok=True)
                    result_manager.screenshots_dir.mkdir(exist_ok=True)
                    st.success("All test runs deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting runs: {e}")
    
    # List existing runs
    st.subheader("📊 Existing Test Runs")
    
    if test_runs:
        # Create dataframe for display
        run_data = []
        for run in test_runs:
            # Get summary stats for each run
            stats = result_manager.get_summary_stats(run['test_id'])
            run_data.append({
                'Test ID': run['test_id'],
                'Tests': run['result_count'],
                'Pass Rate': f"{stats.get('pass_rate', 0):.1f}%" if stats else "N/A",
                'Latest Run': run['latest_timestamp'][:19] if run['latest_timestamp'] else "N/A",
                'Actions': run['test_id']
            })
        
        df = pd.DataFrame(run_data)
        
        # Display dataframe
        st.dataframe(
            df.drop('Actions', axis=1),
            width="stretch",
            hide_index=True
        )
        
        # Simple selection using selectbox
        st.subheader("🎯 Select Test Run for Actions")
        if len(test_runs) > 0:
            selected_run_index = st.selectbox(
                "Choose a test run:",
                range(len(test_runs)),
                format_func=lambda x: f"{test_runs[x]['test_id']} ({test_runs[x]['result_count']} tests)"
            )
            
            selected_runs = [test_runs[selected_run_index]['test_id']]
            
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("📊 Load Results"):
                    # Load results from selected run
                    all_results = []
                    for run_id in selected_runs:
                        results = result_manager.load_test_results(run_id)
                        for result in results:
                            # Add run_id for context
                            result['run_id'] = run_id
                            all_results.append(result)
                    st.session_state.test_results = all_results
                    st.success(f"Loaded {len(all_results)} results from test run")
            
            with action_col2:
                if st.button("📥 Export Run"):
                    export_selected_runs(selected_runs, result_manager)
            
            with action_col3:
                if st.button("🗑️ Delete Run", type="secondary"):
                    if st.checkbox("Confirm deletion of this test run"):
                        for run_id in selected_runs:
                            result_manager.delete_test_run(run_id)
                        st.success("Test run deleted")
                        st.rerun()
        else:
            st.info("No test runs available for selection")

def export_selected_runs(run_ids, result_manager):
    """Export selected test runs as ZIP"""
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            for run_id in run_ids:
                results = result_manager.load_test_results(run_id)
                run_dir = result_manager.results_dir / run_id
                
                # Add all files from the run directory
                if run_dir.exists():
                    for file_path in run_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = f"{run_id}/{file_path.relative_to(run_dir)}"
                            zip_file.write(file_path, arc_name)
        
        zip_buffer.seek(0)
        
        # Create download link
        b64 = base64.b64encode(zip_buffer.read()).decode()
        href = f'<a href="data:application/zip;base64,{b64}" download="selected_test_runs.zip">Download Selected Runs</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Export prepared! Click the download link above.")
        
    except Exception as e:
        st.error(f"Error exporting runs: {e}")

def export_results(df):
    """Export test results as CSV and images as ZIP"""
    try:
        # Create ZIP file with results
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add CSV results
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr("test_results.csv", csv_buffer.getvalue())
            
            # Add screenshots and diff images
            for i, result in enumerate(st.session_state.test_results):
                test_folder = f"test_{i+1}_{result['test_name']}_{result['browser']}_{result['device']}"
                test_folder = test_folder.replace(" ", "_").replace("/", "_")
                
                # Save staging screenshot
                if result['staging_screenshot']:
                    staging_bytes = BytesIO()
                    result['staging_screenshot'].save(staging_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/staging.png", staging_bytes.getvalue())
                
                # Save production screenshot
                if result['production_screenshot']:
                    production_bytes = BytesIO()
                    result['production_screenshot'].save(production_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/production.png", production_bytes.getvalue())
                
                # Save diff image
                if result['diff_image']:
                    diff_bytes = BytesIO()
                    result['diff_image'].save(diff_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/diff.png", diff_bytes.getvalue())
        
        zip_buffer.seek(0)
        
        # Create download link
        b64 = base64.b64encode(zip_buffer.read()).decode()
        href = f'<a href="data:application/zip;base64,{b64}" download="visual_regression_results.zip">Download Results</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Results exported successfully!")
        
    except Exception as e:
        st.error(f"Error exporting results: {str(e)}")

if __name__ == "__main__":
    main()
