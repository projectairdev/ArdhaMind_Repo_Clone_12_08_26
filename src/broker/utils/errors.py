from __future__ import annotations
from typing import Any

class BrokerError(Exception):
    """
    Base class for all structured, immutable Broker exceptions.
    """
    def __init__(self, message: str, error_code: str = "BROKER_ERROR") -> None:
        super().__init__(message)
        # Store as private attributes to enforce immutability
        self._message = message
        self._error_code = error_code

    @property
    def message(self) -> str:
        """The error message."""
        return self._message

    @property
    def error_code(self) -> str:
        """The short error code string identifying the category."""
        return self._error_code

    def __setattr__(self, key: str, value: Any) -> None:
        # Prevent mutating message or error_code after initialization
        if key in ("_message", "_error_code") and hasattr(self, key):
            raise AttributeError("BrokerError instances are immutable.")
        super().__setattr__(key, value)


class InvalidAPIKeyError(BrokerError):
    def __init__(self, message: str = "Invalid API Key") -> None:
        super().__init__(message, "INVALID_API_KEY")


class InvalidAPISecretError(BrokerError):
    def __init__(self, message: str = "Invalid API Secret") -> None:
        super().__init__(message, "INVALID_API_SECRET")


class ExpiredRequestTokenError(BrokerError):
    def __init__(self, message: str = "Expired request token") -> None:
        super().__init__(message, "EXPIRED_REQUEST_TOKEN")


class ExpiredAccessTokenError(BrokerError):
    def __init__(self, message: str = "Expired access token") -> None:
        super().__init__(message, "EXPIRED_ACCESS_TOKEN")


class NetworkFailureError(BrokerError):
    def __init__(self, message: str = "Network failure") -> None:
        super().__init__(message, "NETWORK_FAILURE")


class SessionMissingError(BrokerError):
    def __init__(self, message: str = "Session is missing") -> None:
        super().__init__(message, "SESSION_MISSING")


class AuthenticationFailureError(BrokerError):
    def __init__(self, message: str = "Authentication failure") -> None:
        super().__init__(message, "AUTHENTICATION_FAILURE")
