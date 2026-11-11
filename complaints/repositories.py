"""
Complaints Repositories - Infrastructure Layer
Database access layer, abstracting ORM queries from business logic.
"""
from django.db.models import QuerySet
from .models import Complaint, StatusHistory


class ComplaintRepository:
    """
    Repository for Complaint data access.
    Separates database queries from business logic (Application Layer).
    """

    @staticmethod
    def get_all() -> QuerySet:
        return Complaint.objects.select_related(
            'student', 'assigned_technician'
        ).order_by('-created_at')

    @staticmethod
    def get_by_id(complaint_id: int) -> Complaint:
        return Complaint.objects.select_related(
            'student', 'assigned_technician'
        ).get(pk=complaint_id)

    @staticmethod
    def get_by_student(student_id: int) -> QuerySet:
        return Complaint.objects.filter(
            student_id=student_id
        ).select_related('assigned_technician').order_by('-created_at')

    @staticmethod
    def get_by_technician(technician_id: int) -> QuerySet:
        return Complaint.objects.filter(
            assigned_technician_id=technician_id
        ).select_related('student').order_by('-updated_at')

    @staticmethod
    def get_by_status(status: str) -> QuerySet:
        return Complaint.objects.filter(status=status).select_related(
            'student', 'assigned_technician'
        )

    @staticmethod
    def get_waiting_for_assignment() -> QuerySet:
        return Complaint.objects.filter(
            status=Complaint.STATUS_SUBMITTED
        ).select_related('student').order_by('-created_at')

    @staticmethod
    def save(complaint: Complaint) -> Complaint:
        complaint.save()
        return complaint

    @staticmethod
    def search(query: str, status: str = None, category: str = None) -> QuerySet:
        qs = Complaint.objects.select_related('student', 'assigned_technician')
        if query:
            qs = qs.filter(
                title__icontains=query
            ) | qs.filter(
                location__icontains=query
            ) | qs.filter(
                description__icontains=query
            )
            qs = qs.distinct()
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by('-created_at')


class StatusHistoryRepository:
    """
    Repository for StatusHistory data access.
    """

    @staticmethod
    def get_by_complaint(complaint_id: int) -> QuerySet:
        return StatusHistory.objects.filter(
            complaint_id=complaint_id
        ).select_related('changed_by').order_by('-changed_at')

    @staticmethod
    def create(complaint: Complaint, old_status: str, new_status: str,
               changed_by, notes: str = '') -> StatusHistory:
        return StatusHistory.objects.create(
            complaint=complaint,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes,
        )

