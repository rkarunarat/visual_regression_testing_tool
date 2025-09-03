import asyncio
import sys
from playwright.async_api import async_playwright
from config import PLAYWRIGHT_DEVICE_MAP
import io
from PIL import Image
import warnings
import logging

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
    def __init__(self):
        self.playwright = None
        self.browsers = {}
        self.contexts = {}
    
    async def initialize(self):
        """Initialize Playwright and browsers"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
    
    async def get_browser(self, browser_name):
        """Get or create browser instance"""
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
            
            # Browser launch options - optimized for Replit environment
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
                    '--disable-xvfb'
                ]
            }
            
            # Special handling for Edge
            if browser_name == 'Edge':
                launch_options['channel'] = 'msedge'
            
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
        """Create browser context with specific viewport and optional device emulation"""
        context_options = {
            'viewport': viewport,
            'ignore_https_errors': True,
            'java_script_enabled': True
        }

        # Prefer built-in device descriptors when possible
        if device_name and self.playwright is not None:
            descriptor = PLAYWRIGHT_DEVICE_MAP.get(device_name)
            if descriptor:
                try:
                    dopt = self.playwright.devices.get(descriptor)
                    if dopt:
                        # Merge descriptor but keep explicit viewport override later
                        for k, v in dopt.items():
                            if k not in ['viewport']:
                                context_options[k] = v
                except Exception:
                    pass

        if user_agent:
            context_options['user_agent'] = user_agent

        # Firefox does not support some mobile emulation context options
        if (browser_name or '').lower() == 'firefox':
            for k in ['isMobile', 'is_mobile', 'hasTouch', 'has_touch', 'deviceScaleFactor', 'device_scale_factor']:
                context_options.pop(k, None)
        else:
            # For desktop contexts, capture sharper screenshots by using higher DPR
            if not device_name or 'desktop' in (device_name or '').lower():
                context_options.setdefault('device_scale_factor', 2)

        return await browser.new_context(**context_options)
    
    async def take_screenshot(self, url, browser_name, viewport, wait_time=3, device_name=None):
        """Take screenshot of a webpage"""
        context = None
        try:
            browser = await self.get_browser(browser_name)
            if not browser:
                return None
            context = await self.create_context(browser, viewport, device_name=device_name, browser_name=browser_name)
            page = await context.new_page()
            
            # Navigate to URL with timeout
            try:
                await page.goto(url, wait_until='networkidle', timeout=45000)
            except Exception:
                await page.goto(url, wait_until='load', timeout=45000)

            # Ensure fonts and late resources are ready before capture
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
                await page.evaluate("(async () => { if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch(e) {} } return true; })()")
            except Exception:
                pass
            
            # Additional wait time for dynamic content
            await asyncio.sleep(wait_time)
            
            # Remove any modal dialogs or cookie banners (common issue)
            await self.handle_common_overlays(page)
            
            # Take full page screenshot
            screenshot_bytes = await page.screenshot(full_page=True, type='png', scale='device')
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            await context.close()
            return image
            
        except Exception as e:
            logger.error(f"Error taking screenshot of {url} with {browser_name}: {e}")
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            return None
    
    async def handle_common_overlays(self, page):
        """Handle common overlays like cookie banners, modals, etc."""
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
        """Clean up browser resources"""
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
