"""
Notifications Context Processor
Injects unread notification count into every template context.
"""


def unread_notifications_count(request):
    """Add unread notification count to template context for authenticated users."""
    if request.user.is_authenticated:
        from .models import Notification
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}

