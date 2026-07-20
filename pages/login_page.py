"""Login page object model.

Handles login page interactions and verifications.
"""

from playwright.sync_api import Page, expect
from core.base_page import BasePage
from core.waiter import Waiter
from core.exceptions import AuthenticationException
import logging
import time

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object for Login page."""
    
    # Selectors
    EMAIL_INPUT = "#email"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-btn"
    ERROR_MESSAGE = ".error-message"
    LOADING_SPINNER = ".spinner"
    REMEMBER_ME_CHECKBOX = "#remember-me"
    FORGOT_PASSWORD_LINK = "a[href*='forgot']"
    TWO_FA_PROMPT = ".two-fa-prompt"
    TWO_FA_INPUT = "#two-fa-code"
    TWO_FA_SUBMIT = "#verify-2fa-btn"
    SUCCESS_MESSAGE = ".success-message"
    
    def __init__(self, page: Page, base_url: str = ""):
        """Initialize login page.
        
        Args:
            page: Playwright page object.
            base_url: Base URL for the application.
        """
        super().__init__(page, base_url)
        self.waiter = Waiter(timeout=15)
    
    def navigate(self) -> None:
        """Navigate to login page."""
        login_url = f"{self.base_url}/login"
        logger.info(f"Navigating to login page: {login_url}")
        self.goto(login_url)
        self.wait_for_page_load()
    
    def wait_for_page_load(self) -> None:
        """Wait for login page to load completely.
        
        Waits for email input to be visible, indicating page is ready.
        """
        logger.info("Waiting for login page to load")
        self.wait_for_element(self.EMAIL_INPUT, timeout=10)
        # Wait for any loading spinners to disappear
        self._wait_for_loading_complete()
    
    def enter_email(self, email: str) -> None:
        """Enter email in the login form.
        
        Args:
            email: Email address to enter.
        """
        logger.info(f"Entering email: {email}")
        self.fill(self.EMAIL_INPUT, email)
        # Wait for email to be entered
        self.waiter.wait_for_value_in_element(self, self.EMAIL_INPUT, email, timeout=5)
    
    def enter_password(self, password: str) -> None:
        """Enter password in the login form.
        
        Args:
            password: Password to enter.
        """
        logger.info("Entering password")
        self.fill(self.PASSWORD_INPUT, password)
    
    def enter_credentials(self, email: str, password: str) -> None:
        """Enter both email and password.
        
        Args:
            email: Email address.
            password: Password.
        """
        self.enter_email(email)
        self.enter_password(password)
    
    def click_login_button(self) -> None:
        """Click the login button."""
        logger.info("Clicking login button")
        self.click(self.LOGIN_BUTTON)
        # Wait for loading to complete or 2FA to appear
        time.sleep(1)  # Brief pause for page transition
    
    def login(self, email: str, password: str) -> None:
        """Perform login with email and password.
        
        Args:
            email: Email address.
            password: Password.
            
        Raises:
            AuthenticationException: If login fails.
        """
        try:
            logger.info(f"Logging in with email: {email}")
            self.navigate()
            self.enter_credentials(email, password)
            self.click_login_button()
            self._wait_for_login_response()
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise AuthenticationException(f"Login failed: {str(e)}")
    
    def handle_2fa(self, code: str, timeout: int = 60) -> None:
        """Handle 2FA code entry.
        
        Args:
            code: 2FA code to enter.
            timeout: Timeout for 2FA prompt in seconds.
            
        Raises:
            AuthenticationException: If 2FA fails.
        """
        logger.info("Handling 2FA")
        try:
            # Wait for 2FA prompt to appear
            self.waiter.wait_for_element(self.TWO_FA_PROMPT, timeout=timeout)
            logger.info("2FA prompt appeared")
            
            # Enter 2FA code
            self.fill(self.TWO_FA_INPUT, code)
            
            # Click submit button
            self.click(self.TWO_FA_SUBMIT)
            
            # Wait for response
            time.sleep(1)
        except Exception as e:
            logger.error(f"2FA handling failed: {str(e)}")
            raise AuthenticationException(f"2FA failed: {str(e)}")
    
    def is_login_page(self) -> bool:
        """Check if current page is login page.
        
        Returns:
            bool: True if on login page.
        """
        return self.is_visible(self.EMAIL_INPUT) and self.is_visible(self.LOGIN_BUTTON)
    
    def get_error_message(self) -> str:
        """Get error message from login form.
        
        Returns:
            str: Error message text.
        """
        if self.is_visible(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        return ""
    
    def has_error(self) -> bool:
        """Check if error message is displayed.
        
        Returns:
            bool: True if error is shown.
        """
        return self.is_visible(self.ERROR_MESSAGE)
    
    def is_2fa_required(self) -> bool:
        """Check if 2FA is required.
        
        Returns:
            bool: True if 2FA prompt is visible.
        """
        return self.is_visible(self.TWO_FA_PROMPT)
    
    def check_remember_me(self) -> None:
        """Check the remember me checkbox."""
        if not self.is_checked(self.REMEMBER_ME_CHECKBOX):
            self.click(self.REMEMBER_ME_CHECKBOX)
            logger.info("Checked 'Remember me' checkbox")
    
    def _wait_for_loading_complete(self) -> None:
        """Wait for any loading spinners to disappear."""
        try:
            # Wait for spinner to disappear if it exists
            self.page.wait_for_selector(self.LOADING_SPINNER, state="hidden", timeout=5000)
            logger.info("Loading complete")
        except Exception:
            # Spinner might not exist, which is fine
            pass
    
    def _wait_for_login_response(self) -> None:
        """Wait for login response (either success or error).
        
        This method waits for the page to respond to login attempt.
        """
        # Wait for either success or error message
        try:
            # Try to wait for 2FA first
            if self.page.locator(self.TWO_FA_PROMPT).is_visible():
                logger.info("2FA prompt visible")
                return
        except Exception:
            pass
        
        # Wait for loading to complete
        self._wait_for_loading_complete()
        
        # Give page a moment to transition
        time.sleep(0.5)
