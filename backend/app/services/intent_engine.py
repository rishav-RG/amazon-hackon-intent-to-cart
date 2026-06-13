"""
Intent Engine — Keyword-based classifier for user shopping intents.

Classifies raw text into one of 8 intent types using keyword overlap scoring,
computes a confidence score, and extracts noun-phrase entities.
"""

from dataclasses import dataclass, field

from app.exceptions import AppException, INVALID_INTENT_TEXT


@dataclass
class ClassificationResult:
    """Result of intent classification."""

    intent_type: str
    confidence: float
    entities: list[str] = field(default_factory=list)


INTENT_TYPES: list[str] = [
    "add_to_cart",
    "remove_from_cart",
    "search_product",
    "reorder",
    "substitute",
    "compare",
    "get_recommendation",
    "checkout",
]

KEYWORD_MAP: dict[str, list[str]] = {
    "add_to_cart": [
        "add", "cart", "buy", "purchase", "want", "get", "order", "put",
        "include", "grab",
    ],
    "remove_from_cart": [
        "remove", "delete", "drop", "take out", "discard", "cancel",
        "unwant", "exclude",
    ],
    "search_product": [
        "search", "find", "look", "browse", "show", "display", "list",
        "explore", "discover",
    ],
    "reorder": [
        "reorder", "again", "repeat", "same", "previous", "last",
        "usual", "regular",
    ],
    "substitute": [
        "substitute", "replace", "swap", "alternative", "instead",
        "switch", "exchange",
    ],
    "compare": [
        "compare", "versus", "vs", "difference", "better", "which",
        "between", "match",
    ],
    "get_recommendation": [
        "recommend", "suggest", "recommendation", "suggestion", "best",
        "popular", "top", "trending",
    ],
    "checkout": [
        "checkout", "pay", "complete", "finish", "proceed", "confirm",
        "place order", "submit",
    ],
}


def _extract_entities(tokens: list[str]) -> list[str]:
    """
    Extract noun-phrase entities from tokenized text.

    Uses a simple heuristic: collects sequences of tokens that are not
    common stop words or keywords (likely noun phrases representing
    product names or descriptors).
    """
    stop_words = {
        "i", "me", "my", "we", "our", "you", "your", "the", "a", "an",
        "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "shall", "can", "to", "of", "in", "for", "on",
        "with", "at", "by", "from", "and", "or", "but", "not", "no",
        "if", "then", "so", "that", "this", "it", "its", "some", "any",
        "all", "each", "every", "both", "few", "more", "most", "other",
        "into", "about", "up", "out", "off", "over", "under", "again",
        "there", "here", "when", "where", "how", "what", "who", "whom",
        "which", "than", "too", "very", "just", "also", "please",
    }

    # Collect all keywords from the keyword map as a flat set
    all_keywords = set()
    for keywords in KEYWORD_MAP.values():
        for kw in keywords:
            all_keywords.update(kw.split())

    # Build noun phrases: sequences of non-stop, non-keyword tokens
    entities: list[str] = []
    current_phrase: list[str] = []

    for token in tokens:
        if token not in stop_words and token not in all_keywords and token.isalpha():
            current_phrase.append(token)
        else:
            if current_phrase:
                entities.append(" ".join(current_phrase))
                current_phrase = []

    if current_phrase:
        entities.append(" ".join(current_phrase))

    return entities


def classify(raw_text: str) -> ClassificationResult:
    """
    Classify raw text into an intent type using keyword matching.

    Algorithm:
    1. Validate text (1-500 chars after strip, not whitespace-only)
    2. Lowercase and tokenize
    3. Score each intent type by keyword overlap count
    4. Select highest-scoring type (first in list order for ties)
    5. Compute confidence as matched_keywords / total_keywords ratio (capped at 1.0)
    6. Extract noun-phrase entities
    7. Return ClassificationResult

    Raises:
        AppException: With error code INVALID_INTENT_TEXT if text is
            empty, whitespace-only, or exceeds 500 chars after trimming.

    Returns:
        ClassificationResult with "search_product", confidence 0.0, and
        empty entities if no keywords match any intent type.
    """
    # Step 1: Validate input
    if not isinstance(raw_text, str):
        raise AppException(
            INVALID_INTENT_TEXT[0],
            "Intent text must be a non-empty string.",
            INVALID_INTENT_TEXT[1],
        )

    stripped = raw_text.strip()

    if not stripped:
        raise AppException(
            INVALID_INTENT_TEXT[0],
            "Intent text must not be empty or whitespace-only.",
            INVALID_INTENT_TEXT[1],
        )

    if len(stripped) > 500:
        raise AppException(
            INVALID_INTENT_TEXT[0],
            "Intent text must not exceed 500 characters.",
            INVALID_INTENT_TEXT[1],
        )

    # Step 2: Lowercase and tokenize
    lowered = stripped.lower()
    tokens = lowered.split()

    # Step 3: Score each intent type by keyword overlap
    scores: dict[str, int] = {}
    for intent_type in INTENT_TYPES:
        keywords = KEYWORD_MAP[intent_type]
        score = 0
        for keyword in keywords:
            # Support multi-word keywords (e.g., "take out", "place order")
            if " " in keyword:
                if keyword in lowered:
                    score += 1
            else:
                if keyword in tokens:
                    score += 1
        scores[intent_type] = score

    # Step 4: Select highest score (first in list order for ties)
    best_type = INTENT_TYPES[0]
    best_score = scores[INTENT_TYPES[0]]
    for intent_type in INTENT_TYPES[1:]:
        if scores[intent_type] > best_score:
            best_type = intent_type
            best_score = scores[intent_type]

    # Step 5: Handle no-match fallback
    if best_score == 0:
        return ClassificationResult(
            intent_type="search_product",
            confidence=0.0,
            entities=[],
        )

    # Step 6: Compute confidence as matched_keywords / total_keywords (capped at 1.0)
    total_keywords = len(KEYWORD_MAP[best_type])
    confidence = min(best_score / total_keywords, 1.0)

    # Step 7: Extract noun-phrase entities
    entities = _extract_entities(tokens)

    return ClassificationResult(
        intent_type=best_type,
        confidence=confidence,
        entities=entities,
    )
