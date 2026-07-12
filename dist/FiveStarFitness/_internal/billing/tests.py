"""
Tests for the billing app.
Covers Properties 2, 7, 8 from the design document.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from members.models import Member, MembershipPlan
from .models import Payment


def make_plan(duration_days=30):
    return MembershipPlan.objects.create(name='Plan', price='50.00', duration_days=duration_days)


def make_member(plan=None, email=None):
    if plan is None:
        plan = make_plan()
    today = date.today()
    return Member.objects.create(
        full_name='Test Member',
        phone='000',
        email=email or f'member_{id(plan)}@example.com',
        face_descriptor=[0.0] * 128,
        join_date=today,
        membership_plan=plan,
        expiry_date=today + timedelta(days=plan.duration_days),
    )


class PaymentUpdatesExpiryTest(HypothesisTestCase):
    # Feature: gym-management, Property 2: Payment updates expiry date

    @given(
        days_ahead=st.integers(min_value=1, max_value=730),
    )
    @settings(max_examples=100)
    def test_payment_updates_member_expiry_date(self, days_ahead):
        plan = make_plan()
        member = make_member(plan=plan, email=f'pay_{days_ahead}@example.com')
        today = date.today()
        period_end = today + timedelta(days=days_ahead)

        Payment.objects.create(
            member=member,
            amount=Decimal('50.00'),
            date_paid=today,
            period_start=today,
            period_end=period_end,
            payment_method='cash',
        )

        member.refresh_from_db()
        self.assertEqual(member.expiry_date, period_end)


class MonthlyRevenueTest(HypothesisTestCase):
    # Feature: gym-management, Property 7: Monthly revenue calculation

    @given(
        amounts=st.lists(
            st.decimals(min_value=Decimal('1.00'), max_value=Decimal('999.99'), places=2),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_monthly_revenue_equals_sum_of_current_month_payments(self, amounts):
        from django.db.models import Sum
        plan = make_plan()
        today = date.today()

        # Clear existing payments for isolation
        Payment.objects.all().delete()
        # Also clear members created in previous runs
        Member.objects.all().delete()

        member = make_member(plan=plan, email='revenue_test@example.com')

        for i, amount in enumerate(amounts):
            Payment.objects.create(
                member=member,
                amount=amount,
                date_paid=today,
                period_start=today,
                period_end=today + timedelta(days=30),
                payment_method='cash',
            )

        expected = sum(amounts) if amounts else Decimal('0')
        actual = Payment.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        self.assertAlmostEqual(float(actual), float(expected), places=2)


class OverdueMemberTest(HypothesisTestCase):
    # Feature: gym-management, Property 8: Overdue member detection

    @given(
        days_offsets=st.lists(
            st.integers(min_value=-365, max_value=365),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    @settings(max_examples=50)
    def test_overdue_queryset_contains_exactly_expired_members(self, days_offsets):
        Member.objects.all().delete()
        MembershipPlan.objects.all().delete()

        today = date.today()
        created = []
        for i, offset in enumerate(days_offsets):
            expiry = today + timedelta(days=offset)
            plan = MembershipPlan.objects.create(
                name=f'Plan-{i}', price='50.00', duration_days=abs(offset) + 1
            )
            join = expiry - timedelta(days=plan.duration_days)
            m = Member.objects.create(
                full_name=f'Member {i}',
                phone='000',
                email=f'overdue_{i}@example.com',
                face_descriptor=[0.0] * 128,
                join_date=join,
                membership_plan=plan,
                expiry_date=expiry,
            )
            created.append((m, offset))

        overdue_ids = set(Member.objects.filter(expiry_date__lt=today).values_list('id', flat=True))
        for member, offset in created:
            expiry = today + timedelta(days=offset)
            if expiry < today:
                self.assertIn(member.id, overdue_ids)
            else:
                self.assertNotIn(member.id, overdue_ids)


class PlanDeletionProtectionTest(TestCase):
    def test_cannot_delete_plan_with_active_members(self):
        from django.db.models import ProtectedError
        plan = make_plan()
        make_member(plan=plan)
        with self.assertRaises(ProtectedError):
            plan.delete()

    def test_can_delete_plan_with_no_members(self):
        plan = make_plan()
        plan_id = plan.pk
        plan.delete()
        self.assertFalse(MembershipPlan.objects.filter(pk=plan_id).exists())
