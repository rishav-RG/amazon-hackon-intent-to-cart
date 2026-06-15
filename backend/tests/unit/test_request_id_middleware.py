"""Unit tests for app/middleware/request_id.py — RequestIDMiddleware."""

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI, Request
from hypothesis import given, settings
from hypothesis import strategies as st

from app.middleware.request_id import RequestIDMiddleware


def _create_app() -> FastAPI:
    """Create a minimal FastAPI app with the RequestIDMiddleware."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"request_id": request.state.request_id}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Intentional error")

    return app


@pytest.fixture
def app():
    return _create_app()


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# --- Unit Tests ---


class TestRequestIDMiddleware:
    """Example-based tests for RequestIDMiddleware."""

    @pytest.mark.asyncio
    async def test_generates_uuid4_when_header_missing(self, client):
        """Req 19.2: Generates UUID v4 when X-Request-ID header is absent."""
        response = await client.get("/test")
        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        # Validate it's a valid UUID v4
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    @pytest.mark.asyncio
    async def test_generates_uuid4_when_header_empty(self, client):
        """Req 19.2: Generates UUID v4 when X-Request-ID header is empty."""
        response = await client.get("/test", headers={"X-Request-ID": ""})
        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    @pytest.mark.asyncio
    async def test_generates_uuid4_when_header_exceeds_200_chars(self, client):
        """Req 19.2: Generates UUID v4 when X-Request-ID exceeds 200 characters."""
        long_id = "x" * 201
        response = await client.get("/test", headers={"X-Request-ID": long_id})
        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id != long_id
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    @pytest.mark.asyncio
    async def test_propagates_valid_header(self, client):
        """Req 19.1: Propagates X-Request-ID when present and ≤200 chars."""
        custom_id = "my-custom-request-id-12345"
        response = await client.get("/test", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_id

    @pytest.mark.asyncio
    async def test_propagates_header_at_exactly_200_chars(self, client):
        """Req 19.1: Boundary — exactly 200 characters should be propagated."""
        exact_id = "a" * 200
        response = await client.get("/test", headers={"X-Request-ID": exact_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == exact_id

    @pytest.mark.asyncio
    async def test_stores_in_request_state(self, client):
        """Req 19.4: Request ID is available in request.state.request_id."""
        custom_id = "state-test-id"
        response = await client.get("/test", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        body = response.json()
        assert body["request_id"] == custom_id

    @pytest.mark.asyncio
    async def test_generated_id_in_request_state(self, client):
        """Req 19.4: Generated UUID is also stored in request.state."""
        response = await client.get("/test")
        assert response.status_code == 200
        body = response.json()
        response_header_id = response.headers.get("X-Request-ID")
        assert body["request_id"] == response_header_id

    @pytest.mark.asyncio
    async def test_header_present_on_error_responses(self, client):
        """Req 19.3: X-Request-ID header present even on error responses."""
        response = await client.get("/error")
        assert response.status_code == 500
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        # Should still be a valid UUID since no header was sent
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    @pytest.mark.asyncio
    async def test_header_present_on_error_with_custom_id(self, client):
        """Req 19.3: Custom X-Request-ID propagated even on error responses."""
        custom_id = "error-test-id"
        response = await client.get("/error", headers={"X-Request-ID": custom_id})
        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == custom_id


# --- Property-Based Tests ---


def _run_async(coro):
    """Helper to run async code in property-based tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestRequestIDMiddlewareProperties:
    """
    Property-based tests for RequestIDMiddleware.
    Validates: Requirements 19.1, 19.2, 19.3, 19.4
    """

    @settings(max_examples=50)
    @given(
        request_id=st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        )
    )
    def test_valid_header_always_propagated(self, request_id):
        """
        **Validates: Requirements 19.1**
        Any non-empty X-Request-ID header with ≤200 printable ASCII chars
        is propagated verbatim.
        """
        async def _run():
            app = _create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.get("/test", headers={"X-Request-ID": request_id})
                assert response.headers.get("X-Request-ID") == request_id

        _run_async(_run())

    @settings(max_examples=30)
    @given(
        request_id=st.text(
            min_size=201,
            max_size=500,
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        )
    )
    def test_oversized_header_always_generates_uuid4(self, request_id):
        """
        **Validates: Requirements 19.2**
        Any X-Request-ID header exceeding 200 chars results in a new UUID v4.
        """
        async def _run():
            app = _create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.get("/test", headers={"X-Request-ID": request_id})
                result_id = response.headers.get("X-Request-ID")
                assert result_id != request_id
                parsed = uuid.UUID(result_id)
                assert parsed.version == 4

        _run_async(_run())

    @settings(max_examples=20)
    @given(st.data())
    def test_response_always_has_request_id_header(self, data):
        """
        **Validates: Requirements 19.3**
        Every response, regardless of whether input header was provided,
        always includes an X-Request-ID response header.
        """
        include_header = data.draw(st.booleans())

        async def _run():
            app = _create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                headers = {}
                if include_header:
                    headers["X-Request-ID"] = data.draw(
                        st.text(
                            min_size=0,
                            max_size=300,
                            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
                        )
                    )
                response = await client.get("/test", headers=headers)
                assert "x-request-id" in response.headers

        _run_async(_run())

    @settings(max_examples=30)
    @given(
        request_id=st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        )
    )
    def test_request_state_matches_response_header(self, request_id):
        """
        **Validates: Requirements 19.4**
        The request ID stored in request.state.request_id always matches
        the X-Request-ID response header.
        """
        async def _run():
            app = _create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.get("/test", headers={"X-Request-ID": request_id})
                body = response.json()
                assert body["request_id"] == response.headers.get("X-Request-ID")

        _run_async(_run())
