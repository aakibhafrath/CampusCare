"""
Accounts Models - Domain Layer
User model with role-based access control.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model supporting three roles:
    student, administrator, technician
    """
    ROLE_STUDENT = 'student'
    ROLE_ADMIN = 'administrator'
    ROLE_TECHNICIAN = 'technician'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_TECHNICIAN, 'Technician'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )
    phone_number = models.CharField(max_length=20, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_administrator(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_technician(self):
        return self.role == self.ROLE_TECHNICIAN

    def get_role_display_name(self):
        return dict(self.ROLE_CHOICES).get(self.role, 'Unknown')
