"""Projects API client for WorkFlow Pro.

Wraps the project-management endpoints on `requests.Session()`. The
`create_project` contract below matches the assignment brief exactly:

    POST /api/v1/projects
    Headers: Authorization: Bearer {token}, X-Tenant-ID: {company_id}
    Body: {"name": "Test Project", "description": "...", "team_members": [...]}
    Response: {"id": 123, "name": "Test Project", "status": "active"}

ASSUMPTIONS (get/list/delete were not specified in the brief; inferred
as the minimum needed for test setup, tenant-isolation checks, and
cleanup, and documented here so they can be corrected against the real
API if it differs):
  - GET    /api/v1/projects/{id}       -> full project object
  - GET    /api/v1/projects            -> {"items": [project, ...]}
  - DELETE /api/v1/projects/{id}       -> 204 No Content
  - All endpoints require both the Authorization and X-Tenant-ID headers;
    a request with a mismatched tenant/token pair is expected to return
    403 (Forbidden) or 404 (Not Found), either of which this client
    treats as "not accessible" rather than raising, so isolation tests
    can assert on that outcome instead of catching an exception.
  - `update_project` is intentionally not implemented: the brief never
    documents an update contract, and inventing one would risk testing
    against a shape the real API doesn't use.
"""

import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("wfp_qa")

DEFAULT_TIMEOUT_SECONDS = 10
BLOCKED_STATUS_CODES = {403, 404}


class ProjectsAPIError(Exception):
    """Raised when a projects API call fails unexpectedly (not a tenant-isolation block)."""


class ProjectAccessBlocked(Exception):
    """Raised when the API correctly refuses access to a project (403/404).

    This is a *distinct* exception from ProjectsAPIError because, in
    tenant-isolation tests, a 403/404 is the expected, correct outcome —
    callers should catch this specifically to assert isolation held, not
    treat it as a test-framework failure.
    """

    def __init__(self, status_code: int, project_id: str) -> None:
        self.status_code = status_code
        self.project_id = project_id
        super().__init__(f"Access to project '{project_id}' blocked (status={status_code})")


class ProjectsAPI:
    """Thin, tenant-aware client for WorkFlow Pro's project endpoints."""

    def __init__(self, base_url: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
        # See api/auth_api.py for the same assumption note on config sourcing.
        self.base_url: str = (base_url or os.environ.get("WORKFLOWPRO_API_BASE_URL", "")).rstrip("/")
        self.tenant_id: str = tenant_id or os.environ.get("WORKFLOWPRO_TENANT_ID", "")

        if not self.base_url:
            raise ProjectsAPIError(
                "No API base URL configured. Set WORKFLOWPRO_API_BASE_URL or pass base_url explicitly."
            )

        self.session: requests.Session = requests.Session()
        self.session.headers.update({"X-Tenant-ID": self.tenant_id})

    def create_project(
        self,
        token: str,
        name: str,
        description: str = "",
        team_members: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        """Create a project for the current tenant and return the response payload."""
        url = f"{self.base_url}/api/v1/projects"
        payload = {"name": name, "description": description, "team_members": team_members or []}
        logger.info("Creating project '%s' for tenant '%s'", name, self.tenant_id)

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._auth_headers(token),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Project creation failed for tenant '%s': %s", self.tenant_id, exc)
            raise ProjectsAPIError(f"Project creation failed: {exc}") from exc

        project = response.json()
        if "id" not in project:
            raise ProjectsAPIError(f"Unexpected create-project response shape: {project}")

        logger.info("Project created: id=%s, tenant='%s'", project["id"], self.tenant_id)
        return project

    def get_project(self, token: str, project_id: str) -> Dict[str, object]:
        """Fetch a single project by ID, scoped to the current tenant's token."""
        url = f"{self.base_url}/api/v1/projects/{project_id}"
        logger.info("Fetching project '%s' for tenant '%s'", project_id, self.tenant_id)

        try:
            response = self.session.get(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Get-project request failed for '%s': %s", project_id, exc)
            raise ProjectsAPIError(f"Get-project request failed: {exc}") from exc

        if response.status_code in BLOCKED_STATUS_CODES:
            logger.warning(
                "Access to project '%s' blocked for tenant '%s' (status=%d)",
                project_id, self.tenant_id, response.status_code,
            )
            raise ProjectAccessBlocked(response.status_code, project_id)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise ProjectsAPIError(f"Get-project failed: {exc}") from exc

        return response.json()

    def list_projects(self, token: str) -> List[Dict[str, object]]:
        """List all projects visible to the current tenant's token."""
        url = f"{self.base_url}/api/v1/projects"
        logger.info("Listing projects for tenant '%s'", self.tenant_id)

        try:
            response = self.session.get(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("List-projects request failed for tenant '%s': %s", self.tenant_id, exc)
            raise ProjectsAPIError(f"List-projects request failed: {exc}") from exc

        payload = response.json()
        items = payload.get("items", [])
        logger.info("Retrieved %d project(s) for tenant '%s'", len(items), self.tenant_id)
        return items

    def delete_project(self, token: str, project_id: str) -> None:
        """Delete a project by ID. Used primarily for test-data cleanup."""
        url = f"{self.base_url}/api/v1/projects/{project_id}"
        logger.info("Deleting project '%s' for tenant '%s'", project_id, self.tenant_id)

        try:
            response = self.session.delete(
                url, headers=self._auth_headers(token), timeout=DEFAULT_TIMEOUT_SECONDS
            )
            if response.status_code in BLOCKED_STATUS_CODES:
                raise ProjectAccessBlocked(response.status_code, project_id)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Delete-project request failed for '%s': %s", project_id, exc)
            raise ProjectsAPIError(f"Delete-project request failed: {exc}") from exc

        logger.info("Project '%s' deleted for tenant '%s'", project_id, self.tenant_id)

    def _auth_headers(self, token: str) -> Dict[str, str]:
        """Build the Authorization + tenant headers used by every authenticated call."""
        return {"Authorization": f"Bearer {token}", "X-Tenant-ID": self.tenant_id}

    def close(self) -> None:
        """Release the underlying connection pool. Call in fixture teardown."""
        self.session.close()
