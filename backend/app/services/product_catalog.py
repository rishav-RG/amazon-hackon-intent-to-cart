"""
Product Catalog Service — Semantic search over BigBasket products.

Loads curated product catalog and pre-computed embeddings at startup.
Provides fast semantic search (< 5ms for 150 products) and category filtering.

Used by BundleGenerator to find relevant products for bundle creation.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

SEED_DIR = Path(__file__).parent.parent.parent / "seed_data"
CATALOG_PATH = SEED_DIR / "bigbasket_catalog.json"
EMBEDDINGS_PATH = SEED_DIR / "product_embeddings.npy"
SUBSTITUTIONS_PATH = SEED_DIR / "auto_substitutions.json"
CATEGORY_MAPPING_PATH = SEED_DIR / "category_mapping.json"

# ──────────────────────────────────────────────────────────────────────────────
# Singleton Catalog
# ──────────────────────────────────────────────────────────────────────────────

_catalog_instance: Optional["ProductCatalog"] = None


def get_product_catalog() -> "ProductCatalog":
    """Get or create the singleton ProductCatalog instance."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = ProductCatalog()
    return _catalog_instance


class ProductCatalog:
    """
    In-memory product catalog with semantic search capabilities.

    Loaded once at startup. Provides:
    - semantic_search(query, top_k) → products ranked by cosine similarity
    - get_by_intent(intent_type, limit) → products filtered by mapped category
    - get_substitutes(product_id) → alternative products
    - search_combined(query, intent_type, top_k) → merged semantic + category results
    """

    def __init__(self):
        """Load catalog, embeddings, and substitutions from seed_data."""
        logger.info("Loading product catalog...")

        # Load products
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            self.products: list[dict] = json.load(f)

        # Load embeddings
        self.embeddings: np.ndarray = np.load(EMBEDDINGS_PATH)

        # Load substitutions
        if SUBSTITUTIONS_PATH.exists():
            with open(SUBSTITUTIONS_PATH, "r", encoding="utf-8") as f:
                self._substitutions: list[dict] = json.load(f)
        else:
            self._substitutions = []

        # Load category mapping
        if CATEGORY_MAPPING_PATH.exists():
            with open(CATEGORY_MAPPING_PATH, "r", encoding="utf-8") as f:
                self._category_mapping: dict[str, str] = json.load(f)
        else:
            self._category_mapping = {}

        # Build lookup indices
        self._id_to_index = {p["product_id"]: i for i, p in enumerate(self.products)}
        self._intent_to_products = self._build_intent_index()

        # Load sentence transformer model (shared with semantic_classifier)
        self._model: Optional[SentenceTransformer] = None

        logger.info(
            "Product catalog loaded: %d products, %d substitutions",
            len(self.products),
            len(self._substitutions),
        )

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load sentence transformer model."""
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _build_intent_index(self) -> dict[str, list[int]]:
        """Build index: intent_type → list of product indices."""
        index: dict[str, list[int]] = {}
        for i, product in enumerate(self.products):
            intent_type = product.get("intent_type", "general")
            if intent_type not in index:
                index[intent_type] = []
            index[intent_type].append(i)
        return index

    def semantic_search(self, query: str, top_k: int = 15) -> list[dict]:
        """
        Search products by semantic similarity to query text.

        Args:
            query: Natural language search query (e.g., "protein bars for gym")
            top_k: Number of results to return

        Returns:
            List of product dicts with added "score" field, sorted by similarity.
        """
        if not query or not query.strip():
            return []

        model = self._get_model()
        query_vec = model.encode(query)

        # Compute cosine similarities
        norms = np.linalg.norm(self.embeddings, axis=1)
        query_norm = np.linalg.norm(query_vec)

        # Avoid division by zero
        denom = norms * query_norm
        denom[denom == 0] = 1e-10

        similarities = np.dot(self.embeddings, query_vec) / denom

        # Get top K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            product = self.products[idx].copy()
            product["score"] = round(float(similarities[idx]), 4)
            results.append(product)

        return results

    def get_by_intent(self, intent_type: str, limit: int = 20) -> list[dict]:
        """
        Get products mapped to a specific intent type.

        Args:
            intent_type: One of the mapped intent types
            limit: Max products to return

        Returns:
            List of product dicts for that intent category.
        """
        indices = self._intent_to_products.get(intent_type, [])
        return [self.products[i].copy() for i in indices[:limit]]

    def get_substitutes(self, product_id: str) -> list[dict]:
        """
        Get substitution candidates for a product.

        Args:
            product_id: The product to find alternatives for

        Returns:
            List of substitution dicts with replacement info.
        """
        return [
            sub for sub in self._substitutions
            if sub["original_product_id"] == product_id
        ]

    def search_combined(
        self, query: str, intent_type: str, top_k: int = 15
    ) -> list[dict]:
        """
        Combined search: semantic similarity + category filtering.

        Merges results from both strategies, deduplicates, and ranks
        by semantic score.

        Args:
            query: User's search query / entities
            intent_type: Classified intent type
            top_k: Number of final results

        Returns:
            Top K products ranked by relevance.
        """
        # Strategy 1: Semantic search
        semantic_results = self.semantic_search(query, top_k=top_k)

        # Strategy 2: Category filter
        category_results = self.get_by_intent(intent_type, limit=20)

        # Merge and deduplicate
        seen_ids = set()
        merged = []

        # Semantic results first (they have scores)
        for product in semantic_results:
            if product["product_id"] not in seen_ids:
                seen_ids.add(product["product_id"])
                merged.append(product)

        # Add category results that aren't already included
        for product in category_results:
            if product["product_id"] not in seen_ids:
                seen_ids.add(product["product_id"])
                product["score"] = 0.3  # Base score for category matches
                merged.append(product)

        # Sort by score descending
        merged.sort(key=lambda p: p.get("score", 0), reverse=True)

        return merged[:top_k]

    def get_product_by_id(self, product_id: str) -> Optional[dict]:
        """Get a single product by its ID."""
        idx = self._id_to_index.get(product_id)
        if idx is not None:
            return self.products[idx].copy()
        return None
