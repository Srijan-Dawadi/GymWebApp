from django.urls import path

from . import views

app_name = 'cafe'

urlpatterns = [
    path('', views.CafeView.as_view(), name='cafe_home'),
    path('orders/create/', views.CreateOrderView.as_view(), name='cafe_order_create'),
    path('orders/<int:pk>/status/', views.UpdateOrderStatusView.as_view(), name='cafe_order_status'),
]
