"""
Notifications Views - Presentation Layer
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Notification


@login_required
def notification_list(request):
    """View all notifications for the current user."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('complaint').order_by('-created_at')

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'page_title': 'My Notifications',
    })


@login_required
def mark_as_read(request, pk):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'id': pk})

    messages.success(request, 'Notification marked as read.')
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    if request.method == 'POST':
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')

    return redirect('notifications:list')


@login_required
def unread_count_api(request):
    """API endpoint: return unread notification count as JSON."""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return JsonResponse({'count': count})
