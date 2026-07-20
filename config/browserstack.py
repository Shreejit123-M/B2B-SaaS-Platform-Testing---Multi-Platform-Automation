"""BrowserStack configuration management.

This module handles BrowserStack setup for cloud-based cross-platform testing
including real devices and legacy browsers.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os
import json


@dataclass
class BrowserStackConfig:
    """BrowserStack configuration."""
    
    enabled: bool = False
    username: Optional[str] = None
    access_key: Optional[str] = None
    local_enabled: bool = False
    local_identifier: Optional[str] = None
    browser: str = "Chrome"
    browser_version: str = "latest"
    os: str = "Windows"
    os_version: str = "11"
    resolution: str = "1920x1080"
    build_name: str = "WorkFlowPro-QA-Build"
    project_name: str = "WorkFlowPro-Automation"
    timeout: int = 300
    debug: bool = False
    
    def is_configured(self) -> bool:
        """Check if BrowserStack is properly configured.
        
        Returns:
            bool: True if configured with credentials.
        """
        return self.enabled and self.username and self.access_key
    
    def to_capabilities(self) -> Dict[str, Any]:
        """Convert to Selenium/Playwright capabilities dict.
        
        Returns:
            Dict with BrowserStack capabilities.
        """
        capabilities = {
            "browserstack.user": self.username,
            "browserstack.key": self.access_key,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os": self.os,
            "os_version": self.os_version,
            "resolution": self.resolution,
            "build": self.build_name,
            "project": self.project_name,
            "browserstack.debug": self.debug,
        }
        
        if self.local_enabled:
            capabilities["browserstack.local"] = True
            if self.local_identifier:
                capabilities["browserstack.localIdentifier"] = self.local_identifier
        
        return capabilities
    
    def to_playwright_endpoint(self) -> str:
        """Generate BrowserStack endpoint for Playwright.
        
        Returns:
            str: BrowserStack websocket endpoint.
        """
        if not self.is_configured():
            raise ValueError("BrowserStack not properly configured")
        
        return (
            f"wss://{self.username}:{self.access_key}@cdpws.browserstack.com/playwright"
        )


class BrowserStackManager:
    """Manages BrowserStack configuration."""
    
    @staticmethod
    def from_environment() -> BrowserStackConfig:
        """Load BrowserStack configuration from environment variables.
        
        Returns:
            BrowserStackConfig: Configuration from environment.
        """
        return BrowserStackConfig(
            enabled=os.getenv("BROWSERSTACK_ENABLED", "false").lower() == "true",
            username=os.getenv("BROWSERSTACK_USERNAME"),
            access_key=os.getenv("BROWSERSTACK_ACCESS_KEY"),
            local_enabled=os.getenv("BROWSERSTACK_LOCAL_ENABLED", "false").lower() == "true",
            local_identifier=os.getenv("BROWSERSTACK_LOCAL_IDENTIFIER"),
            browser=os.getenv("BS_BROWSER", "Chrome"),
            browser_version=os.getenv("BS_BROWSER_VERSION", "latest"),
            os=os.getenv("BS_OS", "Windows"),
            os_version=os.getenv("BS_OS_VERSION", "11"),
            resolution=os.getenv("BS_RESOLUTION", "1920x1080"),
            build_name=os.getenv("BS_BUILD_NAME", "WorkFlowPro-QA-Build"),
            project_name=os.getenv("BS_PROJECT_NAME", "WorkFlowPro-Automation"),
            debug=os.getenv("BS_DEBUG", "false").lower() == "true",
        )
    
    @staticmethod
    def validate_configuration(config: BrowserStackConfig) -> tuple[bool, str]:
        """Validate BrowserStack configuration.
        
        Args:
            config: BrowserStack configuration to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not config.enabled:
            return True, "BrowserStack is disabled"
        
        if not config.username:
            return False, "BrowserStack username is not configured"
        
        if not config.access_key:
            return False, "BrowserStack access key is not configured"
        
        return True, "Configuration is valid"
    
    @staticmethod
    def get_device_config(device_name: str) -> Optional[Dict[str, Any]]:
        """Get BrowserStack device configuration.
        
        Args:
            device_name: Name of the device.
            
        Returns:
            Dict with device capabilities or None if not found.
        """
        devices = {
            "iPhone 12": {
                "device": "iPhone 12",
                "os_version": "15.0",
                "realMobile": True,
            },
            "iPhone 14": {
                "device": "iPhone 14",
                "os_version": "16.0",
                "realMobile": True,
            },
            "Pixel 5": {
                "device": "Google Pixel 5",
                "os_version": "11.0",
                "realMobile": True,
            },
            "Pixel 6": {
                "device": "Google Pixel 6",
                "os_version": "12.0",
                "realMobile": True,
            },
            "Galaxy S21": {
                "device": "Samsung Galaxy S21",
                "os_version": "11.0",
                "realMobile": True,
            },
            "iPad Pro": {
                "device": "iPad Pro 12.9 (2021)",
                "os_version": "15.0",
                "realMobile": True,
            },
        }
        
        return devices.get(device_name)
