"""
Tests for the members app.
Covers Properties 1, 3, 5 from the design document.
"""
import json
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from .models import Member, MembershipPlan


def make_plan(duration_days=30):
    return MembershipPlan.objects.create(name='Test Plan', price='50.00', duration_days=duration_days)


def make_member(plan=None, join_date=None, **kwargs):
    if plan is None:
        plan = make_plan()
    if join_date is None:
        join_date = date.today()
    defaults = {
        'full_name': 'Test User',
        'phone': '1234567890',
        'email': f'test_{id(plan)}@example.com',
        'face_descriptor': [0.1] * 128,
        'join_date': join_date,
        'membership_plan': plan,
        'expiry_date': join_date + timedelta(days=plan.duration_days),
    }
    defaults.update(kwargs)
    return Member(**defaults)


class ExpiryDateDerivationTest(HypothesisTestCase):
    # Feature: gym-management, Property 1: Expiry date derivation invariant

    @given(
        join_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        duration_days=st.integers(min_value=1, max_value=3650),
    )
    @settings(max_examples=100)
    def test_expiry_derived_on_create_when_not_provided(self, join_date, duration_days):
        plan = MembershipPlan.objects.create(
            name=f'Plan-{join_date}-{duration_days}',
            price='50.00',
            duration_days=duration_days,
        )
        member = Member(
            full_name='Test',
            phone='000',
            email=f'test_{join_date}_{duration_days}@example.com',
            face_descriptor=[0.0] * 128,
            join_date=join_date,
            membership_plan=plan,
        )
        member.save()
        expected = join_date + timedelta(days=duration_days)
        self.assertEqual(member.expiry_date, expected)

    @given(
        join_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        duration_days=st.integers(min_value=1, max_value=3650),
        extra_days=st.integers(min_value=0, max_value=3650),
    )
    @settings(max_examples=100)
    def test_explicit_expiry_on_create_is_preserved(self, join_date, duration_days, extra_days):
        # An explicitly supplied expiry (e.g. a transfer-in member who already
        # paid) must not be clobbered by plan-based derivation.
        plan = MembershipPlan.objects.create(
            name=f'Plan-{join_date}-{duration_days}-{extra_days}',
            price='50.00',
            duration_days=duration_days,
        )
        custom_expiry = join_date + timedelta(days=duration_days + extra_days)
        member = Member(
            full_name='Test',
            phone='000',
            email=f'test_{join_date}_{duration_days}_{extra_days}@example.com',
            face_descriptor=[0.0] * 128,
            join_date=join_date,
            membership_plan=plan,
            expiry_date=custom_expiry,
        )
        member.save()
        self.assertEqual(member.expiry_date, custom_expiry)

    def test_expiry_not_clobbered_on_later_updates(self):
        # Regression: updating an unrelated field (or a payment extension)
        # must never reset expiry_date back to join_date + duration.
        plan = make_plan(duration_days=30)
        member = make_member(plan=plan)
        member.save()
        extended = date.today() + timedelta(days=120)
        member.expiry_date = extended
        member.save()
        member.phone = '9999999999'
        member.save()
        member.refresh_from_db()
        self.assertEqual(member.expiry_date, extended)


class StatusDerivationTest(HypothesisTestCase):
    # Feature: gym-management, Property 3: Status reflects expiry date

    @given(
        days_offset=st.integers(min_value=-365, max_value=365),
    )
    @settings(max_examples=100)
    def test_status_reflects_expiry_date(self, days_offset):
        today = date.today()
        expiry = today + timedelta(days=days_offset)
        plan = MembershipPlan.objects.create(
            name=f'Plan-offset-{days_offset}',
            price='50.00',
            duration_days=abs(days_offset) + 1,
        )
        join = expiry - timedelta(days=plan.duration_days)
        member = Member(
            full_name='Status Test',
            phone='000',
            email=f'status_{days_offset}@example.com',
            face_descriptor=[0.0] * 128,
            join_date=join,
            membership_plan=plan,
            expiry_date=expiry,
        )
        member.save()
        if expiry > today:
            self.assertEqual(member.status, 'active')
        else:
            self.assertEqual(member.status, 'expired')


class FaceDescriptorRoundTripTest(HypothesisTestCase):
    # Feature: gym-management, Property 5: Face descriptor round-trip

    @given(
        descriptor=st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=128,
            max_size=128,
        )
    )
    @settings(max_examples=100)
    def test_face_descriptor_json_round_trip(self, descriptor):
        serialized = json.dumps(descriptor)
        deserialized = json.loads(serialized)
        self.assertEqual(len(deserialized), 128)
        for original, recovered in zip(descriptor, deserialized):
            self.assertAlmostEqual(original, recovered, places=6)


class AttendanceProtectionTest(TestCase):
    # Feature: gym-management, Property: Attendance history is never destroyed

    def test_member_with_attendance_history_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        from attendance.models import Attendance
        plan = make_plan()
        member = make_member(plan=plan)
        member.save()
        Attendance.objects.create(member=member, date=date.today(), method='manual')
        with self.assertRaises(ProtectedError):
            member.delete()
        self.assertEqual(Attendance.objects.filter(member=member).count(), 1)
        self.assertTrue(Member.objects.filter(pk=member.pk).exists())

    def test_member_without_history_can_be_deleted(self):
        plan = make_plan()
        member = make_member(plan=plan)
        member.save()
        member_id = member.pk
        member.delete()
        self.assertFalse(Member.objects.filter(pk=member_id).exists())


class MemberSearchTest(TestCase):
    def setUp(self):
        self.plan = make_plan()
        m1 = make_member(plan=self.plan, email='alice@example.com')
        m1.full_name = 'Alice Smith'
        m1.save()
        m2 = make_member(plan=self.plan, email='bob@example.com')
        m2.full_name = 'Bob Jones'
        m2.save()

    def test_search_by_name_returns_matching(self):
        results = Member.objects.filter(full_name__icontains='alice')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().full_name, 'Alice Smith')

    def test_search_by_email_returns_matching(self):
        results = Member.objects.filter(email__icontains='bob@')
        self.assertEqual(results.count(), 1)

    def test_search_no_match_returns_empty(self):
        results = Member.objects.filter(full_name__icontains='zzznomatch')
        self.assertEqual(results.count(), 0)


class DuplicateEmailTest(TestCase):
    def test_duplicate_email_raises_error(self):
        from django.db import IntegrityError
        plan = make_plan()
        m1 = make_member(plan=plan, email='dup@example.com')
        m1.save()
        m2 = make_member(plan=plan, email='dup@example.com')
        with self.assertRaises(IntegrityError):
            m2.save()
