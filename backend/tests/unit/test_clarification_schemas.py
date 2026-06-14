"""Unit tests for app/schemas/clarification.py — ClarificationRequest and ClarificationResponse."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.clarification import ClarificationRequest, ClarificationResponse
from app.schemas.bundle_context import BundleContext


# --- ClarificationRequest Tests ---


class TestClarificationRequest:
    """Example-based tests for ClarificationRequest schema. Validates: Requirement 24.1"""

    def test_valid_request(self):
        req = ClarificationRequest(
            intent_id=uuid.uuid4(),
            session_id="session-abc",
            answer="Yes, I want the large size",
        )
        assert isinstance(req.intent_id, uuid.UUID)
        assert req.session_id == "session-abc"
        assert req.answer == "Yes, I want the large size"

    def test_intent_id_must_be_valid_uuid(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id="not-a-uuid",
                session_id="session-1",
                answer="answer",
            )

    def test_session_id_min_length(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                session_id="",
                answer="answer",
            )

    def test_session_id_max_length(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                session_id="x" * 129,
                answer="answer",
            )

    def test_session_id_at_max_length(self):
        req = ClarificationRequest(
            intent_id=uuid.uuid4(),
            session_id="x" * 128,
            answer="answer",
        )
        assert len(req.session_id) == 128

    def test_answer_min_length(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                session_id="session-1",
                answer="",
            )

    def test_answer_max_length(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                session_id="session-1",
                answer="a" * 2001,
            )

    def test_answer_at_max_length(self):
        req = ClarificationRequest(
            intent_id=uuid.uuid4(),
            session_id="session-1",
            answer="a" * 2000,
        )
        assert len(req.answer) == 2000

    def test_missing_intent_id_raises(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                session_id="session-1",
                answer="answer",
            )

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                answer="answer",
            )

    def test_missing_answer_raises(self):
        with pytest.raises(ValidationError):
            ClarificationRequest(
                intent_id=uuid.uuid4(),
                session_id="session-1",
            )


# --- ClarificationResponse Tests ---


class TestClarificationResponse:
    """Example-based tests for ClarificationResponse schema. Validates: Requirements 24.2, 24.3"""

    def test_incomplete_response(self):
        resp = ClarificationResponse(
            complete=False,
            next_question="What size do you need?",
            questions_remaining=2,
            answered_questions=[],
        )
        assert resp.complete is False
        assert resp.next_question == "What size do you need?"
        assert resp.questions_remaining == 2
        assert resp.answered_questions == []

    def test_complete_response(self):
        resp = ClarificationResponse(
            complete=True,
            next_question=None,
            questions_remaining=0,
            answered_questions=[
                {"question": "What size do you need?", "answer": "Large"},
            ],
            bundle_context=BundleContext(
                intent_id=str(uuid.uuid4()),
                intent_type="add_to_cart",
                resolved_category="dairy_and_bakery",
                confirmed_entities=[],
                semantic_query="milk bread",
                category_query="dairy bakery",
                product_query_hints=["milk", "bread"],
            ),
        )
        assert resp.complete is True
        assert resp.next_question is None
        assert resp.questions_remaining == 0
        assert resp.answered_questions[0].question == "What size do you need?"
        assert resp.answered_questions[0].answer == "Large"
        assert resp.bundle_context is not None
        assert resp.bundle_context.resolved_category == "dairy_and_bakery"

    def test_complete_true_with_question_raises(self):
        """Requirement 24.3: complete=True requires next_question=None."""
        with pytest.raises(ValidationError, match="next_question must be None when complete is True"):
            ClarificationResponse(
                complete=True,
                next_question="Should not be here",
                questions_remaining=0,
            )

    def test_complete_true_with_questions_remaining_raises(self):
        """Requirement 24.3: complete=True requires questions_remaining=0."""
        with pytest.raises(ValidationError, match="questions_remaining must be 0 when complete is True"):
            ClarificationResponse(
                complete=True,
                next_question=None,
                questions_remaining=1,
            )

    def test_questions_remaining_min_value(self):
        with pytest.raises(ValidationError):
            ClarificationResponse(
                complete=False,
                next_question="Question?",
                questions_remaining=-1,
            )

    def test_questions_remaining_max_value(self):
        with pytest.raises(ValidationError):
            ClarificationResponse(
                complete=False,
                next_question="Question?",
                questions_remaining=4,
            )

    def test_questions_remaining_at_max(self):
        resp = ClarificationResponse(
            complete=False,
            next_question="Question?",
            questions_remaining=3,
        )
        assert resp.questions_remaining == 3

    def test_next_question_can_be_none_when_incomplete(self):
        """next_question=None is allowed when complete=False (edge case)."""
        resp = ClarificationResponse(
            complete=False,
            next_question=None,
            questions_remaining=0,
        )
        assert resp.next_question is None


# --- Serialization Round-Trip Tests ---


class TestClarificationResponseRoundTrip:
    """Tests for serialization round-trip. Validates: Requirement 24.4"""

    def test_round_trip_complete(self):
        original = ClarificationResponse(
            complete=True,
            next_question=None,
            questions_remaining=0,
            answered_questions=[
                {"question": "What size do you need?", "answer": "Large"},
            ],
            bundle_context=BundleContext(
                intent_id=str(uuid.uuid4()),
                intent_type="add_to_cart",
                resolved_category="dairy_and_bakery",
                confirmed_entities=[],
                semantic_query="milk bread",
                category_query="dairy bakery",
                product_query_hints=["milk", "bread"],
            ),
        )
        data = original.model_dump()
        reconstructed = ClarificationResponse(**data)
        assert reconstructed.complete == original.complete
        assert reconstructed.next_question == original.next_question
        assert reconstructed.questions_remaining == original.questions_remaining
        assert reconstructed.answered_questions == original.answered_questions
        assert reconstructed.bundle_context == original.bundle_context

    def test_round_trip_incomplete(self):
        original = ClarificationResponse(
            complete=False,
            next_question="What brand do you prefer?",
            questions_remaining=2,
            answered_questions=[
                {"question": "What category does the product belong to?", "answer": "Snacks"},
            ],
        )
        data = original.model_dump()
        reconstructed = ClarificationResponse(**data)
        assert reconstructed.complete == original.complete
        assert reconstructed.next_question == original.next_question
        assert reconstructed.questions_remaining == original.questions_remaining
        assert reconstructed.answered_questions == original.answered_questions
        assert reconstructed.bundle_context is None
