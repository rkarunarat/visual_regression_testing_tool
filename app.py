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

def initialize_browser_manager():
    """Initialize browser manager if not already done"""
    if st.session_state.browser_manager is None:
        st.session_state.browser_manager = BrowserManager()

def main():
    st.title("🔍 Visual Regression Testing Tool")
    st.markdown("Compare staging and production URLs across multiple browsers and devices")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Test Configuration")
        
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
        st.subheader("Comparison Settings")
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
    tab1, tab2, tab3 = st.tabs(["URL Configuration", "Test Results", "Detailed Comparison"])
    
    with tab1:
        configure_urls_tab(selected_browsers, selected_devices, similarity_threshold, wait_time)
    
    with tab2:
        display_results_tab()
    
    with tab3:
        detailed_comparison_tab()

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
    
    # Run tests
    if st.button("Run Visual Regression Tests", type="primary") and url_pairs:
        if not selected_browsers:
            st.error("Please select at least one browser")
            return
        if not selected_devices:
            st.error("Please select at least one device")
            return
        
        run_tests(url_pairs, selected_browsers, selected_devices, similarity_threshold, wait_time)

def run_tests(url_pairs, browsers, devices, similarity_threshold, wait_time):
    """Run visual regression tests"""
    initialize_browser_manager()
    
    # Create progress indicators
    total_tests = len(url_pairs) * len(browsers) * len(devices)
    progress_bar = st.progress(0)
    status_text = st.empty()
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
                    current_test += 1
                    progress = current_test / total_tests
                    progress_bar.progress(progress)
                    status_text.text(f"Testing {url_pair['name']} on {browser} ({device})...")
                    
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
        status_text.text("Tests completed!")
        st.success(f"Completed {len(results)} tests successfully!")
        
    except Exception as e:
        st.error(f"Error during testing: {str(e)}")
    finally:
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tests", total_tests)
    with col2:
        st.metric("Passed", passed_tests, delta=None if failed_tests == 0 else f"-{failed_tests}")
    with col3:
        st.metric("Failed", failed_tests, delta=None if failed_tests == 0 else f"+{failed_tests}")
    with col4:
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    
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
            use_container_width=True,
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
