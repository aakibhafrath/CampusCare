"""
CampusCare - Automated Tests
Tests for all modules: authentication, complaints, notifications, reports.
Includes positive and negative (unauthorized access) tests.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from complaints.models import Complaint, StatusHistory
from complaints.services import ComplaintService
from complaints.events import event_publisher, ComplaintStatusChangedEvent, EventPublisher
from complaints.observers import NotificationObserver, LoggingObserver
from notifications.models import Notification

User = get_user_model()


# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

def make_student(username='teststudent', password='testpass123'):
    return User.objects.create_user(
        username=username, password=password,
        first_name='Test', last_name='Student',
        role='student', email=f'{username}@test.edu'
    )


def make_admin(username='testadmin', password='testpass123'):
    return User.objects.create_user(
        username=username, password=password,
        first_name='Test', last_name='Admin',
        role='administrator', email=f'{username}@test.edu'
    )


def make_technician(username='testtech', password='testpass123'):
    return User.objects.create_user(
        username=username, password=password,
        first_name='Test', last_name='Tech',
        role='technician', email=f'{username}@test.edu'
    )


def make_complaint(student, **kwargs):
    defaults = {
        'title': 'Test Complaint',
        'category': 'electrical',
        'location': 'Block A',
        'description': 'Test description',
        'status': 'submitted',
    }
    defaults.update(kwargs)
    return Complaint.objects.create(student=student, **defaults)


# ════════════════════════════════════════════════════════════
#  1. AUTHENTICATION TESTS
# ════════════════════════════════════════════════════════════

class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_student_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'New',
            'last_name': 'Student',
            'username': 'newstudent',
            'email': 'new@test.edu',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.role, 'student')

    def test_student_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'teststudent',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('accounts:student_dashboard'))

    def test_admin_login_redirects_to_admin_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testadmin',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('accounts:admin_dashboard'))

    def test_technician_login_redirects_to_tech_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testtech',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('accounts:technician_dashboard'))

    def test_logout(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_invalid_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'nobody',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)

    def test_password_hashing(self):
        """Passwords must NOT be stored in plain text."""
        self.assertFalse(self.student.password.startswith('testpass'))
        self.assertTrue(self.student.check_password('testpass123'))


# ════════════════════════════════════════════════════════════
#  2. ROLE-BASED DASHBOARD TESTS
# ════════════════════════════════════════════════════════════

class DashboardAccessTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_student_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_student_can_access_student_dashboard(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_admin_dashboard(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)
        # Should redirect
        self.assertIn(response.status_code, [302, 403])

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_access_student_dashboard(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('accounts:student_dashboard'))
        # Must not get student dashboard
        self.assertNotEqual(response.status_code, 200)

    def test_technician_can_access_tech_dashboard(self):
        self.client.login(username='testtech', password='testpass123')
        response = self.client.get(reverse('accounts:technician_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_technician_cannot_access_admin_dashboard(self):
        self.client.login(username='testtech', password='testpass123')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)


# ════════════════════════════════════════════════════════════
#  3. COMPLAINT MANAGEMENT TESTS
# ════════════════════════════════════════════════════════════

class ComplaintSubmissionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_student_can_submit_complaint(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.post(reverse('complaints:submit_complaint'), {
            'title': 'Broken Light',
            'category': 'electrical',
            'location': 'Room 101',
            'description': 'The light bulb is broken.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Complaint.objects.filter(title='Broken Light').exists())

    def test_complaint_has_submitted_status_on_creation(self):
        complaint = ComplaintService.submit_complaint(
            student=self.student,
            title='Test',
            category='electrical',
            location='Room 1',
            description='Desc'
        )
        self.assertEqual(complaint.status, 'submitted')

    def test_complaint_submission_creates_status_history(self):
        complaint = ComplaintService.submit_complaint(
            student=self.student, title='T', category='electrical', location='L', description='D'
        )
        self.assertTrue(StatusHistory.objects.filter(complaint=complaint).exists())

    def test_non_student_cannot_submit_complaint(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.post(reverse('complaints:submit_complaint'), {
            'title': 'Hack', 'category': 'electrical', 'location': 'X', 'description': 'X'
        })
        # Admin should be redirected away, not get a 200
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(Complaint.objects.filter(title='Hack').exists())

    def test_student_can_view_own_complaints(self):
        complaint = make_complaint(self.student)
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('complaints:my_complaints'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_view_another_students_complaint(self):
        """Security: student cannot access another student's complaint detail."""
        other_student = make_student('other_student')
        complaint = make_complaint(other_student)
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('complaints:complaint_detail', args=[complaint.pk]))
        # Should redirect with error, not 200
        self.assertNotEqual(response.status_code, 200)


# ════════════════════════════════════════════════════════════
#  4. ADMIN COMPLAINT MANAGEMENT TESTS
# ════════════════════════════════════════════════════════════

class AdminComplaintTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()
        self.complaint = make_complaint(self.student)

    def test_admin_can_view_all_complaints(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('complaints:all_complaints'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_assign_technician(self):
        ComplaintService.assign_technician(
            complaint=self.complaint,
            technician=self.tech,
            assigned_by=self.admin,
            notes='Please fix ASAP.'
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'assigned')
        self.assertEqual(self.complaint.assigned_technician, self.tech)

    def test_non_admin_cannot_assign_technician(self):
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            ComplaintService.assign_technician(
                complaint=self.complaint,
                technician=self.tech,
                assigned_by=self.student,  # student, not admin!
            )

    def test_cannot_assign_already_assigned_complaint(self):
        from django.core.exceptions import ValidationError
        self.complaint.status = 'assigned'
        self.complaint.save()
        with self.assertRaises(ValidationError):
            ComplaintService.assign_technician(
                complaint=self.complaint,
                technician=self.tech,
                assigned_by=self.admin,
            )

    def test_admin_can_close_resolved_complaint(self):
        self.complaint.status = 'resolved'
        self.complaint.assigned_technician = self.tech
        self.complaint.save()
        ComplaintService.close_complaint(self.complaint, self.admin)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'closed')

    def test_cannot_close_non_resolved_complaint(self):
        from django.core.exceptions import ValidationError
        # complaint is 'submitted', cannot be closed
        with self.assertRaises(ValidationError):
            ComplaintService.close_complaint(self.complaint, self.admin)


# ════════════════════════════════════════════════════════════
#  5. TECHNICIAN TESTS
# ════════════════════════════════════════════════════════════

class TechnicianTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()
        self.other_tech = make_technician('other_tech')
        self.complaint = make_complaint(self.student, status='assigned', assigned_technician=self.tech)

    def test_technician_can_view_my_tasks(self):
        self.client.login(username='testtech', password='testpass123')
        response = self.client.get(reverse('complaints:my_tasks'))
        self.assertEqual(response.status_code, 200)

    def test_technician_can_update_to_in_progress(self):
        ComplaintService.update_status_by_technician(
            complaint=self.complaint,
            technician=self.tech,
            new_status='in_progress',
            notes='Started working.'
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'in_progress')

    def test_technician_can_resolve_in_progress_complaint(self):
        self.complaint.status = 'in_progress'
        self.complaint.save()
        ComplaintService.update_status_by_technician(
            complaint=self.complaint,
            technician=self.tech,
            new_status='resolved',
            notes='Fixed.'
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')

    def test_technician_cannot_update_another_technicians_complaint(self):
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            ComplaintService.update_status_by_technician(
                complaint=self.complaint,
                technician=self.other_tech,  # wrong technician!
                new_status='in_progress',
            )

    def test_invalid_status_transition_raises_error(self):
        from django.core.exceptions import ValidationError
        # Cannot jump from assigned to resolved (must go through in_progress)
        with self.assertRaises(ValidationError):
            ComplaintService.update_status_by_technician(
                complaint=self.complaint,
                technician=self.tech,
                new_status='resolved',  # Invalid: must be in_progress first
            )


# ════════════════════════════════════════════════════════════
#  6. STATUS HISTORY TESTS
# ════════════════════════════════════════════════════════════

class StatusHistoryTests(TestCase):

    def setUp(self):
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_status_history_created_on_submit(self):
        complaint = ComplaintService.submit_complaint(
            student=self.student, title='T', category='electrical',
            location='L', description='D'
        )
        history = StatusHistory.objects.filter(complaint=complaint)
        self.assertTrue(history.exists())
        self.assertEqual(history.first().new_status, 'submitted')

    def test_status_history_created_on_assignment(self):
        complaint = make_complaint(self.student)
        ComplaintService.assign_technician(complaint, self.tech, self.admin)
        history = StatusHistory.objects.filter(complaint=complaint, new_status='assigned')
        self.assertTrue(history.exists())

    def test_status_history_created_on_resolve(self):
        complaint = make_complaint(self.student, status='in_progress', assigned_technician=self.tech)
        ComplaintService.update_status_by_technician(complaint, self.tech, 'resolved', 'Done.')
        history = StatusHistory.objects.filter(complaint=complaint, new_status='resolved')
        self.assertTrue(history.exists())


# ════════════════════════════════════════════════════════════
#  7. OBSERVER PATTERN TESTS
# ════════════════════════════════════════════════════════════

class ObserverPatternTests(TestCase):

    def test_event_publisher_subscribe(self):
        publisher = EventPublisher()
        observer = NotificationObserver()
        publisher.subscribe('test_event', observer)
        self.assertEqual(publisher.get_subscriber_count('test_event'), 1)

    def test_event_publisher_unsubscribe(self):
        publisher = EventPublisher()
        observer = NotificationObserver()
        publisher.subscribe('test_event', observer)
        publisher.unsubscribe('test_event', observer)
        self.assertEqual(publisher.get_subscriber_count('test_event'), 0)

    def test_event_publisher_publish_calls_observers(self):
        """EventPublisher.publish() must call observer.update()."""
        events_received = []

        class TestObserver:
            def update(self, event):
                events_received.append(event)

        publisher = EventPublisher()
        observer = TestObserver()
        publisher.subscribe(ComplaintStatusChangedEvent.EVENT_TYPE, observer)

        event = ComplaintStatusChangedEvent(
            complaint_id=1,
            complaint_title='Test',
            old_status='submitted',
            new_status='assigned',
            student_id=1,
            changed_by_id=1,
        )
        publisher.publish(event)
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].event_type, ComplaintStatusChangedEvent.EVENT_TYPE)


# ════════════════════════════════════════════════════════════
#  8. NOTIFICATION TESTS
# ════════════════════════════════════════════════════════════

class NotificationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_notification_created_when_assigned(self):
        """NotificationObserver must create notification on assignment."""
        complaint = make_complaint(self.student)
        # Use transaction test client - on_commit fires immediately in tests
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        ComplaintService.assign_technician(complaint, self.tech, self.admin)
        # In Django test, on_commit fires immediately
        notifs = Notification.objects.filter(recipient=self.student, complaint=complaint)
        self.assertTrue(notifs.exists())

    def test_student_can_view_notifications(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)

    def test_mark_notification_as_read(self):
        notif = Notification.objects.create(
            recipient=self.student,
            message='Test notification',
            is_read=False
        )
        notif.mark_as_read()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_notifications_read(self):
        for i in range(3):
            Notification.objects.create(recipient=self.student, message=f'Notif {i}', is_read=False)
        self.client.login(username='teststudent', password='testpass123')
        self.client.post(reverse('notifications:mark_all_read'))
        unread = Notification.objects.filter(recipient=self.student, is_read=False)
        self.assertEqual(unread.count(), 0)

    def test_unread_count_api(self):
        Notification.objects.create(recipient=self.student, message='Test', is_read=False)
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertEqual(data['count'], 1)


# ════════════════════════════════════════════════════════════
#  9. REPORTS TESTS
# ════════════════════════════════════════════════════════════

class ReportsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()
        self.admin = make_admin()
        self.tech = make_technician()

    def test_admin_can_access_reports(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_reports(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_reports_show_real_data(self):
        make_complaint(self.student, status='submitted')
        make_complaint(self.student, status='resolved', assigned_technician=self.tech)
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertIn('total_complaints', response.context)
        self.assertEqual(response.context['total_complaints'], 2)

    def test_tech_cannot_access_reports(self):
        self.client.login(username='testtech', password='testpass123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertNotEqual(response.status_code, 200)


# ════════════════════════════════════════════════════════════
#  10. PROFILE TESTS
# ════════════════════════════════════════════════════════════

class ProfileTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_student()

    def test_profile_page_loads(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.edu',
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Updated')
