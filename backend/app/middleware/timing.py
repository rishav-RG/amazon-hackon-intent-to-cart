"""
Request Timing Middleware.

Measures wall-clock duration of each HTTP request and provides
timing information via logging and response headers.
"""

import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that measures request processing duration.

    For every request:
    - Measures wall-clock duration in ms (rounded to 2 decimal places)
    - Logs at INFO level: HTTP method, path, status code, duration_ms
    - Adds X-Process-Time response header with the duration string
    - Handles exceptions gracefully, still logging and adding header on errors
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Calculate duration even on unhandled exceptions
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "%s %s 500 %sms",
                request.method,
                request.url.path,
                duration_ms,
            )
            # Re-raise after logging; the exception handler will produce a 500 response
            # but we create an error response with the header attached
            from starlette.responses import JSONResponse

            error_response = JSONResponse(
                status_code=500,
                content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
            )
            error_response.headers["X-Process-Time"] = str(duration_ms)
            return error_response

        # Normal path: calculate duration and attach to response
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Process-Time"] = str(duration_ms)
        logger.info(
            "%s %s %s %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
