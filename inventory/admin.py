from django.contrib import admin
from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weight_kg', 'quantity', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name', 'description')
    ordering = ('category', 'weight_kg', 'name')
