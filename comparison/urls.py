from django.urls import path
from .views import ComparisonView

urlpatterns = [
    path('<uuid:product_id>/compare/', ComparisonView.as_view(), name='compare-products'),
]
