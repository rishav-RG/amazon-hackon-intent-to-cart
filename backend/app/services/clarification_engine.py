"""
Clarification Engine — Question sequences for intent disambiguation.

Provides a mapping of intent types to clarification questions and
functions to retrieve questions in sequence during a clarification dialogue.
"""

from app.exceptions import AppException, INTENT_NOT_FOUND

MAX_CLARIFICATION_QUESTIONS = 3

# Mapping: intent_type -> list of clarification questions (≥3 each)
CLARIFICATION_MAP: dict[str, list[str]] = {
    "add_to_cart": [
        "What specific product are you looking for?",
        "How many units would you like to add?",
        "Do you have a preferred brand or variant?",
    ],
    "remove_from_cart": [
        "Which item would you like to remove from your cart?",
        "Would you like to remove all units or just reduce the quantity?",
        "Is there a reason you'd like to remove this item?",
    ],
    "search_product": [
        "What category does the product belong to?",
        "Do you have a preferred price range?",
        "Are there any specific features you're looking for?",
    ],
    "reorder": [
        "Which previous order would you like to reorder from?",
        "Would you like to reorder all items or select specific ones?",
        "Should I use the same delivery address as before?",
    ],
    "substitute": [
        "Which product would you like to find a substitute for?",
        "Do you have any preferences for the substitute (brand, price)?",
        "Are there any ingredients or features to avoid?",
    ],
    "compare": [
        "Which products would you like to compare?",
        "What features are most important to you in this comparison?",
        "Do you have a budget limit for the comparison?",
    ],
    "get_recommendation": [
        "What type of product are you looking for recommendations on?",
        "Is this for personal use or a gift?",
        "Do you have a preferred price range for recommendations?",
    ],
    "checkout": [
        "Would you like to use your saved payment method?",
        "Should I apply any available coupons or promotions?",
        "Would you like standard or express delivery?",
    ],
}


def get_first_question(intent_type: str) -> str:
    """
    Return the first clarification question for the given intent type.

    Raises:
        AppException: With INTENT_NOT_FOUND if intent_type is not in CLARIFICATION_MAP.
    """
    if intent_type not in CLARIFICATION_MAP:
        raise AppException(
            error_code=INTENT_NOT_FOUND[0],
            message=f"Intent type '{intent_type}' is not recognized",
            status_code=INTENT_NOT_FOUND[1],
        )
    return CLARIFICATION_MAP[intent_type][0]


def get_next_question(intent_type: str, answered_count: int) -> str | None:
    """
    Return the next static clarification question or None if complete.

    This is the fallback when LLM-generated questions are unavailable.
    For LLM-powered contextual questions, use get_next_question_smart().

    Args:
        intent_type: The type of intent being clarified.
        answered_count: Number of questions already answered.

    Returns:
        The question at index answered_count, or None if answered_count >= MAX_CLARIFICATION_QUESTIONS.

    Raises:
        AppException: With INTENT_NOT_FOUND if intent_type is not in CLARIFICATION_MAP.
    """
    if intent_type not in CLARIFICATION_MAP:
        raise AppException(
            error_code=INTENT_NOT_FOUND[0],
            message=f"Intent type '{intent_type}' is not recognized",
            status_code=INTENT_NOT_FOUND[1],
        )
    if answered_count >= MAX_CLARIFICATION_QUESTIONS:
        return None
    return CLARIFICATION_MAP[intent_type][answered_count]


async def get_next_question_smart(
    user_text: str,
    intent_type: str,
    confidence: float,
    entities: list[str],
    previous_questions: list[str],
    answered_count: int,
) -> str | None:
    """
    Generate a contextual clarification question using Gemini LLM.
    Falls back to static CLARIFICATION_MAP if LLM is unavailable.

    Architecture (from diagram):
        entities present AND intent high-confidence?
            YES → skip or ask only missing fields
            NO →
                LLM available? → generate contextual question
                LLM unavailable? → static CLARIFICATION_MAP fallback

    Args:
        user_text: Original user input text
        intent_type: Classified intent type
        confidence: Classification confidence score
        entities: Extracted entities from the text
        previous_questions: Questions already asked in this session
        answered_count: Number of questions already answered

    Returns:
        A clarification question string, or None if clarification is complete.
    """
    import logging
    _logger = logging.getLogger(__name__)

    # Check if max questions reached
    if answered_count >= MAX_CLARIFICATION_QUESTIONS:
        return None

    # If intent type not recognized, reject
    if intent_type not in CLARIFICATION_MAP:
        raise AppException(
            error_code=INTENT_NOT_FOUND[0],
            message=f"Intent type '{intent_type}' is not recognized",
            status_code=INTENT_NOT_FOUND[1],
        )

    # Smart skip: if entities cover the question topic, skip it
    if entities and confidence >= 0.5 and answered_count == 0:
        static_q = CLARIFICATION_MAP[intent_type][0]
        quantity_words = {"1", "2", "3", "4", "5", "kg", "litre", "pack", "dozen"}
        has_quantity = any(
            word in " ".join(entities).lower() for word in quantity_words
        )
        if has_quantity and "how many" in static_q.lower():
            answered_count += 1
            if answered_count >= MAX_CLARIFICATION_QUESTIONS:
                return None

    # Try LLM-generated question
    try:
        from app.services.llm_client import generate_clarification_question

        llm_question = await generate_clarification_question(
            user_text=user_text,
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            previous_questions=previous_questions,
        )

        if llm_question:
            return llm_question
    except ImportError:
        _logger.debug("google-generativeai not installed, using static fallback")
    except Exception as exc:
        _logger.warning(
            "LLM clarification generation failed: %s — using static fallback", exc
        )

    # Fallback to static question
    if answered_count < len(CLARIFICATION_MAP[intent_type]):
        return CLARIFICATION_MAP[intent_type][answered_count]
    return None
