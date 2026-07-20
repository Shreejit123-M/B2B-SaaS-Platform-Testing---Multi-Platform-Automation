"""Authentication API client for WorkFlow Pro.

Wraps the login, 2FA-verification, and logout endpoints behind a small,
typed interface backed by `requests.Session()`, so the connection pool
and default headers are reused across calls instead of opening a new
TCP connection per request.

ASSUMPTIONS (the assignment only specified the project-creation endpoint
contract; the auth endpoints below are inferred and documented here so
they can be corrected against the real API if it differs):
  - POST {base_url}/api/v1/auth/login
        body: {"email": str, "password": str}
        headers: {"X-Tenant-ID": str}
        response (no 2FA): {"token": str, "requires_2fa": false}
        response (2FA required): {"challenge_token": str, "requires_2fa": true}
  - POST {base_url}/api/v1/auth/verify-2fa
        body: {"challenge_token": str, "otp_code": str}
        headers: {"X-Tenant-ID": str}
        response: {"token": str}
  - POST {base_url}/api/v1/auth/logout
        headers: {"Authorization": "Bearer {token}", "X-Tenant-ID": str}
        response: 204 No Content
  - 2FA is TOTP-based, consistent with the framework's `utils/` OTP helper
    assumption used elsewhere in this project.
"""

import logging
import os
from typing import Dict, Optional

import requests

logger = logging.getLogger("wfp_qa")

DEFAULT_TIMEOUT_SECONDS = 10


class AuthAPIError(Exception):
    """Raised when an authentication API call fails or returns an unexpected shape."""


class AuthAPI:
    """Thin, tenant-aware client for WorkFlow Pro's authentication endpoints."""

    def __init__(self, base_url: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
        # ASSUMPTION: base URL and tenant come from environment variables
        # rather than a shared config module, since this project's
        # `config/` interface wasn't visible when this file was generated.
        # If `config/` already exposes equivalent values, replace the two
        # os.environ reads below with that import.
        self.base_url: str = (base_url or os.environ.get("WORKFLOWPRO_API_BASE_URL", "")).rstrip("/")
        self.tenant_id: str = tenant_id or os.environ.get("WORKFLOWPRO_TENANT_ID", "")

        if not self.base_url:
            raise AuthAPIError(
                "No API base URL configured. Set WORKFLOWPRO_API_BASE_URL or pass base_url explicitly."
            )

        self.session: requests.Session = requests.Session()
        self.session.headers.update({"X-Tenant-ID": self.tenant_id})

    def login(self, email: str, password: str) -> Dict[str, object]:
        """Attempt a standard login and return the raw response payload.

        Returns either {"token": ..., "requires_2fa": False} or
        {"challenge_token": ..., "requires_2fa": True}, so callers can
        branch on 2FA without this client making that decision for them.
        """
        url = f"{self.base_url}/api/v1/auth/login"
        logger.info("Requesting login for tenant '%s'", self.tenant_id)

        try:
            response = self.session.post(
                url,
                json={"email": email, "password": password},
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Login request failed for tenant '%s': %s", self.tenant_id, exc)
            raise AuthAPIError(f"Login request failed: {exc}") from exc

        payload = response.json()
        if "token" not in payload and "challenge_token" not in payload:
            raise AuthAPIError(f"Unexpected login response shape: {payload}")

        logger.info(
            "Login response received for tenant '%s' (requires_2fa=%s)",
            self.tenant_id,
            payload.get("requires_2fa", False),
        )
        return payload

    def verify_2fa(self, challenge_token: str, otp_code: str) -> str:
        """Submit a TOTP code for a pending 2FA challenge and return the auth token."""
        url = f"{self.base_url}/api/v1/auth/verify-2fa"
        logger.info("Submitting 2FA verification for tenant '%s'", self.tenant_id)

        try:
            response = self.session.post(
                url,
                json={"challenge_token": challenge_token, "otp_code": otp_code},
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("2FA verification failed for tenant '%s': %s", self.tenant_id, exc)
            raise AuthAPIError(f"2FA verification failed: {exc}") from exc

        payload = response.json()
        token = payload.get("token")
        if not token:
            raise AuthAPIError(f"2FA verification response missing token: {payload}")

        logger.info("2FA verification succeeded for tenant '%s'", self.tenant_id)
        return token

    def logout(self, token: str) -> None:
        """Invalidate the given session token server-side."""
        url = f"{self.base_url}/api/v1/auth/logout"
        logger.info("Requesting logout for tenant '%s'", self.tenant_id)

        try:
            response = self.session.post(
                url,
                headers=self._auth_headers(token),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Logout request failed for tenant '%s': %s", self.tenant_id, exc)
            raise AuthAPIError(f"Logout request failed: {exc}") from exc

        logger.info("Logout succeeded for tenant '%s'", self.tenant_id)

    def _auth_headers(self, token: str) -> Dict[str, str]:
        """Build the Authorization + tenant headers used by authenticated calls."""
        return {"Authorization": f"Bearer {token}", "X-Tenant-ID": self.tenant_id}

    def close(self) -> None:
        """Release the underlying connection pool. Call in fixture teardown."""
        self.session.close()
