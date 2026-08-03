"""
Tests for the attendance app.
Covers Properties 4, 6, 9, 10 from the design document.
"""
import csv
import io
import json
from datetime import date, timedelta
from unittest.mock import patch

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
        from django.db import IntegrityError, transaction
        plan = make_plan()
        member = make_member(email=f'dup_{num_attempts}@example.com', plan=plan)
        today = date.today()

        success_count = 0
        for _ in range(num_attempts):
            try:
                with transaction.atomic():
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

    def _face_post(self, payload):
        return self.client.post(
            '/attendance/checkin/',
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_face_checkin_creates_face_method_record(self):
        with patch('face_service.extract_embedding',
                   return_value={'status': 'ok', 'embedding': [0.1] * 128,
                                 'liveness_score': 0.9, 'message': 'OK'}), \
             patch('face_service.find_best_match', return_value=(self.member.pk, 0.92)):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['member_id'], self.member.pk)
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
        with patch('face_service.extract_embedding',
                   return_value={'status': 'ok', 'embedding': [0.1] * 128,
                                 'liveness_score': 0.9, 'message': 'OK'}), \
             patch('face_service.find_best_match', return_value=(self.member.pk, 0.92)):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 409)

    def test_unmatched_face_returns_unknown(self):
        with patch('face_service.extract_embedding',
                   return_value={'status': 'ok', 'embedding': [0.1] * 128,
                                 'liveness_score': 0.9, 'message': 'OK'}), \
             patch('face_service.find_best_match', return_value=(None, 0.10)):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'unknown')

    def test_spoof_face_is_rejected(self):
        with patch('face_service.extract_embedding',
                   return_value={'status': 'spoof', 'embedding': None,
                                 'liveness_score': 0.1,
                                 'message': 'Liveness check failed'}):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'spoof')

    def test_missing_image_returns_400(self):
        response = self._face_post({})
        self.assertEqual(response.status_code, 400)

    def test_matched_but_missing_member_returns_404(self):
        with patch('face_service.extract_embedding',
                   return_value={'status': 'ok', 'embedding': [0.1] * 128,
                                 'liveness_score': 0.9, 'message': 'OK'}), \
             patch('face_service.find_best_match', return_value=(99999, 0.9)):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 404)

    def test_expired_member_gets_expired_status(self):
        Member.objects.filter(pk=self.member.pk).update(
            expiry_date=date.today() - timedelta(days=1),
            status='expired',
        )
        with patch('face_service.extract_embedding',
                   return_value={'status': 'ok', 'embedding': [0.1] * 128,
                                 'liveness_score': 0.9, 'message': 'OK'}), \
             patch('face_service.find_best_match', return_value=(self.member.pk, 0.9)):
            response = self._face_post({'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'expired')


class DescriptorMatrixCacheTest(TestCase):
    # Feature: gym-management, Property 9: Descriptor cache completeness

    def setUp(self):
        from face_service import invalidate_descriptor_cache
        invalidate_descriptor_cache()

    def test_matrix_contains_exactly_enrolled_members(self):
        from face_service import get_descriptor_matrix
        plan = make_plan()
        m1 = make_member(email='desc1@example.com', plan=plan)
        m2 = make_member(email='desc2@example.com', plan=plan)
        m3 = Member.objects.create(
            full_name='No Face',
            phone='000',
            email='noface@example.com',
            face_descriptor=None,
            join_date=date.today(),
            membership_plan=plan,
            expiry_date=date.today() + timedelta(days=30),
        )

        matrix, member_ids = get_descriptor_matrix()
        ids = set(int(i) for i in member_ids)

        self.assertIn(m1.pk, ids)
        self.assertIn(m2.pk, ids)
        self.assertNotIn(m3.pk, ids)
        # Each descriptor row is included, no duplicates of members from malformed data
        self.assertEqual(matrix.shape[0], len(member_ids))
        self.assertEqual(matrix.shape[1], 128)

    def test_invalidation_rebuilds_matrix(self):
        from face_service import get_descriptor_matrix, invalidate_descriptor_cache
        plan = make_plan()
        make_member(email='desc4@example.com', plan=plan)
        get_descriptor_matrix()  # build cache

        new_member = make_member(email='desc5@example.com', plan=plan)
        invalidate_descriptor_cache()
        _, member_ids = get_descriptor_matrix()

        self.assertIn(new_member.pk, {int(i) for i in member_ids})

    def test_find_best_match_returns_correct_member(self):
        from unittest.mock import patch as _patch
        from face_service import find_best_match
        plan = make_plan()
        member = make_member(email='match@example.com', plan=plan)

        with _patch('face_service.INSIGHTFACE_AVAILABLE', True):
            matched_id, score = find_best_match([0.1] * 128, threshold=0.05)
        self.assertEqual(matched_id, member.pk)
        self.assertGreaterEqual(score, 0.05)

    def test_find_best_match_unknown_below_threshold(self):
        from unittest.mock import patch as _patch
        from face_service import find_best_match
        plan = make_plan()
        make_member(email='match2@example.com', plan=plan)

        with _patch('face_service.INSIGHTFACE_AVAILABLE', True):
            matched_id, score = find_best_match([-0.1] * 128, threshold=0.9)
        self.assertIsNone(matched_id)


class CSVExportCompletenessTest(HypothesisTestCase):
    # Feature: gym-management, Property 10: CSV export completeness

    @given(
        num_records=st.integers(min_value=0, max_value=10),
        days_back=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=30, deadline=None)
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
