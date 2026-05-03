import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.db.models import Q, Sum

from .models import InventoryItem, EquipmentCategory, EquipmentStatus


class InventoryView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        category_filter = request.GET.get('category', '')
        status_filter = request.GET.get('status', '')
        q = request.GET.get('q', '').strip()

        items = InventoryItem.objects.all()

        if category_filter:
            items = items.filter(category=category_filter)
        if status_filter:
            items = items.filter(status=status_filter)
        if q:
            items = items.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # Summary stats
        total_items = InventoryItem.objects.count()
        total_qty = InventoryItem.objects.aggregate(t=Sum('quantity'))['t'] or 0
        needs_attention = InventoryItem.objects.filter(
            status__in=[EquipmentStatus.MAINTENANCE, EquipmentStatus.OUT_OF_SERVICE]
        ).count()

        # Group items by category for display
        categories = EquipmentCategory.choices  # list of (value, label)

        context = {
            'items': items,
            'categories': categories,
            'category_filter': category_filter,
            'status_filter': status_filter,
            'q': q,
            'total_items': total_items,
            'total_qty': total_qty,
            'needs_attention': needs_attention,
            'status_choices': EquipmentStatus.choices,
        }
        return render(request, 'Inventory/inventory.html', context)


class InventoryAddView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        quantity = request.POST.get('quantity', 1)
        status = request.POST.get('status', EquipmentStatus.GOOD)
        weight_kg = request.POST.get('weight_kg', '') or None
        notes = request.POST.get('notes', '').strip()

        if not name or not category:
            messages.error(request, 'Name and category are required.')
            return redirect('/inventory/')

        try:
            quantity = int(quantity)
            weight_kg = float(weight_kg) if weight_kg else None
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity or weight value.')
            return redirect('/inventory/')

        InventoryItem.objects.create(
            name=name,
            category=category,
            description=description,
            quantity=quantity,
            status=status,
            weight_kg=weight_kg,
            notes=notes,
        )
        messages.success(request, f'"{name}" added to inventory.')
        return redirect('/inventory/')


class InventoryEditView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        item.name = request.POST.get('name', item.name).strip()
        item.category = request.POST.get('category', item.category)
        item.description = request.POST.get('description', '').strip()
        item.quantity = int(request.POST.get('quantity', item.quantity))
        item.status = request.POST.get('status', item.status)
        weight_kg = request.POST.get('weight_kg', '') or None
        item.weight_kg = float(weight_kg) if weight_kg else None
        item.notes = request.POST.get('notes', '').strip()
        item.save()
        messages.success(request, f'"{item.name}" updated.')
        return redirect('/inventory/')


class InventoryDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" removed from inventory.')
        return redirect('/inventory/')


class InventorySearchView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        q = request.GET.get('q', '').strip()
        category = request.GET.get('category', '')
        status = request.GET.get('status', '')

        items = InventoryItem.objects.all()
        if q:
            items = items.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if category:
            items = items.filter(category=category)
        if status:
            items = items.filter(status=status)

        results = [
            {
                'id': item.pk,
                'name': item.name,
                'category': item.category_label,
                'description': item.description,
                'quantity': item.quantity,
                'status': item.status,
                'status_label': item.status_label,
                'weight_kg': item.weight_kg,
            }
            for item in items
        ]
        return JsonResponse({'results': results, 'count': len(results)})
