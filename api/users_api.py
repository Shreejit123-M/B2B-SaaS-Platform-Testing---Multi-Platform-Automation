"""Users API client for WorkFlow Pro.

Wraps user/role-related endpoints on `requests.Session()`. Used primarily
by role-permission and tenant-isolation tests (e.g., confirming an
Employee-role token cannot list another tenant's users, or that a user's
reported role matches what the UI enforces).

ASSUMPTIONS (no user-management endpoint was documented in the
assignment brief; the shape below is inferred as the minimum needed to
support the role-based-access scenarios the assignment explicitly calls
for — Admin/Manager/Employee — and is documented here so it can be
corrected against the real API if it differs):
  - GET /api/v1/users/me            -> current authenticated user's own record
        response: {"id": ..., "email": ..., "role": "Admin"|"Manager"|"Employee", "tenant_id": ...}
  - GET /api/v1/users                -> {"items": [user, ...]} for the current tenant
        (expected to require an Admin-level token; a Manager/Employee
        token is expected to receive 403, matching the pattern used in
        api/projects_api.py's ProjectAccessBlocked)
  - GET /api/v1/users/{id}           -> single user record, tenant-scoped
"""

import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("wfp_qa")

DEFAULT_TIMEOUT_SECONDS = 10
BLOCKED_STATUS_CODES = {403, 404}


class UsersAPIError(Exception):
    """Raised when a users API call fails unexpectedly (not an access-control block)."""


class UserAccessBlocked(Exception):
    """Raised when the API correctly refuses access to a user resource (403/404).

    Mirrors api/projects_api.py's ProjectAccessBlocked: this is the
    *expected* outcome for a role-permission or tenant-isolation test,
    not a framework failure, so it's kept distinct from UsersAPIError.
    """

    def __init__(self, status_code: int, resource: str) -> None:
        self.status_code = status_code
        self.resource = resource
        super().__init__(f"Access to '{resource}' blocked (status={status_code})")


class UsersAPI:
    """Thin, tenant-aware client for WorkFlow Pro's user/role endpoints."""

    def __init__(self, base_url: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
        # See api/auth_api.py for the same assumption note on config sourcing.
        self.base_url: str = (base_url or os.environ.get("WORKFLOWPRO_API_BASE_URL", "")).rstrip("/")
        self.tenant_id: str = tenant_id or os.environ.get("WORKFLOWPRO_TENANT_ID", "")

        if not self.base_url:
            raise UsersAPIError(
                "No API base URL configured. Set WORKFLOWPRO_API_BASE_URL or pass base_url explicitly."
            )

        self.session: requests.Session = requests.Session()
        self.session.headers.update({"X-Tenant-ID": self.tenant_id})

    def get_current_user(self, token: str) -> Dict[str, object]:
        """Fetch the profile (including role) of the token's own user."""
        url = f"{self.base_url}/api/v1/users/me"
        logger.info("Fetching current user for tenant '%s'", self.tenant_id)

        try:
            response = self.session.get(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Get-current-user request failed for tenant '%s': %s", self.tenant_id, exc)
            raise UsersAPIError(f"Get-current-user request failed: {exc}") from exc

        user = response.json()
        if "role" not in user:
            raise UsersAPIError(f"Unexpected current-user response shape: {user}")

        logger.info("Current user resolved: role='%s', tenant='%s'", user["role"], self.tenant_id)
        return user

    def list_users(self, token: str) -> List[Dict[str, object]]:
        """List all users for the current tenant. Expected to require an Admin token."""
        url = f"{self.base_url}/api/v1/users"
        logger.info("Listing users for tenant '%s'", self.tenant_id)

        try:
            response = self.session.get(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as exc:
            logger.error("List-users request failed for tenant '%s': %s", self.tenant_id, exc)
            raise UsersAPIError(f"List-users request failed: {exc}") from exc

        if response.status_code in BLOCKED_STATUS_CODES:
            logger.warning(
                "User list access blocked for tenant '%s' (status=%d)",
                self.tenant_id, response.status_code,
            )
            raise UserAccessBlocked(response.status_code, "users")

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise UsersAPIError(f"List-users failed: {exc}") from exc

        items = response.json().get("items", [])
        logger.info("Retrieved %d user(s) for tenant '%s'", len(items), self.tenant_id)
        return items

    def get_user(self, token: str, user_id: str) -> Dict[str, object]:
        """Fetch a single user by ID, scoped to the current tenant's token."""
        url = f"{self.base_url}/api/v1/users/{user_id}"
        logger.info("Fetching user '%s' for tenant '%s'", user_id, self.tenant_id)

        try:
            response = self.session.get(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Get-user request failed for '%s': %s", user_id, exc)
            raise UsersAPIError(f"Get-user request failed: {exc}") from exc

        if response.status_code in BLOCKED_STATUS_CODES:
            logger.warning(
                "Access to user '%s' blocked for tenant '%s' (status=%d)",
                user_id, self.tenant_id, response.status_code,
            )
            raise UserAccessBlocked(response.status_code, user_id)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise UsersAPIError(f"Get-user failed: {exc}") from exc

        return response.json()

    def _auth_headers(self, token: str) -> Dict[str, str]:
        """Build the Authorization + tenant headers used by every authenticated call."""
        return {"Authorization": f"Bearer {token}", "X-Tenant-ID": self.tenant_id}

    def close(self) -> None:
        """Release the underlying connection pool. Call in fixture teardown."""
        self.session.close()
