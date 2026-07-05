"""Shared dependencies and feature flags for UI modules."""
import logging

logger = logging.getLogger(__name__)

try:
    from browser_automation import BrowserManager
    from image_comparison import ImageComparator
    from result_manager import ResultManager
    from config import BROWSERS, DEVICES, VIEWPORT_CONFIGS, PLAYWRIGHT_DEVICE_MAP
    IMPORTS_OK = True
except ImportError as e:
    logger.error("Import error: %s", e)
    IMPORTS_OK = False
    BrowserManager = None
    ImageComparator = None
    ResultManager = None
    BROWSERS = {'Chrome': {}}
    DEVICES = {'Desktop': {}}
    VIEWPORT_CONFIGS = {'Desktop': {'width': 1920, 'height': 1080}}
    PLAYWRIGHT_DEVICE_MAP = {}

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    PDF_OK = True
except ImportError:
    PDF_OK = False
    A4 = canvas = cm = ImageReader = None
