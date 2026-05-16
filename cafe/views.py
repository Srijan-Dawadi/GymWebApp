import json
from datetime import date

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
from .models import MenuItem, Order, OrderItem


class CafeView(StaffRequiredMixin, View):
    template_name = 'cafe/cafe.html'

    def get(self, request):
        today = date.today()
        active_orders = (
            Order.objects
            .filter(status__in=['pending', 'fulfilled'])
            .prefetch_related('items__menu_item')
            .order_by('created_at')
        )
        history_orders = (
            Order.objects
            .filter(status='payment_received', created_at__date=today)
            .prefetch_related('items__menu_item')
            .order_by('-payment_received_at')
        )
        menu_items = MenuItem.objects.filter(is_active=True).order_by('name')

        # Pass created_at as Unix timestamps for the live order timer in the template
        import time as _time
        active_orders_list = list(active_orders)
        for o in active_orders_list:
            o.created_at_ts = int(o.created_at.timestamp())

        # Compute today's summary for the history header
        from django.db.models import Sum, F
        today_paid = Order.objects.filter(status='payment_received', created_at__date=today)
        today_order_count = today_paid.count()
        today_revenue = today_paid.aggregate(
            t=Sum(F('items__unit_price') * F('items__quantity'))
        )['t'] or 0

        return render(request, self.template_name, {
            'active_orders': active_orders_list,
            'history_orders': history_orders,
            'menu_items': menu_items,
            'today_order_count': today_order_count,
            'today_revenue': today_revenue,
        })


class CreateOrderView(StaffRequiredMixin, View):

    def post(self, request):
        table_number = request.POST.get('table_number', '').strip()

        if not table_number:
            messages.error(request, "Table number is required.")
            return redirect('cafe:cafe_home')

        item_names = request.POST.getlist('item_name[]')
        item_prices = request.POST.getlist('item_price[]')
        item_qtys = request.POST.getlist('item_qty[]')

        # Build list of valid items (quantity > 0)
        valid_items = []
        for name, price, qty in zip(item_names, item_prices, item_qtys):
            try:
                qty_int = int(qty)
            except (ValueError, TypeError):
                qty_int = 0
            if qty_int > 0 and name.strip():
                valid_items.append((name.strip(), price, qty_int))

        if not valid_items:
            messages.error(request, "At least one item with quantity greater than 0 is required.")
            return redirect('cafe:cafe_home')

        try:
            order = Order.objects.create(table_number=table_number)
            for name, price, qty in valid_items:
                # Try to match a menu item by name for the FK
                menu_item = MenuItem.objects.filter(name=name, is_active=True).first()
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    name=name,
                    unit_price=price,
                    quantity=qty,
                )
            messages.success(request, f"Order #{order.pk} created for Table {table_number}.")
        except Exception as e:
            messages.error(request, f"Failed to create order: {e}")

        return redirect('cafe:cafe_home')


class UpdateOrderStatusView(StaffRequiredMixin, View):

    VALID_TRANSITIONS = {
        'fulfill': ('pending', 'fulfilled'),
        'payment_received': ('fulfilled', 'payment_received'),
    }

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        try:
            body = json.loads(request.body)
            action = body.get('action', '')
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"ok": False, "error": "Invalid JSON body"}, status=400)

        if action not in self.VALID_TRANSITIONS:
            return JsonResponse({"ok": False, "error": "Invalid transition"}, status=400)

        required_status, new_status = self.VALID_TRANSITIONS[action]

        if order.status != required_status:
            return JsonResponse({"ok": False, "error": "Invalid transition"}, status=400)

        order.status = new_status
        if action == 'fulfill':
            order.fulfilled_at = timezone.now()
        elif action == 'payment_received':
            order.payment_received_at = timezone.now()
        order.save()

        response_data = {"ok": True, "status": new_status}

        # For payment_received, include order details so the JS can inject a
        # history row without a full page reload (Requirement 3.5 / 5.3-5.4).
        if action == 'payment_received':
            order.refresh_from_db()
            items = list(
                order.items.values('name', 'quantity', 'unit_price')
            )
            response_data['order'] = {
                'id': order.pk,
                'table_number': order.table_number,
                'created_at': order.created_at.strftime('%-I:%M %p'),
                'payment_received_at': order.payment_received_at.strftime('%-I:%M %p'),
                'items': items,
            }

        return JsonResponse(response_data)


# ── Menu Management (admin only) ─────────────────────────────────────────────

class MenuItemListView(AdminRequiredMixin, View):
    template_name = 'cafe/menu_items.html'

    def get(self, request):
        menu_items = MenuItem.objects.all().order_by('name')
        return render(request, self.template_name, {'menu_items': menu_items})


class MenuItemAddView(AdminRequiredMixin, View):

    def post(self, request):
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        is_active = request.POST.get('is_active', 'on') == 'on'

        if not name or not price:
            messages.error(request, "Name and price are required.")
            return redirect('cafe:menu_items')

        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Price must be a valid positive number.")
            return redirect('cafe:menu_items')

        if MenuItem.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A menu item named "{name}" already exists.')
            return redirect('cafe:menu_items')

        MenuItem.objects.create(name=name, price=price, is_active=is_active)
        messages.success(request, f'"{name}" added to the menu.')
        return redirect('cafe:menu_items')


class MenuItemEditView(AdminRequiredMixin, View):

    def post(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        is_active = request.POST.get('is_active', 'off') == 'on'

        if not name or not price:
            messages.error(request, "Name and price are required.")
            return redirect('cafe:menu_items')

        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Price must be a valid positive number.")
            return redirect('cafe:menu_items')

        # Check for name collision with a different item
        if MenuItem.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'A menu item named "{name}" already exists.')
            return redirect('cafe:menu_items')

        item.name = name
        item.price = price
        item.is_active = is_active
        item.save()
        messages.success(request, f'"{item.name}" updated.')
        return redirect('cafe:menu_items')


class MenuItemDeleteView(AdminRequiredMixin, View):

    def post(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" removed from the menu.')
        return redirect('cafe:menu_items')


# ── Cafe Reports (admin only) ─────────────────────────────────────────────────

class CafeReportsView(AdminRequiredMixin, View):
    template_name = 'cafe/reports.html'

    def get(self, request):
        import json
        from django.db.models import Count, Sum, F
        from django.db.models.functions import TruncDate, TruncHour
        from datetime import timedelta

        today = timezone.now().date()
        month_start = today.replace(day=1)

        # ── All-time KPIs ────────────────────────────────────────────
        paid_orders = Order.objects.filter(status='payment_received')

        total_revenue = paid_orders.aggregate(
            t=Sum(F('items__unit_price') * F('items__quantity'))
        )['t'] or 0

        total_orders = paid_orders.count()

        today_orders = paid_orders.filter(created_at__date=today)
        today_revenue = today_orders.aggregate(
            t=Sum(F('items__unit_price') * F('items__quantity'))
        )['t'] or 0
        today_order_count = today_orders.count()

        month_orders = paid_orders.filter(created_at__date__gte=month_start)
        month_revenue = month_orders.aggregate(
            t=Sum(F('items__unit_price') * F('items__quantity'))
        )['t'] or 0
        month_order_count = month_orders.count()

        avg_order_value = round(float(total_revenue) / total_orders, 2) if total_orders else 0

        # ── Daily revenue — last 14 days ─────────────────────────────
        daily_data = []
        for i in range(13, -1, -1):
            day = today - timedelta(days=i)
            rev = paid_orders.filter(created_at__date=day).aggregate(
                t=Sum(F('items__unit_price') * F('items__quantity'))
            )['t'] or 0
            cnt = paid_orders.filter(created_at__date=day).count()
            daily_data.append({
                'date': day.strftime('%d %b'),
                'revenue': float(rev),
                'orders': cnt,
            })

        # ── Item sales breakdown ──────────────────────────────────────
        from django.db.models import ExpressionWrapper, DecimalField

        item_sales = (
            OrderItem.objects
            .filter(order__status='payment_received')
            .values('name')
            .annotate(
                total_qty=Sum('quantity'),
                total_revenue=Sum(
                    ExpressionWrapper(
                        F('unit_price') * F('quantity'),
                        output_field=DecimalField()
                    )
                ),
                order_count=Count('order', distinct=True),
            )
            .order_by('-total_qty')
        )

        # Top 5 and bottom 5 by quantity
        item_sales_list = list(item_sales)
        top_items    = item_sales_list[:5]
        bottom_items = [i for i in item_sales_list if i['total_qty'] <= 2][:5]

        # ── Hourly order distribution (all time) ─────────────────────
        hourly_raw = (
            paid_orders
            .annotate(hour=TruncHour('created_at'))
            .values('hour')
            .annotate(cnt=Count('id'))
            .order_by('hour')
        )
        hourly_buckets = [0] * 24
        for row in hourly_raw:
            if row['hour']:
                h = row['hour'].hour
                hourly_buckets[h] += row['cnt']

        # ── Pending / in-progress orders right now ───────────────────
        pending_count   = Order.objects.filter(status='pending').count()
        fulfilled_count = Order.objects.filter(status='fulfilled').count()

        # ── Average fulfillment time (pending → fulfilled) ────────────
        from django.db.models import Avg, DurationField, ExpressionWrapper as EW, F as Fld
        avg_fulfill = (
            Order.objects
            .filter(status__in=['fulfilled', 'payment_received'], fulfilled_at__isnull=False)
            .annotate(
                duration=EW(Fld('fulfilled_at') - Fld('created_at'), output_field=DurationField())
            )
            .aggregate(avg=Avg('duration'))['avg']
        )
        avg_fulfill_mins = round(avg_fulfill.total_seconds() / 60, 1) if avg_fulfill else None

        ctx = {
            'today': today,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'today_revenue': today_revenue,
            'today_order_count': today_order_count,
            'month_revenue': month_revenue,
            'month_order_count': month_order_count,
            'avg_order_value': avg_order_value,
            'pending_count': pending_count,
            'fulfilled_count': fulfilled_count,
            'avg_fulfill_mins': avg_fulfill_mins,
            'item_sales': item_sales_list,
            'top_items': top_items,
            'bottom_items': bottom_items,
            'daily_data': json.dumps(daily_data),
            'hourly_data': json.dumps(hourly_buckets),
        }
        return render(request, self.template_name, ctx)
