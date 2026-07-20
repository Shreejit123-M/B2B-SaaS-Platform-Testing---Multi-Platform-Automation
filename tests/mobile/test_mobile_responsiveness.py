"""Mobile responsiveness tests, executed via BrowserStack real devices.

Verifies the responsive web layout adapts correctly rather than assuming
"it looks the same as desktop" — checks absence of horizontal overflow
and presence of core elements within the mobile viewport.
"""

import os

import pytest
from playwright.sync_api import expect, sync_playwright

from browserstack.browserstack_config import build_capabilities, connect_browserstack
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)

pytestmark = pytest.mark.mobile


def _require_browserstack() -> None:
    if not os.environ.get("BROWSERSTACK_USERNAME") or not os.environ.get("BROWSERSTACK_ACCESS_KEY"):
        pytest.skip("BrowserStack credentials not configured.")


@pytest.mark.regression
def test_dashboard_has_no_horizontal_overflow_on_mobile(environment: str, tenant: str) -> None:
    """The dashboard's content width must not exceed the mobile viewport width
    (a common responsive-design regression: a fixed-width element causing
    horizontal scroll on small screens)."""
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

            viewport_width = page.viewport_size["width"] if page.viewport_size else None
            body_scroll_width = page.evaluate("document.body.scrollWidth")

            assert viewport_width is not None, "Expected a mobile viewport size to be set."
            assert body_scroll_width <= viewport_width + 1, (  # +1px tolerance for sub-pixel rounding
                f"Dashboard content ({body_scroll_width}px) overflows the mobile "
                f"viewport ({viewport_width}px)."
            )
        finally:
            browser.close()


@pytest.mark.regression
def test_login_form_usable_on_small_viewport(environment: str) -> None:
    """The login form's email/password fields and submit button remain
    visible and tappable on a small mobile viewport, without requiring
    the user to zoom or scroll horizontally."""
    _require_browserstack()
    capabilities = build_capabilities(browser_name="chromium", device="Samsung Galaxy S24")

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            login_page = LoginPage(page, environment).open()
            expect(login_page.email_input).to_be_visible()
            expect(login_page.password_input).to_be_visible()
            expect(login_page.login_button).to_be_visible()
            expect(login_page.login_button).to_be_enabled()
        finally:
            browser.close()
