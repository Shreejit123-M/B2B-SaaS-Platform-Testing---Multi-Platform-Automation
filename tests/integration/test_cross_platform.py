"""Cross-platform smoke coverage: desktop browsers + BrowserStack devices.

Runs the same minimal critical-path check (login -> dashboard load) across
every platform in the supported matrix, so a platform-specific rendering
or timing regression is caught in one place rather than duplicated per
test file. See Framework_Design.md, Section 11, for the BrowserStack
driver design this depends on.
"""

import os

import pytest
from playwright.sync_api import expect, sync_playwright

from browserstack.browserstack_config import build_capabilities, connect_browserstack
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)

BROWSERSTACK_MATRIX = [
    {"browser_name": "webkit", "os_name": "OS X", "os_version": "Sonoma"},  # Safari desktop
    {"browser_name": "webkit", "device": "iPhone 15"},
    {"browser_name": "chromium", "device": "Samsung Galaxy S24"},
]


@pytest.mark.integration
@pytest.mark.regression
def test_login_and_dashboard_on_local_browser(authenticated_page: DashboardPage) -> None:
    """Baseline cross-platform check on the locally/CI-launched browser
    (Chromium or Firefox, per --browser-name)."""
    expect(authenticated_page.welcome_message).to_be_visible()


@pytest.mark.integration
@pytest.mark.mobile
@pytest.mark.parametrize(
    "capability_spec",
    BROWSERSTACK_MATRIX,
    ids=lambda c: c.get("device", c.get("os_name", "unknown")),
)
def test_login_and_dashboard_on_browserstack_matrix(
    environment: str, tenant: str, capability_spec: dict
) -> None:
    """The same login -> dashboard check, run across the BrowserStack matrix
    (Safari desktop, iOS mobile web, Android mobile web)."""
    if not os.environ.get("BROWSERSTACK_USERNAME") or not os.environ.get("BROWSERSTACK_ACCESS_KEY"):
        pytest.skip("BrowserStack credentials not configured.")

    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    capabilities = build_capabilities(**capability_spec)

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            login_page = LoginPage(page, environment).open()
            login_page.login(email, password)

            dashboard = DashboardPage(page, environment)
            dashboard.wait_for_dashboard_loaded()
            expect(dashboard.welcome_message).to_be_visible()
        finally:
            browser.close()
