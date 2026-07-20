"""Playwright browser/context/page fixtures.

Registered as a pytest plugin from the root conftest.py:
    pytest_plugins = ["fixtures.browser_fixtures", "fixtures.auth_fixtures", "fixtures.data_fixtures"]

NOTE: `pytest_addoption` below defines --env/--tenant/--browser-name/--headed.
If your existing conftest.py already defines any of these, pytest will
raise a duplicate-option error when both are loaded — remove the
duplicate from whichever side you keep.
"""

from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from utils.logger import get_logger

logger = get_logger(__name__)

SCREENSHOT_DIR = "reports/screenshots"
TRACE_DIR = "reports/traces"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register CLI options controlling environment, tenant, and browser choice."""
    parser.addoption("--env", action="store", default="qa", help="Target environment")
    parser.addoption("--tenant", action="store", default="company1", help="Target tenant")
    parser.addoption(
        "--browser-name", action="store", default="chromium",
        help="Browser engine: chromium, firefox, or webkit",
    )
    parser.addoption("--headed", action="store_true", default=False, help="Run browser in headed mode")


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and ensure report directories exist."""
    import os

    for marker in ("smoke", "regression", "api", "ui", "integration", "mobile", "security"):
        config.addinivalue_line("markers", f"{marker}: mark test as {marker}")

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(TRACE_DIR, exist_ok=True)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator[None, None, None]:
    """Attach each phase's outcome to the test item so fixtures can detect failures."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def browser(pytestconfig: pytest.Config) -> Generator[Browser, None, None]:
    """Launch a single Playwright browser instance shared across the test session."""
    browser_name = pytestconfig.getoption("--browser-name")
    headless = not pytestconfig.getoption("--headed")

    with sync_playwright() as playwright:
        try:
            launcher = getattr(playwright, browser_name)
        except AttributeError as exc:
            raise ValueError(f"Unsupported browser engine: {browser_name}") from exc

        browser_instance = launcher.launch(headless=headless)
        logger.info("Browser launched: %s (headless=%s)", browser_name, headless)
        yield browser_instance
        browser_instance.close()
        logger.info("Browser closed: %s", browser_name)


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Create an isolated browser context per test, with tracing enabled.

    A fresh context per test (not a shared one) is what actually makes
    parallel execution safe — each test gets its own cookies/storage, so
    no test can leak session state into another.
    """
    browser_context = browser.new_context()
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield browser_context
    browser_context.close()


@pytest.fixture
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    """Provide a page object; capture a screenshot and trace only on failure."""
    test_page = context.new_page()
    yield test_page

    test_failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    test_name = request.node.name

    if test_failed:
        try:
            test_page.screenshot(path=f"{SCREENSHOT_DIR}/{test_name}.png", full_page=True)
            logger.warning("Screenshot captured for failed test: %s", test_name)
        except Exception as exc:  # pragma: no cover - best-effort diagnostic capture
            logger.error("Failed to capture screenshot for '%s': %s", test_name, exc)

        try:
            context.tracing.stop(path=f"{TRACE_DIR}/{test_name}.zip")
            logger.warning("Trace saved for failed test: %s", test_name)
        except Exception as exc:  # pragma: no cover - best-effort diagnostic capture
            logger.error("Failed to save trace for '%s': %s", test_name, exc)
    else:
        context.tracing.stop()

    test_page.close()
