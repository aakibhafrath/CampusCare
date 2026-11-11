from django.contrib import admin
from .models import Complaint, StatusHistory


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'student', 'category', 'status', 'assigned_technician', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'student__username', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at']
    readonly_fields = ['changed_at']
