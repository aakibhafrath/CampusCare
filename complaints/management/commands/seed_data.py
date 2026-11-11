"""
Management command: seed_data
Creates sample accounts and complaint data for demonstration purposes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from complaints.models import Complaint, StatusHistory
from complaints.services import ComplaintService
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Seed the database with sample demonstration data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Notification.objects.all().delete()
            StatusHistory.objects.all().delete()
            Complaint.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating demonstration accounts...')

        # Administrator
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@campuscare.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'administrator',
                'is_staff': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'  ✓ Created admin: admin / admin123')
        else:
            self.stdout.write(f'  → Admin already exists')

        # Technicians
        technicians = [
            {'username': 'tech1', 'first_name': 'Ahmed', 'last_name': 'Hassan', 'email': 'ahmed@campuscare.edu', 'phone_number': '+60-11-1111-1111'},
            {'username': 'tech2', 'first_name': 'Rajan', 'last_name': 'Kumar', 'email': 'rajan@campuscare.edu', 'phone_number': '+60-11-2222-2222'},
            {'username': 'tech3', 'first_name': 'Lim', 'last_name': 'Wei', 'email': 'lim@campuscare.edu', 'phone_number': '+60-11-3333-3333'},
        ]

        tech_objs = []
        for data in technicians:
            tech, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'role': 'technician'}
            )
            if created:
                tech.set_password('tech123')
                tech.save()
                self.stdout.write(f"  ✓ Created technician: {data['username']} / tech123")
            tech_objs.append(tech)

        # Students
        students_data = [
            {'username': 'student1', 'first_name': 'Ali', 'last_name': 'Abdullah', 'email': 'ali@student.edu', 'student_id': 'STU001', 'department': 'Computer Science'},
            {'username': 'student2', 'first_name': 'Priya', 'last_name': 'Sharma', 'email': 'priya@student.edu', 'student_id': 'STU002', 'department': 'Engineering'},
            {'username': 'student3', 'first_name': 'John', 'last_name': 'Lee', 'email': 'john@student.edu', 'student_id': 'STU003', 'department': 'Business'},
        ]

        student_objs = []
        for data in students_data:
            student, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'role': 'student'}
            )
            if created:
                student.set_password('student123')
                student.save()
                self.stdout.write(f"  ✓ Created student: {data['username']} / student123")
            student_objs.append(student)

        self.stdout.write('Creating sample complaints...')

        # Complaint data - various statuses
        complaints_data = [
            {
                'student': student_objs[0],
                'title': 'Air Conditioner Not Working',
                'category': 'electrical',
                'location': 'Block A, Room 204',
                'description': 'The air conditioner in room 204 has not been working for 3 days. Temperature is very high and affecting student concentration.',
                'status': 'submitted',
            },
            {
                'student': student_objs[0],
                'title': 'Broken Chair in Lecture Hall',
                'category': 'furniture',
                'location': 'Main Lecture Hall 1',
                'description': 'Several chairs in the lecture hall are broken. One chair collapsed during class causing a safety concern.',
                'status': 'assigned',
                'technician': tech_objs[0],
            },
            {
                'student': student_objs[1],
                'title': 'Water Leaking from Ceiling',
                'category': 'plumbing',
                'location': 'Library, 2nd Floor',
                'description': 'Water is dripping from the ceiling near the reference books section. Books may get damaged if not fixed urgently.',
                'status': 'in_progress',
                'technician': tech_objs[1],
            },
            {
                'student': student_objs[1],
                'title': 'Wi-Fi Not Available in Hostel',
                'category': 'network',
                'location': 'Hostel Block C',
                'description': 'The Wi-Fi connection in Hostel Block C has been down for 2 days. Students are unable to do their online assignments.',
                'status': 'resolved',
                'technician': tech_objs[2],
            },
            {
                'student': student_objs[2],
                'title': 'Projector Bulb Burned Out',
                'category': 'equipment',
                'location': 'Engineering Block, Room 305',
                'description': 'The projector in Room 305 is not working. The bulb appears to have burned out. Used for daily lectures.',
                'status': 'closed',
                'technician': tech_objs[0],
            },
            {
                'student': student_objs[2],
                'title': 'Broken Window Glass',
                'category': 'other',
                'location': 'Student Cafeteria',
                'description': 'One of the windows in the cafeteria has cracked glass. This poses a safety risk to students dining there.',
                'status': 'submitted',
            },
        ]

        for data in complaints_data:
            # Check if already exists
            if Complaint.objects.filter(title=data['title']).exists():
                self.stdout.write(f"  → Complaint already exists: {data['title'][:40]}")
                continue

            status = data.pop('status')
            technician = data.pop('technician', None)
            student = data.pop('student')

            # Create complaint via direct model (bypassing service to set any status)
            complaint = Complaint.objects.create(
                student=student,
                status='submitted',
                **data
            )

            # Initial status history
            StatusHistory.objects.create(
                complaint=complaint,
                old_status='',
                new_status='submitted',
                changed_by=student,
                notes='Complaint submitted.'
            )

            # Advance status as needed
            if status in ['assigned', 'in_progress', 'resolved', 'closed'] and technician:
                complaint.assigned_technician = technician
                complaint.status = 'assigned'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status='submitted',
                    new_status='assigned',
                    changed_by=admin,
                    notes=f'Assigned to {technician.get_full_name()}.'
                )
                # Create notification for student
                Notification.objects.create(
                    recipient=student,
                    complaint=complaint,
                    message=f'Your complaint "{complaint.title}" has been assigned to a technician.',
                    notification_type='status_change'
                )

            if status in ['in_progress', 'resolved', 'closed']:
                complaint.status = 'in_progress'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status='assigned',
                    new_status='in_progress',
                    changed_by=technician,
                    notes='Work started. Investigating the issue.'
                )
                Notification.objects.create(
                    recipient=student,
                    complaint=complaint,
                    message=f'Your complaint "{complaint.title}" is now In Progress.',
                    notification_type='status_change'
                )

            if status in ['resolved', 'closed']:
                complaint.status = 'resolved'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status='in_progress',
                    new_status='resolved',
                    changed_by=technician,
                    notes='Issue has been resolved successfully.'
                )
                Notification.objects.create(
                    recipient=student,
                    complaint=complaint,
                    message=f'Your complaint "{complaint.title}" has been resolved.',
                    notification_type='status_change'
                )

            if status == 'closed':
                complaint.status = 'closed'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status='resolved',
                    new_status='closed',
                    changed_by=admin,
                    notes='Complaint closed after verification.'
                )

            self.stdout.write(f"  ✓ Created complaint: #{complaint.pk} - {complaint.title[:40]} [{complaint.status}]")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Demo Login Credentials:')
        self.stdout.write('  Administrator : admin / admin123')
        self.stdout.write('  Student 1     : student1 / student123')
        self.stdout.write('  Student 2     : student2 / student123')
        self.stdout.write('  Student 3     : student3 / student123')
        self.stdout.write('  Technician 1  : tech1 / tech123')
        self.stdout.write('  Technician 2  : tech2 / tech123')
        self.stdout.write('  Technician 3  : tech3 / tech123')
        self.stdout.write('')
        self.stdout.write('Run the server: python manage.py runserver')

