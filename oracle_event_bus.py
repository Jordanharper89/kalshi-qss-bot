"""
Oracle Event Bus

ORACLE-022.3

Purpose:
- Central event dispatcher for Oracle.
- Decouples services.
- Allows publish/subscribe communication.
"""

from collections import defaultdict
from typing import Any, Callable, Dict, List


class OracleEventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable) -> None:
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def publish(self, event_name: str, payload: Any = None) -> int:
        callbacks = self._subscribers.get(event_name, [])

        for callback in callbacks:
            callback(payload)

        return len(callbacks)

    def subscriber_count(self, event_name: str) -> int:
        return len(self._subscribers.get(event_name, []))

    def clear(self) -> None:
        self._subscribers.clear()

    def snapshot(self) -> Dict[str, int]:
        return {
            event: len(callbacks)
            for event, callbacks in self._subscribers.items()
        }


oracle_event_bus = OracleEventBus()


class OracleEvents:
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"

    DISCOVERY_STARTED = "discovery_started"
    DISCOVERY_COMPLETED = "discovery_completed"

    SIGNAL_CHANGED = "signal_changed"

    OPPORTUNITY_FOUND = "opportunity_found"

    WATCHLIST_UPDATED = "watchlist_updated"

    ERROR = "error"

    STATUS_CHANGED = "status_changed"