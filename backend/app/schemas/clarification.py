"""Clarification request and response schemas.

Validates: Requirements 24.1, 24.2, 24.3, 24.4
"""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ClarificationRequest(BaseModel):
    """Request schema for POST /v1/clarification.

    Validates: Requirement 24.1
    """

    intent_id: UUID
    session_id: str = Field(min_length=1, max_length=128)
    answer: str = Field(min_length=1, max_length=2000)


class ClarificationResponse(BaseModel):
    """Response schema for POST /v1/clarification.

    Validates: Requirements 24.2, 24.3
    """

    complete: bool
    next_question: str | None = None
    questions_remaining: int = Field(ge=0, le=3)

    @model_validator(mode="after")
    def validate_complete_state(self) -> "ClarificationResponse":
        """When complete is True, next_question must be None and questions_remaining must be 0."""
        if self.complete:
            if self.next_question is not None:
                raise ValueError("next_question must be None when complete is True")
            if self.questions_remaining != 0:
                raise ValueError("questions_remaining must be 0 when complete is True")
        return self
