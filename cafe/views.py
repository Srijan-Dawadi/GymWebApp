import json
from datetime import date

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from accounts.mixins import StaffRequiredMixin
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

        return render(request, self.template_name, {
            'active_orders': active_orders,
            'history_orders': history_orders,
            'menu_items': menu_items,
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

        return JsonResponse({"ok": True, "status": new_status})
