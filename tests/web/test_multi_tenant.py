"""Multi-tenant isolation tests (UI layer) for WorkFlow Pro.

Verifies that Company1, Company2, and Company3 sessions never surface
each other's data through the dashboard, project list, search, or direct
URL access — the platform's core architectural risk (see
Assumptions.md, Test_Plan.md Section 12, risk R2).

Each tenant is authenticated in its own isolated browser context (not
just a new page), so isolation is verified even when sessions run
concurrently — a shared context would only prove client-side rendering
logic, not actual session/cookie isolation.
"""

import dataclasses
import os
from typing import Callable, Dict, Generator, List

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from api.projects_api import ProjectsAPI
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.project_page import ProjectPage  # ASSUMPTION: see tests/web/test_projects.py note
from utils.data_generator import generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)

TENANT_BASE_URLS: Dict[str, str] = {
    "company1": "https://company1.workflowpro.com",
    "company2": "https://company2.workflowpro.com",
    "company3": "https://company3.workflowpro.com",
}

TENANT_CREDENTIALS: Dict[str, Dict[str, str]] = {
    key: {
        "email": os.environ.get(f"TEST_{key.upper()}_EMAIL", f"user@{key}.workflowpro.com"),
        "password": os.environ.get(f"TEST_{key.upper()}_PASSWORD", "ValidPass123!"),
    }
    for key in TENANT_BASE_URLS
}


@dataclasses.dataclass
class TenantSession:
    """Bundles a fully authenticated session and its page objects for one tenant."""

    tenant_key: str
    context: BrowserContext
    page: Page
    dashboard: DashboardPage
    projects: ProjectPage
    api_client: ProjectsAPI
    token: str


@pytest.fixture
def tenant_session_factory(browser: Browser) -> Generator[Callable[[str], TenantSession], None, None]:
    """Factory fixture creating an independent, logged-in session per tenant."""
    created: List[TenantSession] = []

    def _create(tenant_key: str) -> TenantSession:
        base_url = TENANT_BASE_URLS[tenant_key]
        creds = TENANT_CREDENTIALS[tenant_key]

        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page, base_url).open()
        login_page.login(creds["email"], creds["password"])

        dashboard = DashboardPage(page, base_url)
        dashboard.wait_for_dashboard_loaded()

        api_client = ProjectsAPI(base_url=base_url, tenant_id=tenant_key)
        # NOTE: a real token would normally come from AuthAPI.login(); using
        # a tenant-tagged placeholder here keeps this fixture focused on UI
        # isolation. Swap in api_client.auth_token if your API requires a
        # real bearer token for create_project to succeed.
        token = os.environ.get(f"TEST_{tenant_key.upper()}_API_TOKEN", f"test-token-{tenant_key}")

        session = TenantSession(
            tenant_key=tenant_key,
            context=context,
            page=page,
            dashboard=dashboard,
            projects=ProjectPage(page, base_url),
            api_client=api_client,
            token=token,
        )
        logger.info("Authenticated UI session established for tenant '%s'", tenant_key)
        created.append(session)
        return session

    yield _create

    for session in created:
        session.api_client.close()
        session.context.close()
        logger.info("Closed session for tenant '%s'", session.tenant_key)


@pytest.mark.security
def test_dashboard_isolation_between_company1_and_company2(tenant_session_factory) -> None:
    """Company1's dashboard must never show a Company2 project, and vice versa."""
    company1 = tenant_session_factory("company1")
    company2 = tenant_session_factory("company2")

    c1_project = company1.api_client.create_project(company1.token, generate_unique_project_name("C1"))
    c2_project = company2.api_client.create_project(company2.token, generate_unique_project_name("C2"))

    company1.dashboard.page.reload()
    company1.dashboard.wait_for_dashboard_loaded()
    company2.dashboard.page.reload()
    company2.dashboard.wait_for_dashboard_loaded()

    c1_visible = " ".join(company1.dashboard.get_visible_project_names())
    c2_visible = " ".join(company2.dashboard.get_visible_project_names())

    assert c2_project["name"] not in c1_visible, "Company1 dashboard exposed a Company2 project."
    assert c1_project["name"] not in c2_visible, "Company2 dashboard exposed a Company1 project."


@pytest.mark.security
def test_project_list_isolation_across_three_tenants(tenant_session_factory) -> None:
    """The project list must be tenant-scoped even with three tenants active,
    catching isolation bugs that only surface with more than two tenants."""
    sessions = {key: tenant_session_factory(key) for key in TENANT_BASE_URLS}
    created = {}

    for key, session in sessions.items():
        created[key] = session.api_client.create_project(
            session.token, generate_unique_project_name(key.capitalize())
        )
        session.projects.open()

    for key, session in sessions.items():
        visible = " ".join(session.projects.get_visible_project_names())
        for other_key, other_project in created.items():
            if other_key == key:
                continue
            assert other_project["name"] not in visible, (
                f"{key}'s project list exposed a project belonging to {other_key}."
            )


@pytest.mark.security
def test_search_does_not_leak_cross_tenant_results(tenant_session_factory) -> None:
    """A Company2 search must never return a Company1-only project."""
    company1 = tenant_session_factory("company1")
    company2 = tenant_session_factory("company2")

    unique_marker = "XQ7-CrossTenantSearchMarker"
    company1.api_client.create_project(company1.token, f"Company1-{unique_marker}")

    company2.projects.open()
    company2.projects.search(unique_marker)

    results = company2.projects.get_visible_project_names()
    assert not results, "Company2 search returned a result that only exists in Company1's tenant."


@pytest.mark.security
def test_direct_url_access_to_other_tenant_project_denied(tenant_session_factory) -> None:
    """Company2 must not reach Company1's project-details page via a guessed/shared URL,
    even with a real, valid project ID."""
    company1 = tenant_session_factory("company1")
    company2 = tenant_session_factory("company2")

    c1_project = company1.api_client.create_project(
        company1.token, generate_unique_project_name("C1-Sensitive")
    )

    company2.projects.open_project_by_id(str(c1_project["id"]))
    assert company2.projects.is_access_blocked(), (
        "Company2 was able to load Company1's project details via direct URL access."
    )


@pytest.mark.security
def test_session_switching_clears_previous_tenant_data(browser: Browser) -> None:
    """Logging out of Company1 and into Company2 in the SAME browser context
    must leave no residual Company1 project names visible before Company2's
    own data has loaded — targets client-side caching bugs distinct from
    the server-side checks in the tests above."""
    context = browser.new_context()
    page = context.new_page()

    c1_creds = TENANT_CREDENTIALS["company1"]
    login_page = LoginPage(page, TENANT_BASE_URLS["company1"]).open()
    login_page.login(c1_creds["email"], c1_creds["password"])
    dashboard = DashboardPage(page, TENANT_BASE_URLS["company1"])
    dashboard.wait_for_dashboard_loaded()
    company1_names = dashboard.get_visible_project_names()
    dashboard.logout()

    c2_creds = TENANT_CREDENTIALS["company2"]
    login_page = LoginPage(page, TENANT_BASE_URLS["company2"]).open()
    login_page.login(c2_creds["email"], c2_creds["password"])
    dashboard = DashboardPage(page, TENANT_BASE_URLS["company2"])
    dashboard.wait_for_dashboard_loaded()
    company2_names = dashboard.get_visible_project_names()

    leaked = set(company1_names) & set(company2_names)
    assert not leaked, f"Project(s) {leaked} persisted across a same-context tenant session switch."

    context.close()
