"""Centralized logging configuration for the WorkFlow Pro automation suite.

Every module in this framework imports its logger via `get_logger(__name__)`
(or uses the shared `"wfp_qa"` logger directly) rather than calling
`logging.basicConfig()` independently, which avoids duplicate handlers and
inconsistent formatting when modules are imported in different orders.
"""

import logging
from pathlib import Path

LOG_DIR = Path("reports") / "logs"
LOG_FILE = LOG_DIR / "run.log"

_CONFIGURED = False


def _configure_root_logger() -> None:
    """Attach console (INFO) and file (DEBUG) handlers exactly once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("wfp_qa")
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the shared 'wfp_qa' hierarchy.

    Usage: `logger = get_logger(__name__)` at the top of any module.
    """
    _configure_root_logger()
    return logging.getLogger(f"wfp_qa.{name}")
