"""Metrics router — GET /v1/metrics endpoint exposing in-memory counters."""

from fastapi import APIRouter

from app.metrics import metrics

router = APIRouter(prefix="/v1", tags=["metrics"])


@router.get("/metrics")
async def get_metrics() -> dict:
    """Return current system metrics counters.

    Returns JSON with intent_count, bundle_count, cart_count,
    checkout_count, and cache_hit_rate from the MetricsStore singleton.
    """
    return {
        "intent_count": metrics.intent_count,
        "bundle_count": metrics.bundle_count,
        "cart_count": metrics.cart_count,
        "checkout_count": metrics.checkout_count,
        "cache_hit_rate": metrics.cache_hit_rate,
    }
