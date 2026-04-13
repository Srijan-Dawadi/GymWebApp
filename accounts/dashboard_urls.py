from django.urls import path
from .dashboard_views import DashboardView, chart_data_api
from .reports_views import ReportsView, ExportReportView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('chart-data/', chart_data_api, name='chart_data_api'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('reports/export/', ExportReportView.as_view(), name='export_report'),
]
