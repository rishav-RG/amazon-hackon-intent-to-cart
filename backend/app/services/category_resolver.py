"""
Category Resolver — maps a generic shopping_theme to a catalog category.

Loads pre-computed category embeddings (built by scripts/build_seed_data.py)
once at startup and resolves themes via:
    1. keyword fast-path (category_keywords.json)
    2. cosine similarity against category embeddings

Falls back to "meal_preparation" (most populated category) if nothing matches
or if the theme is None/empty.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).parent.parent.parent / "seed_data"
CATEGORY_EMBEDDINGS_PATH = SEED_DIR / "category_embeddings.npy"
CATEGORY_ORDER_PATH = SEED_DIR / "category_order.json"
CATEGORY_KEYWORDS_PATH = SEED_DIR / "category_keywords.json"

DEFAULT_CATEGORY = "meal_preparation"
MIN_COSINE_ACCEPT = 0.25  # below this, fall back to default


class _CategoryResolver:
    """Singleton holder for category embeddings + resolution logic."""

    def __init__(self) -> None:
        self._embeddings: Optional[np.ndarray] = None
        self._order: list[str] = []
        self._keywords: dict[str, list[str]] = {}
        self._model = None
        self._ready = False

    # ── startup warmup ──
    def warmup(self) -> None:
        """Load embeddings + keyword map. Safe to call multiple times."""
        if self._ready:
            return
        try:
            self._embeddings = np.load(CATEGORY_EMBEDDINGS_PATH)
            with open(CATEGORY_ORDER_PATH, "r", encoding="utf-8") as f:
                self._order = json.load(f)
            if CATEGORY_KEYWORDS_PATH.exists():
                with open(CATEGORY_KEYWORDS_PATH, "r", encoding="utf-8") as f:
                    self._keywords = json.load(f)
            self._ready = True
            logger.info(
                "CategoryResolver warmed up: %d categories %s",
                len(self._order), self._order,
            )
        except Exception as exc:
            logger.warning("CategoryResolver warmup failed: %s", exc)
            self._ready = False

    def _get_model(self):
        """Lazy-load the sentence-transformer (shared model name)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _keyword_match(self, theme: str) -> Optional[str]:
        """Fast-path: direct keyword containment."""
        theme_l = theme.lower()
        best_cat, best_hits = None, 0
        for cat, words in self._keywords.items():
            hits = sum(1 for w in words if w in theme_l)
            if hits > best_hits:
                best_cat, best_hits = cat, hits
        return best_cat if best_hits > 0 else None

    def resolve(self, theme: Optional[str]) -> str:
        """
        Resolve a shopping_theme to a catalog category.

        Returns DEFAULT_CATEGORY when theme is None/empty, embeddings are
        unavailable, or no category clears MIN_COSINE_ACCEPT.
        """
        if not theme or not theme.strip():
            return DEFAULT_CATEGORY

        if not self._ready:
            self.warmup()
        if not self._ready or self._embeddings is None:
            return DEFAULT_CATEGORY

        # 1. keyword fast-path
        kw = self._keyword_match(theme)
        if kw is not None:
            logger.debug("Category resolved via keyword: %s -> %s", theme, kw)
            return kw

        # 2. cosine similarity
        try:
            model = self._get_model()
            q = model.encode(theme.replace("_", " "))
            norms = np.linalg.norm(self._embeddings, axis=1)
            qn = np.linalg.norm(q)
            denom = norms * qn
            denom[denom == 0] = 1e-10
            sims = np.dot(self._embeddings, q) / denom
            best_idx = int(np.argmax(sims))
            best_score = float(sims[best_idx])
            if best_score >= MIN_COSINE_ACCEPT:
                resolved = self._order[best_idx]
                logger.debug(
                    "Category resolved via cosine: %s -> %s (%.3f)",
                    theme, resolved, best_score,
                )
                return resolved
        except Exception as exc:
            logger.warning("Category cosine resolution failed: %s", exc)

        return DEFAULT_CATEGORY


# Module-level singleton
_resolver = _CategoryResolver()


def warmup() -> None:
    """Pre-load category embeddings at app startup."""
    _resolver.warmup()


def resolve(theme: Optional[str]) -> str:
    """Resolve a shopping_theme to a catalog category (never raises)."""
    try:
        return _resolver.resolve(theme)
    except Exception as exc:
        logger.warning("CategoryResolver.resolve fatal: %s — using default", exc)
        return DEFAULT_CATEGORY
