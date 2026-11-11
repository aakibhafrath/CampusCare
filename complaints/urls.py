"""
Complaints URL Configuration
"""
from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    # Student
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('my/', views.my_complaints, name='my_complaints'),

    # Shared (access controlled in view)
    path('<int:pk>/', views.complaint_detail, name='complaint_detail'),

    # Admin
    path('all/', views.all_complaints, name='all_complaints'),
    path('waiting/', views.waiting_for_assignment, name='waiting_for_assignment'),
    path('<int:pk>/assign/', views.assign_technician, name='assign_technician'),
    path('<int:pk>/close/', views.close_complaint, name='close_complaint'),

    # Technician
    path('tasks/', views.my_tasks, name='my_tasks'),
    path('<int:pk>/update/', views.update_complaint_status, name='update_status'),
]

