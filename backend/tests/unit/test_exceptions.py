"""Unit tests for app/exceptions.py — AppException and error code constants."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.exceptions import (
    AppException,
    CART_VERSION_CONFLICT,
    CLARIFICATION_NOT_FOUND,
    DB_CONNECTION_ERROR,
    INTENT_NOT_FOUND,
    INVALID_INTENT_TEXT,
    REDIS_CONNECTION_ERROR,
    SESSION_EXPIRED,
    VALIDATION_ERROR,
)


# --- Unit Tests ---


class TestAppException:
    """Example-based tests for AppException."""

    def test_basic_construction(self):
        exc = AppException(error_code="TEST_ERROR", message="Something went wrong", status_code=400)
        assert exc.error_code == "TEST_ERROR"
        assert exc.message == "Something went wrong"
        assert exc.status_code == 400

    def test_inherits_from_exception(self):
        exc = AppException(error_code="ERR", message="msg", status_code=500)
        assert isinstance(exc, Exception)

    def test_str_representation(self):
        exc = AppException(error_code="ERR", message="a message", status_code=404)
        assert str(exc) == "a message"

    def test_error_code_max_64_chars(self):
        code = "A" * 64
        exc = AppException(error_code=code, message="ok", status_code=400)
        assert exc.error_code == code

    def test_error_code_over_64_chars_raises(self):
        with pytest.raises(ValueError, match="error_code must be at most 64 characters"):
            AppException(error_code="A" * 65, message="ok", status_code=400)

    def test_message_max_500_chars(self):
        msg = "B" * 500
        exc = AppException(error_code="ERR", message=msg, status_code=400)
        assert exc.message == msg

    def test_message_over_500_chars_raises(self):
        with pytest.raises(ValueError, match="message must be at most 500 characters"):
            AppException(error_code="ERR", message="B" * 501, status_code=400)

    def test_status_code_lower_bound(self):
        exc = AppException(error_code="ERR", message="msg", status_code=400)
        assert exc.status_code == 400

    def test_status_code_upper_bound(self):
        exc = AppException(error_code="ERR", message="msg", status_code=599)
        assert exc.status_code == 599

    def test_status_code_below_400_raises(self):
        with pytest.raises(ValueError, match="status_code must be between 400 and 599"):
            AppException(error_code="ERR", message="msg", status_code=399)

    def test_status_code_above_599_raises(self):
        with pytest.raises(ValueError, match="status_code must be between 400 and 599"):
            AppException(error_code="ERR", message="msg", status_code=600)


class TestErrorCodeConstants:
    """Tests that error code constants are correctly defined as (code, status) tuples."""

    def test_intent_not_found(self):
        assert INTENT_NOT_FOUND == ("INTENT_NOT_FOUND", 404)

    def test_clarification_not_found(self):
        assert CLARIFICATION_NOT_FOUND == ("CLARIFICATION_NOT_FOUND", 404)

    def test_session_expired(self):
        assert SESSION_EXPIRED == ("SESSION_EXPIRED", 410)

    def test_invalid_intent_text(self):
        assert INVALID_INTENT_TEXT == ("INVALID_INTENT_TEXT", 422)

    def test_db_connection_error(self):
        assert DB_CONNECTION_ERROR == ("DB_CONNECTION_ERROR", 503)

    def test_redis_connection_error(self):
        assert REDIS_CONNECTION_ERROR == ("REDIS_CONNECTION_ERROR", 503)

    def test_validation_error(self):
        assert VALIDATION_ERROR == ("VALIDATION_ERROR", 422)

    def test_cart_version_conflict(self):
        assert CART_VERSION_CONFLICT == ("CART_VERSION_CONFLICT", 409)

    def test_all_constants_are_tuples_of_str_and_int(self):
        constants = [
            INTENT_NOT_FOUND,
            CLARIFICATION_NOT_FOUND,
            SESSION_EXPIRED,
            INVALID_INTENT_TEXT,
            DB_CONNECTION_ERROR,
            REDIS_CONNECTION_ERROR,
            VALIDATION_ERROR,
            CART_VERSION_CONFLICT,
        ]
        for const in constants:
            assert isinstance(const, tuple)
            assert len(const) == 2
            assert isinstance(const[0], str)
            assert isinstance(const[1], int)
            assert 400 <= const[1] <= 599

    def test_error_code_strings_within_64_chars(self):
        constants = [
            INTENT_NOT_FOUND,
            CLARIFICATION_NOT_FOUND,
            SESSION_EXPIRED,
            INVALID_INTENT_TEXT,
            DB_CONNECTION_ERROR,
            REDIS_CONNECTION_ERROR,
            VALIDATION_ERROR,
            CART_VERSION_CONFLICT,
        ]
        for const in constants:
            assert len(const[0]) <= 64

    def test_constants_usable_with_appexception(self):
        """Error code constants can be used to construct AppException instances."""
        code, status = INTENT_NOT_FOUND
        exc = AppException(error_code=code, message="Intent not found", status_code=status)
        assert exc.error_code == "INTENT_NOT_FOUND"
        assert exc.status_code == 404


# --- Property-Based Tests ---


class TestAppExceptionProperties:
    """
    Property-based tests for AppException.
    Validates: Requirements 4.1, 4.3, 4.5
    """

    @settings(max_examples=100)
    @given(
        error_code=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
        message=st.text(min_size=1, max_size=500),
        status_code=st.integers(min_value=400, max_value=599),
    )
    def test_valid_construction_always_succeeds(self, error_code, message, status_code):
        """
        **Validates: Requirements 4.1**
        For any valid error_code (1-64 chars), message (1-500 chars), and
        status_code (400-599), AppException construction succeeds and fields
        are stored correctly.
        """
        exc = AppException(error_code=error_code, message=message, status_code=status_code)
        assert exc.error_code == error_code
        assert exc.message == message
        assert exc.status_code == status_code

    @settings(max_examples=50)
    @given(
        error_code=st.text(min_size=65, max_size=200),
        message=st.text(min_size=1, max_size=500),
        status_code=st.integers(min_value=400, max_value=599),
    )
    def test_error_code_over_64_always_raises(self, error_code, message, status_code):
        """
        **Validates: Requirements 4.1**
        error_code exceeding 64 characters always raises ValueError.
        """
        with pytest.raises(ValueError):
            AppException(error_code=error_code, message=message, status_code=status_code)

    @settings(max_examples=50)
    @given(
        error_code=st.text(min_size=1, max_size=64),
        message=st.text(min_size=501, max_size=1000),
        status_code=st.integers(min_value=400, max_value=599),
    )
    def test_message_over_500_always_raises(self, error_code, message, status_code):
        """
        **Validates: Requirements 4.1**
        message exceeding 500 characters always raises ValueError.
        """
        with pytest.raises(ValueError):
            AppException(error_code=error_code, message=message, status_code=status_code)

    @settings(max_examples=50)
    @given(
        error_code=st.text(min_size=1, max_size=64),
        message=st.text(min_size=1, max_size=500),
        status_code=st.one_of(
            st.integers(min_value=-1000, max_value=399),
            st.integers(min_value=600, max_value=2000),
        ),
    )
    def test_status_code_outside_range_always_raises(self, error_code, message, status_code):
        """
        **Validates: Requirements 4.1**
        status_code outside 400-599 always raises ValueError.
        """
        with pytest.raises(ValueError):
            AppException(error_code=error_code, message=message, status_code=status_code)
