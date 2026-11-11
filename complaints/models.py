"""
Complaints Models - Domain Layer
Core complaint entity with lifecycle management.
"""
from django.db import models
from django.conf import settings


class Complaint(models.Model):
    """
    Core complaint model representing the full lifecycle
    of a campus maintenance complaint.
    """
    # Status choices - defined lifecycle
    STATUS_SUBMITTED = 'submitted'
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # Category choices
    CATEGORY_ELECTRICAL = 'electrical'
    CATEGORY_FURNITURE = 'furniture'
    CATEGORY_PLUMBING = 'plumbing'
    CATEGORY_NETWORK = 'network'
    CATEGORY_EQUIPMENT = 'equipment'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_ELECTRICAL, 'Electrical'),
        (CATEGORY_FURNITURE, 'Furniture'),
        (CATEGORY_PLUMBING, 'Plumbing'),
        (CATEGORY_NETWORK, 'Network / Wi-Fi'),
        (CATEGORY_EQUIPMENT, 'Equipment'),
        (CATEGORY_OTHER, 'Other'),
    ]

    # Fields
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints',
        limit_choices_to={'role': 'student'}
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        limit_choices_to={'role': 'technician'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'complaints_complaint'
        ordering = ['-created_at']
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'

    def __str__(self):
        return f"#{self.pk} - {self.title} ({self.get_status_display()})"

    @property
    def status_badge_class(self):
        """Returns Bootstrap badge class for status."""
        return {
            'submitted': 'bg-secondary',
            'assigned': 'bg-primary',
            'in_progress': 'bg-warning text-dark',
            'resolved': 'bg-success',
            'closed': 'bg-dark',
        }.get(self.status, 'bg-secondary')

    @property
    def category_icon(self):
        """Returns icon for category."""
        return {
            'electrical': 'bi-lightning-charge',
            'furniture': 'bi-chair',
            'plumbing': 'bi-droplet',
            'network': 'bi-wifi',
            'equipment': 'bi-tools',
            'other': 'bi-three-dots',
        }.get(self.category, 'bi-question-circle')

    def can_be_assigned(self):
        """Check if complaint can be assigned (must be Submitted)."""
        return self.status == self.STATUS_SUBMITTED

    def can_be_updated_by_technician(self):
        """Check if technician can update this complaint."""
        return self.status in [self.STATUS_ASSIGNED, self.STATUS_IN_PROGRESS]

    def can_be_closed(self):
        """Check if admin can close (must be Resolved)."""
        return self.status == self.STATUS_RESOLVED


class StatusHistory(models.Model):
    """
    Records every status change for a complaint.
    Part of the Domain Layer - audit trail.
    """
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'complaints_statushistory'
        ordering = ['-changed_at']
        verbose_name = 'Status History'
        verbose_name_plural = 'Status Histories'

    def __str__(self):
        return f"Complaint #{self.complaint_id}: {self.old_status} → {self.new_status}"

    def get_new_status_display(self):
        status_map = dict(Complaint.STATUS_CHOICES)
        return status_map.get(self.new_status, self.new_status)

    def get_old_status_display(self):
        status_map = dict(Complaint.STATUS_CHOICES)
        return status_map.get(self.old_status, self.old_status)
