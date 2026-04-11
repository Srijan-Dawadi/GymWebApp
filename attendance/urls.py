from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttendanceView.as_view(), name='attendance'),
    path('checkin/', views.checkin_api, name='checkin_api'),
    path('export/', views.AttendanceExportView.as_view(), name='attendance_export'),
]
