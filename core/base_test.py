"""Base test class for all tests.

Provides common test setup, teardown, and utility methods.
"""

import pytest
import logging
from typing import Optional
from playwright.sync_api import Page, Browser, BrowserContext

logger = logging.getLogger(__name__)


class BaseTest:
    """Base class for all test classes."""
    
    page: Optional[Page] = None
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    
    def setup_method(self) -> None:
        """Setup before each test method.
        
        Subclasses should override this and call super().setup_method()
        """
        logger.info(f"Setup: {self.__class__.__name__}")
    
    def teardown_method(self) -> None:
        """Teardown after each test method.
        
        Subclasses should override this and call super().teardown_method()
        """
        logger.info(f"Teardown: {self.__class__.__name__}")
    
    @classmethod
    def setup_class(cls) -> None:
        """Setup before all tests in class.
        
        Subclasses should override this and call super().setup_class()
        """
        logger.info(f"Class setup: {cls.__name__}")
    
    @classmethod
    def teardown_class(cls) -> None:
        """Teardown after all tests in class.
        
        Subclasses should override this and call super().teardown_class()
        """
        logger.info(f"Class teardown: {cls.__name__}")
    
    def assert_element_visible(self, page: Page, locator: str, 
                               message: str = "") -> None:
        """Assert element is visible.
        
        Args:
            page: Playwright page object.
            locator: Element selector.
            message: Optional assertion message.
        """
        assert page.locator(locator).is_visible(), \
            message or f"Element '{locator}' is not visible"
    
    def assert_element_not_visible(self, page: Page, locator: str,
                                   message: str = "") -> None:
        """Assert element is not visible.
        
        Args:
            page: Playwright page object.
            locator: Element selector.
            message: Optional assertion message.
        """
        assert not page.locator(locator).is_visible(), \
            message or f"Element '{locator}' is visible"
    
    def assert_text_in_page(self, page: Page, text: str,
                            message: str = "") -> None:
        """Assert text exists in page.
        
        Args:
            page: Playwright page object.
            text: Text to search for.
            message: Optional assertion message.
        """
        assert page.locator(f"text='{text}'").is_visible(), \
            message or f"Text '{text}' not found in page"
    
    def assert_url_contains(self, page: Page, expected_url: str,
                            message: str = "") -> None:
        """Assert current URL contains expected string.
        
        Args:
            page: Playwright page object.
            expected_url: Expected URL substring.
            message: Optional assertion message.
        """
        assert expected_url in page.url, \
            message or f"Expected URL to contain '{expected_url}', got '{page.url}'"
    
    def assert_status_code(self, status_code: int, expected_code: int,
                          message: str = "") -> None:
        """Assert HTTP status code.
        
        Args:
            status_code: Actual status code.
            expected_code: Expected status code.
            message: Optional assertion message.
        """
        assert status_code == expected_code, \
            message or f"Expected status {expected_code}, got {status_code}"
