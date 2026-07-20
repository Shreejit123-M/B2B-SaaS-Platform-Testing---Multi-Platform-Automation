"""Base Page Object Model class.

Provides common page object functionality and utilities for all page objects.
"""

from playwright.sync_api import Page, Locator
from typing import Optional, List
from core.waiter import Waiter
from core.exceptions import NavigationException, ElementNotFoundException
import logging

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects."""
    
    def __init__(self, page: Page, base_url: str = ""):
        """Initialize page object.
        
        Args:
            page: Playwright page object.
            base_url: Base URL for the application.
        """
        self.page = page
        self.base_url = base_url
        self.waiter = Waiter(timeout=10)
    
    def goto(self, url: str) -> None:
        """Navigate to URL.
        
        Args:
            url: URL to navigate to.
            
        Raises:
            NavigationException: If navigation fails.
        """
        try:
            logger.info(f"Navigating to {url}")
            self.page.goto(url)
        except Exception as e:
            raise NavigationException(f"Failed to navigate to {url}: {str(e)}")
    
    def goto_relative(self, path: str) -> None:
        """Navigate to relative path.
        
        Args:
            path: Relative path to navigate to.
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        self.goto(url)
    
    def get_url(self) -> str:
        """Get current page URL.
        
        Returns:
            str: Current URL.
        """
        return self.page.url
    
    def get_title(self) -> str:
        """Get page title.
        
        Returns:
            str: Page title.
        """
        return self.page.title()
    
    def locator(self, selector: str) -> Locator:
        """Get locator for element.
        
        Args:
            selector: CSS selector or other Playwright selector.
            
        Returns:
            Locator: Playwright locator object.
        """
        return self.page.locator(selector)
    
    def click(self, locator: str, timeout: Optional[int] = None) -> None:
        """Click element.
        
        Args:
            locator: Element selector.
            timeout: Optional timeout override.
        """
        element = self.locator(locator)
        element.click(timeout=timeout * 1000 if timeout else None)
        logger.info(f"Clicked element: {locator}")
    
    def fill(self, locator: str, text: str) -> None:
        """Fill input field with text.
        
        Args:
            locator: Element selector.
            text: Text to fill.
        """
        element = self.locator(locator)
        element.fill(text)
        logger.info(f"Filled '{locator}' with text")
    
    def clear(self, locator: str) -> None:
        """Clear input field.
        
        Args:
            locator: Element selector.
        """
        element = self.locator(locator)
        element.fill("")
        logger.info(f"Cleared '{locator}'")
    
    def type_text(self, locator: str, text: str, delay: int = 0) -> None:
        """Type text character by character.
        
        Args:
            locator: Element selector.
            text: Text to type.
            delay: Delay between key presses in milliseconds.
        """
        element = self.locator(locator)
        element.type(text, delay=delay)
        logger.info(f"Typed text in '{locator}'")
    
    def get_text(self, locator: str) -> str:
        """Get element text content.
        
        Args:
            locator: Element selector.
            
        Returns:
            str: Element text.
        """
        return self.locator(locator).text_content() or ""
    
    def get_value(self, locator: str) -> str:
        """Get input element value.
        
        Args:
            locator: Element selector.
            
        Returns:
            str: Input value.
        """
        return self.locator(locator).input_value()
    
    def is_visible(self, locator: str) -> bool:
        """Check if element is visible.
        
        Args:
            locator: Element selector.
            
        Returns:
            bool: True if element is visible.
        """
        return self.locator(locator).is_visible()
    
    def is_enabled(self, locator: str) -> bool:
        """Check if element is enabled.
        
        Args:
            locator: Element selector.
            
        Returns:
            bool: True if element is enabled.
        """
        return self.locator(locator).is_enabled()
    
    def is_checked(self, locator: str) -> bool:
        """Check if checkbox is checked.
        
        Args:
            locator: Element selector.
            
        Returns:
            bool: True if checkbox is checked.
        """
        return self.locator(locator).is_checked()
    
    def wait_for_element(self, locator: str, timeout: Optional[int] = None) -> bool:
        """Wait for element to be visible.
        
        Args:
            locator: Element selector.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if element is visible.
        """
        return self.waiter.wait_for_element(self, locator, timeout)
    
    def wait_for_text(self, locator: str, text: str, timeout: Optional[int] = None) -> bool:
        """Wait for text in element.
        
        Args:
            locator: Element selector.
            text: Text to wait for.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if text is found.
        """
        return self.waiter.wait_for_text_in_element(self, locator, text, timeout)
    
    def get_all_texts(self, locator: str) -> List[str]:
        """Get text from all matching elements.
        
        Args:
            locator: Element selector.
            
        Returns:
            List of text strings.
        """
        elements = self.locator(locator).all()
        return [element.text_content() or "" for element in elements]
    
    def select_option(self, locator: str, value: str) -> None:
        """Select option from dropdown.
        
        Args:
            locator: Select element selector.
            value: Option value to select.
        """
        self.locator(locator).select_option(value)
        logger.info(f"Selected '{value}' from '{locator}'")
    
    def reload(self) -> None:
        """Reload the page."""
        logger.info("Reloading page")
        self.page.reload()
    
    def take_screenshot(self, path: str) -> None:
        """Take screenshot of page.
        
        Args:
            path: Path to save screenshot.
        """
        self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
    
    def start_tracing(self, path: str) -> None:
        """Start Playwright trace recording.
        
        Args:
            path: Path to save trace file.
        """
        self.page.context.tracing.start(screenshots=True, snapshots=True)
        logger.info(f"Trace recording started")
    
    def stop_tracing(self, path: str) -> None:
        """Stop Playwright trace recording.
        
        Args:
            path: Path to save trace file.
        """
        self.page.context.tracing.stop(path=path)
        logger.info(f"Trace saved to {path}")
