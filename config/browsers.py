"""Browser capabilities and configuration.

This module defines browser types, capabilities, and configurations
for Playwright and BrowserStack testing.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os


class BrowserType(Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class MobileDevice(Enum):
    """Supported mobile devices for emulation."""
    IPHONE_12 = "iPhone 12"
    IPHONE_13 = "iPhone 13"
    IPHONE_14 = "iPhone 14"
    IPHONE_15 = "iPhone 15"
    PIXEL_5 = "Pixel 5"
    PIXEL_6 = "Pixel 6"
    PIXEL_7 = "Pixel 7"
    IPAD_PRO = "iPad Pro"
    IPAD_MINI = "iPad mini"
    GALAXY_S21 = "Galaxy S21"


@dataclass
class BrowserCapabilities:
    """Browser capabilities configuration."""
    
    browser_type: BrowserType
    headless: bool = True
    slow_motion: int = 0
    viewport_width: int = 1920
    viewport_height: int = 1080
    device_scale_factor: int = 1
    locale: str = "en-US"
    timezone: str = "America/New_York"
    ignore_https_errors: bool = False
    
    def to_playwright_config(self) -> Dict[str, Any]:
        """Convert to Playwright launch options.
        
        Returns:
            Dict with Playwright launch options.
        """
        config = {
            "headless": self.headless,
            "slow_mo": self.slow_motion,
        }
        return config
    
    def to_browser_context_config(self) -> Dict[str, Any]:
        """Convert to Playwright context options.
        
        Returns:
            Dict with Playwright context options.
        """
        return {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "device_scale_factor": self.device_scale_factor,
            "locale": self.locale,
            "timezone_id": self.timezone,
            "ignore_https_errors": self.ignore_https_errors,
        }


class BrowserManager:
    """Manages browser configuration and capabilities."""
    
    @staticmethod
    def get_browser_type() -> BrowserType:
        """Get browser type from environment or default.
        
        Returns:
            BrowserType: The configured browser type.
        """
        browser_name = os.getenv("BROWSER", "chromium").lower()
        try:
            return BrowserType[browser_name.upper()]
        except KeyError:
            return BrowserType.CHROMIUM
    
    @staticmethod
    def get_headless() -> bool:
        """Check if browser should run in headless mode.
        
        Returns:
            bool: True for headless mode, False for headed mode.
        """
        return os.getenv("HEADLESS", "true").lower() == "true"
    
    @staticmethod
    def get_viewport() -> Dict[str, int]:
        """Get viewport dimensions.
        
        Returns:
            Dict with width and height.
        """
        return {
            "width": int(os.getenv("BROWSER_WIDTH", "1920")),
            "height": int(os.getenv("BROWSER_HEIGHT", "1080")),
        }
    
    @staticmethod
    def get_mobile_device() -> Optional[MobileDevice]:
        """Get mobile device for emulation.
        
        Returns:
            MobileDevice if configured, None for desktop.
        """
        device_name = os.getenv("MOBILE_DEVICE", "").strip()
        if not device_name:
            return None
        
        try:
            return MobileDevice[device_name.replace(" ", "_").upper()]
        except KeyError:
            for device in MobileDevice:
                if device.value == device_name:
                    return device
        return None
    
    @staticmethod
    def get_default_capabilities() -> BrowserCapabilities:
        """Get default browser capabilities.
        
        Returns:
            BrowserCapabilities: Default browser configuration.
        """
        viewport = BrowserManager.get_viewport()
        return BrowserCapabilities(
            browser_type=BrowserManager.get_browser_type(),
            headless=BrowserManager.get_headless(),
            slow_motion=int(os.getenv("SLOW_MO", "0")),
            viewport_width=viewport["width"],
            viewport_height=viewport["height"],
            locale=os.getenv("LOCALE", "en-US"),
            timezone=os.getenv("TIMEZONE", "America/New_York"),
            ignore_https_errors=os.getenv("IGNORE_HTTPS_ERRORS", "false").lower() == "true",
        )
    
    @staticmethod
    def get_mobile_capabilities(device: MobileDevice) -> Dict[str, Any]:
        """Get capabilities for a specific mobile device.
        
        Args:
            device: The mobile device to get capabilities for.
            
        Returns:
            Dict with mobile device capabilities.
        """
        mobile_devices = {
            MobileDevice.IPHONE_12: {
                "device_name": "iPhone 12",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
                "viewport": {"width": 390, "height": 844},
                "device_scale_factor": 3,
                "has_touch": True,
                "is_mobile": True,
            },
            MobileDevice.PIXEL_5: {
                "device_name": "Pixel 5",
                "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
                "viewport": {"width": 393, "height": 851},
                "device_scale_factor": 2.75,
                "has_touch": True,
                "is_mobile": True,
            },
            MobileDevice.IPAD_PRO: {
                "device_name": "iPad Pro",
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
                "viewport": {"width": 1024, "height": 1366},
                "device_scale_factor": 2,
                "has_touch": True,
                "is_mobile": False,
            },
        }
        
        return mobile_devices.get(device, {})
