"""
Semantic Intent Classifier — Sentence embedding fallback for low-confidence keywords.

Uses sentence-transformers to compute cosine similarity between user input
and pre-computed intent description embeddings. Runs locally (no API key required).

Architecture:
    Keyword confidence < 0.7
        → Check Redis cache (key: semantic_intent:{text_hash})
        → Cache hit: return cached result
        → Cache miss: compute embedding similarity
        → Cache result (TTL 3600s)
        → Return

Timeout: 3 seconds max for embedding computation.
Fallback: Returns None on any failure (caller uses keyword result).
"""

import asyncio
import hashlib
import json
import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Model Initialization (loaded once at module import / first use)
# ──────────────────────────────────────────────────────────────────────────────

_model: Optional[SentenceTransformer] = None
_intent_embeddings: Optional[dict[str, np.ndarray]] = None

# Rich intent descriptions for embedding (more context = better similarity)
INTENT_DESCRIPTIONS: dict[str, str] = {
    "add_to_cart": (
        "I want to add items products to my shopping cart. "
        "Buy purchase get grab put include order things."
    ),
    "remove_from_cart": (
        "I want to remove delete take out items from my cart. "
        "Discard cancel unwant exclude drop."
    ),
    "search_product": (
        "I want to search find look for browse discover explore products. "
        "Show me display list what options are available."
    ),
    "reorder": (
        "I want to reorder buy again repeat my previous last usual regular order. "
        "Same items as before."
    ),
    "substitute": (
        "I want a substitute replacement alternative swap exchange instead of. "
        "Replace this product with something similar."
    ),
    "compare": (
        "I want to compare products versus vs difference between which is better. "
        "Compare options features prices."
    ),
    "get_recommendation": (
        "I want recommendations suggestions what should I buy popular trending best. "
        "Recommend suggest top rated products for me."
    ),
    "checkout": (
        "I want to checkout pay complete finish proceed confirm place order submit. "
        "Ready to pay finalize my purchase."
    ),
}

SEMANTIC_CACHE_TTL = 3600  # 1 hour
SEMANTIC_TIMEOUT = 3.0  # seconds
CONFIDENCE_THRESHOLD = 0.7  # minimum semantic confidence to accept


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully.")
    return _model


def _get_intent_embeddings() -> dict[str, np.ndarray]:
    """Compute and cache intent description embeddings."""
    global _intent_embeddings
    if _intent_embeddings is None:
        model = _get_model()
        _intent_embeddings = {
            intent_type: model.encode(description)
            for intent_type, description in INTENT_DESCRIPTIONS.items()
        }
        logger.info("Intent embeddings pre-computed for %d types.", len(_intent_embeddings))
    return _intent_embeddings


def _compute_text_hash(text: str) -> str:
    """Generate a short hash for cache key."""
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()[:16]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _classify_sync(text: str) -> dict:
    """
    Synchronous embedding-based classification.
    
    Returns dict with intent_type, confidence, method="semantic".
    """
    model = _get_model()
    intent_embeddings = _get_intent_embeddings()

    # Encode user text
    user_embedding = model.encode(text)

    # Compute similarity against all intents
    scores: dict[str, float] = {}
    for intent_type, intent_emb in intent_embeddings.items():
        scores[intent_type] = _cosine_similarity(user_embedding, intent_emb)

    # Pick best match
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Normalize confidence to 0.0-1.0 range
    # Cosine similarity for sentence embeddings typically ranges 0.2-0.9
    # Map [0.3, 0.85] → [0.0, 1.0] with clamping
    normalized = (best_score - 0.3) / (0.85 - 0.3)
    confidence = max(0.0, min(1.0, normalized))

    return {
        "intent_type": best_type,
        "confidence": round(confidence, 4),
        "method": "semantic",
        "raw_similarity": round(best_score, 4),
    }


async def classify_semantic(text: str) -> Optional[dict]:
    """
    Async semantic classification with Redis caching and timeout.

    Flow:
        1. Check Redis cache → return on hit
        2. Run embedding model (with 3s timeout)
        3. Cache result → return
        4. On any failure → return None (caller falls back to keyword)

    Returns:
        dict with {intent_type, confidence, method} or None on failure/timeout.
    """
    cache_key = f"semantic_intent:{_compute_text_hash(text)}"

    # Step 1: Check Redis cache
    try:
        cached = await cache_get(cache_key)
        if cached is not None:
            logger.debug("Semantic cache hit for: %s", cache_key)
            cached["cache_hit"] = True
            return cached
    except Exception as exc:
        logger.warning("Semantic cache read failed: %s", exc)

    # Step 2: Run embedding model with timeout
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _classify_sync, text),
            timeout=SEMANTIC_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Semantic classification timed out (%.1fs) for text: %s...", SEMANTIC_TIMEOUT, text[:50])
        return None
    except Exception as exc:
        logger.error("Semantic classification failed: %s", exc)
        return None

    # Step 3: Cache result
    try:
        await cache_set(cache_key, result, SEMANTIC_CACHE_TTL)
    except Exception as exc:
        logger.warning("Semantic cache write failed: %s", exc)

    result["cache_hit"] = False
    return result
