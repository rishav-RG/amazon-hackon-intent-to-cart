"""Property-based tests for app/services/intent_engine.py."""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.intent_engine import (
    classify,
    ClassificationResult,
    KEYWORD_MAP,
    INTENT_TYPES,
)


# Flatten all keywords from the keyword map for filtering
ALL_KEYWORDS: list[str] = []
for keywords in KEYWORD_MAP.values():
    ALL_KEYWORDS.extend(keywords)

# Separate single-word and multi-word keywords
SINGLE_WORD_KEYWORDS = {kw for kw in ALL_KEYWORDS if " " not in kw}
MULTI_WORD_KEYWORDS = {kw for kw in ALL_KEYWORDS if " " in kw}

# Safe alphabet that won't accidentally form keywords
# Use short nonsense syllables that don't appear in any keyword
SAFE_WORDS = [
    "zyx", "qwp", "mxn", "jkf", "tvb", "plq", "hgw", "rnz",
    "dkm", "bft", "xvl", "ywq", "zpn", "kgr", "mjt", "nxf",
    "wlp", "cvz", "fhq", "gdb",
]


def _text_contains_keyword(text: str) -> bool:
    """Check if lowercased text contains any keyword from KEYWORD_MAP."""
    lowered = text.lower()
    tokens = lowered.split()

    # Check multi-word keywords against the full string
    for kw in MULTI_WORD_KEYWORDS:
        if kw in lowered:
            return True

    # Check single-word keywords against individual tokens
    for token in tokens:
        if token in SINGLE_WORD_KEYWORDS:
            return True

    return False


# Strategy: generate text from safe words that won't match any keyword
@st.composite
def no_keyword_text(draw):
    """
    Generate valid input strings (1-500 chars, non-whitespace) that contain
    none of the defined keywords for any intent type.

    Uses a set of safe nonsense words that cannot match any keyword.
    """
    num_words = draw(st.integers(min_value=1, max_value=20))
    words = draw(
        st.lists(
            st.sampled_from(SAFE_WORDS),
            min_size=num_words,
            max_size=num_words,
        )
    )
    text = " ".join(words)
    # Ensure within 500 char limit
    if len(text) > 500:
        text = text[:500].rstrip()
    assume(len(text) >= 1 and not text.isspace())
    assume(not _text_contains_keyword(text))
    return text


class TestIntentEngineKeywordFallback:
    """
    Property 6: Intent Engine keyword fallback.

    For any valid input string (1-500 chars, non-whitespace) that contains
    none of the defined keywords for any intent type, `classify()` SHALL
    return intent_type "search_product" with confidence 0.0 and an empty
    entities list.

    **Validates: Requirements 13.5**
    """

    @settings(max_examples=100)
    @given(text=no_keyword_text())
    def test_no_keyword_match_returns_search_product_fallback(self, text):
        """
        **Validates: Requirements 13.5**

        When text contains no keywords matching any intent type, classify()
        returns "search_product" with confidence 0.0 and empty entities.
        """
        result = classify(text)

        assert isinstance(result, ClassificationResult)
        assert result.intent_type == "search_product"
        assert result.confidence == 0.0
        assert result.entities == []
