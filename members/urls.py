from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberListView.as_view(), name='member_list'),
    path('add/', views.MemberCreateView.as_view(), name='member_add'),
    path('<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('<int:pk>/edit/', views.MemberEditView.as_view(), name='member_edit'),
    path('<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member_delete'),
    path('descriptors/', views.descriptors_api, name='member_descriptors'),
    path('search/', views.member_search_api, name='member_search_api'),
]
