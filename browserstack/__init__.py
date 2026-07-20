"""
BrowserStack integration package.

This package contains BrowserStack configuration helpers and utilities
used for executing Playwright tests on BrowserStack cloud browsers and
mobile devices.
"""

from .browserstack_config import (
    build_capabilities,
    connect_browserstack,
    get_browserstack_credentials,
)

__all__ = [
    "build_capabilities",
    "connect_browserstack",
    "get_browserstack_credentials",
]
