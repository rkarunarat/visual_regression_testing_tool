"""Utility helpers for URL validation, path safety, and image resizing."""
import ipaddress
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
import logging

logger = logging.getLogger(__name__)

ALLOWED_URL_SCHEMES = frozenset({'http', 'https'})
BLOCKED_HOSTS = frozenset({
    '169.254.169.254',
    'metadata.google.internal',
    'metadata.goog',
})


def validate_url(url):
    """Validate URL format and block dangerous targets (SSRF mitigation)."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if len(url) > 2048:
        return False
    try:
        result = urlparse(url)
        if result.scheme not in ALLOWED_URL_SCHEMES:
            return False
        if not result.netloc:
            return False
        if result.username or result.password:
            return False

        host = result.hostname
        if not host:
            return False
        if host.lower() in BLOCKED_HOSTS:
            return False

        try:
            addr = ipaddress.ip_address(host)
            if addr.is_link_local or addr in ipaddress.ip_network('169.254.0.0/16'):
                return False
        except ValueError:
            pass

        return True
    except Exception:
        return False


def validate_url_pairs(url_pairs):
    """Return invalid URL entries from a list of URL pair dicts."""
    invalid = []
    for pair in url_pairs:
        for field in ('staging_url', 'production_url'):
            url = pair.get(field, '')
            if not validate_url(url):
                invalid.append((pair.get('name', 'Unknown'), field, url))
    return invalid


def safe_results_path(base_dir, relative_path):
    """Resolve a path under base_dir; return None if it escapes the base."""
    if not relative_path:
        return None
    try:
        base = Path(base_dir).resolve()
        resolved = (base / relative_path).resolve()
        base_str = str(base)
        resolved_str = str(resolved)
        if resolved_str == base_str or resolved_str.startswith(base_str + os.sep):
            return resolved
    except Exception:
        pass
    return None


def sanitize_filename(filename):
    """Sanitize filename for cross-platform compatibility."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    filename = filename[:100].strip('. ')

    if not filename:
        filename = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return filename


def enrich_test_result(result):
    """Fill missing viewport and device fields on loaded or legacy results."""
    from config import VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP

    device = result.get('device')
    if device and device in VIEWPORT_CONFIGS:
        if not result.get('viewport_width'):
            result['viewport_width'] = VIEWPORT_CONFIGS[device].get('width')
        if not result.get('viewport_height'):
            result['viewport_height'] = VIEWPORT_CONFIGS[device].get('height')
    if not result.get('device_model') and device:
        result['device_model'] = PLAYWRIGHT_DEVICE_MAP.get(device, device)
    result.setdefault('staging_runtime_metrics', {})
    result.setdefault('production_runtime_metrics', {})
    return result


def format_configured_viewport(result):
    """Return configured viewport dimensions for display."""
    enrich_test_result(result)
    width = result.get('viewport_width')
    height = result.get('viewport_height')
    if width and height:
        return f"{int(width)}x{int(height)}"
    return "?x?"


def resize_image_for_display(image, max_width=800, max_height=600):
    """Resize image for display while maintaining aspect ratio."""
    try:
        width, height = image.size

        width_scale = max_width / width
        height_scale = max_height / height
        scale = min(width_scale, height_scale, 1.0)

        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    except Exception as e:
        logger.error("Error resizing image: %s", e)
        return image
