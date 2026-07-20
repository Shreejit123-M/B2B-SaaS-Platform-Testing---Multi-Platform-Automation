"""BrowserStack configuration and connection helper.

Builds capability dictionaries and a connection WebSocket endpoint for
BrowserStack Automate, reading credentials from environment variables
only — no credentials are hardcoded anywhere in this file, and none are
required for the rest of the suite to run (BrowserStack usage is opt-in
per test, via the `browserstack_page` fixture below).
"""

import os
from typing import Dict, Optional
from urllib.parse import quote

from playwright.sync_api import Browser, Playwright

from utils.logger import get_logger

logger = get_logger(__name__)

BROWSERSTACK_HUB_WS = "wss://cdp.browserstack.com/playwright"


def get_browserstack_credentials() -> Dict[str, str]:
    """Read BrowserStack credentials from environment variables.

    Raises a clear error if credentials are missing, rather than silently
    connecting with empty values and producing a confusing remote error.
    """
    username = os.environ.get("BROWSERSTACK_USERNAME")
    access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY")

    if not username or not access_key:
        raise EnvironmentError(
            "BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY must be set "
            "as environment variables to run BrowserStack-backed tests."
        )
    return {"username": username, "access_key": access_key}


def build_capabilities(
    browser_name: str = "chrome",
    os_name: Optional[str] = None,
    os_version: Optional[str] = None,
    device: Optional[str] = None,
    build_name: str = "WorkFlow Pro QA Automation",
) -> Dict[str, object]:
    """Build a BrowserStack capability set for a desktop browser or mobile device.

    Pass `device` (e.g. "iPhone 15") for a mobile web session; omit it for
    a desktop browser session with `os_name`/`os_version` (e.g. "OS X" /
    "Sonoma"). Values are intentionally NOT hardcoded to a single matrix
    here — see browserstack/browserstack.yml for the declarative matrix
    used by CI.
    """
    capabilities: Dict[str, object] = {
        "browserName": browser_name,
        "bstack:options": {
            "buildName": build_name,
            "projectName": "WorkFlow Pro",
            "debug": True,
            "networkLogs": True,
            "consoleLogs": "errors",
        },
    }

    bstack_options = capabilities["bstack:options"]
    if device:
        bstack_options["deviceName"] = device
        bstack_options["realMobile"] = "true"
    if os_name:
        bstack_options["os"] = os_name
    if os_version:
        bstack_options["osVersion"] = os_version

    logger.info("Built BrowserStack capabilities: browser=%s, device=%s", browser_name, device)
    return capabilities


def connect_browserstack(playwright: Playwright, capabilities: Dict[str, object]) -> Browser:
    """Connect to a remote BrowserStack session and return a Playwright Browser.

    Uses the same `playwright.chromium.connect()` API used for any remote
    CDP endpoint, so page objects and tests behave identically whether the
    browser is local or running on BrowserStack — see fixtures/browser_fixtures.py.
    """
    credentials = get_browserstack_credentials()
    caps_query = quote(str(capabilities))
    ws_endpoint = (
        f"{BROWSERSTACK_HUB_WS}?caps={caps_query}"
        f"&username={credentials['username']}&access_key={credentials['access_key']}"
    )

    logger.info("Connecting to BrowserStack session")
    return playwright.chromium.connect(ws_endpoint)
