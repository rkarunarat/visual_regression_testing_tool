"""URL configuration tab — backward-compatible wrapper."""
from ui.new_test_page import new_test_page


def configure_urls_tab(selected_browsers, selected_devices, similarity_threshold, wait_time, selected_region):
    """Legacy signature retained for compatibility; settings are collected on-page."""
    new_test_page()
