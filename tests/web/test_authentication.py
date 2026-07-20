"""UI authentication tests for WorkFlow Pro.

Covers standard login, field validation, and 2FA scenarios described in
Test_Plan.md (Section 9). Credentials are read from environment
variables — see .env.example — never hardcoded.
"""

import os

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage  # ASSUMPTION: see fixtures/auth_fixtures.py note
from pages.login_page import LoginPage  # ASSUMPTION: see fixtures/auth_fixtures.py note
from utils.helpers import generate_otp_code
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")
TWO_FA_USER_EMAIL = os.environ.get("TEST_2FA_USER_EMAIL", "twofa.user@company1.workflowpro.com")


@pytest.fixture
def login_page(page, environment: str) -> LoginPage:
    """Provide a LoginPage already navigated to the login form."""
    return LoginPage(page, environment).open()


@pytest.fixture
def valid_email(tenant: str) -> str:
    """Build a valid test-user email scoped to the resolved tenant."""
    return os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")


@pytest.mark.ui
@pytest.mark.smoke
def test_valid_login(login_page: LoginPage, environment: str, valid_email: str) -> None:
    """A user with correct credentials reaches the dashboard."""
    login_page.login(valid_email, VALID_PASSWORD)
    dashboard = DashboardPage(login_page.page, environment)
    dashboard.wait_for_dashboard_loaded()
    expect(dashboard.welcome_message).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_invalid_password(login_page: LoginPage, valid_email: str) -> None:
    """An incorrect password is rejected with a generic error (no account enumeration)."""
    login_page.login(valid_email, "WrongPassword!23")
    expect(login_page.error_banner).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_invalid_email(login_page: LoginPage) -> None:
    """A non-existent email is rejected the same way as a wrong password."""
    login_page.login("no-such-user@company1.workflowpro.com", VALID_PASSWORD)
    expect(login_page.error_banner).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_empty_email(login_page: LoginPage) -> None:
    """Submitting with no email shows validation and never authenticates."""
    login_page.login("", VALID_PASSWORD)
    expect(login_page.error_banner).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_empty_password(login_page: LoginPage, valid_email: str) -> None:
    """Submitting with no password is rejected."""
    login_page.login(valid_email, "")
    expect(login_page.error_banner).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_empty_credentials(login_page: LoginPage, environment: str) -> None:
    """A fully blank form is rejected and the user remains on /login."""
    login_page.login("", "")
    expect(login_page.error_banner).to_be_visible()
    expect(login_page.page).to_have_url(f"{environment}/login")


@pytest.mark.ui
@pytest.mark.regression
def test_2fa_enabled_login(login_page: LoginPage, environment: str) -> None:
    """A 2FA-enabled user must pass both password and OTP checks to reach the dashboard.

    Assumes generate_otp_code() returns a valid TOTP for the provisioned
    test-only 2FA secret (see utils/helpers.py and .env.example).
    """
    login_page.login(TWO_FA_USER_EMAIL, VALID_PASSWORD)
    otp_code = generate_otp_code()
    login_page.submit_otp(otp_code)

    dashboard = DashboardPage(login_page.page, environment)
    dashboard.wait_for_dashboard_loaded()
    expect(dashboard.welcome_message).to_be_visible()


@pytest.mark.ui
@pytest.mark.smoke
def test_logout(authenticated_page: DashboardPage, environment: str) -> None:
    """Logout terminates the session and returns the user to /login."""
    authenticated_page.logout()
    expect(authenticated_page.page).to_have_url(f"{environment}/login")
