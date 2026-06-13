from typing import Callable, Any
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_subscribers: dict[str, list[Callable]] = {}


def subscribe(event_name: str, handler: Callable) -> None:
    """Register an async handler for the given event name."""
    if event_name not in _subscribers:
        _subscribers[event_name] = []
    _subscribers[event_name].append(handler)


async def emit(event_name: str, payload: dict) -> None:
    """Publish an event to all registered subscribers."""
    # Log the event to stdout in JSON format
    log_entry = json.dumps({"event": event_name, "payload": payload})
    print(log_entry, flush=True)

    handlers = _subscribers.get(event_name, [])
    results = await asyncio.gather(
        *(handler(payload) for handler in handlers),
        return_exceptions=True,
    )

    # Log exceptions from individual handlers but don't propagate
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                f"Handler {handlers[i].__name__} failed for event '{event_name}': {result}"
            )
