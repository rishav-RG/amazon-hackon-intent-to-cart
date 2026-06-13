"""Unit tests for app/metrics.py — In-memory counters."""

import threading

from app.metrics import MetricsStore, metrics


class TestMetricsStoreInit:
    """Verify initial state of MetricsStore."""

    def test_all_counters_start_at_zero(self):
        store = MetricsStore()
        assert store.intent_count == 0
        assert store.bundle_count == 0
        assert store.cart_count == 0
        assert store.checkout_count == 0
        assert store.cache_hits == 0
        assert store.cache_checks == 0

    def test_cache_hit_rate_is_zero_when_no_checks(self):
        store = MetricsStore()
        assert store.cache_hit_rate == 0.0


class TestIncrementMethods:
    """Verify each increment method updates the correct counter."""

    def test_increment_intent(self):
        store = MetricsStore()
        store.increment_intent()
        assert store.intent_count == 1

    def test_increment_bundle(self):
        store = MetricsStore()
        store.increment_bundle()
        assert store.bundle_count == 1

    def test_increment_cart(self):
        store = MetricsStore()
        store.increment_cart()
        assert store.cart_count == 1

    def test_increment_checkout(self):
        store = MetricsStore()
        store.increment_checkout()
        assert store.checkout_count == 1

    def test_multiple_increments(self):
        store = MetricsStore()
        for _ in range(5):
            store.increment_intent()
        assert store.intent_count == 5


class TestCacheMethods:
    """Verify cache hit/check recording and hit rate computation."""

    def test_record_cache_check_increments_checks_only(self):
        store = MetricsStore()
        store.record_cache_check()
        assert store.cache_checks == 1
        assert store.cache_hits == 0

    def test_record_cache_hit_increments_both(self):
        store = MetricsStore()
        store.record_cache_hit()
        assert store.cache_hits == 1
        assert store.cache_checks == 1

    def test_cache_hit_rate_all_hits(self):
        store = MetricsStore()
        store.record_cache_hit()
        store.record_cache_hit()
        assert store.cache_hit_rate == 1.0

    def test_cache_hit_rate_no_hits(self):
        store = MetricsStore()
        store.record_cache_check()
        store.record_cache_check()
        assert store.cache_hit_rate == 0.0

    def test_cache_hit_rate_mixed(self):
        store = MetricsStore()
        store.record_cache_hit()   # 1 hit, 1 check
        store.record_cache_check()  # 0 hit, 1 check
        # Total: 1 hit / 2 checks = 0.5
        assert store.cache_hit_rate == 0.5

    def test_cache_hit_rate_returns_float(self):
        store = MetricsStore()
        store.record_cache_hit()
        store.record_cache_check()
        store.record_cache_check()
        # 1 hit / 3 checks
        rate = store.cache_hit_rate
        assert isinstance(rate, float)
        assert abs(rate - 1.0 / 3.0) < 1e-9


class TestThreadSafety:
    """Verify thread-safe behavior under concurrent access."""

    def test_concurrent_increments(self):
        store = MetricsStore()
        num_threads = 10
        increments_per_thread = 100

        def worker():
            for _ in range(increments_per_thread):
                store.increment_intent()

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert store.intent_count == num_threads * increments_per_thread

    def test_concurrent_cache_operations(self):
        store = MetricsStore()
        num_threads = 10
        ops_per_thread = 50

        def hit_worker():
            for _ in range(ops_per_thread):
                store.record_cache_hit()

        def check_worker():
            for _ in range(ops_per_thread):
                store.record_cache_check()

        threads = []
        for _ in range(num_threads // 2):
            threads.append(threading.Thread(target=hit_worker))
            threads.append(threading.Thread(target=check_worker))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected_hits = (num_threads // 2) * ops_per_thread
        expected_checks = num_threads * ops_per_thread
        assert store.cache_hits == expected_hits
        assert store.cache_checks == expected_checks


class TestSingleton:
    """Verify the module-level singleton is a MetricsStore instance."""

    def test_metrics_is_metrics_store_instance(self):
        assert isinstance(metrics, MetricsStore)
