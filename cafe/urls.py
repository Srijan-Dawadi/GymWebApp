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
]
