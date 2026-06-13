"""Property-based tests for app/services/clarification_engine.py."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.exceptions import AppException
from app.services.clarification_engine import (
    CLARIFICATION_MAP,
    MAX_CLARIFICATION_QUESTIONS,
    get_first_question,
    get_next_question,
)

VALID_INTENT_TYPES = [
    "add_to_cart",
    "remove_from_cart",
    "search_product",
    "reorder",
    "substitute",
    "compare",
    "get_recommendation",
    "checkout",
]


class TestClarificationEngineQuestionRetrieval:
    """
    Property 9: Clarification Engine question retrieval.

    For any valid intent_type and any non-negative integer answered_count:
    if answered_count < MAX_CLARIFICATION_QUESTIONS (3), get_next_question()
    SHALL return a non-empty string equal to the question at index answered_count
    for that intent type. If answered_count >= 3, it SHALL return None.

    **Validates: Requirements 15.2, 15.3, 15.4**
    """

    @settings(max_examples=100)
    @given(
        intent_type=st.sampled_from(VALID_INTENT_TYPES),
        answered_count=st.integers(min_value=0, max_value=2),
    )
    def test_returns_correct_question_when_below_max(self, intent_type, answered_count):
        """
        **Validates: Requirements 15.2, 15.3, 15.4**

        When answered_count < MAX_CLARIFICATION_QUESTIONS, get_next_question
        returns the question at that index — a non-empty string.
        """
        result = get_next_question(intent_type, answered_count)
        expected = CLARIFICATION_MAP[intent_type][answered_count]
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == expected

    @settings(max_examples=100)
    @given(
        intent_type=st.sampled_from(VALID_INTENT_TYPES),
        answered_count=st.integers(min_value=3, max_value=1000),
    )
    def test_returns_none_when_at_or_above_max(self, intent_type, answered_count):
        """
        **Validates: Requirements 15.2, 15.3, 15.4**

        When answered_count >= MAX_CLARIFICATION_QUESTIONS, get_next_question
        returns None indicating clarification is complete.
        """
        result = get_next_question(intent_type, answered_count)
        assert result is None


class TestClarificationEngineMappingCompleteness:
    """
    Property 10: Clarification Engine mapping completeness.

    For any of the 8 defined intent types, the Clarification Engine SHALL have
    a mapped list of at least 3 clarification questions, where each question
    is a non-empty string.

    **Validates: Requirements 15.1**
    """

    @settings(max_examples=100)
    @given(intent_type=st.sampled_from(VALID_INTENT_TYPES))
    def test_each_intent_type_has_at_least_3_questions(self, intent_type):
        """
        **Validates: Requirements 15.1**

        Every valid intent type has at least MAX_CLARIFICATION_QUESTIONS
        non-empty string questions mapped.
        """
        questions = CLARIFICATION_MAP[intent_type]
        assert isinstance(questions, list)
        assert len(questions) >= MAX_CLARIFICATION_QUESTIONS
        for question in questions:
            assert isinstance(question, str)
            assert len(question) > 0


class TestClarificationEngineRejectsInvalidTypes:
    """
    Property 11: Clarification Engine rejects invalid types.

    For any string that is not one of the 8 defined intent types, any
    Clarification Engine method SHALL raise AppException with error code
    INTENT_NOT_FOUND.

    **Validates: Requirements 15.5**
    """

    @settings(max_examples=100)
    @given(
        invalid_type=st.text(min_size=0, max_size=100).filter(
            lambda s: s not in VALID_INTENT_TYPES
        ),
    )
    def test_get_first_question_raises_for_invalid_type(self, invalid_type):
        """
        **Validates: Requirements 15.5**

        get_first_question raises AppException with INTENT_NOT_FOUND
        for any string not in the valid intent types.
        """
        with pytest.raises(AppException) as exc_info:
            get_first_question(invalid_type)
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"

    @settings(max_examples=100)
    @given(
        invalid_type=st.text(min_size=0, max_size=100).filter(
            lambda s: s not in VALID_INTENT_TYPES
        ),
        answered_count=st.integers(min_value=0, max_value=10),
    )
    def test_get_next_question_raises_for_invalid_type(self, invalid_type, answered_count):
        """
        **Validates: Requirements 15.5**

        get_next_question raises AppException with INTENT_NOT_FOUND
        for any string not in the valid intent types, regardless of
        the answered_count value.
        """
        with pytest.raises(AppException) as exc_info:
            get_next_question(invalid_type, answered_count)
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"
