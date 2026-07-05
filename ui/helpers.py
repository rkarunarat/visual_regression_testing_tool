"""Shared helpers for test execution and image loading."""
import os
import subprocess
from datetime import datetime

from result_manager import ResultManager
from config import VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP
from utils import safe_results_path


def build_skipped_result(url_pair, browser, device, selected_region,
                         reason='Screenshot capture failed or test execution error'):
    """Build a skipped-test result record."""
    return {
        'test_name': url_pair['name'],
        'browser': browser,
        'device': device,
        'device_model': PLAYWRIGHT_DEVICE_MAP.get(device, device),
        'staging_url': url_pair['staging_url'],
        'production_url': url_pair['production_url'],
        'similarity_score': 0.0,
        'is_match': False,
        'is_skipped': True,
        'skip_reason': reason,
        'region': selected_region if selected_region != "Default" else None,
        'staging_screenshot': None,
        'production_screenshot': None,
        'diff_image': None,
        'timestamp': datetime.now().isoformat(),
        'viewport_width': VIEWPORT_CONFIGS[device].get('width'),
        'viewport_height': VIEWPORT_CONFIGS[device].get('height'),
        'staging_runtime_metrics': {},
        'production_runtime_metrics': {}
    }


def load_image_from_result(record, key):
    """Load a screenshot from memory or disk for a result record."""
    try:
        img = record.get(key)
        if img is not None:
            return img
        path_key_map = {
            'staging_screenshot': 'staging',
            'production_screenshot': 'production',
            'diff_image': 'diff'
        }
        spaths = record.get('screenshot_paths', {}) or {}
        rel = spaths.get(path_key_map.get(key, ''), None)
        if rel:
            base = ResultManager().results_dir
            fp = safe_results_path(base, rel)
            if fp and fp.exists():
                from PIL import Image as PILImage
                return PILImage.open(fp)
    except Exception:
        return None
    return None


def should_use_parallel_processing():
    """Determine if parallel processing should be used."""
    try:
        cpu_count = os.cpu_count() or 1
        return cpu_count >= 2
    except Exception:
        return False


def is_wsl_environment():
    """Detect if running in WSL."""
    try:
        if os.environ.get('WSL_DISTRO_NAME') or os.environ.get('WSLENV'):
            return True
        if os.environ.get('RANCHER_DESKTOP'):
            return True
        try:
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True, timeout=5)
            if 'microsoft' in result.stdout.lower() or 'wsl' in result.stdout.lower():
                return True
        except Exception:
            pass
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                if 'microsoft' in version_info or 'wsl' in version_info:
                    return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def is_rancher_desktop():
    """Detect if running inside a Docker container."""
    try:
        if os.environ.get('RANCHER_DESKTOP'):
            return True
        if os.path.exists('/.dockerenv'):
            return True
        if os.environ.get('CONTAINER') or os.environ.get('DOCKER_CONTAINER'):
            return True
        return False
    except Exception:
        return False


def get_optimal_worker_count():
    """Get optimal worker thread count for parallel test execution."""
    if not should_use_parallel_processing():
        return 1
    cpu_count = os.cpu_count() or 1
    return min(3, max(2, cpu_count // 2))
