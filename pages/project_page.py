"""Projects page object model.

Handles projects listing page interactions and verifications.
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from core.waiter import Waiter
import logging

logger = logging.getLogger(__name__)


class ProjectPage(BasePage):
    """Page Object for Projects listing page."""
    
    # Selectors
    PROJECT_LIST = ".projects-list"
    PROJECT_ROW = ".project-row"
    PROJECT_NAME_CELL = ".project-name"
    PROJECT_STATUS_CELL = ".project-status"
    DELETE_PROJECT_BUTTON = "button[data-action='delete']"
    EDIT_PROJECT_BUTTON = "button[data-action='edit']"
    CREATE_PROJECT_BUTTON = "button:has-text('Create Project')"
    SEARCH_INPUT = "input[placeholder*='Search']"
    FILTER_SELECT = "select.filter-projects"
    PAGINATION_NEXT = "button[aria-label='Next']"
    PAGINATION_PREV = "button[aria-label='Previous']"
    EMPTY_MESSAGE = ".empty-message"
    LOADING_SPINNER = ".spinner"
    COMPANY_FILTER = "select[name='company']"
    
    def __init__(self, page: Page, base_url: str = ""):
        """Initialize projects page.
        
        Args:
            page: Playwright page object.
            base_url: Base URL for the application.
        """
        super().__init__(page, base_url)
        self.waiter = Waiter(timeout=15)
    
    def navigate(self) -> None:
        """Navigate to projects page."""
        projects_url = f"{self.base_url}/projects"
        logger.info(f"Navigating to projects page: {projects_url}")
        self.goto(projects_url)
        self.wait_for_page_load()
    
    def wait_for_page_load(self) -> None:
        """Wait for projects page to load."""
        logger.info("Waiting for projects page to load")
        try:
            self.page.wait_for_selector(
                f"{self.PROJECT_LIST}, {self.EMPTY_MESSAGE}",
                timeout=15000
            )
        except Exception:
            logger.warning("Projects page elements not found")
    
    def get_project_count(self) -> int:
        """Get number of projects in list.
        
        Returns:
            int: Number of project rows.
        """
        rows = self.locator(self.PROJECT_ROW).all()
        return len(rows)
    
    def get_project_names(self) -> list:
        """Get all project names.
        
        Returns:
            List of project names.
        """
        return self.get_all_texts(f"{self.PROJECT_ROW} {self.PROJECT_NAME_CELL}")
    
    def get_projects_with_company(self, company: str) -> list:
        """Get projects filtered by company.
        
        Args:
            company: Company name to filter by.
            
        Returns:
            List of project names for the company.
        """
        self.select_option(self.COMPANY_FILTER, company)
        self.wait_for_page_load()
        return self.get_project_names()
    
    def search_projects(self, query: str) -> None:
        """Search for projects.
        
        Args:
            query: Search query.
        """
        logger.info(f"Searching for projects: {query}")
        self.fill(self.SEARCH_INPUT, query)
    
    def get_search_results_count(self) -> int:
        """Get number of search results.
        
        Returns:
            int: Number of results.
        """
        return self.get_project_count()
    
    def click_project(self, project_name: str) -> None:
        """Click on a project.
        
        Args:
            project_name: Name of project to click.
        """
        locator = f"{self.PROJECT_ROW}:has-text('{project_name}')"
        logger.info(f"Clicking project: {project_name}")
        self.click(locator)
    
    def delete_project(self, project_name: str) -> None:
        """Delete a project.
        
        Args:
            project_name: Name of project to delete.
        """
        row_locator = f"{self.PROJECT_ROW}:has-text('{project_name}')"
        delete_button = f"{row_locator} {self.DELETE_PROJECT_BUTTON}"
        logger.info(f"Deleting project: {project_name}")
        self.click(delete_button)
    
    def verify_project_in_list(self, project_name: str) -> bool:
        """Verify project exists in list.
        
        Args:
            project_name: Name of project to verify.
            
        Returns:
            bool: True if project is in list.
        """
        try:
            locator = f"{self.PROJECT_ROW}:has-text('{project_name}')"
            return self.is_visible(locator)
        except Exception:
            return False
    
    def is_empty_state_visible(self) -> bool:
        """Check if empty state is shown.
        
        Returns:
            bool: True if no projects are shown.
        """
        return self.is_visible(self.EMPTY_MESSAGE)
