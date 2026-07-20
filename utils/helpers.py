"""General-purpose utility helpers shared across the framework.

Contains only cross-cutting helpers that don't belong to a specific page,
API client, or fixture: a bounded retry decorator, TOTP generation for
2FA test accounts, and log-safe masking of sensitive fields.
"""

import os
import time
from functools import wraps
from typing import Callable, Dict, Optional, Tuple, Type, TypeVar

import pyotp

from utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

SENSITIVE_KEYS = {"password", "token", "otp_code", "authorization", "access_key"}


def retry_on(
    exceptions: Tuple[Type[Exception], ...],
    attempts: int = 2,
    delay_seconds: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a callable a bounded number of times on specific, known-transient exceptions.

    This must never be used to mask genuine assertion failures — only for
    conditions that are expected to be transient by design, such as a
    tenant-dependent dashboard load occasionally exceeding a tight
    timeout. The delay between attempts is a deliberate backoff, not a
    substitute for Playwright's own explicit waits.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            last_error: Optional[Exception] = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s", attempt, attempts, func.__name__, exc
                    )
                    if attempt < attempts:
                        time.sleep(delay_seconds)
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


def generate_otp_code(secret_env_var: str = "TEST_USER_2FA_SECRET") -> str:
    """Generate a current TOTP code for a 2FA-enabled test account.

    ASSUMPTION: 2FA is TOTP-based and a dedicated test-only secret is
    provisioned via the named environment variable (never a real user's
    secret, and never SMS/email-based, which automation cannot intercept).
    """
    secret = os.environ.get(secret_env_var)
    if not secret:
        raise ValueError(f"Missing required environment variable: {secret_env_var}")
    code = pyotp.TOTP(secret).now()
    logger.info("Generated OTP code using secret from '%s'", secret_env_var)
    return code


def mask_sensitive(data: Dict[str, object]) -> Dict[str, object]:
    """Return a copy of `data` with sensitive values redacted, for safe logging.

    Used before logging request/response payloads so credentials and
    tokens never end up in console output, log files, or CI artifacts.
    """
    masked = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            masked[key] = "***REDACTED***"
        else:
            masked[key] = value
    return masked
