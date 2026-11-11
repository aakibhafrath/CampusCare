"""
Reports Views - Presentation Layer / Application Layer
Administrator analytics and reporting.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from complaints.models import Complaint
from accounts.models import User


@login_required
def reports_dashboard(request):
    """Administrator reports with real database statistics."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied. Administrators only.')
        return redirect('accounts:admin_dashboard')

    # Complaints by status
    status_data = {}
    for status_key, status_label in Complaint.STATUS_CHOICES:
        status_data[status_key] = {
            'label': status_label,
            'count': Complaint.objects.filter(status=status_key).count()
        }

    # Complaints by category
    category_data = {}
    for cat_key, cat_label in Complaint.CATEGORY_CHOICES:
        category_data[cat_key] = {
            'label': cat_label,
            'count': Complaint.objects.filter(category=cat_key).count()
        }

    # Complaints by technician
    technicians = User.objects.filter(role='technician')
    technician_data = []
    for tech in technicians:
        assigned = Complaint.objects.filter(assigned_technician=tech)
        technician_data.append({
            'technician': tech,
            'total': assigned.count(),
            'in_progress': assigned.filter(status='in_progress').count(),
            'resolved': assigned.filter(status='resolved').count(),
            'closed': assigned.filter(status='closed').count(),
        })

    # Overall totals
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(
        status__in=['resolved', 'closed']
    ).count()

    resolution_rate = 0
    if total_complaints > 0:
        resolution_rate = round((resolved_complaints / total_complaints) * 100, 1)

    # JSON data for charts
    import json
    status_chart_labels = json.dumps([v['label'] for v in status_data.values()])
    status_chart_values = json.dumps([v['count'] for v in status_data.values()])
    category_chart_labels = json.dumps([v['label'] for v in category_data.values()])
    category_chart_values = json.dumps([v['count'] for v in category_data.values()])

    context = {
        'status_data': status_data,
        'category_data': category_data,
        'technician_data': technician_data,
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'resolution_rate': resolution_rate,
        'total_technicians': technicians.count(),
        'status_chart_labels': status_chart_labels,
        'status_chart_values': status_chart_values,
        'category_chart_labels': category_chart_labels,
        'category_chart_values': category_chart_values,
        'page_title': 'Reports & Analytics',
    }
    return render(request, 'reports/dashboard.html', context)
