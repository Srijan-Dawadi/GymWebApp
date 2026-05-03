from django.urls import path
from . import views

urlpatterns = [
    path('', views.InventoryView.as_view(), name='inventory'),
    path('add/', views.InventoryAddView.as_view(), name='inventory_add'),
    path('<int:pk>/edit/', views.InventoryEditView.as_view(), name='inventory_edit'),
    path('<int:pk>/delete/', views.InventoryDeleteView.as_view(), name='inventory_delete'),
    path('search/', views.InventorySearchView.as_view(), name='inventory_search'),
]
