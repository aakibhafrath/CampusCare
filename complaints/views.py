"""
Complaints Views - Presentation Layer
Handles all complaint-related views for all three roles.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator

from .models import Complaint
from .forms import ComplaintSubmitForm, AssignTechnicianForm, UpdateStatusForm, ComplaintFilterForm
from .repositories import ComplaintRepository, StatusHistoryRepository
from .services import ComplaintService
from accounts.models import User


# ─────────────────────── STUDENT VIEWS ───────────────────────

@login_required
def submit_complaint(request):
    """Student: Submit a new complaint."""
    if not request.user.is_student:
        messages.error(request, 'Only students can submit complaints.')
        return redirect('accounts:login')

    if request.method == 'POST':
        form = ComplaintSubmitForm(request.POST)
        if form.is_valid():
            try:
                complaint = ComplaintService.submit_complaint(
                    student=request.user,
                    title=form.cleaned_data['title'],
                    category=form.cleaned_data['category'],
                    location=form.cleaned_data['location'],
                    description=form.cleaned_data['description'],
                )
                messages.success(request, f'Complaint #{complaint.pk} submitted successfully!')
                return redirect('complaints:my_complaints')
            except Exception as e:
                messages.error(request, f'Error submitting complaint: {str(e)}')
    else:
        form = ComplaintSubmitForm()

    return render(request, 'complaints/submit.html', {
        'form': form,
        'page_title': 'Submit New Complaint'
    })


@login_required
def my_complaints(request):
    """Student: View own complaints with filtering."""
    if not request.user.is_student:
        messages.error(request, 'Access denied.')
        return redirect('accounts:login')

    filter_form = ComplaintFilterForm(request.GET)
    complaints_qs = ComplaintRepository.get_by_student(request.user.pk)

    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        category = filter_form.cleaned_data.get('category')
        search = filter_form.cleaned_data.get('search')

        if status:
            complaints_qs = complaints_qs.filter(status=status)
        if category:
            complaints_qs = complaints_qs.filter(category=category)
        if search:
            complaints_qs = complaints_qs.filter(title__icontains=search)

    paginator = Paginator(complaints_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaints/my_complaints.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'page_title': 'My Complaints',
    })


@login_required
def complaint_detail(request, pk):
    """Detail view for a complaint. Access controlled by role."""
    complaint = get_object_or_404(Complaint, pk=pk)

    # Access control
    user = request.user
    if user.is_student and complaint.student != user:
        messages.error(request, 'You can only view your own complaints.')
        return redirect('complaints:my_complaints')
    elif user.is_technician and complaint.assigned_technician != user:
        messages.error(request, 'You can only view complaints assigned to you.')
        return redirect('complaints:my_tasks')

    history = StatusHistoryRepository.get_by_complaint(complaint.pk)

    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'history': history,
        'page_title': f'Complaint #{complaint.pk}',
    })


# ─────────────────────── ADMIN VIEWS ───────────────────────

@login_required
def all_complaints(request):
    """Admin: View all complaints with filtering."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied. Administrators only.')
        return redirect('accounts:login')

    filter_form = ComplaintFilterForm(request.GET)
    complaints_qs = ComplaintRepository.get_all()

    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        category = filter_form.cleaned_data.get('category')
        search = filter_form.cleaned_data.get('search')

        if status:
            complaints_qs = complaints_qs.filter(status=status)
        if category:
            complaints_qs = complaints_qs.filter(category=category)
        if search:
            complaints_qs = complaints_qs.filter(title__icontains=search) | \
                           complaints_qs.filter(student__username__icontains=search)
            complaints_qs = complaints_qs.distinct()

    paginator = Paginator(complaints_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'administrator/all_complaints.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'page_title': 'All Complaints',
    })


@login_required
def waiting_for_assignment(request):
    """Admin: View complaints waiting for technician assignment."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied.')
        return redirect('accounts:login')

    complaints_qs = ComplaintRepository.get_waiting_for_assignment()
    paginator = Paginator(complaints_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'administrator/waiting_assignment.html', {
        'page_obj': page_obj,
        'page_title': 'Waiting for Assignment',
    })


@login_required
def assign_technician(request, pk):
    """Admin: Assign a technician to a complaint."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied.')
        return redirect('accounts:login')

    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        form = AssignTechnicianForm(request.POST)
        if form.is_valid():
            technician_id = form.cleaned_data['technician']
            notes = form.cleaned_data.get('notes', '')

            try:
                technician = User.objects.get(pk=technician_id, role='technician')
                ComplaintService.assign_technician(
                    complaint=complaint,
                    technician=technician,
                    assigned_by=request.user,
                    notes=notes
                )
                messages.success(
                    request,
                    f'Complaint #{complaint.pk} assigned to {technician.get_full_name() or technician.username}.'
                )
                return redirect('complaints:all_complaints')
            except (User.DoesNotExist, ValidationError, PermissionDenied) as e:
                messages.error(request, str(e))
    else:
        form = AssignTechnicianForm()

    return render(request, 'administrator/assign_technician.html', {
        'complaint': complaint,
        'form': form,
        'page_title': f'Assign Technician - Complaint #{complaint.pk}',
    })


@login_required
def close_complaint(request, pk):
    """Admin: Close a resolved complaint."""
    if not request.user.is_administrator:
        messages.error(request, 'Access denied.')
        return redirect('accounts:login')

    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        try:
            ComplaintService.close_complaint(complaint, request.user, notes)
            messages.success(request, f'Complaint #{complaint.pk} has been closed.')
            return redirect('complaints:complaint_detail', pk=pk)
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, str(e))

    return render(request, 'administrator/close_complaint.html', {
        'complaint': complaint,
        'page_title': f'Close Complaint #{complaint.pk}',
    })


# ─────────────────────── TECHNICIAN VIEWS ───────────────────────

@login_required
def my_tasks(request):
    """Technician: View assigned tasks."""
    if not request.user.is_technician:
        messages.error(request, 'Access denied. Technicians only.')
        return redirect('accounts:login')

    filter_form = ComplaintFilterForm(request.GET)
    tasks_qs = ComplaintRepository.get_by_technician(request.user.pk)

    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        category = filter_form.cleaned_data.get('category')
        search = filter_form.cleaned_data.get('search')

        if status:
            tasks_qs = tasks_qs.filter(status=status)
        if category:
            tasks_qs = tasks_qs.filter(category=category)
        if search:
            tasks_qs = tasks_qs.filter(title__icontains=search)

    paginator = Paginator(tasks_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'technician/my_tasks.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'page_title': 'My Tasks',
    })


@login_required
def update_complaint_status(request, pk):
    """Technician: Update complaint status (In Progress / Resolved)."""
    if not request.user.is_technician:
        messages.error(request, 'Access denied.')
        return redirect('accounts:login')

    complaint = get_object_or_404(Complaint, pk=pk)

    if complaint.assigned_technician != request.user:
        messages.error(request, 'You can only update complaints assigned to you.')
        return redirect('complaints:my_tasks')

    if request.method == 'POST':
        form = UpdateStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            notes = form.cleaned_data.get('notes', '')

            try:
                ComplaintService.update_status_by_technician(
                    complaint=complaint,
                    technician=request.user,
                    new_status=new_status,
                    notes=notes
                )
                status_labels = {
                    'in_progress': 'In Progress',
                    'resolved': 'Resolved',
                }
                messages.success(
                    request,
                    f'Complaint #{complaint.pk} marked as {status_labels.get(new_status, new_status)}.'
                )
                return redirect('complaints:complaint_detail', pk=pk)
            except (ValidationError, PermissionDenied) as e:
                messages.error(request, str(e))
    else:
        # Pre-select appropriate status based on current
        initial_status = 'in_progress'
        if complaint.status == 'in_progress':
            initial_status = 'resolved'
        form = UpdateStatusForm(initial={'new_status': initial_status})

    return render(request, 'technician/update_status.html', {
        'complaint': complaint,
        'form': form,
        'page_title': f'Update Complaint #{complaint.pk}',
    })
