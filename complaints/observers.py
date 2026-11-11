"""
Observer Pattern - Observers Module
Domain Layer: Observer contracts and concrete observer implementations.

Implements the Observer Design Pattern as required by the academic specification.
"""
from abc import ABC, abstractmethod
from .events import Event, ComplaintStatusChangedEvent


class Observer(ABC):
    """
    Abstract Observer base class.
    All concrete observers must implement the update() method.
    """

    @abstractmethod
    def update(self, event: Event) -> None:
        """Called by the publisher when an event is fired."""
        pass


class NotificationObserver(Observer):
    """
    Concrete Observer: Creates in-app notifications for students
    when their complaint status changes.

    This observer is decoupled from the complaint business logic —
    it reacts to events published by the EventPublisher.
    """

    def update(self, event: Event) -> None:
        """
        Handle a complaint status change event by creating
        an in-app notification for the student.
        """
        if event.event_type != ComplaintStatusChangedEvent.EVENT_TYPE:
            return

        data = event.data
        self._create_notification(
            complaint_id=data['complaint_id'],
            complaint_title=data['complaint_title'],
            old_status=data['old_status'],
            new_status=data['new_status'],
            student_id=data['student_id'],
        )

    def _create_notification(self, complaint_id: int, complaint_title: str,
                              old_status: str, new_status: str, student_id: int) -> None:
        """Create the notification record in the database."""
        from django.db import transaction

        status_labels = {
            'submitted': 'Submitted',
            'assigned': 'Assigned to a Technician',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed',
        }

        new_label = status_labels.get(new_status, new_status.title())
        message = (
            f'Your complaint "{complaint_title}" (#{complaint_id}) '
            f'status has been updated to: {new_label}.'
        )

        def _save_notification():
            from notifications.models import Notification
            Notification.objects.create(
                recipient_id=student_id,
                complaint_id=complaint_id,
                message=message,
                notification_type='status_change',
            )

        # Use on_commit to ensure notification is saved after the transaction commits
        transaction.on_commit(_save_notification)


class LoggingObserver(Observer):
    """
    Concrete Observer: Logs all complaint status changes.
    Useful for auditing and debugging.
    """

    def update(self, event: Event) -> None:
        """Log the status change event."""
        import logging
        logger = logging.getLogger('campuscare.events')

        if event.event_type == ComplaintStatusChangedEvent.EVENT_TYPE:
            data = event.data
            logger.info(
                f"Complaint #{data['complaint_id']} status changed: "
                f"{data['old_status']} → {data['new_status']} "
                f"(changed by user #{data['changed_by_id']})"
            )

