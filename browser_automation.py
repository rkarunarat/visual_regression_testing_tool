import asyncio
from playwright.async_api import async_playwright
import io
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    logger.warning(f"Minimal launch also failed for {browser_name}: {e2}")
                    # Try multiple fallbacks
                    if browser_name == 'Chrome':
                        # Try Firefox first
                        try:
                            logger.info("Trying Firefox as fallback...")
                            self.browsers[browser_name] = await self.playwright.firefox.launch(headless=True)
                            logger.info("Successfully launched Firefox as Chrome fallback")
                        except Exception as e3:
                            logger.warning(f"Firefox fallback failed: {e3}")
                            # Try WebKit as final fallback
                            try:
                                logger.info("Trying WebKit as final fallback...")
                                self.browsers[browser_name] = await self.playwright.webkit.launch(headless=True)
                                logger.info("Successfully launched WebKit as final fallback")
                            except Exception as e4:
                                logger.error(f"All browser fallbacks failed: {e4}")
                                raise RuntimeError(f"Cannot launch any browser: Chrome failed ({e}), Firefox failed ({e3}), WebKit failed ({e4})")
                    else:
                        raise
        
        return self.browsers[browser_name]
    
    async def create_context(self, browser, viewport, user_agent=None):
        """Create browser context with specific viewport and user agent"""
        context_options = {
            'viewport': viewport,
            'ignore_https_errors': True,
            'java_script_enabled': True
        }
        
        if user_agent:
            context_options['user_agent'] = user_agent
        
        return await browser.new_context(**context_options)
    
    async def take_screenshot(self, url, browser_name, viewport, wait_time=3):
        """Take screenshot of a webpage"""
        context = None
        try:
            browser = await self.get_browser(browser_name)
            context = await self.create_context(browser, viewport)
            page = await context.new_page()
            
            # Navigate to URL with timeout
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Additional wait time for dynamic content
            await asyncio.sleep(wait_time)
            
            # Remove any modal dialogs or cookie banners (common issue)
            await self.handle_common_overlays(page)
            
            # Take full page screenshot
            screenshot_bytes = await page.screenshot(
                full_page=True,
                type='png'
            )
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            await context.close()
            return image
            
        except Exception as e:
            logger.error(f"Error taking screenshot of {url} with {browser_name}: {e}")
            if context is not None:
                await context.close()
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
        """Destructor to ensure cleanup"""
        if self.browsers or self.playwright:
            try:
                # Create new event loop if none exists
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # If loop is already running, schedule cleanup
                    asyncio.create_task(self.cleanup())
                else:
                    # If loop is not running, run cleanup
                    loop.run_until_complete(self.cleanup())
                    
            except Exception as e:
                logger.error(f"Error in destructor cleanup: {e}")
