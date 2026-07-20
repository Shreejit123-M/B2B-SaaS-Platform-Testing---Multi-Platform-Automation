"""Environment, tenant, and authentication fixtures.

Provides both API-level authentication (an auth token via AuthAPI, for
tests/api and test-data setup) and UI-level authentication (a logged-in
Page via the existing pages/ Page Object Model, for tests/web and
tests/integration).

Registered as a pytest plugin from the root conftest.py — see
fixtures/browser_fixtures.py's module docstring for the required
pytest_plugins entry.
"""

import os
from typing import Dict, Generator

import pytest
from playwright.sync_api import Page

from api.auth_api import AuthAPI
from pages.dashboard_page import DashboardPage  # ASSUMPTION: see module note below
from pages.login_page import LoginPage  # ASSUMPTION: see module note below
from utils.helpers import generate_otp_code
from utils.logger import get_logger

logger = get_logger(__name__)

# ASSUMPTION: pages.login_page.LoginPage and pages.dashboard_page.DashboardPage
# expose .open(), .login(email, password), .submit_otp(code), and
# DashboardPage exposes .wait_for_dashboard_loaded() and .logout(). If your
# existing pages/ module uses different method names, update the calls in
# `authenticated_page` below accordingly — the rest of this framework does
# not depend on these exact names beyond this one fixture.

ENVIRONMENTS: Dict[str, str] = {
    "qa": "https://qa.workflowpro.com",
    "staging": "https://staging.workflowpro.com",
    "production": "https://app.workflowpro.com",
}

TENANTS: Dict[str, str] = {
    "company1": "company1.workflowpro.com",
    "company2": "company2.workflowpro.com",
    "company3": "company3.workflowpro.com",
}


@pytest.fixture(scope="session")
def environment(pytestconfig: pytest.Config) -> str:
    """Resolve the base URL for the environment selected via --env."""
    env_name = pytestconfig.getoption("--env")
    base_url = ENVIRONMENTS.get(env_name)
    if base_url is None:
        raise ValueError(f"Unknown environment '{env_name}'. Valid options: {list(ENVIRONMENTS)}")
    logger.info("Environment resolved: %s -> %s", env_name, base_url)
    return base_url


@pytest.fixture(scope="session")
def tenant(pytestconfig: pytest.Config) -> str:
    """Resolve the tenant domain for the tenant selected via --tenant."""
    tenant_key = pytestconfig.getoption("--tenant")
    tenant_domain = TENANTS.get(tenant_key)
    if tenant_domain is None:
        raise ValueError(f"Unknown tenant '{tenant_key}'. Valid options: {list(TENANTS)}")
    logger.info("Tenant resolved: %s -> %s", tenant_key, tenant_domain)
    return tenant_domain


@pytest.fixture
def auth_token(environment: str, tenant: str) -> str:
    """Authenticate via the API and return a bearer token for the default test user.

    Handles the 2FA branch automatically if the configured test account
    requires it, so any test needing an API token doesn't have to know
    whether 2FA is involved.
    """
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    auth_api = AuthAPI(base_url=environment, tenant_id=tenant)
    try:
        login_response = auth_api.login(email, password)
        if login_response.get("requires_2fa"):
            otp_code = generate_otp_code()
            token = auth_api.verify_2fa(str(login_response["challenge_token"]), otp_code)
        else:
            token = str(login_response["token"])
        logger.info("API auth token acquired for tenant '%s'", tenant)
        return token
    finally:
        auth_api.close()


@pytest.fixture
def authenticated_page(
    page: Page, environment: str, tenant: str
) -> Generator[DashboardPage, None, None]:
    """Log in through the real UI and yield a loaded DashboardPage.

    Used by UI/integration tests that need to start from an authenticated
    dashboard state, without duplicating the login sequence in every test.
    """
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    password = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")

    login_page = LoginPage(page, environment).open()
    login_page.login(email, password)

    if os.environ.get("TEST_USER_REQUIRES_2FA", "false").lower() == "true":
        otp_code = generate_otp_code()
        login_page.submit_otp(otp_code)

    dashboard_page = DashboardPage(page, environment)
    dashboard_page.wait_for_dashboard_loaded()
    logger.info("UI authentication complete for tenant '%s'", tenant)

    yield dashboard_page
