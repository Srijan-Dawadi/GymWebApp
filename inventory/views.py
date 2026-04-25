from django.shortcuts import render
from django.views import View

# Create your views here.
class InventoryView(View):
    def get(self, request):
        return render(request, 'Inventory/inventory.html')