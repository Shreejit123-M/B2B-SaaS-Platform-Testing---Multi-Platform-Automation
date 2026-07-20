"""UI project-management tests for WorkFlow Pro.

ASSUMPTION: pages.project_page.ProjectPage exposes .open(), .create_project(name,
description), .get_visible_project_names(), and .search(query). If your
existing pages/ module splits these across separate list/detail page
objects, adjust the imports/calls below accordingly.
"""

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.project_page import ProjectPage  # ASSUMPTION: see module note above
from utils.data_generator import generate_unique_project_name
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def project_page(authenticated_page: DashboardPage, environment: str) -> ProjectPage:
    """Provide a ProjectPage bound to the current authenticated session."""
    return ProjectPage(authenticated_page.page, environment)


@pytest.mark.ui
@pytest.mark.smoke
def test_create_project_via_ui(project_page: ProjectPage) -> None:
    """A user can create a project through the UI and see it in the project list."""
    project_name = generate_unique_project_name(prefix="UI-Created")
    project_page.open()
    project_page.create_project(name=project_name, description="Created via UI test")

    visible_names = " ".join(project_page.get_visible_project_names())
    assert project_name in visible_names, "Newly created project did not appear in the project list."


@pytest.mark.ui
@pytest.mark.regression
def test_project_created_via_api_visible_in_ui(project_page: ProjectPage, test_project: dict) -> None:
    """A project created via the API layer is visible in the UI project list
    without requiring anything beyond normal navigation."""
    project_page.open()
    visible_names = " ".join(project_page.get_visible_project_names())
    assert test_project["name"] in visible_names, (
        "API-created project was not visible in the UI project list."
    )


@pytest.mark.ui
@pytest.mark.regression
def test_project_search_returns_matching_result(project_page: ProjectPage, test_project: dict) -> None:
    """Searching for an existing project's name returns that project."""
    project_page.open()
    project_page.search(str(test_project["name"]))

    visible_names = " ".join(project_page.get_visible_project_names())
    assert test_project["name"] in visible_names, "Search did not return the expected project."


@pytest.mark.ui
@pytest.mark.regression
def test_project_search_no_match_shows_empty_state(project_page: ProjectPage) -> None:
    """Searching for a term matching nothing shows an explicit empty-results state,
    not a blank/ambiguous screen."""
    project_page.open()
    project_page.search("NoSuchProjectNameShouldEverExist-ZZZ")
    expect(project_page.no_results_message).to_be_visible()
