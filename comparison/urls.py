from django.urls import path
from .views import ComparisonView

urlpatterns = [
    path('', ComparisonView.as_view(), name='compare-products-generic'),  # لدعم GET و POST بدون معرف
    path('<uuid:product_id>/compare/', ComparisonView.as_view(), name='compare-products'),
]
