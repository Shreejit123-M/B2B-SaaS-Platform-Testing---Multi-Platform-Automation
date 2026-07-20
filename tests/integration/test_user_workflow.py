"""Full user workflow integration test.

Chains login -> dashboard -> project creation -> project visibility ->
logout into one realistic session, complementing the narrower,
single-concern tests elsewhere in tests/web/ and tests/api/.
"""

import os

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.project_page import ProjectPage  # ASSUMPTION: see tests/web/test_projects.py note
from utils.data_generator import generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.integration
@pytest.mark.regression
def test_full_user_workflow_login_to_logout(environment: str, tenant: str, page) -> None:
    """Simulates a realistic session: a user logs in, creates a project,
    confirms it appears, and logs out cleanly."""
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    # Step 1: Login
    login_page = LoginPage(page, environment).open()
    login_page.login(email, password)

    dashboard = DashboardPage(page, environment)
    dashboard.wait_for_dashboard_loaded()
    expect(dashboard.welcome_message).to_be_visible()

    # Step 2: Create a project
    project_name = generate_unique_project_name(prefix="Workflow")
    project_page = ProjectPage(page, environment)
    project_page.open()
    project_page.create_project(name=project_name, description="Created during full-workflow test")

    # Step 3: Confirm the project is visible
    visible_names = " ".join(project_page.get_visible_project_names())
    assert project_name in visible_names, "Created project was not visible after creation."

    # Step 4: Logout and confirm the session ends cleanly
    dashboard.logout()
    expect(page).to_have_url(f"{environment}/login")
