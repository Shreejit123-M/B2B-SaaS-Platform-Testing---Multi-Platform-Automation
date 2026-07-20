"""Dashboard page object model.

Handles dashboard page interactions and verifications.
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from core.waiter import Waiter
import logging

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """Page Object for Dashboard page."""
    
    # Selectors
    WELCOME_MESSAGE = ".welcome-message"
    USER_NAME = ".user-name"
    PROFILE_MENU = "button[aria-label='Profile']"
    LOGOUT_BUTTON = "a[href*='logout']"
    PROJECT_CARD = ".project-card"
    CREATE_PROJECT_BUTTON = "button:has-text('Create Project')"
    QUICK_STATS = ".quick-stats"
    RECENT_ACTIVITY = ".recent-activity"
    LOADING_INDICATOR = ".loading"
    EMPTY_STATE = ".empty-state"
    
    def __init__(self, page: Page, base_url: str = ""):
        """Initialize dashboard page.
        
        Args:
            page: Playwright page object.
            base_url: Base URL for the application.
        """
        super().__init__(page, base_url)
        self.waiter = Waiter(timeout=15)
    
    def navigate(self) -> None:
        """Navigate to dashboard."""
        dashboard_url = f"{self.base_url}/dashboard"
        logger.info(f"Navigating to dashboard: {dashboard_url}")
        self.goto(dashboard_url)
        self.wait_for_page_load()
    
    def wait_for_page_load(self) -> None:
        """Wait for dashboard to load completely.
        
        Waits for welcome message or empty state to be visible.
        """
        logger.info("Waiting for dashboard to load")
        try:
            # Wait for either welcome message or empty state
            self.page.wait_for_selector(
                f"{self.WELCOME_MESSAGE}, {self.EMPTY_STATE}",
                timeout=15000
            )
        except Exception:
            logger.warning("Dashboard elements not found, but proceeding")
    
    def is_dashboard_page(self) -> bool:
        """Check if current page is dashboard.
        
        Returns:
            bool: True if on dashboard page.
        """
        return (self.is_visible(self.WELCOME_MESSAGE) or 
                self.is_visible(self.EMPTY_STATE))
    
    def get_welcome_message(self) -> str:
        """Get welcome message text.
        
        Returns:
            str: Welcome message.
        """
        if self.is_visible(self.WELCOME_MESSAGE):
            return self.get_text(self.WELCOME_MESSAGE)
        return ""
    
    def get_user_name(self) -> str:
        """Get logged-in user name.
        
        Returns:
            str: User name.
        """
        if self.is_visible(self.USER_NAME):
            return self.get_text(self.USER_NAME)
        return ""
    
    def get_project_count(self) -> int:
        """Get number of projects displayed.
        
        Returns:
            int: Number of project cards.
        """
        projects = self.locator(self.PROJECT_CARD).all()
        return len(projects)
    
    def get_project_names(self) -> list:
        """Get all project names displayed.
        
        Returns:
            List of project names.
        """
        return self.get_all_texts(f"{self.PROJECT_CARD} .project-name")
    
    def click_create_project(self) -> None:
        """Click create project button."""
        logger.info("Clicking create project button")
        self.click(self.CREATE_PROJECT_BUTTON)
    
    def open_profile_menu(self) -> None:
        """Open profile menu."""
        logger.info("Opening profile menu")
        self.click(self.PROFILE_MENU)
    
    def logout(self) -> None:
        """Logout from dashboard."""
        logger.info("Logging out")
        self.open_profile_menu()
        self.click(self.LOGOUT_BUTTON)
    
    def is_empty_state_visible(self) -> bool:
        """Check if empty state is shown (no projects).
        
        Returns:
            bool: True if empty state is visible.
        """
        return self.is_visible(self.EMPTY_STATE)
    
    def wait_for_projects_to_load(self, timeout: int = 10) -> None:
        """Wait for projects to load on dashboard.
        
        Args:
            timeout: Timeout in seconds.
        """
        logger.info("Waiting for projects to load")
        self.waiter.wait_for_element(self.PROJECT_CARD, timeout=timeout)
