"""Unit tests for app/services/clarification_engine.py — Clarification Engine."""

import pytest

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


class TestClarificationMapCompleteness:
    """Tests for CLARIFICATION_MAP structure and content."""

    def test_max_clarification_questions_is_three(self):
        assert MAX_CLARIFICATION_QUESTIONS == 3

    def test_all_eight_intent_types_are_mapped(self):
        for intent_type in VALID_INTENT_TYPES:
            assert intent_type in CLARIFICATION_MAP

    def test_each_intent_has_at_least_three_questions(self):
        for intent_type in VALID_INTENT_TYPES:
            assert len(CLARIFICATION_MAP[intent_type]) >= 3

    def test_all_questions_are_non_empty_strings(self):
        for intent_type, questions in CLARIFICATION_MAP.items():
            for question in questions:
                assert isinstance(question, str)
                assert len(question.strip()) > 0


class TestGetFirstQuestion:
    """Tests for get_first_question()."""

    def test_returns_first_question_for_add_to_cart(self):
        result = get_first_question("add_to_cart")
        assert result == CLARIFICATION_MAP["add_to_cart"][0]

    def test_returns_first_question_for_checkout(self):
        result = get_first_question("checkout")
        assert result == CLARIFICATION_MAP["checkout"][0]

    def test_returns_string_for_all_valid_types(self):
        for intent_type in VALID_INTENT_TYPES:
            result = get_first_question(intent_type)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_raises_for_invalid_intent_type(self):
        with pytest.raises(AppException) as exc_info:
            get_first_question("invalid_type")
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"
        assert exc_info.value.status_code == 404

    def test_raises_for_empty_string(self):
        with pytest.raises(AppException) as exc_info:
            get_first_question("")
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"


class TestGetNextQuestion:
    """Tests for get_next_question()."""

    def test_returns_first_question_when_answered_zero(self):
        result = get_next_question("add_to_cart", 0)
        assert result == CLARIFICATION_MAP["add_to_cart"][0]

    def test_returns_second_question_when_answered_one(self):
        result = get_next_question("add_to_cart", 1)
        assert result == CLARIFICATION_MAP["add_to_cart"][1]

    def test_returns_third_question_when_answered_two(self):
        result = get_next_question("add_to_cart", 2)
        assert result == CLARIFICATION_MAP["add_to_cart"][2]

    def test_returns_none_when_answered_equals_max(self):
        result = get_next_question("add_to_cart", 3)
        assert result is None

    def test_returns_none_when_answered_exceeds_max(self):
        result = get_next_question("add_to_cart", 10)
        assert result is None

    def test_raises_for_invalid_intent_type(self):
        with pytest.raises(AppException) as exc_info:
            get_next_question("nonexistent", 0)
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"
        assert exc_info.value.status_code == 404

    def test_raises_for_invalid_type_even_when_answered_exceeds_max(self):
        """Invalid intent type should raise even if answered_count >= MAX."""
        with pytest.raises(AppException) as exc_info:
            get_next_question("invalid", 5)
        assert exc_info.value.error_code == "INTENT_NOT_FOUND"

    def test_works_for_all_valid_intent_types(self):
        for intent_type in VALID_INTENT_TYPES:
            result = get_next_question(intent_type, 0)
            assert isinstance(result, str)
            assert len(result) > 0
