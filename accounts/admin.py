from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'student_id']
    fieldsets = UserAdmin.fieldsets + (
        ('CampusCare Info', {
            'fields': ('role', 'phone_number', 'student_id', 'department', 'profile_picture')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CampusCare Info', {
            'fields': ('role', 'phone_number', 'student_id', 'department')
        }),
    )
