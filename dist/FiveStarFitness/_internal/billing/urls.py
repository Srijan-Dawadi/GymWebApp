from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/<int:pk>/edit/', views.PlanEditView.as_view(), name='plan_edit'),
    path('plans/<int:pk>/delete/', views.PlanDeleteView.as_view(), name='plan_delete'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('member-plan/<int:pk>/', views.MemberPlanInfoView.as_view(), name='member_plan_info'),
    # Payment approval
    path('payments/approval/', views.PaymentApprovalView.as_view(), name='payment_approval'),
    path('payments/<int:pk>/approve/', views.PaymentApproveView.as_view(), name='payment_approve'),
    path('payments/<int:pk>/flag/', views.PaymentFlagView.as_view(), name='payment_flag'),
    path('payments/<int:pk>/unflag/', views.PaymentUnflagView.as_view(), name='payment_unflag'),
    path('payments/approve-all/', views.PaymentApproveAllView.as_view(), name='payment_approve_all'),
]
