from io import StringIO
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from apps.complaints.models import Complaint
from apps.locations.models import CampusLocation, ComplaintCategory


User = get_user_model()


class AdministratorSetupAndRoutingTests(TestCase):
    def test_setup_command_creates_idempotent_hashed_administrators(self):
        output = StringIO()
        call_command('initialize_cewms_administrators', stdout=output)
        for username, password in [('Lincoln1234', 'Ignatius12345'), ('Menny-wizzy1', 'menny1234')]:
            user = User.objects.get(username=username)
            self.assertEqual(user.user_type, 'SYSTEM_ADMIN')
            self.assertTrue(user.check_password(password))
            self.assertNotEqual(user.password, password)
            self.assertEqual(authenticate(username=username, password=password), user)
        call_command('initialize_cewms_administrators')
        self.assertEqual(User.objects.filter(username__in=['Lincoln1234', 'Menny-wizzy1']).count(), 2)

    def test_system_admin_routes_to_dedicated_dashboard_and_student_is_denied(self):
        call_command('initialize_cewms_administrators')
        self.assertTrue(self.client.login(username='Lincoln1234', password='Ignatius12345'))
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('accounts:administrator_dashboard'))
        self.assertContains(response, 'Administrator Dashboard')
        self.client.logout()
        student = User.objects.create_user(username='student', password='student-password', user_type='STUDENT')
        self.client.force_login(student)
        response = self.client.get(reverse('accounts:administrator_dashboard'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_role_login_destinations_remain_distinct(self):
        management = User.objects.create_user(username='management', password='test-password', user_type='ESTATES_ADMIN')
        engineer = User.objects.create_user(username='engineer', password='test-password', user_type='MAINTENANCE_WORKER')
        student = User.objects.create_user(username='student', password='test-password', user_type='STUDENT')
        for user, destination in ((management, 'accounts:management_dashboard'), (engineer, 'complaints:officer_dashboard'), (student, 'accounts:dashboard')):
            self.client.force_login(user)
            response = self.client.get(reverse('accounts:login'))
            self.client.logout()
            # LoginView only calculates its destination after a successful POST.
            response = self.client.post(reverse('accounts:login'), {'username': user.username, 'password': 'test-password'})
            self.assertRedirects(response, reverse(destination))
            self.client.logout()

    def test_management_dashboard_actions_stay_in_cewms_after_relogin(self):
        manager = User.objects.create_user(username='manager', password='test-password', user_type='ESTATES_ADMIN')
        location = CampusLocation.objects.create(name='Management Building', code='MGMT-01')
        category = ComplaintCategory.objects.create(name='Management Test')
        complaint = Complaint.objects.create(
            reference_number='CMP-MGMT-001', complaint_title='Review me',
            category=category, location=location, complaint_details='Test complaint',
        )
        for _ in range(2):
            self.assertTrue(self.client.login(username='manager', password='test-password'))
            response = self.client.get(reverse('accounts:management_dashboard'))
            self.assertContains(response, reverse('complaints:management_complaints'))
            self.assertContains(response, reverse('complaints:assign_complaint', args=[complaint.id]))
            self.assertNotContains(response, '/admin/')
            self.assertEqual(self.client.get(reverse('complaints:management_complaints')).status_code, 200)
            self.assertEqual(self.client.get(reverse('complaints:assign_complaint', args=[complaint.id])).status_code, 200)
            self.client.logout()
