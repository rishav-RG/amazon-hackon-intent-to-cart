"""
Request ID Middleware.

Propagates or generates a unique request identifier for every request,
making it available to downstream handlers and including it in all responses.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_HEADER_NAME = "X-Request-ID"
_MAX_LENGTH = 200


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request/response carries an X-Request-ID header.

    Behavior:
    - If the incoming request includes an X-Request-ID header with a value
      of 200 characters or fewer, that value is propagated.
    - If the header is missing, empty, or exceeds 200 characters, a new
      UUID v4 is generated.
    - The resolved request ID is stored in request.state.request_id for
      downstream handlers.
    - The X-Request-ID header is added to all responses, including errors.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get(_HEADER_NAME)

        if incoming_id and len(incoming_id) <= _MAX_LENGTH:
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        # Store in request state for downstream access
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            # Even on unhandled exceptions, ensure the header is present
            # by returning a 500 response with the request ID attached.
            response = Response(
                content="Internal Server Error",
                status_code=500,
                media_type="text/plain",
            )

        # Attach header to response
        response.headers[_HEADER_NAME] = request_id

        return response
