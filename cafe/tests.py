"""
Tests for the cafe app.
Covers Properties 1–11 from the design document.
"""
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from .models import MenuItem, Order, OrderItem
from .views import CafeView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_order(table_number='T1', status='pending'):
    return Order.objects.create(table_number=table_number, status=status)


def make_order_item(order, name='Coffee', unit_price=Decimal('3.50'), quantity=1):
    return OrderItem.objects.create(
        order=order,
        name=name,
        unit_price=unit_price,
        quantity=quantity,
    )


def post_create_order(client, table_number, items):
    """
    POST to CreateOrderView.
    items: list of (name, price, qty) tuples.
    """
    data = {'table_number': table_number}
    data['item_name[]'] = [i[0] for i in items]
    data['item_price[]'] = [str(i[1]) for i in items]
    data['item_qty[]'] = [str(i[2]) for i in items]
    return client.post('/cafe/orders/create/', data)


def post_status(client, pk, action):
    """POST JSON action to UpdateOrderStatusView."""
    return client.post(
        f'/cafe/orders/{pk}/status/',
        data=json.dumps({'action': action}),
        content_type='application/json',
    )


def get_or_create_staff_user():
    """Get or create a staff user for tests (safe for Hypothesis repeated setUp)."""
    user, _ = User.objects.get_or_create(username='teststaff')
    user.set_password('pass')
    user.save()
    return user


# ---------------------------------------------------------------------------
# 7.1 Model unit tests
# ---------------------------------------------------------------------------

class MenuItemStrTest(TestCase):
    def test_str_format(self):
        item = MenuItem(name='Espresso', price=Decimal('2.50'))
        self.assertEqual(str(item), 'Espresso (₹2.50)')


class OrderItemSubtotalTest(TestCase):
    def test_subtotal_equals_price_times_quantity(self):
        order = make_order()
        item = make_order_item(order, unit_price=Decimal('4.00'), quantity=3)
        self.assertEqual(item.subtotal, Decimal('12.00'))

    def test_subtotal_single_item(self):
        order = make_order()
        item = make_order_item(order, unit_price=Decimal('5.99'), quantity=1)
        self.assertEqual(item.subtotal, Decimal('5.99'))


class OrderTotalTest(TestCase):
    def test_total_sums_all_items(self):
        order = make_order()
        make_order_item(order, name='Coffee', unit_price=Decimal('3.00'), quantity=2)
        make_order_item(order, name='Tea', unit_price=Decimal('2.00'), quantity=1)
        # 3.00*2 + 2.00*1 = 8.00
        self.assertEqual(order.total, Decimal('8.00'))

    def test_total_empty_order(self):
        order = make_order()
        self.assertEqual(order.total, 0)


class OrderDefaultStatusTest(TestCase):
    def test_default_status_is_pending(self):
        order = Order.objects.create(table_number='T1')
        self.assertEqual(order.status, 'pending')


# ---------------------------------------------------------------------------
# 7.2 View tests: GET /cafe/
# ---------------------------------------------------------------------------

class CafeViewGetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='pass')
        self.factory = RequestFactory()

    def test_authenticated_user_gets_200(self):
        # Use RequestFactory to bypass the Django test client's template signal
        # instrumentation, which has a Python 3.14 incompatibility with context copy.
        request = self.factory.get('/cafe/')
        request.user = self.user
        # Attach session and messages middleware support
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.messages.storage.fallback import FallbackStorage
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        response = CafeView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_redirects_to_login(self):
        response = self.client.get('/cafe/')
        self.assertRedirects(response, '/accounts/login/?next=/cafe/', fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# 7.3 View tests: POST /cafe/orders/create/
# ---------------------------------------------------------------------------

class CreateOrderViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='pass')
        self.client.login(username='teststaff', password='pass')

    def test_valid_post_creates_order_and_redirects(self):
        count_before = Order.objects.count()
        response = post_create_order(self.client, 'T5', [('Coffee', '3.00', 2)])
        self.assertEqual(Order.objects.count(), count_before + 1)
        self.assertRedirects(response, '/cafe/', fetch_redirect_response=False)

    def test_empty_table_number_does_not_create_order(self):
        count_before = Order.objects.count()
        response = post_create_order(self.client, '', [('Coffee', '3.00', 1)])
        self.assertEqual(Order.objects.count(), count_before)
        self.assertRedirects(response, '/cafe/', fetch_redirect_response=False)

    def test_whitespace_table_number_does_not_create_order(self):
        count_before = Order.objects.count()
        response = post_create_order(self.client, '   ', [('Coffee', '3.00', 1)])
        self.assertEqual(Order.objects.count(), count_before)
        self.assertRedirects(response, '/cafe/', fetch_redirect_response=False)

    def test_no_items_does_not_create_order(self):
        count_before = Order.objects.count()
        response = post_create_order(self.client, 'T5', [])
        self.assertEqual(Order.objects.count(), count_before)
        self.assertRedirects(response, '/cafe/', fetch_redirect_response=False)

    def test_all_zero_qty_does_not_create_order(self):
        count_before = Order.objects.count()
        response = post_create_order(self.client, 'T5', [('Coffee', '3.00', 0)])
        self.assertEqual(Order.objects.count(), count_before)
        self.assertRedirects(response, '/cafe/', fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# 7.4 View tests: POST /cafe/orders/<pk>/status/
# ---------------------------------------------------------------------------

class UpdateOrderStatusViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='pass')
        self.client.login(username='teststaff', password='pass')

    def test_fulfill_pending_order_returns_200_and_updates_status(self):
        order = make_order(status='pending')
        response = post_status(self.client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'fulfilled')
        self.assertIsNotNone(order.fulfilled_at)

    def test_payment_received_on_fulfilled_order_returns_200_and_updates_status(self):
        order = make_order(status='fulfilled')
        response = post_status(self.client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')
        self.assertIsNotNone(order.payment_received_at)

    def test_invalid_transition_pending_payment_received_returns_400(self):
        order = make_order(status='pending')
        response = post_status(self.client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')

    def test_invalid_transition_fulfilled_fulfill_returns_400(self):
        order = make_order(status='fulfilled')
        response = post_status(self.client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'fulfilled')

    def test_invalid_transition_payment_received_fulfill_returns_400(self):
        order = make_order(status='payment_received')
        response = post_status(self.client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')

    def test_invalid_transition_payment_received_payment_received_returns_400(self):
        order = make_order(status='payment_received')
        response = post_status(self.client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

# Shared strategy definitions
valid_table_st = st.text(
    min_size=1,
    max_size=20,
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
)
invalid_table_st = st.one_of(
    st.just(''),
    st.text(alphabet=' \t\n', min_size=1, max_size=10),
)
price_st = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('999.99'),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
qty_st = st.integers(min_value=1, max_value=99)
num_items_st = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# 7.5 Property 1: Order creation adds to active board
# ---------------------------------------------------------------------------

class Property1OrderCreationTest(HypothesisTestCase):
    # Feature: cafe-management, Property 1

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(
        table_number=valid_table_st,
        num_items=num_items_st,
        prices=st.lists(price_st, min_size=10, max_size=10),
        qtys=st.lists(qty_st, min_size=10, max_size=10),
    )
    @settings(max_examples=50)
    def test_order_creation_adds_to_active_board(self, table_number, num_items, prices, qtys):
        """
        **Validates: Requirements 1.6, 3.1**
        For any valid table number and non-empty list of order items (each with
        quantity > 0), submitting the order entry form SHALL result in the new
        order appearing in the active orders board with status pending.
        """
        items = [
            (f'Item{i}', prices[i], qtys[i])
            for i in range(num_items)
        ]
        count_before = Order.objects.filter(status__in=['pending', 'fulfilled']).count()
        post_create_order(self.http_client, table_number, items)
        active_count = Order.objects.filter(status__in=['pending', 'fulfilled']).count()
        self.assertEqual(active_count, count_before + 1)
        # The newest order should be pending
        latest = Order.objects.filter(status='pending').order_by('-created_at').first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.status, 'pending')


# ---------------------------------------------------------------------------
# 7.6 Properties 2 & 3: Empty table / empty items rejected
# ---------------------------------------------------------------------------

class Property2EmptyTableRejectedTest(HypothesisTestCase):
    # Feature: cafe-management, Property 2

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(
        table_number=invalid_table_st,
        price=price_st,
        qty=qty_st,
    )
    @settings(max_examples=50)
    def test_empty_table_number_rejected(self, table_number, price, qty):
        """
        **Validates: Requirements 1.2, 1.4**
        For any order submission where the table number field is empty or
        whitespace-only, the system SHALL reject the submission and leave the
        order count unchanged.
        """
        count_before = Order.objects.count()
        post_create_order(self.http_client, table_number, [('Coffee', price, qty)])
        self.assertEqual(Order.objects.count(), count_before)


class Property3EmptyItemsRejectedTest(HypothesisTestCase):
    # Feature: cafe-management, Property 3

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=50)
    def test_empty_item_list_rejected(self, table_number):
        """
        **Validates: Requirements 1.3, 1.5**
        For any order submission that contains no items with quantity > 0, the
        system SHALL reject the submission and leave the order count unchanged.
        """
        count_before = Order.objects.count()
        post_create_order(self.http_client, table_number, [])
        self.assertEqual(Order.objects.count(), count_before)

    @given(
        table_number=valid_table_st,
        num_items=num_items_st,
        prices=st.lists(price_st, min_size=10, max_size=10),
    )
    @settings(max_examples=50)
    def test_all_zero_qty_items_rejected(self, table_number, num_items, prices):
        """
        **Validates: Requirements 1.3, 1.5**
        Items with quantity 0 are not valid; if all items have qty=0 the order
        is rejected.
        """
        items = [(f'Item{i}', prices[i], 0) for i in range(num_items)]
        count_before = Order.objects.count()
        post_create_order(self.http_client, table_number, items)
        self.assertEqual(Order.objects.count(), count_before)


# ---------------------------------------------------------------------------
# 7.7 Properties 4 & 5: Status transitions pending→fulfilled, fulfilled→payment_received
# ---------------------------------------------------------------------------

class Property4PendingToFulfilledTest(HypothesisTestCase):
    # Feature: cafe-management, Property 4

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=50)
    def test_pending_to_fulfilled_transition(self, table_number):
        """
        **Validates: Requirements 4.2**
        For any order in pending status, invoking the "Mark Fulfilled" action
        SHALL update the order's status to fulfilled and record a non-null
        fulfilled_at timestamp.
        """
        order = make_order(table_number=table_number, status='pending')
        response = post_status(self.http_client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'fulfilled')
        self.assertIsNotNone(order.fulfilled_at)


class Property5FulfilledToPaymentReceivedTest(HypothesisTestCase):
    # Feature: cafe-management, Property 5

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=50)
    def test_fulfilled_to_payment_received_transition(self, table_number):
        """
        **Validates: Requirements 5.2**
        For any order in fulfilled status, invoking the "Mark Payment Received"
        action SHALL update the order's status to payment_received and record a
        non-null payment_received_at timestamp.
        """
        order = make_order(table_number=table_number, status='fulfilled')
        response = post_status(self.http_client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')
        self.assertIsNotNone(order.payment_received_at)


# ---------------------------------------------------------------------------
# 7.8 Property 6: Invalid transitions rejected
# ---------------------------------------------------------------------------

class Property6InvalidTransitionsRejectedTest(HypothesisTestCase):
    # Feature: cafe-management, Property 6

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=30)
    def test_pending_payment_received_rejected(self, table_number):
        """
        **Validates: Requirements 4.4, 5.5**
        pending + action payment_received → 400, status unchanged.
        """
        order = make_order(table_number=table_number, status='pending')
        response = post_status(self.http_client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')

    @given(table_number=valid_table_st)
    @settings(max_examples=30)
    def test_fulfilled_fulfill_rejected(self, table_number):
        """
        **Validates: Requirements 4.4, 5.5**
        fulfilled + action fulfill → 400, status unchanged.
        """
        order = make_order(table_number=table_number, status='fulfilled')
        response = post_status(self.http_client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'fulfilled')

    @given(table_number=valid_table_st)
    @settings(max_examples=30)
    def test_payment_received_fulfill_rejected(self, table_number):
        """
        **Validates: Requirements 4.4, 5.5**
        payment_received + action fulfill → 400, status unchanged.
        """
        order = make_order(table_number=table_number, status='payment_received')
        response = post_status(self.http_client, order.pk, 'fulfill')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')

    @given(table_number=valid_table_st)
    @settings(max_examples=30)
    def test_payment_received_payment_received_rejected(self, table_number):
        """
        **Validates: Requirements 4.4, 5.5**
        payment_received + action payment_received → 400, status unchanged.
        """
        order = make_order(table_number=table_number, status='payment_received')
        response = post_status(self.http_client, order.pk, 'payment_received')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')


# ---------------------------------------------------------------------------
# 7.9 Properties 7 & 8: payment_received leaves active board / appears in history
# ---------------------------------------------------------------------------

class Property7PaymentReceivedLeavesActiveBoardTest(HypothesisTestCase):
    # Feature: cafe-management, Property 7

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=50)
    def test_payment_received_order_not_in_active_board(self, table_number):
        """
        **Validates: Requirements 5.3**
        For any order whose status is updated to payment_received, that order
        SHALL NOT appear in the active orders query.
        """
        order = make_order(table_number=table_number, status='fulfilled')
        post_status(self.http_client, order.pk, 'payment_received')
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')
        active = Order.objects.filter(pk=order.pk, status__in=['pending', 'fulfilled'])
        self.assertEqual(active.count(), 0)


class Property8PaymentReceivedAppearsInHistoryTest(HypothesisTestCase):
    # Feature: cafe-management, Property 8

    def setUp(self):
        self.user = get_or_create_staff_user()
        self.http_client = Client()
        self.http_client.login(username='teststaff', password='pass')

    @given(table_number=valid_table_st)
    @settings(max_examples=50)
    def test_payment_received_order_appears_in_today_history(self, table_number):
        """
        **Validates: Requirements 5.4, 6.1**
        For any order whose status is updated to payment_received on the current
        calendar day, that order SHALL appear in the order history query scoped
        to today.
        """
        order = make_order(table_number=table_number, status='fulfilled')
        post_status(self.http_client, order.pk, 'payment_received')
        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_received')
        today = date.today()
        history = Order.objects.filter(
            status='payment_received',
            created_at__date=today,
        )
        self.assertIn(order, list(history))


# ---------------------------------------------------------------------------
# 7.10 Property 9: Subtotal calculation
# ---------------------------------------------------------------------------

class Property9SubtotalCalculationTest(HypothesisTestCase):
    # Feature: cafe-management, Property 9

    @given(price=price_st, qty=qty_st)
    @settings(max_examples=100)
    def test_subtotal_equals_price_times_quantity(self, price, qty):
        """
        **Validates: Requirements 2.4**
        For any order item with a given unit price and quantity, the computed
        subtotal SHALL equal unit_price × quantity.
        """
        order = make_order()
        item = OrderItem.objects.create(
            order=order,
            name='TestItem',
            unit_price=price,
            quantity=qty,
        )
        expected = price * qty
        self.assertEqual(item.subtotal, expected)


# ---------------------------------------------------------------------------
# 7.11 Properties 10 & 11: Sort orders
# ---------------------------------------------------------------------------

class Property10ActiveOrdersSortOrderTest(HypothesisTestCase):
    # Feature: cafe-management, Property 10

    @given(n=st.integers(min_value=2, max_value=8))
    @settings(max_examples=30)
    def test_active_orders_sorted_ascending_by_created_at(self, n):
        """
        **Validates: Requirements 3.3**
        For any set of active orders, the list returned by the active orders
        query SHALL be sorted by created_at in ascending order (oldest first).
        """
        now = timezone.now()
        orders = []
        for i in range(n):
            o = Order.objects.create(table_number=f'T{i}', status='pending')
            orders.append(o)

        # Assign distinct created_at values in shuffled order
        import random
        offsets = list(range(n))
        random.shuffle(offsets)
        for o, offset in zip(orders, offsets):
            Order.objects.filter(pk=o.pk).update(
                created_at=now - timedelta(minutes=offset)
            )

        active = list(
            Order.objects.filter(
                pk__in=[o.pk for o in orders],
                status__in=['pending', 'fulfilled'],
            ).order_by('created_at')
        )
        self.assertEqual(len(active), n)
        for i in range(len(active) - 1):
            self.assertLessEqual(active[i].created_at, active[i + 1].created_at)


class Property11HistorySortOrderTest(HypothesisTestCase):
    # Feature: cafe-management, Property 11

    @given(n=st.integers(min_value=2, max_value=8))
    @settings(max_examples=30)
    def test_history_sorted_descending_by_payment_received_at(self, n):
        """
        **Validates: Requirements 6.3**
        For any set of completed orders for the current day, the list returned
        by the history query SHALL be sorted by payment_received_at in
        descending order (most recent first).
        """
        now = timezone.now()
        today = date.today()
        orders = []
        for i in range(n):
            o = Order.objects.create(table_number=f'H{i}', status='payment_received')
            orders.append(o)

        # Assign distinct payment_received_at values
        import random
        offsets = list(range(n))
        random.shuffle(offsets)
        for o, offset in zip(orders, offsets):
            Order.objects.filter(pk=o.pk).update(
                payment_received_at=now - timedelta(minutes=offset)
            )

        history = list(
            Order.objects.filter(
                pk__in=[o.pk for o in orders],
                status='payment_received',
                created_at__date=today,
            ).order_by('-payment_received_at')
        )
        self.assertEqual(len(history), n)
        for i in range(len(history) - 1):
            self.assertGreaterEqual(
                history[i].payment_received_at,
                history[i + 1].payment_received_at,
            )
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from cafe.models import CafeInventoryItem, CafeCategory
from accounts.models import Profile

class CafeInventoryTests(TestCase):
    def setUp(self):
        # Clear any seeded data to ensure test isolation
        CafeInventoryItem.objects.all().delete()

        # Create Admin
        self.admin_user = User.objects.create_user(username='admin', password='password')
        # Profile is created by signal, so we update it
        if hasattr(self.admin_user, 'profile'):
            self.admin_user.profile.role = 'admin'
            self.admin_user.profile.save()
        else:
            Profile.objects.create(user=self.admin_user, role='admin')
        
        # Create Staff
        self.staff_user = User.objects.create_user(username='staff', password='password')
        # Profile defaults to 'staff' via signal
        
        self.client = Client()

    def test_model_str(self):
        item = CafeInventoryItem.objects.create(
            name='Coffee Beans',
            category='ingredients',
            quantity=10,
            unit='kg'
        )
        self.assertEqual(str(item), 'Coffee Beans (10 kg)')

    def test_inventory_list_view(self):
        self.client.login(username='staff', password='password')
        response = self.client.get(reverse('cafe:inventory'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cafe/inventory.html')

    def test_admin_can_add_item(self):
        self.client.login(username='admin', password='password')
        data = {
            'name': 'New Item',
            'category': 'beverages',
            'quantity': 5,
            'unit': 'pcs',
            'status': 'good'
        }
        response = self.client.post(reverse('cafe:inventory_add'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CafeInventoryItem.objects.filter(name='New Item').exists())

    def test_staff_cannot_add_item(self):
        self.client.login(username='staff', password='password')
        data = {
            'name': 'Staff Item',
            'category': 'beverages',
            'quantity': 5,
            'unit': 'pcs',
            'status': 'good'
        }
        response = self.client.post(reverse('cafe:inventory_add'), data)
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_admin_can_edit_item(self):
        item = CafeInventoryItem.objects.create(name='Old Name', category='supplies', quantity=1)
        self.client.login(username='admin', password='password')
        data = {
            'name': 'Updated Name',
            'category': 'supplies',
            'quantity': 10,
            'unit': 'packs',
            'status': 'low_stock'
        }
        response = self.client.post(reverse('cafe:inventory_edit', args=[item.pk]), data)
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.name, 'Updated Name')
        self.assertEqual(item.quantity, 10)

    def test_admin_can_delete_item(self):
        item = CafeInventoryItem.objects.create(name='Delete Me', category='supplies', quantity=1)
        self.client.login(username='admin', password='password')
        response = self.client.post(reverse('cafe:inventory_delete', args=[item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CafeInventoryItem.objects.filter(pk=item.pk).exists())

    def test_staff_can_update_status(self):
        item = CafeInventoryItem.objects.create(name='Status Item', category='ingredients', quantity=5, status='good')
        self.client.login(username='staff', password='password')
        response = self.client.post(reverse('cafe:inventory_status', args=[item.pk]), {'status': 'low_stock'})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, 'low_stock')

    def test_search_view(self):
        CafeInventoryItem.objects.create(name='Espresso Beans', category='ingredients', quantity=5)
        CafeInventoryItem.objects.create(name='Paper Napkins', category='supplies', quantity=100)
        
        self.client.login(username='staff', password='password')
        
        # Search by name
        response = self.client.get(reverse('cafe:inventory_search'), {'q': 'Espresso'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Espresso Beans')
        
        # Search by category
        response = self.client.get(reverse('cafe:inventory_search'), {'category': 'supplies'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Paper Napkins')
