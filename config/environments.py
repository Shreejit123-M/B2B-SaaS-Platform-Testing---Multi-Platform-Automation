"""Environment configuration management.

This module handles different environment configurations (local, staging, production, CI)
and provides environment-specific settings for the test framework.
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
import os


class EnvironmentType(Enum):
    """Supported environment types."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    CI = "ci"


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    
    name: str
    base_url: str
    api_base_url: str
    login_url: str
    dashboard_url: str
    default_timeout: int = 10
    explicit_wait_timeout: int = 15
    page_load_timeout: int = 30
    dynamic_element_timeout: int = 20
    two_fa_timeout: int = 60
    use_headless: bool = True
    screenshot_on_failure: bool = True
    trace_on_failure: bool = True
    video_on_failure: bool = False
    cleanup_test_data: bool = True
    delete_test_projects: bool = True
    max_retries: int = 3
    retry_delay: int = 2
    parallel_workers: int = 0
    verify_ssl: bool = True


class EnvironmentManager:
    """Manages environment-specific configurations."""
    
    _ENVIRONMENTS: Dict[EnvironmentType, EnvironmentConfig] = {
        EnvironmentType.LOCAL: EnvironmentConfig(
            name="Local",
            base_url=os.getenv("APP_BASE_URL", "http://localhost:3000"),
            api_base_url=os.getenv("APP_API_BASE_URL", "http://localhost:3001/api"),
            login_url=os.getenv("APP_LOGIN_URL", "http://localhost:3000/login"),
            dashboard_url=os.getenv("APP_DASHBOARD_URL", "http://localhost:3000/dashboard"),
            default_timeout=10,
            explicit_wait_timeout=15,
            page_load_timeout=30,
            dynamic_element_timeout=20,
            two_fa_timeout=60,
            use_headless=False,
            screenshot_on_failure=True,
            trace_on_failure=True,
            video_on_failure=False,
            cleanup_test_data=True,
            delete_test_projects=True,
            verify_ssl=False,
        ),
        EnvironmentType.STAGING: EnvironmentConfig(
            name="Staging",
            base_url=os.getenv("APP_BASE_URL", "https://staging.workflowpro.com"),
            api_base_url=os.getenv("APP_API_BASE_URL", "https://staging-api.workflowpro.com"),
            login_url=os.getenv("APP_LOGIN_URL", "https://staging.workflowpro.com/login"),
            dashboard_url=os.getenv("APP_DASHBOARD_URL", "https://staging.workflowpro.com/dashboard"),
            default_timeout=15,
            explicit_wait_timeout=20,
            page_load_timeout=40,
            dynamic_element_timeout=25,
            two_fa_timeout=90,
            use_headless=True,
            screenshot_on_failure=True,
            trace_on_failure=True,
            video_on_failure=False,
            cleanup_test_data=True,
            delete_test_projects=True,
            verify_ssl=True,
        ),
        EnvironmentType.PRODUCTION: EnvironmentConfig(
            name="Production",
            base_url=os.getenv("APP_BASE_URL", "https://app.workflowpro.com"),
            api_base_url=os.getenv("APP_API_BASE_URL", "https://api.workflowpro.com"),
            login_url=os.getenv("APP_LOGIN_URL", "https://app.workflowpro.com/login"),
            dashboard_url=os.getenv("APP_DASHBOARD_URL", "https://app.workflowpro.com/dashboard"),
            default_timeout=20,
            explicit_wait_timeout=25,
            page_load_timeout=50,
            dynamic_element_timeout=30,
            two_fa_timeout=120,
            use_headless=True,
            screenshot_on_failure=False,
            trace_on_failure=False,
            video_on_failure=False,
            cleanup_test_data=False,
            delete_test_projects=False,
            verify_ssl=True,
        ),
        EnvironmentType.CI: EnvironmentConfig(
            name="CI/CD",
            base_url=os.getenv("APP_BASE_URL", "https://staging.workflowpro.com"),
            api_base_url=os.getenv("APP_API_BASE_URL", "https://staging-api.workflowpro.com"),
            login_url=os.getenv("APP_LOGIN_URL", "https://staging.workflowpro.com/login"),
            dashboard_url=os.getenv("APP_DASHBOARD_URL", "https://staging.workflowpro.com/dashboard"),
            default_timeout=15,
            explicit_wait_timeout=20,
            page_load_timeout=40,
            dynamic_element_timeout=25,
            two_fa_timeout=90,
            use_headless=True,
            screenshot_on_failure=True,
            trace_on_failure=True,
            video_on_failure=True,
            cleanup_test_data=True,
            delete_test_projects=True,
            parallel_workers=4,
            verify_ssl=True,
        ),
    }
    
    @staticmethod
    def get_environment_type() -> EnvironmentType:
        """Get the current environment type from environment variables.
        
        Returns:
            EnvironmentType: The current environment type.
        """
        env_name = os.getenv("TEST_ENVIRONMENT", "staging").lower()
        try:
            return EnvironmentType[env_name.upper()]
        except KeyError:
            return EnvironmentType.STAGING
    
    @staticmethod
    def get_config(env_type: Optional[EnvironmentType] = None) -> EnvironmentConfig:
        """Get configuration for a specific environment.
        
        Args:
            env_type: Environment type to get config for. If None, uses current environment.
            
        Returns:
            EnvironmentConfig: Configuration for the specified environment.
        """
        if env_type is None:
            env_type = EnvironmentManager.get_environment_type()
        
        return EnvironmentManager._ENVIRONMENTS[env_type]
    
    @staticmethod
    def get_current_config() -> EnvironmentConfig:
        """Get configuration for the current environment.
        
        Returns:
            EnvironmentConfig: Configuration for current environment.
        """
        return EnvironmentManager.get_config()
