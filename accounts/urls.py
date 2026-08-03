from django.urls import path
from .views import LoginView, LogoutView, HealthView, ChangePasswordView
from .user_views import UserListView, UserCreateView, UserEditView, UserDeleteView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/', ChangePasswordView.as_view(), name='change_password'),
    path('health/', HealthView.as_view(), name='health'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/add/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
]
