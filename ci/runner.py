"""Headless test execution for CI (no Streamlit dependency)."""
import asyncio
import logging
from datetime import datetime

from browser_automation import BrowserManager
from config import PLAYWRIGHT_DEVICE_MAP, VIEWPORT_CONFIGS
from image_comparison import ImageComparator
from ui.helpers import build_skipped_result
from utils import validate_url_pairs

logger = logging.getLogger(__name__)


async def run_single_test(url_pair, browser, device, similarity_threshold, wait_time, selected_region):
    """Run one visual regression test and return a result dict."""
    browser_manager = None
    try:
        browser_manager = BrowserManager()
        viewport = VIEWPORT_CONFIGS[device]
        region = selected_region if selected_region != "Default" else None
        logger.info("Capturing %s (%s, %s) region=%s", url_pair['name'], browser, device, region)

        staging_capture = await browser_manager.take_screenshot(
            url_pair['staging_url'], browser, viewport, wait_time,
            device_name=device, return_metrics=True, region=region,
        )
        production_capture = await browser_manager.take_screenshot(
            url_pair['production_url'], browser, viewport, wait_time,
            device_name=device, return_metrics=True, region=region,
        )

        staging_screenshot, staging_metrics = (
            staging_capture if isinstance(staging_capture, tuple) else (staging_capture, {})
        )
        production_screenshot, production_metrics = (
            production_capture if isinstance(production_capture, tuple) else (production_capture, {})
        )

        if not staging_screenshot or not production_screenshot:
            logger.warning("Screenshot capture failed for %s (%s, %s)", url_pair['name'], browser, device)
            return None

        comparison_result = ImageComparator().compare_images(
            staging_screenshot, production_screenshot, similarity_threshold,
        )

        return {
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
            'production_runtime_metrics': production_metrics,
            'region': selected_region if selected_region != "Default" else None,
        }
    except Exception as e:
        logger.error("Error in test %s (%s, %s): %s", url_pair['name'], browser, device, e)
        return None
    finally:
        if browser_manager is not None:
            try:
                await browser_manager.cleanup()
            except Exception as cleanup_error:
                logger.warning("Browser cleanup error: %s", cleanup_error)


async def run_test_matrix(url_pairs, browsers, devices, similarity_threshold, wait_time, selected_region):
    """Run the full browser/device/url matrix sequentially."""
    invalid_urls = validate_url_pairs(url_pairs)
    if invalid_urls:
        details = ", ".join(f"{name}:{field}" for name, field, _ in invalid_urls)
        raise ValueError(f"Invalid URLs in config: {details}")

    if not browsers:
        raise ValueError("At least one browser is required")
    if not devices:
        raise ValueError("At least one device is required")

    results = []
    total = len(url_pairs) * len(browsers) * len(devices)
    current = 0

    for url_pair in url_pairs:
        for browser in browsers:
            for device in devices:
                current += 1
                logger.info("Running test %s/%s: %s %s %s", current, total, url_pair['name'], browser, device)
                result = await run_single_test(
                    url_pair, browser, device, similarity_threshold, wait_time, selected_region,
                )
                if result:
                    results.append(result)
                else:
                    results.append(build_skipped_result(url_pair, browser, device, selected_region))

    return results
