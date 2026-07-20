"""Mobile web project tests, executed via BrowserStack real devices.

Scope: mobile WEB browsers only (Safari on iOS, Chrome on Android) — no
native app is in scope, since none was provided in the assignment brief
(see Assumptions.md, A-19).
"""

import os

import pytest
from playwright.sync_api import sync_playwright

from browserstack.browserstack_config import build_capabilities, connect_browserstack
from pages.login_page import LoginPage
from pages.project_page import ProjectPage  # ASSUMPTION: see tests/web/test_projects.py note
from utils.data_generator import generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)

pytestmark = pytest.mark.mobile


def _require_browserstack() -> None:
    if not os.environ.get("BROWSERSTACK_USERNAME") or not os.environ.get("BROWSERSTACK_ACCESS_KEY"):
        pytest.skip("BrowserStack credentials not configured.")


@pytest.mark.regression
def test_create_project_on_ios_safari(environment: str, tenant: str) -> None:
    """A project can be created end-to-end on iOS Safari (mobile web)."""
    _require_browserstack()
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")
    project_name = generate_unique_project_name(prefix="iOS")

    capabilities = build_capabilities(browser_name="webkit", device="iPhone 15")

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            login_page = LoginPage(page, environment).open()
            login_page.login(email, password)

            project_page = ProjectPage(page, environment)
            project_page.open()
            project_page.create_project(name=project_name, description="Created on iOS Safari")

            visible_names = " ".join(project_page.get_visible_project_names())
            assert project_name in visible_names, "Project creation did not succeed on iOS Safari."
        finally:
            browser.close()


@pytest.mark.regression
def test_create_project_on_android_chrome(environment: str, tenant: str) -> None:
    """A project can be created end-to-end on Android Chrome (mobile web)."""
    _require_browserstack()
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")
    project_name = generate_unique_project_name(prefix="Android")

    capabilities = build_capabilities(browser_name="chromium", device="Samsung Galaxy S24")

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            login_page = LoginPage(page, environment).open()
            login_page.login(email, password)

            project_page = ProjectPage(page, environment)
            project_page.open()
            project_page.create_project(name=project_name, description="Created on Android Chrome")

            visible_names = " ".join(project_page.get_visible_project_names())
            assert project_name in visible_names, "Project creation did not succeed on Android Chrome."
        finally:
            browser.close()
