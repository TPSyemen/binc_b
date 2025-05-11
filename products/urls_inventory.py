from django.urls import path
from .views_inventory import InventoryUpdateView, BulkInventoryUpdateView, VerifiedInventoryUpdateView

urlpatterns = [
    path('<uuid:product_id>/inventory/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('bulk-inventory/', BulkInventoryUpdateView.as_view(), name='bulk-inventory-update'),
    path('verified-inventory/<uuid:token_id>/', VerifiedInventoryUpdateView.as_view(), name='verified-inventory-update'),
]
