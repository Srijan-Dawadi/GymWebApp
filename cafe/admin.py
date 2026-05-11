from django.contrib import admin
from .models import MenuItem, Order, OrderItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('name', 'menu_item', 'unit_price', 'quantity', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_number', 'status', 'created_at', 'total')
    list_filter = ('status',)
    search_fields = ('table_number',)
    readonly_fields = ('total',)
    inlines = [OrderItemInline]
