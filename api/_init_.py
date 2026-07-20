
"""API client layer for WorkFlow Pro.

Exposes thin, tenant-aware wrappers around the WorkFlow Pro REST API,
built on `requests.Session()`. These clients are consumed by:
  - fixtures/ (to seed/clean up test data)
  - tests/api/ (to test the API directly)
  - tests/integration/ (to combine API setup with UI/mobile verification)

ASSUMPTION (undocumented in the original assignment, see docs/ for the
full assumptions register if present): all endpoints live under a single
versioned base path (`/api/v1`), and tenant scoping is enforced via an
`X-Tenant-ID` header rather than a path segment, matching the one
concrete example given in the assignment brief
(`POST /api/v1/projects`, headers: `Authorization`, `X-Tenant-ID`).
"""

from api.auth_api import AuthAPI
from api.projects_api import ProjectsAPI
from api.users_api import UsersAPI

__all__ = ["AuthAPI", "ProjectsAPI", "UsersAPI"]
