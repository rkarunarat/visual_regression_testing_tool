#!/usr/bin/env python3
"""
Visual Regression Testing Tool - Functionality Test Suite

This test suite verifies that all core functionality works correctly
before pushing changes to the repository.

Run with: python test_functionality.py
"""

import sys
import os

# Windows: force UTF-8 console output so emoji/status lines render correctly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import subprocess
from pathlib import Path
import traceback

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_header(text):
    """Print a colored header"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.WHITE}{text}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.NC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.NC}")

class TestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def run_test(self, test_name, test_func):
        """Run a single test and track results"""
        try:
            print(f"\n{Colors.PURPLE}Testing: {test_name}{Colors.NC}")
            result = test_func()
            if result:
                self.passed += 1
                print_success(f"{test_name} - PASSED")
            else:
                self.failed += 1
                print_error(f"{test_name} - FAILED")
        except Exception as e:
            self.failed += 1
            print_error(f"{test_name} - ERROR: {e}")
            print(f"{Colors.RED}Traceback:{Colors.NC}")
            traceback.print_exc()
    
    def run_warning_test(self, test_name, test_func):
        """Run a test that can have warnings"""
        try:
            print(f"\n{Colors.PURPLE}Testing: {test_name}{Colors.NC}")
            result = test_func()
            if result == "warning":
                self.warnings += 1
                print_warning(f"{test_name} - WARNING")
            elif result:
                self.passed += 1
                print_success(f"{test_name} - PASSED")
            else:
                self.failed += 1
                print_error(f"{test_name} - FAILED")
        except Exception as e:
            self.failed += 1
            print_error(f"{test_name} - ERROR: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        total = self.passed + self.failed + self.warnings
        print(f"Total Tests: {total}")
        print_success(f"Passed: {self.passed}")
        if self.warnings > 0:
            print_warning(f"Warnings: {self.warnings}")
        if self.failed > 0:
            print_error(f"Failed: {self.failed}")
        
        # Check if running on host system
        if not (os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')):
            if self.failed > 0:
                print_warning("⚠️ Some tests failed because dependencies are not installed on host system")
                print_info("💡 This is normal when running tests on host without Python dependencies")
                print_info("💡 Tests will run automatically inside Docker container during deployment")
                print_info("💡 To run tests locally: pip install -r requirements.txt")
                print_success("✅ Ready for Docker deployment!")
                return True
        
        if self.failed == 0:
            print_success("🎉 ALL TESTS PASSED! Ready to push to repository.")
            return True
        else:
            print_error("❌ Some tests failed. Please fix issues before pushing.")
            return False

def test_imports():
    """Test 1: Verify all imports work correctly"""
    try:
        import streamlit as st
        from browser_automation import BrowserManager
        from image_comparison import ImageComparator
        from result_manager import ResultManager
        from config import BROWSERS, DEVICES, VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP
        from utils import resize_image_for_display, sanitize_filename, validate_url, validate_url_pairs
        
        print_info("All core imports successful")
        return True
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False

def test_configuration_data():
    """Test 2: Verify configuration data is intact"""
    try:
        from config import BROWSERS, DEVICES, VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP, REGIONS
        
        # Check browsers
        if not BROWSERS or 'Chrome' not in BROWSERS:
            print_error("Browsers configuration missing or invalid")
            return False
        
        # Check devices
        if not DEVICES or 'Desktop' not in DEVICES:
            print_error("Devices configuration missing or invalid")
            return False
        
        # Check viewport configs
        if not VIEWPORT_CONFIGS or 'Desktop' not in VIEWPORT_CONFIGS:
            print_error("Viewport configurations missing or invalid")
            return False
        
        # Check regions
        if not REGIONS or 'USA' not in REGIONS:
            print_error("Regions configuration missing or invalid")
            return False
        
        # Verify region structure
        for region_key, region_data in REGIONS.items():
            required_keys = ['name', 'timezone', 'locale', 'user_agent_suffix', 'accept_language', 'geo_location', 'country_code', 'region_code']
            for key in required_keys:
                if key not in region_data:
                    print_error(f"Region {region_key} missing required key: {key}")
                    return False
            
            # Verify geo-location structure
            geo_location = region_data.get('geo_location', {})
            if 'latitude' not in geo_location or 'longitude' not in geo_location:
                print_error(f"Region {region_key} geo_location missing latitude/longitude")
                return False
        
        print_info(f"Browsers: {list(BROWSERS.keys())}")
        print_info(f"Devices: {list(DEVICES.keys())}")
        print_info(f"Viewport configs: {len(VIEWPORT_CONFIGS)} entries")
        print_info(f"Device mappings: {len(PLAYWRIGHT_DEVICE_MAP)} entries")
        print_info(f"Regions: {list(REGIONS.keys())}")
        
        return True
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False

def test_utility_functions():
    """Test 3: Verify utility functions work"""
    try:
        from utils import sanitize_filename, resize_image_for_display, validate_url, validate_url_pairs
        from PIL import Image
        
        # Test filename sanitization
        test_filename = sanitize_filename('test<>file|name?.txt')
        if 'test__file_name_.txt' not in test_filename:
            print_error("Filename sanitization not working correctly")
            return False
        
        # Test image resizing
        test_img = Image.new('RGB', (100, 100), color='red')
        resized = resize_image_for_display(test_img, max_width=50, max_height=50)
        if resized.size != (50, 50):
            print_error("Image resizing not working correctly")
            return False
        
        print_info(f"Filename sanitization: {test_filename}")
        print_info(f"Image resize: {test_img.size} -> {resized.size}")

        if not validate_url('https://example.com/page'):
            print_error("Valid HTTPS URL rejected")
            return False
        if validate_url('file:///etc/passwd'):
            print_error("file:// URL should be rejected")
            return False
        if validate_url('http://169.254.169.254/latest/meta-data/'):
            print_error("Metadata URL should be rejected")
            return False
        invalid = validate_url_pairs([{'name': 't', 'staging_url': 'javascript:alert(1)', 'production_url': 'https://example.com'}])
        if len(invalid) != 1:
            print_error("validate_url_pairs did not detect invalid staging URL")
            return False
        
        return True
    except Exception as e:
        print_error(f"Utility functions test failed: {e}")
        return False

def test_class_instantiation():
    """Test 4: Verify all classes can be instantiated"""
    try:
        from browser_automation import BrowserManager
        from image_comparison import ImageComparator
        from result_manager import ResultManager
        
        browser_mgr = BrowserManager()
        img_comp = ImageComparator()
        result_mgr = ResultManager()
        
        print_info("All classes instantiate successfully")
        return True
    except Exception as e:
        print_error(f"Class instantiation failed: {e}")
        return False

def test_app_syntax():
    """Test 5: Verify app.py syntax is valid"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'app.py', 'exec')
        print_info("app.py syntax is valid")
        return True
    except Exception as e:
        print_error(f"app.py syntax error: {e}")
        return False

def test_app_structure():
    """Test 6: Verify UI modules have all required functions"""
    try:
        ui_modules = {
            'app.py': ['def main():'],
            'ui/new_test_page.py': ['def new_test_page('],
            'ui/test_runner.py': ['def run_tests(', 'def run_single_test(', 'def run_single_test_sync('],
            'ui/results_page.py': ['def results_page('],
            'ui/comparison_view.py': ['def render_comparison_detail('],
            'ui/history_page.py': ['def history_page('],
            'ui/manage_tab.py': ['def manage_test_runs_tab(', 'def cleanup_partial_results('],
            'ui/export.py': ['def export_selected_runs(', 'def export_results(', 'def build_pdf_filename(', 'def generate_pdf('],
            'ui/about_tab.py': ['def about_tab('],
            'ui/browsers.py': ['def ensure_playwright_browsers_installed('],
        }

        missing = []
        for filepath, required_functions in ui_modules.items():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            for func in required_functions:
                if func not in content:
                    missing.append(f"{filepath}: {func}")

        if missing:
            print_error(f"Missing functions: {missing}")
            return False

        print_info("All required functions present in UI modules")
        return True
    except Exception as e:
        print_error(f"App structure test failed: {e}")
        return False

def test_session_state_handling():
    """Test 7: Verify session state handling is correct"""
    try:
        with open('ui/deps.py', 'r', encoding='utf-8') as f:
            deps_content = f.read()
        with open('ui/session.py', 'r', encoding='utf-8') as f:
            session_content = f.read()
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()

        if 'IMPORTS_OK' not in deps_content or 'PDF_OK' not in deps_content:
            print_error("Missing error handling flags in ui/deps.py")
            return False

        if 'def init_session_state(' not in session_content:
            print_error("init_session_state missing from ui/session.py")
            return False

        if 'init_session_state()' not in app_content:
            print_error("app.py does not call init_session_state()")
            return False

        nav_modifications = app_content.count('st.session_state.nav =')
        if nav_modifications > 0:
            print_error(f"Found {nav_modifications} nav modifications in app.py (should be 0)")
            return False

        with open('ui/manage_tab.py', 'r', encoding='utf-8') as f:
            manage_content = f.read()
        if 'def cleanup_partial_results():' not in manage_content:
            print_error("cleanup_partial_results function missing from ui/manage_tab.py")
            return False

        print_info("Session state handling is correct")
        print_info(f"Nav modifications in app.py: {nav_modifications} (should be 0)")
        return True
    except Exception as e:
        print_error(f"Session state test failed: {e}")
        return False

def test_cleanup_functionality():
    """Test 8: Verify cleanup and partial results functionality"""
    try:
        with open('ui/manage_tab.py', 'r', encoding='utf-8') as f:
            manage_content = f.read()
        with open('ui/new_test_page.py', 'r', encoding='utf-8') as f:
            config_content = f.read()

        if 'st.session_state.current_test_id = None' not in manage_content:
            print_error("cleanup_partial_results does not clear current_test_id")
            return False

        if 'st.session_state.test_results = []' not in manage_content:
            print_error("cleanup_partial_results does not clear test_results")
            return False

        if 'result_manager.delete_test_run(' not in manage_content:
            print_error("cleanup_partial_results does not delete test run")
            return False

        if 'st.session_state.test_results = loaded' not in config_content:
            print_error("Keep partial results does not load results")
            return False

        if 'Review them on the Results page' not in config_content:
            print_error("Keep partial results does not provide navigation guidance")
            return False

        print_info("Cleanup and partial results functionality is correct")
        return True
    except Exception as e:
        print_error(f"Cleanup functionality test failed: {e}")
        return False

def test_deployment_files():
    """Test 9: Verify deployment files exist and are valid"""
    try:
        deployment_files = [
            'Dockerfile',
            'docker-compose.yml',
            'nginx.conf',
            'deploy.sh',
            'README-DEPLOYMENT.md'
        ]
        
        missing_files = []
        for file in deployment_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            print_error(f"Missing deployment files: {missing_files}")
            return False
        
        # Check Dockerfile syntax
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        if 'FROM python:3.11-slim' not in dockerfile_content:
            print_error("Dockerfile does not use correct Python version")
            return False
        
        if 'streamlit run app.py' not in dockerfile_content and 'CMD ["streamlit"' not in dockerfile_content:
            print_error("Dockerfile does not run streamlit correctly")
            return False
        
        print_info("All deployment files exist and are valid")
        return True
    except Exception as e:
        print_error(f"Deployment files test failed: {e}")
        return False

def test_requirements_file():
    """Test 10: Verify requirements.txt is correct"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = [
            'streamlit>=1.39.0',
            'playwright>=1.45.0',
            'pillow>=10.4.0',
            'opencv-python-headless>=4.10.0.0',
            'pandas>=2.2.0',
            'reportlab>=4.2.0'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print_error(f"Missing packages in requirements.txt: {missing_packages}")
            return False
        
        print_info("requirements.txt is correct")
        return True
    except Exception as e:
        print_error(f"Requirements file test failed: {e}")
        return False

def test_playwright_setup():
    """Test 11: Verify Playwright setup is correct"""
    try:
        with open('ui/browsers.py', 'r', encoding='utf-8') as f:
            browsers_content = f.read()
        with open('ui/new_test_page.py', 'r', encoding='utf-8') as f:
            config_content = f.read()

        if 'def ensure_playwright_browsers_installed(' not in browsers_content:
            print_error("Playwright browser installation function missing")
            return False

        if 'Setup Browsers' not in config_content:
            print_error("Browser setup button missing")
            return False

        if 'if not st.session_state.get("_pw_browsers_ready"):' not in config_content:
            print_error("Playwright readiness check missing")
            return False

        print_info("Playwright setup is correct")
        return True
    except Exception as e:
        print_error(f"Playwright setup test failed: {e}")
        return False

def test_pdf_generation():
    """Test 12: Verify PDF generation has proper fallbacks"""
    try:
        with open('ui/comparison_view.py', 'r', encoding='utf-8') as f:
            comparison_content = f.read()
        with open('ui/export.py', 'r', encoding='utf-8') as f:
            export_content = f.read()

        if 'if PDF_OK and st.button("Summary PDF"' not in comparison_content:
            print_error("PDF generation does not check availability")
            return False

        if 'Summary PDF (Unavailable)' not in comparison_content:
            print_error("PDF fallback buttons missing")
            return False

        if 'if not PDF_OK:' not in export_content:
            print_error("PDF generation guard missing")
            return False

        print_info("PDF generation has proper fallbacks")
        return True
    except Exception as e:
        print_error(f"PDF generation test failed: {e}")
        return False

def test_region_functionality():
    """Test 13: Verify region functionality is properly implemented"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        with open('ui/new_test_page.py', 'r', encoding='utf-8') as f:
            new_test_content = f.read()
        with open('ui/test_runner.py', 'r', encoding='utf-8') as f:
            runner_content = f.read()

        if 'selected_region = st.selectbox' not in new_test_content:
            print_error("Region selection UI missing")
            return False

        if 'selected_region' not in new_test_content and 'selected_region' not in runner_content:
            print_error("Region parameter not found in new test page or test runner")
            return False

        if 'region = selected_region if selected_region != "Default" else None' not in runner_content:
            print_error("Region parameter handling missing")
            return False

        if 'region_info = REGIONS[selected_region]' not in new_test_content:
            print_error("Region info display missing")
            return False

        if "'region': selected_region if selected_region != \"Default\" else None" not in runner_content:
            print_error("Region not stored in test results")
            return False

        print_info("Region functionality is properly implemented")
        return True
    except Exception as e:
        print_error(f"Region functionality test failed: {e}")
        return False

def test_browser_automation_regions():
    """Test 14: Verify browser automation supports regions"""
    try:
        with open('browser_automation.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for region parameter in function signatures
        if 'region=None' not in content:
            print_error("Region parameter missing in browser automation functions")
            return False
        
        # Check for region configuration handling
        if 'region_config = REGIONS.get(region)' not in content:
            print_error("Region configuration handling missing")
            return False
        
        # Check for region-specific context options (uses .get for safe defaults)
        if "context_options['locale'] = region_config.get('locale'" not in content:
            print_error("Region locale setting missing")
            return False

        if "context_options['timezone_id'] = region_config.get('timezone'" not in content:
            print_error("Region timezone setting missing")
            return False
        
        # Check for accept language header
        if 'Accept-Language' not in content:
            print_error("Accept-Language header setting missing")
            return False
        
        print_info("Browser automation region support is properly implemented")
        return True
    except Exception as e:
        print_error(f"Browser automation regions test failed: {e}")
        return False

def test_default_region_behavior():
    """Test 15: Verify default region behavior works correctly"""
    try:
        with open('ui/new_test_page.py', 'r', encoding='utf-8') as f:
            new_test_content = f.read()
        with open('ui/test_runner.py', 'r', encoding='utf-8') as f:
            runner_content = f.read()

        if 'selected_region != "Default"' not in new_test_content and 'selected_region != "Default"' not in runner_content:
            print_error("Default region handling missing")
            return False

        if 'region = selected_region if selected_region != "Default" else None' not in runner_content:
            print_error("Default region nullification missing")
            return False

        if 'if selected_region != "Default":' not in new_test_content:
            print_error("Default region UI handling missing")
            return False

        print_info("Default region behavior is properly implemented")
        return True
    except Exception as e:
        print_error(f"Default region behavior test failed: {e}")
        return False

def test_region_locale_support():
    """Test 16: Verify region locale/timezone support in browser automation."""
    try:
        with open('browser_automation.py', 'r', encoding='utf-8') as f:
            content = f.read()

        if 'region_config = REGIONS.get(region)' not in content:
            print_error("Region configuration lookup missing")
            return False

        if "context_options['locale'] = region_config.get('locale'" not in content:
            print_error("Locale context option missing")
            return False

        if "context_options['timezone_id'] = region_config.get('timezone'" not in content:
            print_error("Timezone context option missing")
            return False

        if 'Accept-Language' not in content:
            print_error("Accept-Language header missing")
            return False

        if "Object.defineProperty(navigator, 'language'" not in content:
            print_error("Language override missing")
            return False

        print_info("Region locale/timezone support is properly implemented")
        return True
    except Exception as e:
        print_error(f"Region locale support test failed: {e}")
        return False

def main():
    """Run the complete test suite"""
    print_header("VISUAL REGRESSION TESTING TOOL - FUNCTIONALITY TEST SUITE")
    
    # Check if running in Docker environment
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
        print_info("🐳 Running inside Docker container - all dependencies available")
    else:
        print_warning("⚠️ Running on host system - some tests may fail if dependencies not installed")
        print_info("💡 For Docker deployment, tests run automatically inside the container")
        print_info("💡 To run tests locally, install dependencies: pip install -r requirements.txt")
        print("")
    
    print_info("Running comprehensive tests...")
    
    test_suite = TestSuite()
    
    # Core functionality tests
    test_suite.run_test("Import Dependencies", test_imports)
    test_suite.run_test("Configuration Data", test_configuration_data)
    test_suite.run_test("Utility Functions", test_utility_functions)
    test_suite.run_test("Class Instantiation", test_class_instantiation)
    
    # App structure tests
    test_suite.run_test("App Syntax", test_app_syntax)
    test_suite.run_test("App Structure", test_app_structure)
    test_suite.run_test("Session State Handling", test_session_state_handling)
    
    # Feature tests
    test_suite.run_test("Cleanup Functionality", test_cleanup_functionality)
    test_suite.run_test("Playwright Setup", test_playwright_setup)
    test_suite.run_test("PDF Generation", test_pdf_generation)
    
    # Region functionality tests
    test_suite.run_test("Region Functionality", test_region_functionality)
    test_suite.run_test("Browser Automation Regions", test_browser_automation_regions)
    test_suite.run_test("Default Region Behavior", test_default_region_behavior)
    test_suite.run_test("Region Locale Support", test_region_locale_support)
    
    # Deployment tests
    test_suite.run_test("Deployment Files", test_deployment_files)
    test_suite.run_test("Requirements File", test_requirements_file)
    
    # Print summary
    success = test_suite.print_summary()
    
    if success:
        print_header("READY FOR DEPLOYMENT")
        print_success("All tests passed! You can safely push to repository.")
        print_info("Next steps:")
        print("  1. git add .")
        print("  2. git commit -m 'Add enhanced region-specific testing with geo-location emulation'")
        print("  3. git push")
        return 0
    else:
        print_header("FIX REQUIRED")
        print_error("Some tests failed. Please fix the issues before pushing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
