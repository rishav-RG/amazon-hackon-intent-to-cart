"""
Intent Engine — Hybrid classifier for user shopping intents.

Architecture (matches the Architecture Overview diagram):
    1. Validate input (unchanged)
    2. Keyword classifier (< 1ms)
        ├─ confidence ≥ 0.7 → fast path: return immediately
        └─ confidence < 0.7
              ├─ Check semantic/LLM result cache (Redis)
              │     hit → return cached result
              └─ miss
                    ├─ Semantic model (async, 3s timeout)
                    │     success → cache + return
                    └─ timeout/error
                          fallback to keyword result → return

The ClassificationResult now includes:
    - llm_used: bool — whether semantic model was invoked
    - fallback: bool — whether keyword fallback was used after semantic failure
"""

import logging
from dataclasses import dataclass, field

from app.exceptions import AppException, INVALID_INTENT_TEXT

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of intent classification."""

    intent_type: str
    confidence: float
    entities: list[str] = field(default_factory=list)
    llm_used: bool = False
    fallback: bool = False


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
    Classify raw text using keyword matching (fast path).

    This is the synchronous keyword-only classifier. For the full hybrid
    flow (keyword → semantic fallback), use `classify_hybrid()`.

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
            llm_used=False,
            fallback=False,
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
        llm_used=False,
        fallback=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Hybrid Classifier (Keyword + Semantic Fallback)
# ──────────────────────────────────────────────────────────────────────────────

FAST_PATH_THRESHOLD = 0.7


async def classify_hybrid(raw_text: str) -> ClassificationResult:
    """
    Hybrid intent classification matching the Architecture Overview diagram:

        1. Validate input (unchanged)
        2. Keyword classifier (< 1ms)
            ├─ confidence ≥ 0.7 → fast path: return immediately
            └─ confidence < 0.7
                  ├─ Check LLM result cache (Redis)
                  │     hit → return cached result
                  └─ miss
                        ├─ LLM client (async, 3s timeout)
                        │     success → cache + return
                        └─ timeout/error
                              fallback to keyword result → return

    Returns:
        ClassificationResult with llm_used and fallback flags set accordingly.
    """
    # Step 1-7: Run keyword classifier first (always, < 1ms)
    keyword_result = classify(raw_text)

    # Fast path: high confidence keyword match
    if keyword_result.confidence >= FAST_PATH_THRESHOLD:
        logger.debug(
            "Fast path: keyword confidence %.2f ≥ %.2f for '%s...'",
            keyword_result.confidence, FAST_PATH_THRESHOLD, raw_text[:30]
        )
        return keyword_result

    # Slow path: keyword confidence is low, invoke LLM classifier
    logger.info(
        "Low keyword confidence (%.2f) — invoking LLM classifier for '%s...'",
        keyword_result.confidence, raw_text[:50]
    )

    try:
        from app.services.llm_client import classify_intent_llm

        llm_result = await classify_intent_llm(raw_text)

        if llm_result is not None and llm_result.get("confidence", 0) >= 0.4:
            # LLM returned a usable result
            # Merge entities: LLM entities + keyword entities (deduplicated)
            llm_entities = llm_result.get("entities", [])
            keyword_entities = keyword_result.entities
            merged_entities = list(dict.fromkeys(llm_entities + keyword_entities))

            return ClassificationResult(
                intent_type=llm_result["intent_type"],
                confidence=llm_result["confidence"],
                entities=merged_entities,
                llm_used=True,
                fallback=False,
            )
        else:
            # LLM result too low confidence or None — try semantic, then keyword
            logger.info(
                "LLM result insufficient (got: %s) — trying semantic fallback",
                llm_result,
            )
    except Exception as exc:
        logger.error("LLM classifier error: %s — trying semantic fallback", exc)

    # Secondary fallback: semantic classifier (if sentence-transformers available)
    try:
        from app.services.semantic_classifier import classify_semantic

        semantic_result = await classify_semantic(raw_text)

        if semantic_result is not None and semantic_result["confidence"] >= 0.4:
            entities = keyword_result.entities
            return ClassificationResult(
                intent_type=semantic_result["intent_type"],
                confidence=semantic_result["confidence"],
                entities=entities,
                llm_used=True,  # semantic model counts as "llm_used" in response
                fallback=False,
            )
    except ImportError:
        logger.debug("sentence-transformers not installed, skipping semantic fallback")
    except Exception as exc:
        logger.error("Semantic classifier error: %s", exc)

    # Final fallback: return keyword result
    logger.info("All fallbacks exhausted — using keyword result")
    keyword_result.fallback = True
    return keyword_result
