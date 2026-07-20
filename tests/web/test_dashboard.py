"""Dashboard tests for WorkFlow Pro.

Covers the dynamic-loading behavior called out in the assignment brief
("App uses dynamic loading for dashboard elements", "Different tenants
have different loading times"). All waits are explicit and tied to real
UI state transitions — no time.sleep() anywhere in this file.
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect

from pages.dashboard_page import DashboardPage  # ASSUMPTION: see fixtures/auth_fixtures.py note
from utils.helpers import retry_on
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.ui
@pytest.mark.smoke
def test_dashboard_loads_after_login(authenticated_page: DashboardPage) -> None:
    """The dashboard renders its welcome message once loading completes."""
    expect(authenticated_page.welcome_message).to_be_visible()


@retry_on(exceptions=(PlaywrightTimeoutError,), attempts=2, delay_seconds=2.0)
def _wait_for_slow_dashboard(dashboard: DashboardPage) -> None:
    """Isolated so the retry decorator applies only to this one call.

    Retry is scoped here deliberately: per the brief, different tenants
    have different loading times, so an occasional timeout on this
    specific wait is a known-transient condition, not a product defect —
    every other assertion in this suite must fail immediately, unretried.
    """
    dashboard.wait_for_dashboard_loaded(timeout=20_000)


@pytest.mark.ui
@pytest.mark.regression
def test_slow_dashboard_loading_still_resolves(authenticated_page: DashboardPage) -> None:
    """The dashboard eventually renders correctly even under slow tenant load."""
    _wait_for_slow_dashboard(authenticated_page)
    expect(authenticated_page.welcome_message).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_dashboard_project_cards_render(authenticated_page: DashboardPage, test_project: dict) -> None:
    """A project created via the API appears in the dashboard's project widget
    once the dashboard's async data load completes."""
    authenticated_page.page.reload()
    authenticated_page.wait_for_dashboard_loaded()

    visible_names = authenticated_page.get_visible_project_names()
    assert test_project["name"] in " ".join(visible_names), (
        "Expected the API-created project to appear on the dashboard after reload."
    )
