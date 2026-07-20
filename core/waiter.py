"""Custom waiter utilities for Playwright.

Provides explicit wait mechanisms and custom wait conditions for test reliability.
"""

from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import time
from core.exceptions import TimeoutException, ElementNotFoundException


class Waiter:
    """Custom waiter for explicit waits with timeout handling."""
    
    def __init__(self, timeout: int = 10, poll_frequency: float = 0.5):
        """Initialize waiter.
        
        Args:
            timeout: Maximum wait time in seconds.
            poll_frequency: How often to check condition in seconds.
        """
        self.timeout = timeout
        self.poll_frequency = poll_frequency
    
    def wait_for(self, condition: Callable[[], bool], message: str = "") -> bool:
        """Wait for a condition to be true.
        
        Args:
            condition: Callable that returns True when condition is met.
            message: Error message if timeout occurs.
            
        Returns:
            bool: True if condition is met.
            
        Raises:
            TimeoutException: If timeout occurs.
        """
        end_time = datetime.now() + timedelta(seconds=self.timeout)
        last_exception = None
        
        while datetime.now() < end_time:
            try:
                if condition():
                    return True
            except Exception as e:
                last_exception = e
            
            time.sleep(self.poll_frequency)
        
        error_msg = message or "Condition not met within timeout period"
        raise TimeoutException(f"{error_msg} (waited {self.timeout}s)")
    
    def wait_for_element(self, page_obj: Any, locator: str, timeout: Optional[int] = None) -> bool:
        """Wait for element to be visible on page.
        
        Args:
            page_obj: Page object with locator method.
            locator: Element locator string.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if element is visible.
            
        Raises:
            TimeoutException: If element not found.
        """
        timeout_val = timeout or self.timeout
        end_time = datetime.now() + timedelta(seconds=timeout_val)
        
        while datetime.now() < end_time:
            try:
                element = page_obj.locator(locator)
                if element.is_visible():
                    return True
            except Exception:
                pass
            
            time.sleep(self.poll_frequency)
        
        raise TimeoutException(f"Element '{locator}' not visible after {timeout_val}s")
    
    def wait_for_text_in_element(self, page_obj: Any, locator: str, text: str, 
                                  timeout: Optional[int] = None) -> bool:
        """Wait for text to appear in element.
        
        Args:
            page_obj: Page object.
            locator: Element locator.
            text: Text to wait for.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if text is found.
            
        Raises:
            TimeoutException: If text not found.
        """
        def condition():
            element = page_obj.locator(locator)
            return text.lower() in element.text_content().lower()
        
        timeout_val = timeout or self.timeout
        old_timeout = self.timeout
        self.timeout = timeout_val
        try:
            return self.wait_for(condition, 
                               f"Text '{text}' not found in '{locator}'")
        finally:
            self.timeout = old_timeout
    
    def wait_for_value_in_element(self, page_obj: Any, locator: str, 
                                   value: str, timeout: Optional[int] = None) -> bool:
        """Wait for element to have specific value.
        
        Args:
            page_obj: Page object.
            locator: Element locator.
            value: Expected value.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if value matches.
            
        Raises:
            TimeoutException: If value doesn't match.
        """
        def condition():
            element = page_obj.locator(locator)
            return element.input_value() == value
        
        timeout_val = timeout or self.timeout
        old_timeout = self.timeout
        self.timeout = timeout_val
        try:
            return self.wait_for(condition, 
                               f"Element value not '{value}'")
        finally:
            self.timeout = old_timeout
    
    def wait_for_element_count(self, page_obj: Any, locator: str, count: int,
                               timeout: Optional[int] = None) -> bool:
        """Wait for specific number of elements.
        
        Args:
            page_obj: Page object.
            locator: Element locator.
            count: Expected element count.
            timeout: Optional timeout override.
            
        Returns:
            bool: True if count matches.
            
        Raises:
            TimeoutException: If count doesn't match.
        """
        def condition():
            elements = page_obj.locator(locator).all()
            return len(elements) == count
        
        timeout_val = timeout or self.timeout
        old_timeout = self.timeout
        self.timeout = timeout_val
        try:
            return self.wait_for(condition,
                               f"Expected {count} elements, didn't find")
        finally:
            self.timeout = old_timeout
