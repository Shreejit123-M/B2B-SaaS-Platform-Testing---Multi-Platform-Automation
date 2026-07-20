"""End-to-end project creation flow: API -> Web UI -> Mobile.

Directly implements the assignment's Part 3 scenario: create via API,
verify in the web UI, check mobile accessibility via BrowserStack, and
validate tenant isolation.
"""

import pytest
from playwright.sync_api import sync_playwright

from api.projects_api import ProjectAccessBlocked, ProjectsAPI
from browserstack.browserstack_config import build_capabilities, connect_browserstack
from pages.dashboard_page import DashboardPage
from pages.project_page import ProjectPage  # ASSUMPTION: see tests/web/test_projects.py note
from utils.data_generator import generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.integration
@pytest.mark.smoke
def test_project_creation_visible_across_api_and_web(
    authenticated_page: DashboardPage, environment: str, projects_api: ProjectsAPI, auth_token: str
) -> None:
    """1. Create via API. 2. Verify the project appears correctly in the web UI."""
    project_name = generate_unique_project_name(prefix="E2E")
    created = projects_api.create_project(auth_token, name=project_name, description="E2E flow test")

    project_page = ProjectPage(authenticated_page.page, environment)
    project_page.open()

    visible_names = " ".join(project_page.get_visible_project_names())
    assert project_name in visible_names, "API-created project was not visible in the web UI."

    projects_api.delete_project(auth_token, str(created["id"]))


@pytest.mark.integration
@pytest.mark.mobile
def test_project_accessible_on_mobile(
    environment: str, tenant: str, projects_api: ProjectsAPI, auth_token: str
) -> None:
    """3. Check the created project is accessible on a mobile (BrowserStack) session.

    Skips gracefully if BrowserStack credentials aren't configured, so this
    test doesn't block a local/CI run that isn't set up for BrowserStack.
    """
    import os

    if not os.environ.get("BROWSERSTACK_USERNAME") or not os.environ.get("BROWSERSTACK_ACCESS_KEY"):
        pytest.skip("BrowserStack credentials not configured.")

    project_name = generate_unique_project_name(prefix="Mobile-E2E")
    created = projects_api.create_project(auth_token, name=project_name)

    capabilities = build_capabilities(browser_name="webkit", device="iPhone 15")

    with sync_playwright() as playwright:
        browser = connect_browserstack(playwright, capabilities)
        try:
            context = browser.new_context()
            page = context.new_page()

            project_page = ProjectPage(page, environment)
            project_page.open()

            visible_names = " ".join(project_page.get_visible_project_names())
            assert project_name in visible_names, "Project not visible on mobile web session."
        finally:
            browser.close()

    projects_api.delete_project(auth_token, str(created["id"]))


@pytest.mark.integration
@pytest.mark.security
def test_project_tenant_isolation_end_to_end(environment: str, auth_token: str) -> None:
    """4. Validate tenant isolation: a project created for one tenant must be
    inaccessible via the API when queried from a different tenant's client."""
    company1_client = ProjectsAPI(base_url=environment, tenant_id="company1")
    company2_client = ProjectsAPI(base_url=environment, tenant_id="company2")

    try:
        project = company1_client.create_project(
            auth_token, name=generate_unique_project_name(prefix="Isolation-E2E")
        )
        with pytest.raises(ProjectAccessBlocked):
            company2_client.get_project(auth_token, str(project["id"]))
    finally:
        company1_client.close()
        company2_client.close()
