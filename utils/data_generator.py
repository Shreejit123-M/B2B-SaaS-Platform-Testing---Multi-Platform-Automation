"""Test data generation utilities.

Generates dynamic, uniquely-namespaced test data so tests remain safe to
run in parallel (via pytest-xdist) without name collisions, and so
created data is easy to identify and clean up.
"""

import os
import uuid
from typing import List

from utils.logger import get_logger

logger = get_logger(__name__)


def get_worker_id() -> str:
    """Return the current pytest-xdist worker ID, or 'master' if not parallelized."""
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def generate_unique_project_name(prefix: str = "Automated-Project") -> str:
    """Generate a project name unique across parallel workers and repeated runs."""
    name = f"{prefix}-{get_worker_id()}-{uuid.uuid4().hex[:8]}"
    logger.debug("Generated unique project name: %s", name)
    return name


def generate_unique_email(tenant_domain: str, local_prefix: str = "autotest") -> str:
    """Generate a unique email address scoped to a tenant domain, for accounts
    that must be created fresh per test rather than reused static accounts."""
    email = f"{local_prefix}-{uuid.uuid4().hex[:8]}@{tenant_domain}"
    logger.debug("Generated unique email: %s", email)
    return email


def generate_team_members(count: int = 2, tenant_domain: str = "company1.workflowpro.com") -> List[str]:
    """Generate a list of plausible team-member emails for project-creation payloads."""
    return [generate_unique_email(tenant_domain, local_prefix=f"member{i}") for i in range(count)]


def generate_project_description(scenario: str) -> str:
    """Generate a descriptive, traceable project description tagged with the scenario name.

    Tagging the description (not just the name) with the originating
    scenario makes orphaned data easy to identify manually if automated
    cleanup ever fails.
    """
    return f"Created by automated test scenario '{scenario}' (worker={get_worker_id()})"
