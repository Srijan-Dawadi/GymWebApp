from django.urls import path

from . import views

app_name = 'cafe'

urlpatterns = [
    path('', views.CafeView.as_view(), name='cafe_home'),
    path('orders/create/', views.CreateOrderView.as_view(), name='cafe_order_create'),
    path('orders/<int:pk>/status/', views.UpdateOrderStatusView.as_view(), name='cafe_order_status'),
    # Menu management (admin only)
    path('menu/', views.MenuItemListView.as_view(), name='menu_items'),
    path('menu/add/', views.MenuItemAddView.as_view(), name='menu_item_add'),
    path('menu/<int:pk>/edit/', views.MenuItemEditView.as_view(), name='menu_item_edit'),
    path('menu/<int:pk>/delete/', views.MenuItemDeleteView.as_view(), name='menu_item_delete'),
    # Cafe reports (admin only)
    path('reports/', views.CafeReportsView.as_view(), name='cafe_reports'),
    # Inventory management
    path('inventory/', views.CafeInventoryView.as_view(), name='inventory'),
    path('inventory/add/', views.CafeInventoryAddView.as_view(), name='inventory_add'),
    path('inventory/<int:pk>/edit/', views.CafeInventoryEditView.as_view(), name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.CafeInventoryDeleteView.as_view(), name='inventory_delete'),
    path('inventory/<int:pk>/status/', views.CafeInventoryStatusView.as_view(), name='inventory_status'),
    path('inventory/search/', views.CafeInventorySearchView.as_view(), name='inventory_search'),
]
