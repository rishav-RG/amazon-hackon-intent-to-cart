"""In-memory metrics counters for the Intent-to-Cart backend engine."""

import threading


class MetricsStore:
    """Thread-safe in-memory metrics store for tracking system counters."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.intent_count: int = 0
        self.bundle_count: int = 0
        self.cart_count: int = 0
        self.checkout_count: int = 0
        self.cache_hits: int = 0
        self.cache_checks: int = 0

    def increment_intent(self) -> None:
        """Increment the intent classification counter."""
        with self._lock:
            self.intent_count += 1

    def increment_bundle(self) -> None:
        """Increment the bundle creation counter."""
        with self._lock:
            self.bundle_count += 1

    def increment_cart(self) -> None:
        """Increment the cart creation counter."""
        with self._lock:
            self.cart_count += 1

    def increment_checkout(self) -> None:
        """Increment the checkout counter."""
        with self._lock:
            self.checkout_count += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit (also increments cache_checks)."""
        with self._lock:
            self.cache_hits += 1
            self.cache_checks += 1

    def record_cache_check(self) -> None:
        """Record a cache check (miss — only increments cache_checks)."""
        with self._lock:
            self.cache_checks += 1

    @property
    def cache_hit_rate(self) -> float:
        """Returns cache_hits / cache_checks, or 0.0 if no checks have occurred."""
        with self._lock:
            if self.cache_checks == 0:
                return 0.0
            return self.cache_hits / self.cache_checks


metrics = MetricsStore()  # Singleton instance
