"""Health check response schema."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema for the GET /health endpoint.

    Validates: Requirement 12.1
    """

    status: Literal["healthy", "unhealthy"]
    db: Literal["connected", "disconnected"]
    redis: Literal["connected", "disconnected"]
