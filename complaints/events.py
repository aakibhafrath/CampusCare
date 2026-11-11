"""
Observer Pattern - Events Module
Infrastructure Layer: Event definitions and EventPublisher.

Implements the Observer Design Pattern as required by the academic specification.
"""
from typing import Callable, Dict, List, Any


class Event:
    """Base event class."""
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

    def __repr__(self):
        return f"Event(type={self.event_type}, data={self.data})"


class ComplaintStatusChangedEvent(Event):
    """
    Domain event: fired when a complaint's status changes.
    Carries all relevant data for observers to act on.
    """
    EVENT_TYPE = 'complaint_status_changed'

    def __init__(self, complaint_id: int, complaint_title: str,
                 old_status: str, new_status: str,
                 student_id: int, changed_by_id: int, notes: str = ''):
        super().__init__(
            event_type=self.EVENT_TYPE,
            data={
                'complaint_id': complaint_id,
                'complaint_title': complaint_title,
                'old_status': old_status,
                'new_status': new_status,
                'student_id': student_id,
                'changed_by_id': changed_by_id,
                'notes': notes,
            }
        )


class EventPublisher:
    """
    Observer Pattern: Subject/Publisher.
    Manages subscriptions and publishes events to registered observers.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, observer: Callable) -> None:
        """Register an observer for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if observer not in self._subscribers[event_type]:
            self._subscribers[event_type].append(observer)

    def unsubscribe(self, event_type: str, observer: Callable) -> None:
        """Remove an observer for a specific event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                obs for obs in self._subscribers[event_type] if obs != observer
            ]

    def publish(self, event: Event) -> None:
        """
        Publish an event to all registered observers.
        Each observer's update() method is called with the event.
        """
        observers = self._subscribers.get(event.event_type, [])
        for observer in observers:
            try:
                observer.update(event)
            except Exception as e:
                # Log error but don't break other observers
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Observer error: {observer} - {e}")

    def get_subscriber_count(self, event_type: str) -> int:
        """Return the number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))


# Singleton event publisher instance
event_publisher = EventPublisher()

