"""
User identity dependency for FastAPI route injection.

Provides get_current_user_id() which extracts and validates
the X-User-ID header from incoming requests.
"""

from fastapi import Request

from app.exceptions import AppException, VALIDATION_ERROR


async def get_current_user_id(request: Request) -> str:
    """
    Extract X-User-ID header from the request.

    Returns the header value as-is if it is non-empty after stripping.
    Raises AppException(VALIDATION_ERROR, status_code=401) if the header
    is missing, empty, or contains only whitespace.
    """
    user_id = request.headers.get("X-User-ID")

    if user_id is None or user_id.strip() == "":
        raise AppException(
            error_code=VALIDATION_ERROR[0],
            message="X-User-ID header is required",
            status_code=401,
        )

    return user_id
