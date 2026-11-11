"""
Complaints Services - Application Layer
Business use-case coordination. Contains complaint lifecycle logic,
technician assignment, and event publishing.
"""
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from .models import Complaint, StatusHistory
from .repositories import ComplaintRepository, StatusHistoryRepository
from .events import event_publisher, ComplaintStatusChangedEvent
from .observers import NotificationObserver, LoggingObserver

# Register observers (Observer Pattern: subscribe at startup)
_notification_observer = NotificationObserver()
_logging_observer = LoggingObserver()

event_publisher.subscribe(
    ComplaintStatusChangedEvent.EVENT_TYPE,
    _notification_observer
)
event_publisher.subscribe(
    ComplaintStatusChangedEvent.EVENT_TYPE,
    _logging_observer
)


class ComplaintService:
    """
    Application Layer service: Complaint management use cases.
    Coordinates domain objects, repositories, and event publishing.
    """

    @staticmethod
    @transaction.atomic
    def submit_complaint(student, title: str, category: str,
                         location: str, description: str) -> Complaint:
        """
        Use case: Student submits a new complaint.
        Creates complaint with Submitted status and records initial history.
        """
        complaint = Complaint(
            student=student,
            title=title,
            category=category,
            location=location,
            description=description,
            status=Complaint.STATUS_SUBMITTED,
        )
        ComplaintRepository.save(complaint)

        # Record initial status history
        StatusHistoryRepository.create(
            complaint=complaint,
            old_status='',
            new_status=Complaint.STATUS_SUBMITTED,
            changed_by=student,
            notes='Complaint submitted by student.'
        )

        return complaint

    @staticmethod
    @transaction.atomic
    def assign_technician(complaint: Complaint, technician, assigned_by,
                          notes: str = '') -> Complaint:
        """
        Use case: Administrator assigns a technician to a complaint.
        """
        if not assigned_by.is_administrator:
            raise PermissionDenied("Only administrators can assign technicians.")

        if not complaint.can_be_assigned():
            raise ValidationError(
                f"Complaint cannot be assigned. Current status: {complaint.get_status_display()}"
            )

        if not technician.is_technician:
            raise ValidationError("Selected user is not a technician.")

        old_status = complaint.status
        complaint.assigned_technician = technician
        complaint.status = Complaint.STATUS_ASSIGNED
        ComplaintRepository.save(complaint)

        note_text = notes or f'Assigned to {technician.get_full_name() or technician.username}.'
        StatusHistoryRepository.create(
            complaint=complaint,
            old_status=old_status,
            new_status=Complaint.STATUS_ASSIGNED,
            changed_by=assigned_by,
            notes=note_text
        )

        # Publish event → triggers observers (NotificationObserver creates notification)
        event = ComplaintStatusChangedEvent(
            complaint_id=complaint.pk,
            complaint_title=complaint.title,
            old_status=old_status,
            new_status=Complaint.STATUS_ASSIGNED,
            student_id=complaint.student_id,
            changed_by_id=assigned_by.pk,
            notes=note_text
        )
        event_publisher.publish(event)

        return complaint

    @staticmethod
    @transaction.atomic
    def update_status_by_technician(complaint: Complaint, technician,
                                     new_status: str, notes: str = '') -> Complaint:
        """
        Use case: Technician updates complaint to In Progress or Resolved.
        """
        if not technician.is_technician:
            raise PermissionDenied("Only technicians can update complaint status.")

        if complaint.assigned_technician != technician:
            raise PermissionDenied("You can only update complaints assigned to you.")

        valid_transitions = {
            Complaint.STATUS_ASSIGNED: [Complaint.STATUS_IN_PROGRESS],
            Complaint.STATUS_IN_PROGRESS: [Complaint.STATUS_RESOLVED],
        }

        allowed = valid_transitions.get(complaint.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot transition from '{complaint.get_status_display()}' "
                f"to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            )

        old_status = complaint.status
        complaint.status = new_status
        ComplaintRepository.save(complaint)

        StatusHistoryRepository.create(
            complaint=complaint,
            old_status=old_status,
            new_status=new_status,
            changed_by=technician,
            notes=notes or f'Status updated by technician.'
        )

        # Publish event → NotificationObserver creates student notification
        event = ComplaintStatusChangedEvent(
            complaint_id=complaint.pk,
            complaint_title=complaint.title,
            old_status=old_status,
            new_status=new_status,
            student_id=complaint.student_id,
            changed_by_id=technician.pk,
            notes=notes
        )
        event_publisher.publish(event)

        return complaint

    @staticmethod
    @transaction.atomic
    def close_complaint(complaint: Complaint, admin, notes: str = '') -> Complaint:
        """
        Use case: Administrator closes a resolved complaint.
        """
        if not admin.is_administrator:
            raise PermissionDenied("Only administrators can close complaints.")

        if not complaint.can_be_closed():
            raise ValidationError(
                f"Complaint cannot be closed. Must be Resolved first. "
                f"Current status: {complaint.get_status_display()}"
            )

        old_status = complaint.status
        complaint.status = Complaint.STATUS_CLOSED
        ComplaintRepository.save(complaint)

        StatusHistoryRepository.create(
            complaint=complaint,
            old_status=old_status,
            new_status=Complaint.STATUS_CLOSED,
            changed_by=admin,
            notes=notes or 'Complaint closed by administrator.'
        )

        # Publish event → student gets notified
        event = ComplaintStatusChangedEvent(
            complaint_id=complaint.pk,
            complaint_title=complaint.title,
            old_status=old_status,
            new_status=Complaint.STATUS_CLOSED,
            student_id=complaint.student_id,
            changed_by_id=admin.pk,
            notes=notes
        )
        event_publisher.publish(event)

        return complaint

