"""Unit tests for app.events — in-process asyncio event bus."""
import json
import pytest

from app.events import emit, subscribe, _subscribers

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def clear_subscribers():
    """Clear the subscriber registry between tests."""
    _subscribers.clear()
    yield
    _subscribers.clear()


async def test_emit_calls_all_registered_handlers_with_correct_payload():
    """All subscribed handlers receive the exact payload passed to emit."""
    received = []

    async def handler_a(payload):
        received.append(("a", payload))

    async def handler_b(payload):
        received.append(("b", payload))

    subscribe("order.placed", handler_a)
    subscribe("order.placed", handler_b)

    payload = {"orderId": "123", "total": 42.0}
    await emit("order.placed", payload)

    assert len(received) == 2
    assert ("a", payload) in received
    assert ("b", payload) in received


async def test_emit_with_zero_subscribers_does_not_raise():
    """Emitting an event with no subscribers should complete without error."""
    # No subscribers registered — should not raise
    await emit("some.event", {"key": "value"})


async def test_handler_exception_does_not_crash_other_handlers():
    """If one handler raises, other handlers still execute."""
    results = []

    async def good_handler(payload):
        results.append("good")

    async def bad_handler(payload):
        raise RuntimeError("I broke")

    async def another_good_handler(payload):
        results.append("another_good")

    subscribe("test.event", good_handler)
    subscribe("test.event", bad_handler)
    subscribe("test.event", another_good_handler)

    await emit("test.event", {"data": 1})

    assert "good" in results
    assert "another_good" in results
    assert len(results) == 2


async def test_json_log_output_on_emit(capsys):
    """emit() prints a JSON log line containing event name and payload."""
    payload = {"userId": "u1", "action": "test"}
    await emit("cart.updated", payload)

    captured = capsys.readouterr()
    log_line = captured.out.strip()
    parsed = json.loads(log_line)

    assert parsed["event"] == "cart.updated"
    assert parsed["payload"] == payload


async def test_subscribe_multiple_handlers_to_same_event():
    """Multiple handlers can be registered for the same event and all are called."""
    call_count = []

    async def handler_1(payload):
        call_count.append(1)

    async def handler_2(payload):
        call_count.append(2)

    async def handler_3(payload):
        call_count.append(3)

    subscribe("multi.event", handler_1)
    subscribe("multi.event", handler_2)
    subscribe("multi.event", handler_3)

    await emit("multi.event", {"x": "y"})

    assert len(call_count) == 3
    assert set(call_count) == {1, 2, 3}
