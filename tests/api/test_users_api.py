"""API tests for user/role endpoints (api/users_api.py).

Covers the role-based access control scenarios called out in the
assignment (Admin, Manager, Employee), verified directly at the API
layer per Test_Plan.md TC-013–TC-015.
"""

import os

import pytest

from api.users_api import UserAccessBlocked, UsersAPI
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def users_api(environment: str, tenant: str):
    """Provide a UsersAPI client, closed after the test."""
    client = UsersAPI(
        base_url=environment.api_base_url,
        tenant_id=tenant.tenant_id
    )
    yield client
    client.close()


@pytest.mark.api
@pytest.mark.smoke
def test_get_current_user_returns_role(users_api: UsersAPI, auth_token: str) -> None:
    """The authenticated user's own profile includes a valid role value."""
    user = users_api.get_current_user(auth_token)
    assert user.get("role") in {"Admin", "Manager", "Employee"}


@pytest.mark.api
@pytest.mark.regression
def test_admin_can_list_tenant_users(users_api: UsersAPI) -> None:
    """An Admin-role token can list all users for its tenant."""
    admin_token = os.environ.get("TEST_ADMIN_API_TOKEN")
    if not admin_token:
        pytest.skip("TEST_ADMIN_API_TOKEN not configured; skipping admin-only check.")

    users = users_api.list_users(admin_token)
    assert isinstance(users, list)


@pytest.mark.api
@pytest.mark.security
def test_employee_cannot_list_tenant_users(users_api: UsersAPI, auth_token: str) -> None:
    """An Employee-role token must not be able to list the full tenant user directory.

    ASSUMPTION: the default `auth_token` fixture authenticates an
    Employee-level test account (see .env.example / fixtures/auth_fixtures.py).
    If your default test account is Admin-level instead, this test should
    use a dedicated non-admin token via a separate fixture.
    """
    with pytest.raises(UserAccessBlocked):
        users_api.list_users(auth_token)
