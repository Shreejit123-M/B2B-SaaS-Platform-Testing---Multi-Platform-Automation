"""API tests for authentication endpoints (api/auth_api.py)."""

import os

import pytest

from api.auth_api import AuthAPI, AuthAPIError
from utils.helpers import generate_otp_code
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "ValidPass123!")


@pytest.fixture
def auth_api(environment: str, tenant: str):
    """Provide an AuthAPI client, closed after the test."""
    client = AuthAPI(
        base_url=environment.api_base_url,
        tenant_id=tenant.tenant_id)
    yield client
    client.close()


@pytest.mark.api
@pytest.mark.smoke
def test_login_with_valid_credentials_returns_token_or_challenge(auth_api: AuthAPI, tenant: str) -> None:
    """A valid login returns either a token directly or a 2FA challenge token."""
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    response = auth_api.login(email, VALID_PASSWORD)
    assert "token" in response or "challenge_token" in response


@pytest.mark.api
@pytest.mark.regression
def test_login_with_invalid_password_raises_auth_error(auth_api: AuthAPI, tenant: str) -> None:
    """An incorrect password causes the API call to fail with a clear error."""
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    with pytest.raises(AuthAPIError):
        auth_api.login(email, "DefinitelyWrongPassword!23")


@pytest.mark.api
@pytest.mark.regression
def test_2fa_flow_completes_with_valid_otp(auth_api: AuthAPI) -> None:
    """A 2FA-enabled account completes login after a valid OTP is submitted."""
    two_fa_email = os.environ.get("TEST_2FA_USER_EMAIL", "twofa.user@company1.workflowpro.com")
    response = auth_api.login(two_fa_email, VALID_PASSWORD)

    assert response.get("requires_2fa") is True, "Expected the 2FA account to require a challenge."
    otp_code = generate_otp_code()
    token = auth_api.verify_2fa(str(response["challenge_token"]), otp_code)
    assert token, "Expected a non-empty token after successful 2FA verification."


@pytest.mark.api
@pytest.mark.regression
def test_logout_invalidates_token(auth_api: AuthAPI, tenant: str) -> None:
    """After logout, the previously issued token can no longer be used
    (verified indirectly here by confirming logout itself succeeds without error;
    a full reuse-after-logout check lives in tests/web/test_authentication.py
    at the UI/session-cookie level)."""
    email = os.environ.get("TEST_USER_EMAIL", f"user@{tenant}")
    response = auth_api.login(email, VALID_PASSWORD)
    token = str(response.get("token") or response.get("challenge_token"))

    auth_api.logout(token)  # Should not raise.
