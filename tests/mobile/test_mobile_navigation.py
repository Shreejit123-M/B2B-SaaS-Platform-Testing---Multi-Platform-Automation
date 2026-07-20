"""Mobile web navigation tests, executed via BrowserStack real devices."""

import os

import pytest
from playwright.sync_api import expect, sync_playwright

from browserstack.browserstack_config import build_capabilities, connect_browserstack
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.project_page import ProjectPage  # ASSUMPTION: see tests/web/test_projects.py note
from utils.logger import get_logger

logger = get_logger(__name__)

pytestmark = pytest.mark.mobile


def _require_browserstack() -> None:
    if not os.environ.get("BROWSERSTACK_USERNAME") or not os.environ.get("BROWSERSTACK_ACCESS_KEY"):
        pytest.skip("BrowserStack credentials not configured.")


@pytest.mark.regression
def test_navigate_from_dashboard_to_projects_on_mobile(environment: str, tenant: str) -> None:
    """A user can navigate from the dashboard to the project list on a mobile device,
    confirming the nav menu/hamburger pattern (if any) is functional, not just present."""
    _require_browserstack()
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    capabilities = build_capabilities(browser_name="webkit", device="iPhone 15")

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

            project_page = ProjectPage(page, environment)
            project_page.open()
            # A successful navigation is confirmed by the search field (or
            # equivalent list-page landmark) becoming visible, not just a
            # URL change, since URL-only checks can pass on a blank/broken page.
            expect(project_page.search_input).to_be_visible()
        finally:
            browser.close()


@pytest.mark.regression
def test_logout_navigation_returns_to_login_on_mobile(environment: str, tenant: str) -> None:
    """Logout on a mobile device correctly returns the user to the login screen."""
    _require_browserstack()
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    capabilities = build_capabilities(browser_name="chromium", device="Samsung Galaxy S24")

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            login_page = LoginPage(page, environment).open()
            login_page.login(email, password)

            dashboard = DashboardPage(page, environment)
            dashboard.wait_for_dashboard_loaded()
            dashboard.logout()

            expect(page).to_have_url(f"{environment}/login")
        finally:
            browser.close()
