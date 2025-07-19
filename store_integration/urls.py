"""
store_integration/urls.py
-------------------------
URL configuration for store integration API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StoreIntegrationConfigViewSet,
    ProductMappingViewSet,
    PriceHistoryViewSet,
    SyncLogViewSet,
    ProductComparisonViewSet,
    StorePerformanceViewSet,
    ProductAggregationViewSet
)

router = DefaultRouter()
router.register(r'configs', StoreIntegrationConfigViewSet, basename='integration-config')
router.register(r'mappings', ProductMappingViewSet, basename='product-mapping')
router.register(r'price-history', PriceHistoryViewSet, basename='price-history')
router.register(r'sync-logs', SyncLogViewSet, basename='sync-log')
router.register(r'comparisons', ProductComparisonViewSet, basename='product-comparison')
router.register(r'performance', StorePerformanceViewSet, basename='store-performance')
router.register(r'aggregation', ProductAggregationViewSet, basename='product-aggregation')

urlpatterns = [
    path('api/store-integration/', include(router.urls)),
]
