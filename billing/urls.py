from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/<int:pk>/edit/', views.PlanEditView.as_view(), name='plan_edit'),
    path('plans/<int:pk>/delete/', views.PlanDeleteView.as_view(), name='plan_delete'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
]
