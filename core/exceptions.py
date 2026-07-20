"""Custom exceptions for the QA framework."""


class QAFrameworkException(Exception):
    """Base exception for QA framework."""
    pass


class ElementNotFoundException(QAFrameworkException):
    """Raised when an element is not found on the page."""
    pass


class TimeoutException(QAFrameworkException):
    """Raised when a wait operation times out."""
    pass


class StaleElementException(QAFrameworkException):
    """Raised when an element becomes stale."""
    pass


class NavigationException(QAFrameworkException):
    """Raised when navigation fails."""
    pass


class AuthenticationException(QAFrameworkException):
    """Raised when authentication fails."""
    pass


class APIException(QAFrameworkException):
    """Raised when API request fails."""
    pass


class TenantIsolationException(QAFrameworkException):
    """Raised when tenant isolation is violated."""
    pass


class InvalidConfigurationException(QAFrameworkException):
    """Raised when configuration is invalid."""
    pass
