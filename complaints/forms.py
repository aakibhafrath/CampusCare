"""
Complaints Forms - Presentation Layer
"""
from django import forms
from .models import Complaint


class ComplaintSubmitForm(forms.ModelForm):
    """Form for student complaint submission."""
    class Meta:
        model = Complaint
        fields = ['title', 'category', 'location', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title for your complaint'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Block A, Room 204'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue in detail...'
            }),
        }


class AssignTechnicianForm(forms.Form):
    """Form for administrator to assign a technician."""
    technician = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes for the assignment...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        technicians = User.objects.filter(role='technician', is_active=True)
        self.fields['technician'].choices = [('', '-- Select Technician --')] + [
            (t.pk, f"{t.get_full_name() or t.username} ({t.username})")
            for t in technicians
        ]


class UpdateStatusForm(forms.Form):
    """Form for technician to update complaint status."""
    STATUS_CHOICES = [
        ('in_progress', 'Mark as In Progress'),
        ('resolved', 'Mark as Resolved'),
    ]
    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Progress notes (optional)...'
        })
    )


class ComplaintFilterForm(forms.Form):
    """Form for filtering complaints list."""
    STATUS_CHOICES = [('', 'All Statuses')] + Complaint.STATUS_CHOICES
    CATEGORY_CHOICES = [('', 'All Categories')] + Complaint.CATEGORY_CHOICES

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Search complaints...'
        })
    )

