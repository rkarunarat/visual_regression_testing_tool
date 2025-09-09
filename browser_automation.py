"""Async Playwright automation for capturing screenshots across browsers/devices.

Provides `BrowserManager` to manage Playwright lifecycle, create contexts with
device emulation, capture full-page screenshots, and handle common overlays.
"""
import asyncio
import sys
from playwright.async_api import async_playwright
from config import PLAYWRIGHT_DEVICE_MAP
import io
from PIL import Image
import warnings
import logging
import platform
import os
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow very large images from full-page screenshots and silence PIL warning
Image.MAX_IMAGE_PIXELS = None
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

class BrowserManager:
    """Manage Playwright, browsers/contexts, and screenshot capture."""
    def __init__(self):
        self.playwright = None
        self.browsers = {}
        self.contexts = {}
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
    
    async def initialize(self):
        """Start Playwright if not already started."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
    
    async def get_browser(self, browser_name):
        """Get or launch a browser engine by friendly name (Chrome, Firefox...)."""
        await self.initialize()
        
        if browser_name not in self.browsers:
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
            
            # Browser launch options - optimized for speed
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--no-first-run',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-software-rasterizer',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-ipc-flooding-protection',
                    '--disable-xvfb',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-domain-reliability',
                    '--disable-component-extensions-with-background-pages'
                ]
            }
            
            # Special handling for Edge
            if browser_name == 'Edge':
                launch_options['channel'] = 'msedge'
            
            # WSL + Windows browser integration
            if self.is_wsl and self.windows_browser_paths:
                windows_path = self._get_windows_browser_path(browser_name)
                if windows_path:
                    launch_options['executable_path'] = windows_path
                    logger.info(f"Using Windows browser: {windows_path}")
            
            try:
                self.browsers[browser_name] = await browser_engine.launch(**launch_options)
            except Exception as e:
                logger.warning(f"Could not launch {browser_name}: {e}")
                # Try with minimal flags first
                minimal_options = {
                    'headless': True,
                    'args': ['--no-sandbox', '--disable-dev-shm-usage']
                }
                try:
                    self.browsers[browser_name] = await browser_engine.launch(**minimal_options)
                    logger.info(f"Successfully launched {browser_name} with minimal options")
                except Exception as e2:
                    logger.error(f"Launch failed for {browser_name} even with minimal options: {e2}")
                    raise
        
        return self.browsers[browser_name]
    
    async def create_context(self, browser, viewport, device_name=None, user_agent=None, browser_name=None):
        """Create a browser context with viewport and optional device emulation."""
        context_options = {
            'ignore_https_errors': True,
            'java_script_enabled': True
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

        return await browser.new_context(**context_options)
    
    async def take_screenshot(self, url, browser_name, viewport, wait_time=3, device_name=None, return_metrics=False):
        """Take a full-page screenshot and optionally return runtime metrics."""
        context = None
        try:
            browser = await self.get_browser(browser_name)
            if not browser:
                return None
            context = await self.create_context(browser, viewport, device_name=device_name, browser_name=browser_name)
            page = await context.new_page()
            
            # Navigate to URL with optimized timeout
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            except Exception:
                # Fallback to load if domcontentloaded fails
                await page.goto(url, wait_until='load', timeout=15000)

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
                metrics = await page.evaluate("() => ({ innerWidth: window.innerWidth, innerHeight: window.innerHeight, devicePixelRatio: window.devicePixelRatio, userAgent: navigator.userAgent, screen: { width: window.screen.width, height: window.screen.height } })")
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
            logger.error(f"Error taking screenshot of {url} with {browser_name}: {e}")
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
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
                    await page.evaluate(f'document.querySelector("{selector}").style.display = "none"')
                except:
                    continue  # Selector not found, continue to next
                    
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
                    await asyncio.sleep(0.5)  # Small delay after clicking
                except:
                    continue
                    
        except Exception as e:
            # Ignore overlay handling errors as they're not critical
            logger.debug(f"Overlay handling error: {e}")
            pass
    
    async def cleanup(self):
        """Close contexts/browsers and stop Playwright if started."""
        try:
            # Close all contexts
            for context in self.contexts.values():
                await context.close()
            
            # Close all browsers
            for browser in self.browsers.values():
                await browser.close()
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
            
            # Reset state
            self.browsers = {}
            self.contexts = {}
            self.playwright = None
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Avoid event-loop operations during interpreter shutdown."""
        try:
            # Best-effort: don't touch asyncio loop on teardown to prevent 'Event loop is closed' errors
            self.browsers = {}
            self.contexts = {}
            self.playwright = None
        except Exception:
            pass
