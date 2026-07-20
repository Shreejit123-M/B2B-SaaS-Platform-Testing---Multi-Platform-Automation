"""Project details page object model.

Handles project details page interactions and verifications.
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from core.waiter import Waiter
import logging

logger = logging.getLogger(__name__)


class ProjectDetailsPage(BasePage):
    """Page Object for Project Details page."""
    
    # Selectors
    PROJECT_TITLE = ".project-title"
    PROJECT_DESCRIPTION = ".project-description"
    PROJECT_STATUS = ".project-status"
    TEAM_MEMBERS_LIST = ".team-members-list"
    TEAM_MEMBER_CARD = ".team-member-card"
    ADD_MEMBER_BUTTON = "button:has-text('Add Member')"
    EDIT_PROJECT_BUTTON = "button:has-text('Edit')"
    DELETE_PROJECT_BUTTON = "button:has-text('Delete')"
    BACK_BUTTON = "button[aria-label='Back']"
    TASKS_TAB = "button[aria-label='Tasks']"
    FILES_TAB = "button[aria-label='Files']"
    SETTINGS_TAB = "button[aria-label='Settings']"
    TASKS_LIST = ".tasks-list"
    TASK_ITEM = ".task-item"
    EMPTY_STATE = ".empty-state"
    LOADING_SPINNER = ".spinner"
    
    def __init__(self, page: Page, base_url: str = ""):
        """Initialize project details page.
        
        Args:
            page: Playwright page object.
            base_url: Base URL for the application.
        """
        super().__init__(page, base_url)
        self.waiter = Waiter(timeout=15)
    
    def navigate_to_project(self, project_id: str) -> None:
        """Navigate to project details.
        
        Args:
            project_id: ID of project to navigate to.
        """
        url = f"{self.base_url}/projects/{project_id}"
        logger.info(f"Navigating to project: {url}")
        self.goto(url)
        self.wait_for_page_load()
    
    def wait_for_page_load(self) -> None:
        """Wait for project details page to load."""
        logger.info("Waiting for project details to load")
        try:
            self.wait_for_element(self.PROJECT_TITLE, timeout=10)
        except Exception:
            logger.warning("Project title not found")
    
    def get_project_title(self) -> str:
        """Get project title.
        
        Returns:
            str: Project title.
        """
        return self.get_text(self.PROJECT_TITLE)
    
    def get_project_description(self) -> str:
        """Get project description.
        
        Returns:
            str: Project description.
        """
        if self.is_visible(self.PROJECT_DESCRIPTION):
            return self.get_text(self.PROJECT_DESCRIPTION)
        return ""
    
    def get_project_status(self) -> str:
        """Get project status.
        
        Returns:
            str: Project status.
        """
        return self.get_text(self.PROJECT_STATUS)
    
    def get_team_member_count(self) -> int:
        """Get number of team members.
        
        Returns:
            int: Number of team member cards.
        """
        members = self.locator(self.TEAM_MEMBER_CARD).all()
        return len(members)
    
    def get_team_member_names(self) -> list:
        """Get all team member names.
        
        Returns:
            List of team member names.
        """
        return self.get_all_texts(f"{self.TEAM_MEMBER_CARD} .member-name")
    
    def click_add_member(self) -> None:
        """Click add member button."""
        logger.info("Clicking add member button")
        self.click(self.ADD_MEMBER_BUTTON)
    
    def click_edit_project(self) -> None:
        """Click edit project button."""
        logger.info("Clicking edit project button")
        self.click(self.EDIT_PROJECT_BUTTON)
    
    def click_delete_project(self) -> None:
        """Click delete project button."""
        logger.info("Clicking delete project button")
        self.click(self.DELETE_PROJECT_BUTTON)
    
    def click_tasks_tab(self) -> None:
        """Click tasks tab."""
        logger.info("Clicking tasks tab")
        self.click(self.TASKS_TAB)
    
    def click_files_tab(self) -> None:
        """Click files tab."""
        logger.info("Clicking files tab")
        self.click(self.FILES_TAB)
    
    def click_settings_tab(self) -> None:
        """Click settings tab."""
        logger.info("Clicking settings tab")
        self.click(self.SETTINGS_TAB)
    
    def get_task_count(self) -> int:
        """Get number of tasks.
        
        Returns:
            int: Number of task items.
        """
        self.click_tasks_tab()
        tasks = self.locator(self.TASK_ITEM).all()
        return len(tasks)
    
    def go_back(self) -> None:
        """Click back button."""
        logger.info("Clicking back button")
        self.click(self.BACK_BUTTON)
