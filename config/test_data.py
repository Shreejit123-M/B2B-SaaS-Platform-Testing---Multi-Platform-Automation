"""Test data constants and configurations.

This module defines test data constants used across the test suite,
including test user accounts, project templates, and other fixtures.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import os


@dataclass
class TestUser:
    """Test user account configuration."""
    
    email: str
    password: str
    full_name: str
    role: str
    company: str
    two_fa_enabled: bool = False


class TestDataConstants:
    """Constants for test data."""
    
    # Company 1 - Test Tenant
    COMPANY_1_ID = "company1"
    COMPANY_1_NAME = "Company 1"
    COMPANY_1_DOMAIN = "company1.workflowpro.com"
    
    # Company 2 - For Multi-tenant Tests
    COMPANY_2_ID = "company2"
    COMPANY_2_NAME = "Company 2"
    COMPANY_2_DOMAIN = "company2.workflowpro.com"
    
    # Test Projects
    TEST_PROJECT_PREFIX = "AUTO_TEST_PROJECT"
    TEST_PROJECT_NAME = f"{TEST_PROJECT_PREFIX}_001"
    TEST_PROJECT_DESCRIPTION = "This is an automated test project"
    
    # Test Team Names
    TEST_TEAM_PREFIX = "AUTO_TEST_TEAM"
    TEST_TEAM_NAME = f"{TEST_TEAM_PREFIX}_001"
    
    # Test Task Templates
    TEST_TASK_TITLE = "Automated Test Task"
    TEST_TASK_DESCRIPTION = "This is an automated test task"
    
    # Timeouts (in seconds)
    ELEMENT_WAIT_TIMEOUT = 10
    EXPLICIT_WAIT_TIMEOUT = 15
    PAGE_LOAD_TIMEOUT = 30
    
    # API Constants
    API_TIMEOUT = 30
    API_MAX_RETRIES = 3
    
    # Test Data Retention
    AUTO_CLEANUP_TEST_DATA = True
    
    # Pagination
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100


class TestUsers:
    """Test user accounts for different roles and tenants."""
    
    @staticmethod
    def get_company1_admin() -> TestUser:
        """Get Company 1 admin account.
        
        Returns:
            TestUser: Admin user for Company 1.
        """
        return TestUser(
            email=os.getenv("ADMIN_EMAIL", "admin@company1.com"),
            password=os.getenv("ADMIN_PASSWORD", "SecurePassword123!"),
            full_name="Admin User",
            role="admin",
            company=TestDataConstants.COMPANY_1_ID,
            two_fa_enabled=False,
        )
    
    @staticmethod
    def get_company1_user() -> TestUser:
        """Get Company 1 regular user account.
        
        Returns:
            TestUser: Regular user for Company 1.
        """
        return TestUser(
            email=os.getenv("COMPANY1_USER_EMAIL", "user@company1.com"),
            password=os.getenv("COMPANY1_USER_PASSWORD", "SecurePassword123!"),
            full_name="Company 1 User",
            role="user",
            company=TestDataConstants.COMPANY_1_ID,
            two_fa_enabled=False,
        )
    
    @staticmethod
    def get_company2_user() -> TestUser:
        """Get Company 2 regular user account.
        
        Returns:
            TestUser: Regular user for Company 2.
        """
        return TestUser(
            email=os.getenv("COMPANY2_USER_EMAIL", "user@company2.com"),
            password=os.getenv("COMPANY2_USER_PASSWORD", "SecurePassword123!"),
            full_name="Company 2 User",
            role="user",
            company=TestDataConstants.COMPANY_2_ID,
            two_fa_enabled=False,
        )
    
    @staticmethod
    def get_2fa_enabled_user() -> TestUser:
        """Get user with 2FA enabled.
        
        Returns:
            TestUser: User with 2FA enabled.
        """
        return TestUser(
            email=os.getenv("2FA_ENABLED_USER_EMAIL", "2fa@company1.com"),
            password=os.getenv("2FA_ENABLED_USER_PASSWORD", "SecurePassword123!"),
            full_name="2FA Enabled User",
            role="user",
            company=TestDataConstants.COMPANY_1_ID,
            two_fa_enabled=True,
        )


class TestDataBuilder:
    """Builder for creating test data objects."""
    
    @staticmethod
    def create_project_payload(name: str = None, description: str = None) -> Dict[str, Any]:
        """Create a project creation payload.
        
        Args:
            name: Project name.
            description: Project description.
            
        Returns:
            Dict with project payload for API.
        """
        return {
            "name": name or TestDataConstants.TEST_PROJECT_NAME,
            "description": description or TestDataConstants.TEST_PROJECT_DESCRIPTION,
            "status": "active",
            "visibility": "private",
        }
    
    @staticmethod
    def create_team_payload(name: str = None) -> Dict[str, Any]:
        """Create a team creation payload.
        
        Args:
            name: Team name.
            
        Returns:
            Dict with team payload for API.
        """
        return {
            "name": name or TestDataConstants.TEST_TEAM_NAME,
            "description": "Automated test team",
        }
    
    @staticmethod
    def create_task_payload(title: str = None, description: str = None) -> Dict[str, Any]:
        """Create a task creation payload.
        
        Args:
            title: Task title.
            description: Task description.
            
        Returns:
            Dict with task payload for API.
        """
        return {
            "title": title or TestDataConstants.TEST_TASK_TITLE,
            "description": description or TestDataConstants.TEST_TASK_DESCRIPTION,
            "status": "todo",
            "priority": "medium",
        }
