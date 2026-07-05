"""
Configuration file for Visual Regression Testing Tool
"""
import os

# Browser configurations
BROWSERS = {
    'Chrome': {
        'engine': 'chromium',
        'channel': 'chrome',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'
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
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0'
    }
}

# Region configurations for geo-specific testing
REGIONS = {
    'USA': {
        'name': 'United States',
        'timezone': 'America/New_York',
        'locale': 'en-US',
        'user_agent_suffix': 'US',
        'accept_language': 'en-US,en;q=0.9',
        'geo_location': {'latitude': 40.7128, 'longitude': -74.0060},  # New York
        'country_code': 'US',
        'region_code': 'NY'
    },
    'Europe': {
        'name': 'Europe',
        'timezone': 'Europe/London',
        'locale': 'en-GB',
        'user_agent_suffix': 'EU',
        'accept_language': 'en-GB,en;q=0.9,de;q=0.8,fr;q=0.8,es;q=0.8',
        'geo_location': {'latitude': 51.5074, 'longitude': -0.1278},  # London
        'country_code': 'GB',
        'region_code': 'ENG'
    },
    'Asia': {
        'name': 'Asia',
        'timezone': 'Asia/Tokyo',
        'locale': 'en-US',
        'user_agent_suffix': 'AS',
        'accept_language': 'en-US,en;q=0.9,ja;q=0.8,ko;q=0.8,zh;q=0.8',
        'geo_location': {'latitude': 35.6762, 'longitude': 139.6503},  # Tokyo
        'country_code': 'JP',
        'region_code': '13'
    },
    'Arab': {
        'name': 'Middle East & Arab',
        'timezone': 'Asia/Dubai',
        'locale': 'ar-AE',
        'user_agent_suffix': 'AE',
        'accept_language': 'ar-AE,ar;q=0.9,en;q=0.8',
        'geo_location': {'latitude': 25.2048, 'longitude': 55.2708},  # Dubai
        'country_code': 'AE',
        'region_code': 'DU'
    },
    'Africa': {
        'name': 'Africa',
        'timezone': 'Africa/Cairo',
        'locale': 'en-ZA',
        'user_agent_suffix': 'AF',
        'accept_language': 'en-ZA,en;q=0.9,ar;q=0.8,fr;q=0.8',
        'geo_location': {'latitude': -26.2041, 'longitude': 28.0473},  # Johannesburg
        'country_code': 'ZA',
        'region_code': 'GP'
    },
    'Oceania': {
        'name': 'Oceania',
        'timezone': 'Australia/Sydney',
        'locale': 'en-AU',
        'user_agent_suffix': 'OC',
        'accept_language': 'en-AU,en;q=0.9',
        'geo_location': {'latitude': -33.8688, 'longitude': 151.2093},  # Sydney
        'country_code': 'AU',
        'region_code': 'NSW'
    },
    'South America': {
        'name': 'South America',
        'timezone': 'America/Sao_Paulo',
        'locale': 'pt-BR',
        'user_agent_suffix': 'SA',
        'accept_language': 'pt-BR,pt;q=0.9,es;q=0.8,en;q=0.8',
        'geo_location': {'latitude': -23.5505, 'longitude': -46.6333},  # São Paulo
        'country_code': 'BR',
        'region_code': 'SP'
    },
    'North America': {
        'name': 'North America',
        'timezone': 'America/Toronto',
        'locale': 'en-CA',
        'user_agent_suffix': 'NA',
        'accept_language': 'en-CA,en;q=0.9,fr;q=0.8,es;q=0.8',
        'geo_location': {'latitude': 43.6532, 'longitude': -79.3832},  # Toronto
        'country_code': 'CA',
        'region_code': 'ON'
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

# Playwright device descriptors mapping for our device names
PLAYWRIGHT_DEVICE_MAP = {
    'Mobile': 'iPhone 14 Pro',
    'Mobile Android': 'Pixel 7',
    'Tablet': 'iPad Pro 11',
    'Tablet Android': 'Galaxy Tab S7'
}

# Viewport configurations
VIEWPORT_CONFIGS = {
    'Desktop': {'width': 1920, 'height': 1080},  # Standard desktop resolution
    'Desktop Mac': {'width': 1440, 'height': 900},  # MacBook resolution
    'Tablet': {'width': 768, 'height': 1024},  # iPad portrait
    'Tablet Android': {'width': 800, 'height': 1280},  # Android tablet
    'Mobile': {'width': 375, 'height': 667},  # iPhone
    'Mobile Android': {'width': 360, 'height': 640}  # Android phone
}

# Default test settings
DEFAULT_SETTINGS = {
    'similarity_threshold': 95.0,
    'wait_time': 3,  # Keep 3s for slower sites
    'timeout': 45000,
    'full_page_screenshot': True,
    'ignore_https_errors': os.environ.get('IGNORE_HTTPS_ERRORS', 'true').lower() in ('true', '1', 'yes'),
}

# Browser launch / anti-bot settings (Cloudflare-friendly defaults)
BROWSER_LAUNCH = {
    # Use installed Chrome/Edge instead of bundled Chromium when available
    'use_installed_browser': os.environ.get('PLAYWRIGHT_USE_SYSTEM_BROWSER', 'true').lower() in ('true', '1', 'yes'),
    # Headless mode; set PLAYWRIGHT_HEADLESS=false to run a visible browser (helps with strict CF sites)
    'headless': os.environ.get('PLAYWRIGHT_HEADLESS', 'true').lower() in ('true', '1', 'yes'),
    # Extra wait while Cloudflare interstitials resolve
    'cloudflare_wait_seconds': int(os.environ.get('CLOUDFLARE_WAIT_SECONDS', '20')),
    'navigation_timeout_ms': int(os.environ.get('PLAYWRIGHT_NAVIGATION_TIMEOUT_MS', '45000')),
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
