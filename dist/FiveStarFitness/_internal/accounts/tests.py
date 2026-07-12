"""
Tests for the accounts app — authentication and role-based access.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase


def make_user(username, role='staff', password='pass123'):
    user = User.objects.create_user(username=username, password=password)
    user.profile.role = role
    user.profile.save()
    return user


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('teststaff', role='staff')

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post('/accounts/login/', {
            'username': 'teststaff',
            'password': 'pass123',
        })
        self.assertRedirects(response, '/dashboard/')

    def test_invalid_login_stays_on_login_page(self):
        response = self.client.post('/accounts/login/', {
            'username': 'teststaff',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username')

    def test_unauthenticated_access_redirects_to_login(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_logout_redirects_to_login(self):
        self.client.login(username='teststaff', password='pass123')
        response = self.client.get('/accounts/logout/')
        self.assertRedirects(response, '/accounts/login/')


class RoleAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_user', role='admin')
        self.staff = make_user('staff_user', role='staff')

    def test_admin_can_access_billing(self):
        self.client.login(username='admin_user', password='pass123')
        response = self.client.get('/billing/plans/')
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_billing(self):
        self.client.login(username='staff_user', password='pass123')
        response = self.client.get('/billing/plans/')
        self.assertEqual(response.status_code, 403)

    def test_staff_can_access_attendance(self):
        self.client.login(username='staff_user', password='pass123')
        response = self.client.get('/attendance/')
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_members(self):
        self.client.login(username='staff_user', password='pass123')
        response = self.client.get('/members/')
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_csv_export(self):
        self.client.login(username='staff_user', password='pass123')
        response = self.client.get('/attendance/export/')
        self.assertEqual(response.status_code, 403)
