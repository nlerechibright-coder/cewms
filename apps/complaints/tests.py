from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.locations.models import CampusLocation, ComplaintCategory
from .models import Complaint, WorkAssignment, StatusHistory

User = get_user_model()

class ComplaintModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type='STUDENT'
        )
        self.officer = User.objects.create_user(
            username='officer',
            password='testpass123',
            user_type='MAINTENANCE_WORKER'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            user_type='ESTATES_ADMIN'
        )
        self.location = CampusLocation.objects.create(
            name='Test Building',
            code='TEST-01'
        )
        self.category = ComplaintCategory.objects.create(
            name='Test Category',
            description='Test description'
        )

    def test_complaint_creation(self):
        """Test that a complaint can be created with Chapter 3 fields"""
        complaint = Complaint.objects.create(
            reference_number='CMP-TEST-001',
            full_name='John Doe',
            contact_address='123 Test St',
            phone='1234567890',
            complaint_title='Test Complaint',
            category=self.category,
            location=self.location,
            location_desc='Near the entrance',
            complaint_details='This is a test complaint',
            status='SUBMITTED'
        )
        self.assertEqual(complaint.full_name, 'John Doe')
        self.assertEqual(complaint.complaint_title, 'Test Complaint')
        self.assertEqual(complaint.status, 'SUBMITTED')

    def test_work_assignment_creation(self):
        """Test that a work assignment can be created"""
        complaint = Complaint.objects.create(
            reference_number='CMP-TEST-002',
            category=self.category,
            location=self.location,
            complaint_details='Test'
        )
        assignment = WorkAssignment.objects.create(
            complaint=complaint,
            officer=self.officer,
            assigned_by=self.admin,
            status='PENDING',
            notes='Test assignment'
        )
        self.assertEqual(assignment.officer, self.officer)
        self.assertEqual(assignment.status, 'PENDING')

    def test_status_history_creation(self):
        """Test that status history can be recorded"""
        complaint = Complaint.objects.create(
            reference_number='CMP-TEST-003',
            category=self.category,
            location=self.location,
            complaint_details='Test'
        )
        history = StatusHistory.objects.create(
            complaint=complaint,
            status_value='SUBMITTED',
            changed_by=self.user,
            remarks='Initial submission'
        )
        self.assertEqual(history.status_value, 'SUBMITTED')
        self.assertEqual(history.remarks, 'Initial submission')

    def test_submitted_complaint_is_visible_in_management_listing(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('complaints:public_submit'), {
            'complaint_title': 'Broken light',
            'location': self.location.pk,
            'category': self.category.pk,
            'complaint_details': 'The corridor light is broken.',
            'reporter_declared_urgency': 'NORMAL',
        })
        self.assertRedirects(response, reverse('complaints:submission_success'))
        complaint = Complaint.objects.get(complaint_title='Broken light')
        response = self.client.get(reverse('complaints:management_complaints'))
        self.assertContains(response, complaint.reference_number)
