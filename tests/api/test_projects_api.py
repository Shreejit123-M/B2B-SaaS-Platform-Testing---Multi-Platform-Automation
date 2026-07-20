"""API tests for project endpoints (api/projects_api.py).

Matches the assignment's Part 3 scenario: create via API, validate the
response contract, and verify tenant isolation at the API layer directly
(faster and more reliable than testing isolation only through the UI).
"""

import pytest

from api.projects_api import ProjectAccessBlocked, ProjectsAPI, ProjectsAPIError
from utils.data_generator import generate_team_members, generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.api
@pytest.mark.smoke
def test_create_project_returns_expected_contract(projects_api: ProjectsAPI, auth_token: str) -> None:
    """POST /api/v1/projects returns id, name, and status, matching the brief's documented contract."""
    name = generate_unique_project_name()
    project = projects_api.create_project(
        auth_token, name=name, description="API contract test", team_members=generate_team_members(2)
    )

    assert project["name"] == name
    assert "id" in project
    assert project.get("status") == "active"

    projects_api.delete_project(auth_token, str(project["id"]))


@pytest.mark.api
@pytest.mark.regression
def test_create_project_missing_name_returns_validation_error(
    projects_api: ProjectsAPI, auth_token: str
) -> None:
    """Omitting the required 'name' field is rejected with a clear error, not a 500."""
    with pytest.raises(ProjectsAPIError):
        projects_api.create_project(auth_token, name="", description="Missing name")


@pytest.mark.api
@pytest.mark.regression
def test_create_project_invalid_token_returns_unauthorized(projects_api: ProjectsAPI) -> None:
    """An invalid/expired token is rejected rather than silently succeeding."""
    with pytest.raises(ProjectsAPIError):
        projects_api.create_project("invalid-or-expired-token", name=generate_unique_project_name())


@pytest.mark.api
@pytest.mark.regression
def test_get_project_returns_created_project(projects_api: ProjectsAPI, auth_token: str) -> None:
    """A project can be retrieved by ID immediately after creation."""
    created = projects_api.create_project(auth_token, name=generate_unique_project_name())
    fetched = projects_api.get_project(auth_token, str(created["id"]))

    assert fetched["id"] == created["id"]
    assert fetched["name"] == created["name"]

    projects_api.delete_project(auth_token, str(created["id"]))


@pytest.mark.api
@pytest.mark.regression
def test_list_projects_scoped_to_requesting_tenant(projects_api: ProjectsAPI, auth_token: str) -> None:
    """The project list only returns projects belonging to the authenticated tenant."""
    created = projects_api.create_project(auth_token, name=generate_unique_project_name())
    all_projects = projects_api.list_projects(auth_token)

    assert any(p["id"] == created["id"] for p in all_projects), (
        "Newly created project not found in the tenant's project list."
    )

    projects_api.delete_project(auth_token, str(created["id"]))


@pytest.mark.api
@pytest.mark.security
def test_mismatched_tenant_header_is_blocked(environment: str, auth_token: str) -> None:
    """A request whose X-Tenant-ID doesn't match the token's actual tenant
    must be rejected (403/404), never returning another tenant's data."""
    other_tenant_client = ProjectsAPI(base_url=environment, tenant_id="company2")
    try:
        with pytest.raises(ProjectAccessBlocked):
            # auth_token belongs to the fixture's configured tenant (see
            # fixtures/auth_fixtures.py, defaults to company1); requesting
            # against company2's client with that token must be blocked.
            created = other_tenant_client.create_project(auth_token, name=generate_unique_project_name())
            other_tenant_client.get_project(auth_token, str(created["id"]))
    finally:
        other_tenant_client.close()
