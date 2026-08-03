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


class ForcePasswordChangeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('flagged_admin', role='admin')
        self.user.profile.must_change_password = True
        self.user.profile.save(update_fields=['must_change_password'])

    def test_login_redirects_to_password_change_when_flagged(self):
        response = self.client.post('/accounts/login/', {
            'username': 'flagged_admin',
            'password': 'pass123',
        })
        self.assertRedirects(response, '/accounts/password/')

    def test_flagged_user_is_blocked_from_app_pages(self):
        self.client.login(username='flagged_admin', password='pass123')
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/password/')

    def test_password_change_clears_flag_and_restores_access(self):
        self.client.login(username='flagged_admin', password='pass123')
        response = self.client.post('/accounts/password/', {
            'old_password': 'pass123',
            'new_password1': 'NewStrongPass!42',
            'new_password2': 'NewStrongPass!42',
        })
        self.assertRedirects(response, '/dashboard/')
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.must_change_password)
        # Old password no longer works
        self.assertFalse(self.client.login(username='flagged_admin', password='pass123'))
        self.assertTrue(self.client.login(username='flagged_admin', password='NewStrongPass!42'))

    def test_normal_user_is_not_intercepted(self):
        normal = make_user('normal_user', role='staff')
        self.client.login(username='normal_user', password='pass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
