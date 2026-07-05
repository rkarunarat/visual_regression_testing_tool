"""Async Playwright automation for capturing screenshots across browsers/devices.

Provides `BrowserManager` to manage Playwright lifecycle, create contexts with
device emulation, capture full-page screenshots, and handle common overlays.
"""
import asyncio
import sys
from playwright.async_api import async_playwright
from config import BROWSER_LAUNCH, BROWSERS, DEFAULT_SETTINGS, PLAYWRIGHT_DEVICE_MAP
import io
from PIL import Image
import warnings
import logging
import os
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cap image size to mitigate decompression-bomb attacks from untrusted pages
Image.MAX_IMAGE_PIXELS = 200_000_000
try:
    warnings.filterwarnings('ignore', category=Image.DecompressionBombWarning)
except Exception:
    pass

# Ensure proper event loop policy on Windows for subprocess support (Playwright)
if sys.platform.startswith("win"):
    try:
        # Proactor policy supports subprocesses required by Playwright
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Geo-location proxy mechanism removed - keeping simple locale support only

STEALTH_INIT_SCRIPT = """
// Reduce automation fingerprints commonly checked by bot protection (e.g. Cloudflare)
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
if (!window.chrome) {
    window.chrome = { runtime: {} };
}
if (!navigator.languages || navigator.languages.length === 0) {
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
}
"""

CLOUDFLARE_TITLE_MARKERS = (
    'just a moment',
    'attention required',
    'please wait',
    'checking your browser',
)

CLOUDFLARE_BODY_MARKERS = (
    'cf-browser-verification',
    'challenge-platform',
    'challenges.cloudflare.com',
    'turnstile',
    'verify you are human',
)


class BrowserManager:
    """Manage Playwright, browsers/contexts, and screenshot capture."""
    def __init__(self):
        self.playwright = None
        self.browsers = {}
        self.is_wsl = self._detect_wsl()
        self.windows_browser_paths = self._get_windows_browser_paths()
    
    def _detect_wsl(self):
        """Detect if running in WSL environment."""
        try:
            # Check for WSL-specific environment variables
            if os.environ.get('WSL_DISTRO_NAME') or os.environ.get('WSLENV'):
                return True
            
            # Check for Rancher Desktop environment
            if os.environ.get('RANCHER_DESKTOP'):
                return True
            
            # Check for WSL in uname
            try:
                result = subprocess.run(['uname', '-r'], capture_output=True, text=True, timeout=5)
                if 'microsoft' in result.stdout.lower() or 'wsl' in result.stdout.lower():
                    return True
            except:
                pass
            
            # Check for WSL in /proc/version
            try:
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    if 'microsoft' in version_info or 'wsl' in version_info:
                        return True
            except:
                pass
                
            return False
        except:
            return False
    
    def _get_windows_browser_paths(self):
        """Get paths to Windows browsers for WSL integration."""
        if not self.is_wsl:
            return {}
        
        browser_paths = {}
        
        # Common Windows browser paths
        windows_paths = {
            'chrome': [
                '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
                '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
                '/mnt/c/Users/*/AppData/Local/Google/Chrome/Application/chrome.exe'
            ],
            'edge': [
                '/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                '/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe'
            ],
            'firefox': [
                '/mnt/c/Program Files/Mozilla Firefox/firefox.exe',
                '/mnt/c/Program Files (x86)/Mozilla Firefox/firefox.exe'
            ]
        }
        
        # Check which browsers are available
        for browser, paths in windows_paths.items():
            for path in paths:
                if os.path.exists(path):
                    browser_paths[browser] = path
                    break
        
        return browser_paths
    
    def _get_windows_browser_path(self, browser_name):
        """Get Windows browser path for specific browser."""
        browser_mapping = {
            'Chrome': 'chrome',
            'Edge': 'edge', 
            'Firefox': 'firefox'
        }
        
        browser_key = browser_mapping.get(browser_name)
        if browser_key and browser_key in self.windows_browser_paths:
            return self.windows_browser_paths[browser_key]
        
        return None

    def _uses_system_browser(self, browser_name):
        """Whether to launch the locally installed Chrome/Edge instead of bundled Chromium."""
        return (
            browser_name in ('Chrome', 'Edge')
            and BROWSER_LAUNCH.get('use_installed_browser', True)
        )

    def _build_launch_options(self, browser_name):
        """Build launch options that resemble a normal desktop browser session."""
        headless = BROWSER_LAUNCH.get('headless', True)
        in_container = os.path.exists('/.dockerenv') or os.environ.get('CONTAINER')

        args = [
            '--disable-blink-features=AutomationControlled',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        if headless and browser_name in ('Chrome', 'Edge'):
            # Chrome new headless uses a normal user agent (no "HeadlessChrome" prefix)
            launch_options_extra = {'ignore_default_args': ['--headless']}
            args.append('--headless=new')
        else:
            launch_options_extra = {}
        if in_container:
            args.extend(['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])

        launch_options = {'headless': headless, 'args': args, **launch_options_extra}

        browser_cfg = BROWSERS.get(browser_name, {})
        channel = browser_cfg.get('channel')
        if self._uses_system_browser(browser_name) and channel:
            launch_options['channel'] = channel

        if self.is_wsl and self.windows_browser_paths:
            windows_path = self._get_windows_browser_path(browser_name)
            if windows_path:
                launch_options['executable_path'] = windows_path
                launch_options.pop('channel', None)
                logger.info("Using Windows browser: %s", windows_path)

        return launch_options
    
    async def initialize(self):
        """Start Playwright if not already started."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
    
    async def get_browser(self, browser_name):
        """Get or launch a browser engine by friendly name (Chrome, Firefox...)."""
        await self.initialize()
        
        # Check if browser exists and is still connected
        if browser_name in self.browsers:
            try:
                # Test if browser is still alive by checking if it's connected
                browser = self.browsers[browser_name]
                if browser.is_connected():
                    return browser
                else:
                    logger.warning(f"Browser {browser_name} is no longer connected, removing from cache")
                    del self.browsers[browser_name]
            except Exception as e:
                logger.warning(f"Browser {browser_name} health check failed: {e}, removing from cache")
                if browser_name in self.browsers:
                    del self.browsers[browser_name]
        
        # Launch new browser if not in cache or if previous one failed
        if self.playwright is None:
            raise RuntimeError("Playwright not initialized")
            
        browser_map = {
            'Chrome': self.playwright.chromium,
            'Firefox': self.playwright.firefox,
            'Safari': self.playwright.webkit,
            'Edge': self.playwright.chromium  # Edge uses Chromium engine
        }
        
        if browser_name not in browser_map:
            raise ValueError(f"Unsupported browser: {browser_name}")
        
        browser_engine = browser_map[browser_name]
        launch_options = self._build_launch_options(browser_name)

        try:
            self.browsers[browser_name] = await browser_engine.launch(**launch_options)
            logger.info(
                "Successfully launched %s (headless=%s, channel=%s)",
                browser_name,
                launch_options.get('headless'),
                launch_options.get('channel', 'bundled'),
            )
        except Exception as e:
            logger.warning("Could not launch %s with system browser: %s", browser_name, e)
            fallback = {
                'headless': BROWSER_LAUNCH.get('headless', True),
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ],
            }
            try:
                self.browsers[browser_name] = await browser_engine.launch(**fallback)
                logger.info("Successfully launched %s with bundled Chromium fallback", browser_name)
            except Exception as e2:
                logger.error("Launch failed for %s: %s", browser_name, e2)
                raise
        
        return self.browsers[browser_name]
    
    async def create_context(self, browser, viewport, device_name=None, user_agent=None, browser_name=None, region=None):
        """Create a browser context with viewport and optional device emulation."""
        context_options = {
            'ignore_https_errors': DEFAULT_SETTINGS['ignore_https_errors'],
            'java_script_enabled': True,
            'extra_http_headers': {'Accept-Language': 'en-US,en;q=0.9'},
        }

        # Prefer built-in device descriptors when possible
        used_descriptor = False
        if device_name and self.playwright is not None:
            descriptor_name = PLAYWRIGHT_DEVICE_MAP.get(device_name)
            if descriptor_name:
                try:
                    dopt = self.playwright.devices.get(descriptor_name)
                    if dopt:
                        # Merge full descriptor, including viewport
                        for k, v in dopt.items():
                            context_options[k] = v
                        used_descriptor = True
                except Exception:
                    used_descriptor = False

        if user_agent:
            context_options['user_agent'] = user_agent
        elif browser_name and browser_name in BROWSERS and not used_descriptor:
            browser_cfg = BROWSERS[browser_name]
            use_native_ua = (
                self._uses_system_browser(browser_name)
                and not BROWSER_LAUNCH.get('headless', True)
            )
            # Headless Chrome exposes "HeadlessChrome" in UA — override for bot protection
            if not use_native_ua and browser_cfg.get('user_agent'):
                context_options['user_agent'] = browser_cfg['user_agent']
        
        # Add simple locale support (geo-location proxy removed)
        if region:
            from config import REGIONS
            region_config = REGIONS.get(region)
            if region_config:
                try:
                    context_options['locale'] = region_config.get('locale', 'en-US')
                    context_options['timezone_id'] = region_config.get('timezone', 'UTC')
                    context_options['extra_http_headers'] = {
                        'Accept-Language': region_config.get('accept_language', 'en-US,en;q=0.9')
                    }
                    
                    logger.info(f"Applied simple locale settings for {region}: locale={region_config.get('locale', 'en-US')}, timezone={region_config.get('timezone', 'UTC')}")
                except Exception as e:
                    logger.warning(f"Error applying locale settings for {region}: {e}")
                    # Continue without locale settings if they fail

        # Firefox does not support some mobile emulation context options
        if (browser_name or '').lower() == 'firefox':
            for k in ['isMobile', 'is_mobile', 'hasTouch', 'has_touch', 'deviceScaleFactor', 'device_scale_factor']:
                context_options.pop(k, None)
        else:
            # For desktop contexts, capture sharper screenshots by using higher DPR
            if (not device_name or 'desktop' in (device_name or '').lower()) and not used_descriptor:
                context_options.setdefault('device_scale_factor', 2)

        # If no descriptor (e.g., Desktop), set explicit viewport from config
        if not used_descriptor and viewport:
            # For desktop, use a larger viewport to capture more content naturally
            if 'desktop' in (device_name or '').lower():
                # Use a larger viewport for desktop to capture more content
                context_options['viewport'] = {
                    'width': max(viewport.get('width', 1920), 1920),
                    'height': max(viewport.get('height', 1080), 1080)
                }
            else:
                context_options['viewport'] = viewport

        context = await browser.new_context(**context_options)
        await context.add_init_script(STEALTH_INIT_SCRIPT)
        return context

    async def _is_cloudflare_challenge(self, page):
        """Return True when the page still looks like a Cloudflare interstitial."""
        try:
            title = (await page.title() or '').lower()
            if any(marker in title for marker in CLOUDFLARE_TITLE_MARKERS):
                return True
            html = (await page.content() or '').lower()
            return any(marker in html for marker in CLOUDFLARE_BODY_MARKERS)
        except Exception:
            return False

    async def _wait_for_cloudflare(self, page):
        """Wait for Cloudflare/Turnstile challenges to finish before screenshotting."""
        max_wait = BROWSER_LAUNCH.get('cloudflare_wait_seconds', 20)
        if max_wait <= 0:
            return

        deadline = asyncio.get_running_loop().time() + max_wait
        saw_challenge = False

        while asyncio.get_running_loop().time() < deadline:
            if await self._is_cloudflare_challenge(page):
                saw_challenge = True
                logger.info("Cloudflare challenge detected, waiting...")
                await asyncio.sleep(1)
                continue
            if saw_challenge:
                logger.info("Cloudflare challenge appears resolved")
                await asyncio.sleep(2)
            return

        if saw_challenge:
            logger.warning("Cloudflare challenge may not have completed within %ss", max_wait)

    async def _navigate_to_url(self, page, url):
        """Navigate with timeouts suited to protected sites."""
        timeout = BROWSER_LAUNCH.get('navigation_timeout_ms', DEFAULT_SETTINGS['timeout'])
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
        except Exception:
            await page.goto(url, wait_until='load', timeout=timeout)
        await self._wait_for_cloudflare(page)
    
    async def take_screenshot(self, url, browser_name, viewport, wait_time=3, device_name=None, return_metrics=False, region=None, max_retries=3):
        """Take a full-page screenshot and optionally return runtime metrics."""
        from utils import validate_url
        if not validate_url(url):
            logger.error(f"Rejected invalid or blocked URL: {url}")
            return None

        context = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting screenshot for {url} with region: {region} (attempt {attempt + 1}/{max_retries})")
                browser = await self.get_browser(browser_name)
                if not browser:
                    logger.error(f"Failed to get browser: {browser_name}")
                    return None
                context = await self.create_context(browser, viewport, device_name=device_name, browser_name=browser_name, region=region)
                page = await context.new_page()

                if region:
                    from config import REGIONS
                    region_config = REGIONS.get(region, {})
                    locale = region_config.get('locale', 'en-US')
                    await page.add_init_script(f"""
                        Object.defineProperty(navigator, 'language', {{
                            get: function() {{ return '{locale}'; }}
                        }});
                    """)

                await self._navigate_to_url(page, url)

                # Quick font loading check (non-blocking)
                try:
                    await page.evaluate("(async () => { if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch(e) {} } return true; })()")
                except Exception:
                    pass
                
                # Additional wait time for dynamic content
                await asyncio.sleep(wait_time)
                
                # Remove any modal dialogs or cookie banners (common issue)
                await self.handle_common_overlays(page)
                
                # Capture runtime viewport metrics
                metrics = None
                try:
                    metrics = await page.evaluate(
                        "() => ({"
                        " innerWidth: window.innerWidth,"
                        " innerHeight: window.innerHeight,"
                        " devicePixelRatio: window.devicePixelRatio,"
                        " userAgent: navigator.userAgent,"
                        " webdriver: navigator.webdriver,"
                        " screen: { width: window.screen.width, height: window.screen.height }"
                        " })"
                    )
                    logger.info(
                        "Browser fingerprint for %s: ua=%s webdriver=%s",
                        url,
                        (metrics or {}).get('userAgent', '')[:80],
                        (metrics or {}).get('webdriver'),
                    )
                except Exception:
                    metrics = None

                # Take high-quality full page screenshot with better settings
                screenshot_bytes = await page.screenshot(
                    full_page=True, 
                    type='png',
                    animations='disabled',  # Disable animations for consistent screenshots
                    caret='hide'  # Hide text cursor
                )
                
                # Convert to PIL Image and enhance quality
                image = Image.open(io.BytesIO(screenshot_bytes))
                
                # Log screenshot dimensions for debugging
                logger.info(f"Screenshot captured: {image.size[0]}x{image.size[1]} for {url} on {browser_name} {device_name}")
                
                # Enhance image quality without forcing dimensions
                image = self._enhance_screenshot_quality(image, viewport)
                
                await context.close()
                if return_metrics:
                    return image, (metrics or {})
                return image
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                logger.error(f"Error taking screenshot of {url} with {browser_name} (region: {region}) on attempt {attempt + 1}: {e}")
                logger.error(f"Error type: {error_type}")
                
                # Clean up context on error
                if context is not None:
                    try:
                        await context.close()
                    except Exception:
                        pass
                    context = None
                
                # Check if this is a TargetClosedError and we should retry
                if error_type == 'TargetClosedError' and attempt < max_retries - 1:
                    logger.warning(f"Browser context was closed, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                    # Force browser recreation on next attempt
                    if browser_name in self.browsers:
                        try:
                            await self.browsers[browser_name].close()
                        except Exception:
                            pass
                        del self.browsers[browser_name]
                    await asyncio.sleep(2)  # Wait before retry
                    continue
                else:
                    # Log full traceback for non-retryable errors or final attempt
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    break
        
        # If we get here, all retries failed
        logger.error(f"Failed to take screenshot after {max_retries} attempts. Last error: {last_error}")
        return None
    
    def _enhance_screenshot_quality(self, image, viewport):
        """Enhance screenshot quality without forcing dimensions."""
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance sharpness for better clarity
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)  # Slightly increase sharpness
            
            # Enhance contrast for better visibility
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)  # Slightly increase contrast
            
            # For desktop screenshots, preserve the actual page dimensions
            # Only apply minimal quality enhancements without resizing
            # This prevents stretching and maintains the true site appearance
            
            return image
            
        except Exception as e:
            logger.warning(f"Error enhancing screenshot quality: {e}")
            return image  # Return original if enhancement fails
    
    async def handle_common_overlays(self, page):
        """Attempt to dismiss or hide common overlays to reduce visual noise."""
        try:
            # Common selectors for cookie banners and overlays
            overlay_selectors = [
                '[data-testid="cookie-banner"]',
                '.cookie-banner',
                '.cookie-notice',
                '.gdpr-banner',
                '.modal-overlay',
                '[role="dialog"]',
                '.popup-overlay',
                '#cookie-consent'
            ]
            
            for selector in overlay_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=1000)
                    await page.evaluate(
                        "(sel) => { const el = document.querySelector(sel); if (el) el.style.display = 'none'; }",
                        selector
                    )
                except Exception:
                    continue
                    
            # Try to click common "Accept" or "Close" buttons
            accept_buttons = [
                'button:has-text("Accept")',
                'button:has-text("OK")',
                'button:has-text("Close")',
                'button:has-text("Got it")',
                '[data-testid="accept-cookies"]'
            ]
            
            for button_selector in accept_buttons:
                try:
                    await page.click(button_selector, timeout=1000)
                    await asyncio.sleep(0.5)
                except Exception:
                    continue
                    
        except Exception as e:
            # Ignore overlay handling errors as they're not critical
            logger.debug(f"Overlay handling error: {e}")
            pass
    
    async def cleanup(self):
        """Close browsers and stop Playwright if started."""
        try:
            for browser in self.browsers.values():
                await browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self.browsers = {}
            self.playwright = None
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Avoid event-loop operations during interpreter shutdown."""
        try:
            self.browsers = {}
            self.playwright = None
        except Exception:
            pass
