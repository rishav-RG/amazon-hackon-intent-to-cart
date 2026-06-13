"""
Exception hierarchy and error codes for the Intent-to-Cart backend.

Provides a standardized AppException class and error code constants
that map to specific HTTP status codes.
"""


class AppException(Exception):
    """
    Base application exception with structured error information.

    Attributes:
        error_code: Machine-readable error identifier (max 64 characters).
        message: Human-readable error description (max 500 characters).
        status_code: HTTP status code to return (400-599).
    """

    def __init__(self, error_code: str, message: str, status_code: int):
        if len(error_code) > 64:
            raise ValueError("error_code must be at most 64 characters")
        if len(message) > 500:
            raise ValueError("message must be at most 500 characters")
        if not (400 <= status_code <= 599):
            raise ValueError("status_code must be between 400 and 599")

        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Error code constants as tuples: (error_code_string, default_status_code)
INTENT_NOT_FOUND = ("INTENT_NOT_FOUND", 404)
CLARIFICATION_NOT_FOUND = ("CLARIFICATION_NOT_FOUND", 404)
SESSION_EXPIRED = ("SESSION_EXPIRED", 410)
INVALID_INTENT_TEXT = ("INVALID_INTENT_TEXT", 422)
DB_CONNECTION_ERROR = ("DB_CONNECTION_ERROR", 503)
REDIS_CONNECTION_ERROR = ("REDIS_CONNECTION_ERROR", 503)
VALIDATION_ERROR = ("VALIDATION_ERROR", 422)
CART_VERSION_CONFLICT = ("CART_VERSION_CONFLICT", 409)
