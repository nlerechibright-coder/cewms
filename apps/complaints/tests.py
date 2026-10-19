from io import BytesIO
import tempfile
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.locations.models import CampusLocation, ComplaintCategory
from .models import Complaint, ComplaintAttachment, WorkAssignment, StatusHistory

User = get_user_model()


def make_test_png():
    image = Image.new('RGB', (2, 2), color='red')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


class ComplaintModelTest(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
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

    def test_complaint_photo_upload_storage_and_student_display(self):
        self.client.force_login(self.user)
        photo = SimpleUploadedFile(
            'issue.png',
            make_test_png(),
            content_type='image/png',
        )
        response = self.client.post(reverse('complaints:public_submit'), {
            'complaint_title': 'Broken light',
            'location': self.location.pk,
            'category': self.category.pk,
            'complaint_details': 'The corridor light is broken.',
            'reporter_declared_urgency': 'NORMAL',
            'photo': photo,
        })

        self.assertRedirects(response, reverse('complaints:submission_success'))
        complaint = Complaint.objects.get(complaint_title='Broken light')
        attachment = complaint.attachments.get()
        self.assertEqual(attachment.file.name.split('/')[-1], 'issue.png')
        self.assertTrue(attachment.file.storage.exists(attachment.file.name))
        self.assertTrue(attachment.file.url.startswith('/media/'))

        detail = self.client.get(reverse(
            'complaints:complaint_detail', args=[complaint.reference_number]
        ))
        image_url = reverse('complaints:attachment_image', args=[attachment.pk])
        self.assertContains(detail, f'src="{image_url}"')
        image_response = self.client.get(image_url)
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response['Content-Type'], 'image/png')
        image_response.close()

    def test_tracking_displays_photo_after_token_verification(self):
        complaint = Complaint.objects.create(
            reference_number='CMP-TRACK-001',
            category=self.category,
            location=self.location,
            complaint_details='Test tracking image.',
        )
        attachment = ComplaintAttachment.objects.create(
            complaint=complaint,
            file=SimpleUploadedFile(
                'track.png',
                make_test_png(),
                content_type='image/png',
            ),
        )
        from .views import generate_tracking_token_hash
        complaint.tracking_token_hash = generate_tracking_token_hash('secret-tracking-token')
        complaint.save(update_fields=['tracking_token_hash'])

        response = self.client.post(reverse('complaints:track_complaint'), {
            'reference_number': complaint.reference_number,
            'tracking_token': 'secret-tracking-token',
        })
        self.assertContains(response, reverse('complaints:attachment_image', args=[attachment.pk]))
        image_response = self.client.get(reverse('complaints:attachment_image', args=[attachment.pk]))
        self.assertEqual(image_response.status_code, 200)
        image_response.close()

    def test_complaint_without_photo_renders_fallback(self):
        complaint = Complaint.objects.create(
            reference_number='CMP-NO-PHOTO',
            reporter=self.user,
            category=self.category,
            location=self.location,
            complaint_details='No image attached.',
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse(
            'complaints:complaint_detail', args=[complaint.reference_number]
        ))
        self.assertContains(response, 'No photo was attached to this complaint.')
        self.assertNotContains(response, '<img')

    def test_management_and_assigned_engineer_can_view_photo(self):
        complaint = Complaint.objects.create(
            reference_number='CMP-VIEW-001',
            category=self.category,
            location=self.location,
            complaint_details='Photo permissions.',
        )
        attachment = ComplaintAttachment.objects.create(
            complaint=complaint,
            file=SimpleUploadedFile(
                'access.png',
                make_test_png(),
                content_type='image/png',
            ),
        )
        image_url = reverse('complaints:attachment_image', args=[attachment.pk])

        self.client.force_login(self.admin)
        management_page = self.client.get(reverse(
            'complaints:assign_complaint', args=[complaint.pk]
        ))
        self.assertContains(management_page, image_url)
        image_response = self.client.get(image_url)
        self.assertEqual(image_response.status_code, 200)
        image_response.close()

        self.client.force_login(self.officer)
        self.assertEqual(self.client.get(image_url).status_code, 403)
        assignment = WorkAssignment.objects.create(
            complaint=complaint, officer=self.officer, assigned_by=self.admin
        )
        engineer_page = self.client.get(reverse(
            'complaints:officer_job_detail', args=[assignment.pk]
        ))
        self.assertContains(engineer_page, image_url)
        image_response = self.client.get(image_url)
        self.assertEqual(image_response.status_code, 200)
        image_response.close()

    def test_assignment_and_status_update_workflow_remains_functional(self):
        complaint = Complaint.objects.create(
            reference_number='CMP-WORKFLOW-001',
            category=self.category,
            location=self.location,
            complaint_details='Workflow regression.',
        )
        self.client.force_login(self.admin)
        assignment_response = self.client.post(
            reverse('complaints:assign_complaint', args=[complaint.pk]),
            {'engineer': self.officer.pk, 'notes': 'Please inspect.'},
        )
        self.assertRedirects(assignment_response, reverse('complaints:management_complaints'))
        assignment = WorkAssignment.objects.get(complaint=complaint)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'ASSIGNED')

        self.client.force_login(self.officer)
        update_response = self.client.post(
            reverse('complaints:officer_job_detail', args=[assignment.pk]),
            {'status': 'IN_PROGRESS', 'notes': 'Work started.'},
        )
        self.assertRedirects(
            update_response,
            reverse('complaints:officer_job_detail', args=[assignment.pk]),
        )
        complaint.refresh_from_db()
        assignment.refresh_from_db()
        self.assertEqual(complaint.status, 'IN_PROGRESS')
        self.assertEqual(assignment.status, 'IN_PROGRESS')

