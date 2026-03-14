"""
Event Bus - Async Pub/Sub System for Decoupled Communication

Provides loose coupling between modules through async event-driven architecture.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import threading
import logging

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class Event:
    """Event object with metadata"""
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL

    # Backward-compat alias (older code/tests expect `.data`)
    @property
    def data(self) -> Dict[str, Any]:
        return self.payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "priority": self.priority.name,
        }


class EventBus:
    """
    Async Event Bus with Pub/Sub pattern

    Features:
    - Async/await support
    - Event persistence (optional)
    - Priority handling
    - Error isolation (one handler failure doesn't affect others)
    """

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        # Keep history mutation safe across sync + async paths without relying
        # on a pre-existing asyncio event loop during object construction.
        self._history_lock = threading.Lock()

    async def emit(self, event_type: str, payload: Dict[str, Any],
                   source: Optional[str] = None,
                   priority: EventPriority = EventPriority.NORMAL) -> None:
        """
        Emit an event to all subscribers

        Args:
            event_type: Event type/topic
            payload: Event data
            source: Event source identifier
            priority: Event priority level
        """
        event = Event(
            type=event_type,
            payload=payload,
            source=source,
            priority=priority
        )

        # Persist to history
        with self._history_lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        # Notify subscribers
        tasks = []
        if event_type in self._subscribers:
            handlers = self._subscribers[event_type][:]
            for callback in handlers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(asyncio.create_task(self._safe_handler(callback, event)))
                    else:
                        result = self._safe_sync_handler(callback, event)
                        if asyncio.iscoroutine(result):
                            tasks.append(asyncio.create_task(self._safe_awaitable_handler(result, event)))
                except Exception as e:
                    logger.error(f"Error dispatching event {event_type}: {e}")
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_handler(self, callback: Callable, event: Event):
        """Safely execute async handler"""
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.type}: {e}")

    def _safe_sync_handler(self, callback: Callable, event: Event):
        """Safely execute sync handler"""
        try:
            return callback(event)
        except Exception as e:
            logger.error(f"Sync event handler error for {event.type}: {e}")
        return None

    async def _safe_awaitable_handler(self, awaitable: Any, event: Event):
        """Safely execute awaitable returned by a sync callback wrapper."""
        try:
            await awaitable
        except Exception as e:
            logger.error(f"Awaitable event handler error for {event.type}: {e}")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type}")

    # Backward-compat alias (tests + legacy code)
    def publish(self, event_type: str, payload: Dict[str, Any], source: Optional[str] = None) -> None:
        """Synchronous publish wrapper for `emit`.

        This matches legacy API naming used in tests.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(event_type, payload, source=source))
        except RuntimeError:
            import asyncio
            asyncio.run(self.emit(event_type, payload, source=source))

    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event type

        Returns:
            bool: True if unsubscribed, False if not found
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                return True
        return False

    def clear_subscribers(self) -> None:
        """Clear all subscribers (test helper)."""
        self._subscribers.clear()

    def clear_history(self) -> None:
        """Clear event history (test helper)."""
        self._history.clear()

    def get_history(self, event_type: Optional[str] = None,
                    limit: int = 100,
                    since: Optional[datetime] = None) -> List[Event]:
        """
        Get event history

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            since: Only return events after this time

        Returns:
            List of events (most recent first)
        """
        events = list(self._history)

        if event_type:
            events = [e for e in events if e.type == event_type]

        if since:
            events = [e for e in events if e.timestamp > since]

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get number of subscribers"""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())


# Standard event types for Deep-Sea Nexus
class EventTypes:
    """System-wide event type constants"""

    # Session lifecycle
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_CLOSED = "session.closed"
    SESSION_ARCHIVED = "session.archived"

    # Document operations
    DOCUMENT_ADDED = "document.added"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # Flush operations
    FLUSH_STARTED = "flush.started"
    FLUSH_COMPLETED = "flush.completed"
    FLUSH_FAILED = "flush.failed"

    # System events
    CONFIG_RELOADED = "config.reloaded"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"

    # Memory operations
    RECALL_PERFORMED = "recall.performed"
    INDEX_UPDATED = "index.updated"


# Global event bus instance
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance

    Returns:
        EventBus: Global event bus (singleton)
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def reset_event_bus() -> EventBus:
    """
    Reset and recreate the global event bus

    Useful for testing or complete system reset.

    Returns:
        EventBus: New event bus instance
    """
    global _event_bus_instance
    _event_bus_instance = EventBus()
    return _event_bus_instance


# Convenience functions for common operations
async def emit_event(event_type: str, payload: Dict[str, Any],
                     source: Optional[str] = None) -> None:
    """Emit an event to the global event bus"""
    await get_event_bus().emit(event_type, payload, source)


def on_event(event_type: str, callback: Callable) -> None:
    """Subscribe to an event on the global event bus"""
    get_event_bus().subscribe(event_type, callback)
