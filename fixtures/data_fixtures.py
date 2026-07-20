"""Test-data fixtures.

Provides API-created, self-cleaning test data so UI/integration tests
don't need to create their own setup data through slower UI flows, and
so no test leaves orphaned data behind regardless of pass/fail outcome.

Registered as a pytest plugin from the root conftest.py — see
fixtures/browser_fixtures.py's module docstring for the required
pytest_plugins entry.
"""

from typing import Dict, Generator

import pytest

from api.projects_api import ProjectsAPI, ProjectsAPIError
from utils.data_generator import generate_project_description, generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def projects_api(environment: str, tenant: str) -> Generator[ProjectsAPI, None, None]:
    """Provide a tenant-scoped ProjectsAPI client, closed after the test."""
    client = ProjectsAPI(base_url=environment, tenant_id=tenant)
    yield client
    client.close()


@pytest.fixture
def test_project(
    projects_api: ProjectsAPI, auth_token: str, request: pytest.FixtureRequest
) -> Generator[Dict[str, object], None, None]:
    """Create a uniquely-named project via the API and delete it after the test.

    The project name is tagged with the requesting test's name (via
    `request.node.name`) so orphaned data is traceable back to its
    originating test if teardown ever fails to run.
    """
    scenario_name = request.node.name
    project_name = generate_unique_project_name(prefix=f"TC-{scenario_name}")
    description = generate_project_description(scenario_name)

    project = projects_api.create_project(auth_token, name=project_name, description=description)
    logger.info("test_project fixture created project id=%s", project["id"])

    yield project

    try:
        projects_api.delete_project(auth_token, str(project["id"]))
    except ProjectsAPIError as exc:
        # Cleanup failures are logged loudly rather than silently swallowed,
        # per the framework's test-data cleanup strategy (Test_Plan.md,
        # Section 7): an orphaned project should never go unnoticed.
        logger.error("Cleanup failed for project id=%s: %s", project["id"], exc)
