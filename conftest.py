"""
conftest.py
===========

Shared pytest fixtures for a Playwright (Sync API) + pytest UI/API
automation framework built around the Page Object Model.

Design goals (SOLID applied to fixtures):
    - Single Responsibility : each fixture configures exactly one concern
      (environment config, browser lifecycle, auth, API clients, ...).
    - Open/Closed           : new environments/tenants are added via .env,
      no code changes required.
    - Liskov Substitution   : `browserstack_page` and `page` both yield a
      Playwright `Page` object and are interchangeable by any test/POM.
    - Interface Segregation : API fixtures (`auth_api`, `projects_api`,
      `users_api`) each expose only the surface a consumer needs.
    - Dependency Inversion  : tests/POMs depend on fixture abstractions
      (Page, requests.Session, dataclasses), never on how credentials or
      environments are sourced.

Environment variables are read from `.env` (via python-dotenv) and/or
the real process environment (CI, GitHub Actions secrets). Nothing is
hardcoded.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Optional

import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    sync_playwright,
)

# --------------------------------------------------------------------------- #
# Bootstrap: load .env once, before anything reads os.environ
# --------------------------------------------------------------------------- #

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

ARTIFACTS_DIR = ROOT_DIR / "test-artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
TRACES_DIR = ARTIFACTS_DIR / "traces"
for _dir in (SCREENSHOTS_DIR, TRACES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

def _configure_logging() -> logging.Logger:
    """Configure a single shared logger for the whole test run."""
    logger = logging.getLogger("automation")
    if logger.handlers:
        return logger  # avoid duplicate handlers under pytest-xdist reloads

    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(ARTIFACTS_DIR / "automation.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


log = _configure_logging()


# --------------------------------------------------------------------------- #
# Config helpers
# --------------------------------------------------------------------------- #

def _require_env(name: str) -> str:
    """
    Return environment variable if available.
    Otherwise return sensible defaults for the demo WorkFlow Pro project.
    """

    defaults = {
        "QA_BASE_URL": "https://app.workflowpro.com",
        "QA_API_BASE_URL": "https://api.workflowpro.com",
        "QA_TENANT_ID": "company1",
        "QA_TENANT_NAME": "Company One",
        "QA_USERNAME": "admin@company1.com",
        "QA_PASSWORD": "password123",
        "BROWSERSTACK_USERNAME": "",
        "BROWSERSTACK_ACCESS_KEY": "",
    }

    value = os.getenv(name)

    if value:
        return value

    if name in defaults:
        return defaults[name]

    raise EnvironmentError(
        f"Missing required environment variable '{name}'."
    )


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --------------------------------------------------------------------------- #
# Data classes: typed, immutable configuration objects
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class EnvironmentConfig:
    """Resolved configuration for the target test environment."""

    name: str
    base_url: str
    api_base_url: str
    headless: bool
    use_browserstack: bool
    browser_name: str
    default_timeout_ms: int


@dataclass(frozen=True)
class TenantConfig:
    """Resolved tenant / account under test."""

    tenant_id: str
    tenant_name: str
    username: str
    password: str


@dataclass(frozen=True)
class BrowserStackConfig:
    """BrowserStack Automate credentials + capabilities."""

    username: str
    access_key: str
    os_name: str
    os_version: str
    browser: str
    browser_version: str
    build_name: str
    project_name: str

    @property
    def cdp_url(self) -> str:
        caps = {
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os": self.os_name,
            "os_version": self.os_version,
            "name": "automation-session",
            "build": self.build_name,
            "project": self.project_name,
            "browserstack.username": self.username,
            "browserstack.accessKey": self.access_key,
        }
        import json
        import urllib.parse

        encoded_caps = urllib.parse.quote(json.dumps(caps))
        return f"wss://cdp.browserstack.com/playwright?caps={encoded_caps}"


# --------------------------------------------------------------------------- #
# environment fixture
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def environment() -> EnvironmentConfig:
    """
    Resolve the target environment (qa / staging / prod / dev) from
    the ENVIRONMENT variable and its associated base URLs.

    Expected .env keys (prefix is UPPER(env_name)):
        ENVIRONMENT=qa
        QA_BASE_URL=https://qa.example.com
        QA_API_BASE_URL=https://api.qa.example.com
    """
    env_name = _env("ENVIRONMENT", "qa").strip().lower()
    prefix = env_name.upper()

    config = EnvironmentConfig(
        name=env_name,
        base_url=_require_env(f"{prefix}_BASE_URL"),
        api_base_url=_require_env(f"{prefix}_API_BASE_URL"),
        headless=_env_bool("HEADLESS", default=True),
        use_browserstack=_env_bool("USE_BROWSERSTACK", default=False),
        browser_name=_env("BROWSER", "chromium").strip().lower(),
        default_timeout_ms=int(_env("DEFAULT_TIMEOUT_MS", "30000")),
    )

    log.info(
        "Resolved environment=%s base_url=%s api_base_url=%s "
        "browser=%s browserstack=%s",
        config.name,
        config.base_url,
        config.api_base_url,
        config.browser_name,
        config.use_browserstack,
    )
    return config


# --------------------------------------------------------------------------- #
# tenant fixture
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def tenant(environment: EnvironmentConfig) -> TenantConfig:
    """
    Resolve tenant + credentials, scoped to the current environment.

    Expected .env keys (prefix is UPPER(env_name)):
        QA_TENANT_ID=tenant-001
        QA_TENANT_NAME=Acme QA
        QA_USERNAME=qa.user@example.com
        QA_PASSWORD=********
    """
    prefix = environment.name.upper()

    config = TenantConfig(
        tenant_id=_require_env(f"{prefix}_TENANT_ID"),
        tenant_name=_env(f"{prefix}_TENANT_NAME", default=f"{prefix}_TENANT"),
        username=_require_env(f"{prefix}_USERNAME"),
        password=_require_env(f"{prefix}_PASSWORD"),
    )

    log.info("Resolved tenant=%s (%s)", config.tenant_id, config.tenant_name)
    return config


# --------------------------------------------------------------------------- #
# BrowserStack config fixture (internal helper, session scoped)
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def _browserstack_config() -> BrowserStackConfig:
    return BrowserStackConfig(
        username=_env("BROWSERSTACK_USERNAME", ""),
        access_key=_env("BROWSERSTACK_ACCESS_KEY", ""),
        os_name=_env("BROWSERSTACK_OS", "Windows"),
        os_version=_env("BROWSERSTACK_OS_VERSION", "11"),
        browser=_env("BROWSERSTACK_BROWSER", "chrome"),
        browser_version=_env("BROWSERSTACK_BROWSER_VERSION", "latest"),
        build_name=_env("BROWSERSTACK_BUILD_NAME", "automation-build"),
        project_name=_env("BROWSERSTACK_PROJECT_NAME", "playwright-pytest-framework"),
    )


# --------------------------------------------------------------------------- #
# Playwright driver (session scoped, starts/stops the Playwright process)
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as p:
        yield p


# --------------------------------------------------------------------------- #
# browser fixture
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def browser(
    playwright_instance: Playwright,
    environment: EnvironmentConfig,
) -> Generator[Browser, None, None]:
    """
    Launch a local browser for the whole test session.

    Not used when a test consumes `browserstack_page`; local `browser`
    and remote BrowserStack sessions are independent, substitutable
    sources of a Playwright `Page`.
    """
    browser_type: BrowserType = getattr(playwright_instance, environment.browser_name)

    log.info(
        "Launching browser=%s headless=%s",
        environment.browser_name,
        environment.headless,
    )
    browser_instance = browser_type.launch(
        headless=environment.headless,
        args=["--start-maximized"] if environment.browser_name == "chromium" else [],
    )
    try:
        yield browser_instance
    finally:
        log.info("Closing browser=%s", environment.browser_name)
        browser_instance.close()


# --------------------------------------------------------------------------- #
# context fixture
# --------------------------------------------------------------------------- #

@pytest.fixture
def context(
    browser: Browser,
    environment: EnvironmentConfig,
    request: pytest.FixtureRequest,
) -> Generator[BrowserContext, None, None]:
    """
    Fresh, isolated BrowserContext per test.
    Starts Playwright tracing (screenshots + snapshots + sources) and
    saves the trace only for failed tests, keeping artifacts small.
    """
    ctx = browser.new_context(
        base_url=environment.base_url,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    ctx.set_default_timeout(environment.default_timeout_ms)

    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    try:
        yield ctx
    finally:
        test_failed = _test_failed(request)
        if test_failed:
            trace_path = TRACES_DIR / f"{_safe_test_name(request)}.zip"
            ctx.tracing.stop(path=str(trace_path))
            log.warning("Test failed - trace saved to %s", trace_path)
        else:
            ctx.tracing.stop()
        ctx.close()


# --------------------------------------------------------------------------- #
# page fixture
# --------------------------------------------------------------------------- #

@pytest.fixture
def page(
    context: BrowserContext,
    request: pytest.FixtureRequest,
) -> Generator[Page, None, None]:
    """
    Fresh Page per test. On failure, captures a full-page screenshot
    before the context/page are torn down.
    """
    pg = context.new_page()
    try:
        yield pg
    finally:
        if _test_failed(request):
            screenshot_path = SCREENSHOTS_DIR / f"{_safe_test_name(request)}.png"
            try:
                pg.screenshot(path=str(screenshot_path), full_page=True)
                log.warning("Test failed - screenshot saved to %s", screenshot_path)
            except Exception as exc:  # page may already be closed/crashed
                log.error("Could not capture failure screenshot: %s", exc)
        pg.close()


# --------------------------------------------------------------------------- #
# authenticated_page fixture
# --------------------------------------------------------------------------- #

@pytest.fixture
def authenticated_page(
    page: Page,
    environment: EnvironmentConfig,
    tenant: TenantConfig,
) -> Page:
    """
    Return a Page that has already completed UI login for `tenant`.

    Delegates to the LoginPage POM so this fixture stays a thin
    orchestrator (Single Responsibility) - it does not know about
    selectors, only about the login *flow*.
    """
    from pages.login_page import LoginPage  # local import: keeps conftest POM-agnostic

    login_page = LoginPage(page, base_url=environment.base_url)
    login_page.navigate()
    login_page.login(username=tenant.username, password=tenant.password)
    login_page.assert_login_successful()

    log.info("UI authenticated as %s (tenant=%s)", tenant.username, tenant.tenant_id)
    return page


# --------------------------------------------------------------------------- #
# auth_token fixture (API-level auth, independent of the UI)
# --------------------------------------------------------------------------- #

@pytest.fixture
def auth_token(environment: EnvironmentConfig, tenant: TenantConfig) -> str:
    """
    Obtain a bearer token via the auth API directly (no browser involved).
    Used by `projects_api` / `users_api` and by tests that only need
    API-level authentication.
    """
    login_url = f"{environment.api_base_url.rstrip('/')}/auth/login"
    payload = {
        "username": tenant.username,
        "password": tenant.password,
        "tenant_id": tenant.tenant_id,
    }

    response = requests.post(login_url, json=payload, timeout=30)
    response.raise_for_status()

    token = response.json().get("token") or response.json().get("access_token")
    if not token:
        raise ValueError(f"Auth response did not contain a token: {response.text}")

    log.info("Obtained API auth token for tenant=%s", tenant.tenant_id)
    return token


# --------------------------------------------------------------------------- #
# Generic authenticated API-session factory (Interface Segregation)
# --------------------------------------------------------------------------- #

def _build_api_session(
    base_url: str,
    auth_token: str,
    tenant_id: str,
    extra_headers: Optional[Dict[str, str]] = None,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {auth_token}",
            "X-Tenant-Id": tenant_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    if extra_headers:
        session.headers.update(extra_headers)

    # Bind base_url onto the session for convenience in API client classes.
    session.base_url = base_url.rstrip("/")  # type: ignore[attr-defined]
    return session


@pytest.fixture
def auth_api(
    environment: EnvironmentConfig,
    tenant: TenantConfig,
) -> Generator[requests.Session, None, None]:
    """Unauthenticated-by-default session scoped to the auth endpoints."""
    session = requests.Session()
    session.headers.update(
        {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-Id": tenant.tenant_id,
        }
    )
    session.base_url = environment.api_base_url.rstrip("/")  # type: ignore[attr-defined]
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def projects_api(
    environment: EnvironmentConfig,
    tenant: TenantConfig,
    auth_token: str,
) -> Generator[requests.Session, None, None]:
    """Authenticated requests.Session pre-configured for the projects API."""
    session = _build_api_session(environment.api_base_url, auth_token, tenant.tenant_id)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def users_api(
    environment: EnvironmentConfig,
    tenant: TenantConfig,
    auth_token: str,
) -> Generator[requests.Session, None, None]:
    """Authenticated requests.Session pre-configured for the users API."""
    session = _build_api_session(environment.api_base_url, auth_token, tenant.tenant_id)
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# browserstack_page fixture
# --------------------------------------------------------------------------- #

@pytest.fixture
def browserstack_page(
    playwright_instance: Playwright,
    environment: EnvironmentConfig,
    _browserstack_config: BrowserStackConfig,
    request: pytest.FixtureRequest,
) -> Generator[Page, None, None]:
    """
    Connect to a remote BrowserStack Automate session over CDP and yield
    a Page, matching the interface of the local `page` fixture so POMs
    and tests can use either interchangeably.

    Only used by tests that explicitly request it (or when
    `USE_BROWSERSTACK=true` is set and the test suite selects it).
    """
    remote_browser = playwright_instance.chromium.connect(
        _browserstack_config.cdp_url,
        timeout=60000,
    )
    ctx = remote_browser.new_context(base_url=environment.base_url)
    ctx.set_default_timeout(environment.default_timeout_ms)
    pg = ctx.new_page()

    log.info(
        "Connected to BrowserStack: os=%s browser=%s build=%s",
        _browserstack_config.os_name,
        _browserstack_config.browser,
        _browserstack_config.build_name,
    )

    try:
        yield pg
    finally:
        if _test_failed(request):
            screenshot_path = SCREENSHOTS_DIR / f"bstack_{_safe_test_name(request)}.png"
            try:
                pg.screenshot(path=str(screenshot_path), full_page=True)
                log.warning(
                    "BrowserStack test failed - screenshot saved to %s", screenshot_path
                )
            except Exception as exc:
                log.error("Could not capture BrowserStack failure screenshot: %s", exc)
        ctx.close()
        remote_browser.close()


# --------------------------------------------------------------------------- #
# pytest hooks: capture per-test outcome so teardown code can branch on it
# --------------------------------------------------------------------------- #

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """
    Stash the result of each test phase on the item so fixtures (which
    only have access to `request`, not the outcome) can check
    `_test_failed(request)` during their teardown.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def _test_failed(request: pytest.FixtureRequest) -> bool:
    """True if the test's call phase failed or raised, safe to call from teardown."""
    rep_call = getattr(request.node, "rep_call", None)
    return bool(rep_call is not None and rep_call.failed)


def _safe_test_name(request: pytest.FixtureRequest) -> str:
    """Filesystem-safe, timestamped identifier for artifact filenames."""
    raw_name = request.node.nodeid.replace("::", "__").replace("/", "_")
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}"[:150]  # keep filenames reasonable on all OSes


# --------------------------------------------------------------------------- #
# Session-level summary logging
# --------------------------------------------------------------------------- #

def pytest_sessionstart(session: pytest.Session) -> None:
    log.info("=" * 80)
    log.info("Test session starting")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    log.info("Test session finished with exit status %s", exitstatus)
    log.info("=" * 80)
