"""
Accounts Views - Presentation Layer
Handles authentication, registration, dashboards, and profile management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from .forms import StudentRegistrationForm, LoginForm, ProfileEditForm
from .models import User
from complaints.models import Complaint


def login_view(request):
    """Login view for all roles."""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Secure logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def register_view(request):
    """Student self-registration."""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to CampusCare, {user.first_name}! Your account has been created.')
            return redirect('accounts:student_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def redirect_by_role(user):
    """Redirect user to their role-specific dashboard."""
    from django.shortcuts import redirect
    if user.is_student:
        return redirect('accounts:student_dashboard')
    elif user.is_administrator:
        return redirect('accounts:admin_dashboard')
    elif user.is_technician:
        return redirect('accounts:technician_dashboard')
    return redirect('accounts:login')


@login_required
def student_dashboard(request):
    """Student dashboard with complaint statistics."""
    if not request.user.is_student:
        messages.error(request, 'Access denied. Students only.')
        return redirect_by_role(request.user)

    complaints = Complaint.objects.filter(student=request.user)
    stats = {
        'total': complaints.count(),
        'submitted': complaints.filter(status='submitted').count(),
        'assigned': complaints.filter(status='assigned').count(),
        'in_progress': complaints.filter(status='in_progress').count(),
        'resolved': complaints.filter(status='resolved').count(),
        'closed': complaints.filter(status='closed').count(),
    }
    recent_complaints = complaints.order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'recent_complaints': recent_complaints,
        'page_title': 'Student Dashboard',
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Administrator dashboard with full statistics."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied. Administrators only.')
        return redirect_by_role(request.user)

    all_complaints = Complaint.objects.all()
    stats = {
        'total': all_complaints.count(),
        'submitted': all_complaints.filter(status='submitted').count(),
        'assigned': all_complaints.filter(status='assigned').count(),
        'in_progress': all_complaints.filter(status='in_progress').count(),
        'resolved': all_complaints.filter(status='resolved').count(),
        'closed': all_complaints.filter(status='closed').count(),
        'waiting': all_complaints.filter(status='submitted').count(),
    }
    recent_complaints = all_complaints.order_by('-created_at')[:10]
    technicians = User.objects.filter(role='technician')

    context = {
        'stats': stats,
        'recent_complaints': recent_complaints,
        'technicians': technicians,
        'page_title': 'Administrator Dashboard',
    }
    return render(request, 'administrator/dashboard.html', context)


@login_required
def technician_dashboard(request):
    """Technician dashboard with assigned task statistics."""
    if not request.user.is_technician:
        messages.error(request, 'Access denied. Technicians only.')
        return redirect_by_role(request.user)

    assigned_complaints = Complaint.objects.filter(assigned_technician=request.user)
    stats = {
        'total': assigned_complaints.count(),
        'assigned': assigned_complaints.filter(status='assigned').count(),
        'in_progress': assigned_complaints.filter(status='in_progress').count(),
        'resolved': assigned_complaints.filter(status='resolved').count(),
    }
    recent_tasks = assigned_complaints.order_by('-updated_at')[:5]

    context = {
        'stats': stats,
        'recent_tasks': recent_tasks,
        'page_title': 'Technician Dashboard',
    }
    return render(request, 'technician/dashboard.html', context)


@login_required
def profile_view(request):
    """View and edit user profile."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'page_title': 'My Profile'})


@login_required
def user_list_view(request):
    """Admin: list all users."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied.')
        return redirect_by_role(request.user)

    students = User.objects.filter(role='student').order_by('-created_at')
    technicians = User.objects.filter(role='technician').order_by('-created_at')

    context = {
        'students': students,
        'technicians': technicians,
        'page_title': 'Manage Users',
    }
    return render(request, 'administrator/users.html', context)
