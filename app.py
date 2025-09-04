import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
import os
import base64
from io import BytesIO
from pathlib import Path
import zipfile

from browser_manager import BrowserManager
from image_comparator import ImageComparator
from results_store import ResultManager
from config import BROWSERS, DEVICES, VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP
from utils import create_download_link, resize_image_for_display, sanitize_filename
from pathlib import Path
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

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
if 'nav' not in st.session_state:
    st.session_state.nav = "Run Tests"
if 'banner_message' not in st.session_state:
    st.session_state.banner_message = None
if 'banner_type' not in st.session_state:
    st.session_state.banner_type = "info"

def initialize_browser_manager():
    """Initialize browser manager if not already done"""
    if st.session_state.browser_manager is None:
        st.session_state.browser_manager = BrowserManager()

def main():
    # Simple dark theme with subtle green accents
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

    # Global banner (one-shot)
    if st.session_state.banner_message:
        if st.session_state.banner_type == "success":
            st.success(st.session_state.banner_message)
        elif st.session_state.banner_type == "warning":
            st.warning(st.session_state.banner_message)
        elif st.session_state.banner_type == "error":
            st.error(st.session_state.banner_message)
        else:
            st.info(st.session_state.banner_message)
        # Clear after display
        st.session_state.banner_message = None

    # Sidebar navigation
    with st.sidebar:
        nav = st.radio("Navigation", ["Run Tests", "Manage Test Runs"], index=0, key="nav")

    if nav == "Run Tests":
        # Sidebar for configuration (only for Run Tests page)
        with st.sidebar:
            st.header("⚙️ Test Configuration")
            selected_browsers = st.multiselect(
                "Select Browsers",
                options=list(BROWSERS.keys()),
                default=["Chrome"],
                help="Choose browsers for testing"
            )
            selected_devices = st.multiselect(
                "Select Devices",
                options=list(DEVICES.keys()),
                default=["Desktop", "Mobile"],
                help="Choose device types for testing"
            )
            st.subheader("🎯 Comparison Settings")
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
        # Tabs for the main workflow
        tab1, tab2, tab3 = st.tabs(["URL Configuration", "Test Results", "Detailed Comparison"])
        with tab1:
            configure_urls_tab(selected_browsers, selected_devices, similarity_threshold, wait_time)
        with tab2:
            display_results_tab()
        with tab3:
            detailed_comparison_tab()
    elif nav == "Manage Test Runs":
        manage_test_runs_tab()

def _load_image_from_result(record, key):
    try:
        # Try in-memory first
        img = record.get(key)
        if img is not None:
            return img
        # Map key to stored path key
        path_key_map = {
            'staging_screenshot': 'staging',
            'production_screenshot': 'production',
            'diff_image': 'diff'
        }
        spaths = record.get('screenshot_paths', {}) or {}
        rel = spaths.get(path_key_map.get(key, ''), None)
        if rel:
            base = ResultManager().results_dir
            fp = base / rel
            if fp.exists():
                from PIL import Image as _PILImage
                return _PILImage.open(fp)
    except Exception:
        return None
    return None

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
        run_tests_clicked = st.button("Run Visual Regression Tests", type="primary", disabled=st.session_state.test_running)
        
        if run_tests_clicked and url_pairs:
            if not selected_browsers:
                st.error("Please select at least one browser")
                return
            if not selected_devices:
                st.error("Please select at least one device")
                return
            
            # Set test running state immediately for UI
            st.session_state.stop_testing = False
            st.session_state.test_running = True
            st.rerun()  # Refresh to show stop button
    
    with col2:
        if st.session_state.test_running:
            if st.button("🛑 Stop Tests", help="Stop the current test run"):
                st.session_state.stop_testing = True
                st.session_state.cleanup_needed = True
                st.warning("⚠️ Stopping tests...")
    
    # Show current status and run tests if needed
    if st.session_state.test_running and not st.session_state.get('tests_started', False):
        st.session_state.tests_started = True
        st.info("⏳ Starting visual regression tests...")
        run_tests(url_pairs, selected_browsers, selected_devices, similarity_threshold, wait_time)
        st.session_state.tests_started = False
    elif st.session_state.test_running:
        st.info("⏳ Test is currently running...")
    
    # Cleanup dialog
    if st.session_state.cleanup_needed:
        st.warning("Tests were stopped mid-process. What would you like to do with partial results?")
        cleanup_col1, cleanup_col2 = st.columns(2)
        
        with cleanup_col1:
            if st.button("🗑️ Clean Up Partial Results"):
                cleanup_partial_results()
                st.session_state.cleanup_needed = False
                st.session_state.nav = "Run Tests"
                st.session_state.banner_message = "🗑️ Partial results cleared. You can start a new test."
                st.session_state.banner_type = "success"
                st.rerun()
        
        with cleanup_col2:
            if st.button("💾 Keep Partial Results"):
                # Load partial results from disk for current test id
                try:
                    result_manager = ResultManager()
                    if st.session_state.current_test_id:
                        loaded = result_manager.load_test_results(st.session_state.current_test_id)
                        st.session_state.test_results = loaded
                        st.session_state.banner_message = f"💾 Loaded {len(loaded)} results from {st.session_state.current_test_id}. Review them in Test Results/Detailed Comparison."
                        st.session_state.banner_type = "success"
                    else:
                        st.session_state.banner_message = "No current test run found to load."
                        st.session_state.banner_type = "warning"
                except Exception as e:
                    st.session_state.banner_message = f"Error loading partial results: {e}"
                    st.session_state.banner_type = "error"
                finally:
                    st.session_state.cleanup_needed = False
                    st.session_state.nav = "Run Tests"
                    st.rerun()

def run_tests(url_pairs, browsers, devices, similarity_threshold, wait_time):
    """Run visual regression tests"""
    # State already set in UI, just continue
    
    # Use fresh browser managers per test to avoid cross-event-loop issues
    
    # Create progress indicators
    total_tests = len(url_pairs) * len(browsers) * len(devices)
    if total_tests == 0:
        st.warning("No valid browser/device combinations to run.")
        st.session_state.test_running = False
        return
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Add timing info
    start_time = datetime.now()
    timing_text = st.empty()
    current_test = 0
    # Live metrics
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    m_completed = metrics_col1.empty()
    m_passed = metrics_col2.empty()
    m_failed = metrics_col3.empty()
    m_skipped = metrics_col4.empty()
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
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
                    progress_bar.progress(int(progress * 100))
                    
                    # Show detailed status
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if current_test > 1 and current_test < total_tests:
                        avg_time = elapsed / (current_test - 1)  # Use completed tests only
                        remaining = (total_tests - current_test) * avg_time
                        timing_text.text(f"⏱️ Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")
                    else:
                        timing_text.text(f"⏱️ Elapsed: {elapsed:.1f}s")
                    
                    status_text.text(f"Testing {url_pair['name']} on {browser} ({device})... ({current_test}/{total_tests})")
                    
                    # Run the actual test
                    # Run the async single test in this thread
                    result = asyncio.run(
                        run_single_test(url_pair, browser, device, similarity_threshold, wait_time)
                    )
                    
                    if result:
                        results.append(result)
                        result_manager.save_result(test_id, result)
                        if result.get('is_match'):
                            passed_count += 1
                        else:
                            failed_count += 1
        
                    else:
                        skipped_count += 1

                    # Update live metrics
                    m_completed.metric("Completed", f"{current_test}/{total_tests}")
                    m_passed.metric("Passed", passed_count)
                    m_failed.metric("Failed", failed_count)
                    m_skipped.metric("Skipped", skipped_count)
        # Store results in session state
        st.session_state.test_results = results
        
        # Complete the test successfully
        progress_bar.progress(100)
        total_time = (datetime.now() - start_time).total_seconds()
        status_text.text("🎉 All tests completed successfully!")
        timing_text.text(f"✅ Total time: {total_time:.1f}s")
        
        # Show completion status
        if len(results) > 0:
            passed = sum(1 for r in results if r['is_match'])
            failed = len(results) - passed
            
            st.success(f"🎉 Completed {len(results)} tests successfully in {total_time:.1f} seconds!")
            st.success(f"📊 **Results Summary**: {passed} passed, {failed} failed, {skipped_count} skipped | Average similarity: {sum(r['similarity_score'] for r in results)/len(results):.1f}%")
            
            # Show results immediately in expandable section
            with st.expander("📋 Quick Results Summary", expanded=True):
                for i, result in enumerate(results, 1):
                    status = "✅ Pass" if result['is_match'] else "❌ Fail"
                    st.write(f"**Test {i}**: {result['test_name']} - {result['browser']} ({result['device']}) - {status} - {result['similarity_score']:.1f}%")
            
            # Clear guidance for next steps
            st.info("💡 **Next Steps**: Switch to 'Test Results' or 'Detailed Comparison' tabs to view full results and images")
            
            # Small completion animation
            st.toast("🎈 Tests complete!", icon="🎉")
        else:
            st.warning("⚠️ Tests completed but no results were generated. Please check your URLs and try again.")
        
    except Exception as e:
        st.error(f"Error during testing: {str(e)}")
    finally:
        # Reset test state
        st.session_state.test_running = False
        st.session_state.tests_started = False
        # No shared browser manager to clean here
        
        # Don't clear progress indicators immediately, let user see final state

async def run_single_test(url_pair, browser, device, similarity_threshold, wait_time):
    """Run a single visual regression test"""
    try:
        # Use a fresh BrowserManager per test to avoid cross-loop transport issues
        browser_manager = BrowserManager()
        
        # Get viewport configuration
        viewport = VIEWPORT_CONFIGS[device]
        
        # Take screenshots
        staging_capture = await browser_manager.take_screenshot(
            url_pair['staging_url'], browser, viewport, wait_time, device_name=device, return_metrics=True
        )
        production_capture = await browser_manager.take_screenshot(
            url_pair['production_url'], browser, viewport, wait_time, device_name=device, return_metrics=True
        )

        # Unpack images and metrics
        staging_screenshot, staging_metrics = staging_capture if isinstance(staging_capture, tuple) else (staging_capture, {})
        production_screenshot, production_metrics = production_capture if isinstance(production_capture, tuple) else (production_capture, {})
        
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
            'device_model': PLAYWRIGHT_DEVICE_MAP.get(device, device),
            'staging_url': url_pair['staging_url'],
            'production_url': url_pair['production_url'],
            'similarity_score': comparison_result['similarity_score'],
            'is_match': comparison_result['is_match'],
            'staging_screenshot': staging_screenshot,
            'production_screenshot': production_screenshot,
            'diff_image': comparison_result['diff_image'],
            'timestamp': datetime.now().isoformat(),
            'viewport_width': viewport.get('width'),
            'viewport_height': viewport.get('height'),
            'staging_runtime_metrics': staging_metrics,
            'production_runtime_metrics': production_metrics
        }
        
        return result
        
    except Exception as e:
        st.error(f"Error in test {url_pair['name']} ({browser}, {device}): {str(e)}")
        return None
    finally:
        try:
            await browser_manager.cleanup()
        except Exception:
            pass

def display_results_tab():
    st.header("Test Results")
    
    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return
    
    # Create results DataFrame
    results_data = []
    for result in st.session_state.test_results:
        device_model = PLAYWRIGHT_DEVICE_MAP.get(result['device'], result['device'])
        results_data.append({
            'Test Name': result['test_name'],
            'Browser': result['browser'],
            'Device': f"{result['device']} ({device_model})",
            'Viewport': f"{result.get('viewport_width','?')}x{result.get('viewport_height','?')}",
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
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Tests", total_tests)
    with col2:
        st.metric("✅ Passed", passed_tests)
    with col3:
        st.metric("❌ Failed", failed_tests)
    with col4:
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        st.metric("📈 Pass Rate", f"{pass_rate:.1f}%")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pass", "Fail"], help="Show only passing, failing, or all results")
    with col2:
        browser_filter = st.selectbox("Filter by Browser", ["All"] + list(set(df['Browser'])), help="Limit results to a specific browser")
    with col3:
        device_filter = st.selectbox("Filter by Device", ["All"] + list(set(df['Device'])), help="Limit results to a specific device type")
    
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
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export functionality
        if st.button("Export Results", help="Prepare a ZIP with CSV + images for download"):
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

        # Top bar: URLs and Report actions (sticky)
        st.markdown("<style>.sticky-top{position:sticky; top:0; z-index:5; background:var(--background-color,#fff); padding:8px 0; border-bottom:1px solid #eee}</style>", unsafe_allow_html=True)
        st.markdown('<div class="sticky-top">', unsafe_allow_html=True)
        top_left, top_right = st.columns([3, 2])
        with top_left:
            st.markdown("**Staging URL**")
            st.write(f"{result.get('staging_url', 'N/A')}")
            st.markdown("**Production URL**")
            st.write(f"{result.get('production_url', 'N/A')}")
        with top_right:
            st.markdown("**Generate Report**")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Summary PDF", key="btn_pdf_summary_top"):
                    pdf_bytes = generate_pdf(summary_only=True)
                    st.download_button(
                        label="Download Summary PDF",
                        data=pdf_bytes,
                        file_name=build_pdf_filename(summary_only=True),
                        mime="application/pdf",
                        key="dl_pdf_summary_top"
                    )
            with col_b:
                if st.button("Full PDF", key="btn_pdf_full_top"):
                    pdf_bytes = generate_pdf(summary_only=False)
                    st.download_button(
                        label="Download Full PDF",
                        data=pdf_bytes,
                        file_name=build_pdf_filename(summary_only=False),
                        mime="application/pdf",
                        key="dl_pdf_full_top"
                    )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Test information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Similarity Score", f"{result['similarity_score']:.1f}%")
        with col2:
            st.metric("Status", "Pass" if result['is_match'] else "Fail")
        with col3:
            device = result['device']
            device_model = PLAYWRIGHT_DEVICE_MAP.get(device)
            device_display = f"{device} ({device_model})" if device_model and device_model != device else device
            vp = f"{result.get('viewport_width','?')}x{result.get('viewport_height','?')}"
            st.markdown("<style>.wrap-val{font-size:22px; font-weight:600; line-height:1.25; word-break:break-word;}</style>", unsafe_allow_html=True)
            st.caption("Browser / Device")
            st.markdown(f"<div class='wrap-val'>{result['browser']} / {device_display} @ {vp}</div>", unsafe_allow_html=True)
        
        # Comparison mode selection
        comparison_mode = st.radio(
            "Comparison Mode:",
            ["Side by Side", "Overlay", "Difference Only"],
            horizontal=True
        )
        
        # Context chips, including runtime viewport metrics
        chip = lambda text: f"<span style='display:inline-block;padding:2px 8px;margin-right:6px;border:1px solid #ddd;border-radius:999px;font-size:12px;'>{text}</span>"
        device_model = PLAYWRIGHT_DEVICE_MAP.get(result['device'], result['device'])
        vp_cfg = f"{result.get('viewport_width','?')}x{result.get('viewport_height','?')}"
        # Prefer runtime metrics if available (from production capture)
        rt = result.get('production_runtime_metrics') or result.get('staging_runtime_metrics') or {}
        vp_rt = f"{rt.get('innerWidth','?')}x{rt.get('innerHeight','?')}@{rt.get('devicePixelRatio','?')}" if rt else "-"
        status = 'PASS' if result['is_match'] else 'FAIL'
        st.markdown(
            chip(f"Browser: {result['browser']}") +
            chip(f"Device: {device_model}") +
            chip(f"Viewport cfg: {vp_cfg}") +
            chip(f"Viewport rt: {vp_rt}") +
            chip(f"Status: {status}"),
            unsafe_allow_html=True
        )

        # Display images based on mode
        if comparison_mode == "Side by Side":
            st.markdown("<style>[data-testid='stImage']{max-height:70vh; overflow:auto; border:1px solid #eee; border-radius:6px; padding:8px;}</style>", unsafe_allow_html=True)
            staging_loaded = _load_image_from_result(result, 'staging_screenshot')
            production_loaded = _load_image_from_result(result, 'production_screenshot')

            if staging_loaded is None and production_loaded is None:
                st.info("No screenshots available for this test.")
            elif staging_loaded is not None and production_loaded is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Staging")
                    img = resize_image_for_display(staging_loaded, max_width=1200, max_height=1600)
                    st.image(img, use_container_width=True)
                    st.caption(result.get('staging_url', 'URL not available'))
                with col2:
                    st.subheader("Production")
                    img = resize_image_for_display(production_loaded, max_width=1200, max_height=1600)
                    st.image(img, use_container_width=True)
                    st.caption(result.get('production_url', 'URL not available'))
            else:
                # Adaptive single column when only one image is available
                available_label = "Staging" if staging_loaded is not None else "Production"
                available_url = result.get('staging_url') if staging_loaded is not None else result.get('production_url')
                available_img = staging_loaded if staging_loaded is not None else production_loaded
                st.subheader(available_label)
                img = resize_image_for_display(available_img, max_width=1400, max_height=1600)
                st.image(img, use_container_width=True)
                st.caption(available_url or 'URL not available')
        
        elif comparison_mode == "Overlay":
            st.subheader("Overlay Comparison")
            staging_loaded = _load_image_from_result(result, 'staging_screenshot')
            production_loaded = _load_image_from_result(result, 'production_screenshot')
            if staging_loaded is not None and production_loaded is not None:
                opacity = st.slider("Staging Opacity", 0.0, 1.0, 0.5, 0.1)
                with st.spinner("Generating overlay..."):
                    try:
                        comparator = ImageComparator()
                        overlay_image = comparator.create_overlay(staging_loaded, production_loaded, opacity)
                        overlay_resized = resize_image_for_display(overlay_image, max_width=1400, max_height=900)
                        st.image(overlay_resized, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating overlay: {e}")
            else:
                st.error("Both staging and production screenshots are required for overlay comparison")
        
        elif comparison_mode == "Difference Only":
            st.subheader("Visual Differences")
            diff_loaded = _load_image_from_result(result, 'diff_image')
            if diff_loaded is None:
                # Attempt to compute diff on the fly if both images exist
                staging_loaded = _load_image_from_result(result, 'staging_screenshot')
                production_loaded = _load_image_from_result(result, 'production_screenshot')
                if staging_loaded is not None and production_loaded is not None:
                    with st.spinner("Computing visual diff..."):
                        try:
                            comparator = ImageComparator()
                            diff_loaded = comparator.create_difference_image(staging_loaded, production_loaded)
                        except Exception as e:
                            st.error(f"Error generating difference image: {e}")
                            diff_loaded = None
            if diff_loaded is not None:
                img = resize_image_for_display(diff_loaded, max_width=1600, max_height=1600)
                st.image(img, use_container_width=True)
                st.caption("Red areas indicate differences between staging and production")
            else:
                st.info("No differences detected or difference image not available")

        # (Report buttons moved to top)

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
        days_to_keep = st.number_input("Keep runs from last N days", min_value=1, max_value=365, value=30, help="Delete runs older than this many days")
        if st.button("🗓️ Clean Old Runs", key="clean_old_runs"):
            try:
                cleaned = result_manager.cleanup_old_results(days_to_keep)
                st.success(f"Cleaned up {cleaned} old test runs")
                st.rerun()
            except Exception as e:
                st.error(f"Error cleaning old runs: {e}")
    
    with cleanup_col2:
        confirm_delete = st.checkbox("I understand this will delete all test results", key="confirm_delete_all")
        if st.button("🗑️ Delete All Runs", type="secondary", key="delete_all_runs"):
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
            use_container_width=True,
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
                    try:
                        # Load results from selected run
                        all_results = []
                        for run_id in selected_runs:
                            results = result_manager.load_test_results(run_id)
                            for result in results:
                                # Add run_id for context
                                result['run_id'] = run_id
                                all_results.append(result)
                        
                        if all_results:
                            st.session_state.test_results = all_results
                            st.session_state.current_test_id = selected_runs[0]  # Set for current context
                            st.success(f"✅ Loaded {len(all_results)} results from test run {selected_runs[0]}")
                            st.info("🔄 Switch to 'Test Results' or 'Detailed Comparison' tabs to view the loaded data")
                        else:
                            st.warning("No results found in selected test run")
                    except Exception as e:
                        st.error(f"Error loading results: {e}")
            
            with action_col2:
                if st.button("📥 Export Run"):
                    export_selected_runs(selected_runs, result_manager)
            
            with action_col3:
                # Use session state to track delete confirmation
                if f"delete_confirm_{selected_runs[0]}" not in st.session_state:
                    st.session_state[f"delete_confirm_{selected_runs[0]}"] = False
                
                if not st.session_state[f"delete_confirm_{selected_runs[0]}"]:
                    if st.button("🗑️ Delete Run", type="secondary"):
                        st.session_state[f"delete_confirm_{selected_runs[0]}"] = True
                        st.rerun()
                else:
                    st.warning(f"⚠️ Really delete test run: {selected_runs[0]}?")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Yes, Delete", type="primary"):
                            try:
                                for run_id in selected_runs:
                                    result_manager.delete_test_run(run_id)
                                # Clear session if the deleted run was loaded
                                if st.session_state.get('current_test_id') in selected_runs:
                                    st.session_state.test_results = []
                                    st.session_state.current_test_id = None
                                st.success(f"🗑️ Test run {selected_runs[0]} deleted successfully")
                                # Reset confirmation state
                                del st.session_state[f"delete_confirm_{selected_runs[0]}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting test run: {e}")
                    
                    with col_cancel:
                        if st.button("❌ Cancel"):
                            st.session_state[f"delete_confirm_{selected_runs[0]}"] = False
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
        
        # Provide a download button
        data = zip_buffer.read()
        st.download_button(
            label="Download Selected Runs",
            data=data,
            file_name="selected_test_runs.zip",
            mime="application/zip"
        )
        st.success("Export prepared! Use the button above to download.")
        
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
                staging_img = result.get('staging_screenshot')
                if staging_img is not None:
                    staging_bytes = BytesIO()
                    staging_img.save(staging_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/staging.png", staging_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('staging'):
                    try:
                        p = Path('test_results') / result['screenshot_paths']['staging']
                        if p.exists():
                            zip_file.write(p, f"{test_folder}/staging.png")
                    except Exception:
                        pass
                
                # Save production screenshot
                production_img = result.get('production_screenshot')
                if production_img is not None:
                    production_bytes = BytesIO()
                    production_img.save(production_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/production.png", production_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('production'):
                    try:
                        p = Path('test_results') / result['screenshot_paths']['production']
                        if p.exists():
                            zip_file.write(p, f"{test_folder}/production.png")
                    except Exception:
                        pass
                
                # Save diff image
                diff_img = result.get('diff_image')
                if diff_img is not None:
                    diff_bytes = BytesIO()
                    diff_img.save(diff_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/diff.png", diff_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('diff'):
                    try:
                        p = Path('test_results') / result['screenshot_paths']['diff']
                        if p.exists():
                            zip_file.write(p, f"{test_folder}/diff.png")
                    except Exception:
                        pass
        
        zip_buffer.seek(0)

        data = zip_buffer.read()
        st.download_button(label="Download Results (ZIP)", data=data, file_name="visual_regression_results.zip", mime="application/zip")
        st.success("Results exported successfully!")
        
    except Exception as e:
        st.error(f"Error exporting results: {str(e)}")

def build_pdf_filename(summary_only=True):
    results = st.session_state.get('test_results', [])
    total = len(results)
    passed = sum(1 for r in results if r.get('is_match'))
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    test_id = st.session_state.get('current_test_id') or 'run'
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    kind = 'summary' if summary_only else 'full'
    base = f"VisualDiff_{test_id}_{total}tests_{passed}pass_{failed}fail_{pass_rate:.0f}pr_{ts}_{kind}.pdf"
    return sanitize_filename(base)

def generate_pdf(summary_only=True):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 2 * cm
        y = height - margin
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Visual Regression Report")
        y -= 1.2 * cm
        c.setFont("Helvetica", 10)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.drawString(margin, y, f"Generated: {now}")
        y -= 0.7 * cm

        # Cover page: engineering summary
        results = st.session_state.get('test_results', [])
        total = len(results)
        passed = sum(1 for r in results if r.get('is_match'))
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        avg_similarity = (sum(r.get('similarity_score', 0) for r in results) / total) if total > 0 else 0
        browsers = sorted({r.get('browser', 'Unknown') for r in results})
        devices = sorted({r.get('device', 'Unknown') for r in results})
        run_id = st.session_state.get('current_test_id') or 'N/A'

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Executive Summary")
        y -= 0.8 * cm

        c.setFont("Helvetica", 10)
        def draw_kv(label, value):
            nonlocal y
            c.drawString(margin, y, f"{label}:")
            c.drawString(margin + 4.5 * cm, y, str(value))
            y -= 0.6 * cm

        draw_kv("Run ID", run_id)
        draw_kv("Total Tests", total)
        draw_kv("Passed", passed)
        draw_kv("Failed", failed)
        draw_kv("Pass Rate", f"{pass_rate:.1f}%")
        draw_kv("Average Similarity", f"{avg_similarity:.1f}%")
        draw_kv("Browsers", ", ".join(browsers) if browsers else "-")
        draw_kv("Devices", ", ".join(devices) if devices else "-")

        # Separator
        y -= 0.2 * cm
        c.line(margin, y, width - margin, y)
        y -= 0.6 * cm

        # Optional quick table of tests on the cover if space allows
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Tests (name | browser | device | score | status)")
        y -= 0.7 * cm
        c.setFont("Helvetica", 9)
        for r in results:
            line = f"{r['test_name']} | {r['browser']} | {r['device']} | {r['similarity_score']:.1f}% | {'PASS' if r['is_match'] else 'FAIL'}"
            c.drawString(margin, y, line[:170])
            y -= 0.55 * cm
            if y < margin + 1.5 * cm:
                c.showPage(); y = height - margin; c.setFont("Helvetica", 9)

        # Start next section on a new page
        c.showPage()

        if summary_only:
            y = height - margin
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y, "Summary Details")
            y -= 0.9 * cm
            c.setFont("Helvetica", 9)
            for r in results:
                line = f"{r['test_name']} | {r['browser']} | {r['device']} | {r['similarity_score']:.1f}% | {'PASS' if r['is_match'] else 'FAIL'}"
                c.drawString(margin, y, line[:170])
                y -= 0.55 * cm
                if y < margin + 1.0 * cm:
                    c.showPage(); y = height - margin; c.setFont("Helvetica", 9)
        else:
            # Helpers
            from PIL import Image as _PILImage
            from pathlib import Path as _Path
            def _load_img(record, which):
                img = record.get(which)
                if img is not None:
                    return img
                p = record.get('screenshot_paths', {}).get('staging' if which=='staging_screenshot' else 'production' if which=='production_screenshot' else 'diff')
                if p:
                    fp = _Path('test_results') / p
                    try:
                        if fp.exists():
                            return _PILImage.open(fp)
                    except Exception:
                        return None
                return None

            def draw_img_jpeg(pil_img, x, y, max_w, max_h, quality=70):
                if not pil_img:
                    return y
                try:
                    img = pil_img.convert('RGB')
                    iw, ih = img.size
                    scale = min(max_w / iw, max_h / ih, 1.0)
                    dw, dh = int(iw * scale), int(ih * scale)
                    if scale < 1.0:
                        img = img.resize((dw, dh), _PILImage.Resampling.LANCZOS)
                    buf = BytesIO()
                    img.save(buf, format='JPEG', quality=quality, optimize=True)
                    buf.seek(0)
                    ir = ImageReader(buf)
                    c.drawImage(ir, x, y - dh, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                    return y - dh - 0.5 * cm
                except Exception:
                    return y

            comparator = ImageComparator()
            for idx, r in enumerate(results, 1):
                # New page per test for consistent pagination
                if idx > 1:
                    c.showPage()
                y = height - margin
                c.setFont("Helvetica-Bold", 12)
                title = f"{idx}. {r['test_name']} - {r['browser']} ({r['device']})"
                c.drawString(margin, y, title)
                y -= 0.7 * cm
                c.setFont("Helvetica", 9)
                meta = f"Similarity: {r['similarity_score']:.1f}% | Status: {'PASS' if r['is_match'] else 'FAIL'}"
                c.drawString(margin, y, meta)
                y -= 0.5 * cm

                # Load images (fallback to disk if not in memory)
                staging_img = _load_img(r, 'staging_screenshot')
                production_img = _load_img(r, 'production_screenshot')
                diff_img = r.get('diff_image') or _load_img(r, 'diff_image')

                # If mobile, crop extremely tall screenshots to a reasonable window
                try:
                    is_mobile = 'mobile' in str(r.get('device', '')).lower()
                    if is_mobile:
                        vp_h = r.get('viewport_height') or 0
                        # Crop to about 2.5x viewport height or max 2400px
                        crop_h = int(2.5 * vp_h) if vp_h else 2400
                        def _crop_tall(img):
                            if img is None:
                                return None
                            w, h = img.size
                            if h > crop_h:
                                return img.crop((0, 0, w, crop_h))
                            return img
                        staging_img = _crop_tall(staging_img)
                        production_img = _crop_tall(production_img)
                        diff_img = _crop_tall(diff_img)
                except Exception:
                    pass

                # Overlay
                overlay_img = None
                try:
                    if staging_img is not None and production_img is not None:
                        overlay_img = comparator.create_overlay(staging_img, production_img, opacity=0.5)
                except Exception:
                    overlay_img = None

                # Layout: two columns for staging/production, then overlay and diff below
                col_gap = 0.5 * cm
                col_w = (width - 2 * margin - col_gap) / 2
                row_h = (height - 5 * cm) / 3

                # Staging (left) and Production (right)
                y1 = y
                y1 = draw_img_jpeg(staging_img, margin, y1, col_w, row_h)
                y2 = y
                y2 = draw_img_jpeg(production_img, margin + col_w + col_gap, y2, col_w, row_h)
                y = min(y1, y2)

                # Overlay
                y = draw_img_jpeg(overlay_img, margin, y, width - 2 * margin, row_h, quality=65)

                # Diff
                y = draw_img_jpeg(diff_img, margin, y, width - 2 * margin, row_h, quality=65)

                # Guidance note
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(margin, y, "Guidance: In overlay, verify key regions align (header, nav, CTAs, forms). In diff, red shows changes.")
                # No manual pagination here since each test uses its own page
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return b""

if __name__ == "__main__":
    main()
