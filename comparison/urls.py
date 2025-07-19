"""
comparison/urls.py
-----------------
Defines product comparison API endpoints with advanced cross-store comparison.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComparisonView, AdvancedComparisonViewSet

# Create router for advanced comparison features
router = DefaultRouter()
router.register(r'advanced', AdvancedComparisonViewSet, basename='advanced-comparison')

urlpatterns = [
    # Legacy comparison endpoints
    path('', ComparisonView.as_view(), name='compare-products-generic'),
    path('<uuid:product_id>/compare/', ComparisonView.as_view(), name='compare-products'),

    # Advanced comparison endpoints
    path('', include(router.urls)),
]
