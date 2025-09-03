"""
Configuration file for Visual Regression Testing Tool
"""

# Browser configurations
BROWSERS = {
    'Chrome': {
        'engine': 'chromium',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    },
    'Firefox': {
        'engine': 'firefox',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
    },
    'Safari': {
        'engine': 'webkit',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
    },
    'Edge': {
        'engine': 'chromium',
        'channel': 'msedge',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    }
}

# Device configurations
DEVICES = {
    'Desktop': {
        'category': 'desktop',
        'os': 'Windows',
        'description': 'Desktop Windows'
    },
    'Desktop Mac': {
        'category': 'desktop',
        'os': 'macOS',
        'description': 'Desktop macOS'
    },
    'Tablet': {
        'category': 'tablet',
        'os': 'iOS',
        'description': 'iPad'
    },
    'Tablet Android': {
        'category': 'tablet',
        'os': 'Android',
        'description': 'Android Tablet'
    },
    'Mobile': {
        'category': 'mobile',
        'os': 'iOS',
        'description': 'iPhone'
    },
    'Mobile Android': {
        'category': 'mobile',
        'os': 'Android',
        'description': 'Android Phone'
    }
}

# Viewport configurations
VIEWPORT_CONFIGS = {
    'Desktop': {'width': 1920, 'height': 1080},
    'Desktop Mac': {'width': 1440, 'height': 900},
    'Tablet': {'width': 768, 'height': 1024},
    'Tablet Android': {'width': 800, 'height': 1280},
    'Mobile': {'width': 375, 'height': 667},
    'Mobile Android': {'width': 360, 'height': 640}
}

# Default test settings
DEFAULT_SETTINGS = {
    'similarity_threshold': 95.0,
    'wait_time': 3,
    'timeout': 30000,
    'full_page_screenshot': True,
    'ignore_https_errors': True
}

# Image comparison settings
IMAGE_COMPARISON = {
    'difference_threshold': 30,  # Minimum pixel difference to be considered significant
    'blur_radius': 0.5,  # Optional blur to reduce noise
    'similarity_metrics': ['ssim', 'pixel_similarity', 'histogram_similarity']
}

# Results storage settings
RESULTS_CONFIG = {
    'results_directory': 'test_results',
    'screenshots_directory': 'screenshots',
    'max_filename_length': 100,
    'cleanup_days': 30,
    'image_format': 'PNG',
    'image_quality': 95
}

# UI Configuration
UI_CONFIG = {
    'page_title': 'Visual Regression Testing Tool',
    'page_icon': '🔍',
    'layout': 'wide',
    'sidebar_state': 'expanded',
    'max_upload_size': 10  # MB
}

# Common overlays and elements to handle
OVERLAY_SELECTORS = [
    '[data-testid="cookie-banner"]',
    '.cookie-banner',
    '.cookie-notice',
    '.cookie-consent',
    '.gdpr-banner',
    '.modal-overlay',
    '[role="dialog"]',
    '.popup-overlay',
    '#cookie-consent',
    '.privacy-banner',
    '.notification-banner'
]

# Common accept/close button selectors
ACCEPT_BUTTON_SELECTORS = [
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("OK")',
    'button:has-text("Close")',
    'button:has-text("Got it")',
    'button:has-text("Dismiss")',
    '[data-testid="accept-cookies"]',
    '[data-testid="close-modal"]',
    '.accept-button',
    '.close-button'
]

# Error messages
ERROR_MESSAGES = {
    'browser_launch_failed': 'Failed to launch browser: {}',
    'screenshot_failed': 'Failed to take screenshot of {}: {}',
    'image_comparison_failed': 'Failed to compare images: {}',
    'invalid_url': 'Invalid URL provided: {}',
    'network_error': 'Network error accessing {}: {}',
    'timeout_error': 'Timeout waiting for page to load: {}'
}

# Success messages
SUCCESS_MESSAGES = {
    'test_completed': 'Test completed successfully',
    'results_exported': 'Results exported successfully',
    'browser_initialized': 'Browser initialized successfully'
}
