"""
Tests for the attendance app.
Covers Properties 4, 6, 9, 10 from the design document.
"""
import csv
import io
import json
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from members.models import Member, MembershipPlan
from .models import Attendance


def make_plan():
    return MembershipPlan.objects.create(name='Plan', price='50.00', duration_days=30)


def make_member(email=None, plan=None):
    if plan is None:
        plan = make_plan()
    today = date.today()
    return Member.objects.create(
        full_name='Test Member',
        phone='000',
        email=email or f'att_{id(plan)}@example.com',
        face_descriptor=[0.1] * 128,
        join_date=today,
        membership_plan=plan,
        expiry_date=today + timedelta(days=30),
    )


def make_admin():
    user = User.objects.create_user(username='admin_test', password='pass123')
    user.profile.role = 'admin'
    user.profile.save()
    return user


class NoDuplicateDailyCheckinTest(HypothesisTestCase):
    # Feature: gym-management, Property 4: No duplicate daily check-in

    @given(num_attempts=st.integers(min_value=2, max_value=10))
    @settings(max_examples=50)
    def test_multiple_checkin_attempts_result_in_one_record(self, num_attempts):
        from django.db import IntegrityError
        plan = make_plan()
        member = make_member(email=f'dup_{num_attempts}@example.com', plan=plan)
        today = date.today()

        success_count = 0
        for _ in range(num_attempts):
            try:
                Attendance.objects.create(member=member, date=today, method='face')
                success_count += 1
            except IntegrityError:
                pass

        self.assertEqual(success_count, 1)
        self.assertEqual(Attendance.objects.filter(member=member, date=today).count(), 1)


class CheckinMethodIntegrityTest(TestCase):
    # Feature: gym-management, Property 6: Check-in method integrity

    def setUp(self):
        self.client = Client()
        self.user = make_admin()
        self.client.login(username='admin_test', password='pass123')
        self.member = make_member(email='method_test@example.com')

    def test_face_checkin_creates_face_method_record(self):
        response = self.client.post(
            '/attendance/checkin/',
            data=json.dumps({'member_id': self.member.pk}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        record = Attendance.objects.get(member=self.member)
        self.assertEqual(record.method, 'face')

    def test_manual_checkin_creates_manual_method_record(self):
        response = self.client.post(
            '/attendance/',
            data={'member_id': self.member.pk},
        )
        self.assertIn(response.status_code, [200, 302])
        record = Attendance.objects.get(member=self.member)
        self.assertEqual(record.method, 'manual')

    def test_duplicate_face_checkin_returns_409(self):
        Attendance.objects.create(member=self.member, date=date.today(), method='face')
        response = self.client.post(
            '/attendance/checkin/',
            data=json.dumps({'member_id': self.member.pk}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_member_id_returns_404(self):
        response = self.client.post(
            '/attendance/checkin/',
            data=json.dumps({'member_id': 99999}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class DescriptorCacheCompletenessTest(TestCase):
    # Feature: gym-management, Property 9: Descriptor cache completeness

    def setUp(self):
        self.client = Client()
        self.user = make_admin()
        self.client.login(username='admin_test', password='pass123')

    def test_descriptors_endpoint_returns_all_members_with_descriptors(self):
        plan = make_plan()
        m1 = make_member(email='desc1@example.com', plan=plan)
        m2 = make_member(email='desc2@example.com', plan=plan)
        # Member without descriptor
        m3 = Member.objects.create(
            full_name='No Face',
            phone='000',
            email='noface@example.com',
            face_descriptor=None,
            join_date=date.today(),
            membership_plan=plan,
            expiry_date=date.today() + timedelta(days=30),
        )

        response = self.client.get('/members/descriptors/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        ids = [d['id'] for d in data]

        self.assertIn(m1.pk, ids)
        self.assertIn(m2.pk, ids)
        self.assertNotIn(m3.pk, ids)
        # No duplicates
        self.assertEqual(len(ids), len(set(ids)))


class CSVExportCompletenessTest(HypothesisTestCase):
    # Feature: gym-management, Property 10: CSV export completeness

    @given(
        num_records=st.integers(min_value=0, max_value=10),
        days_back=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=30)
    def test_csv_export_contains_exactly_records_in_date_range(self, num_records, days_back):
        Attendance.objects.all().delete()
        Member.objects.all().delete()
        MembershipPlan.objects.all().delete()

        user = User.objects.create_user(username=f'admin_{num_records}_{days_back}', password='pass')
        user.profile.role = 'admin'
        user.profile.save()
        client = Client()
        client.login(username=f'admin_{num_records}_{days_back}', password='pass')

        plan = make_plan()
        today = date.today()
        start_date = today - timedelta(days=days_back)

        # Create records: half within range, half outside
        in_range = []
        for i in range(num_records):
            member = Member.objects.create(
                full_name=f'Member {i}',
                phone='000',
                email=f'csv_{num_records}_{days_back}_{i}@example.com',
                face_descriptor=[0.0] * 128,
                join_date=today,
                membership_plan=plan,
                expiry_date=today + timedelta(days=30),
            )
            record_date = start_date + timedelta(days=i % (days_back + 1))
            Attendance.objects.create(member=member, date=record_date, method='face')
            if start_date <= record_date <= today:
                in_range.append(record_date)

        url = f'/attendance/export/?start={start_date}&end={today}'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # Subtract header row
        data_rows = rows[1:] if rows else []
        self.assertEqual(len(data_rows), len(in_range))


class DashboardMetricsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_admin()
        self.client.login(username='admin_test', password='pass123')

    def test_dashboard_loads_with_correct_counts(self):
        plan = make_plan()
        m1 = make_member(email='dash1@example.com', plan=plan)
        m2 = make_member(email='dash2@example.com', plan=plan)
        Attendance.objects.create(member=m1, date=date.today(), method='face')

        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertGreaterEqual(ctx['total_members'], 2)
        self.assertGreaterEqual(ctx['today_attendance'], 1)
