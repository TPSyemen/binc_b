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
    ProductAggregationViewSet,
    StoreIntegrationManagementViewSet,
    WebhookReceiverViewSet,
    RealTimeSyncViewSet,
    StoreAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'configs', StoreIntegrationConfigViewSet, basename='integration-config')
router.register(r'mappings', ProductMappingViewSet, basename='product-mapping')
router.register(r'price-history', PriceHistoryViewSet, basename='price-history')
router.register(r'sync-logs', SyncLogViewSet, basename='sync-log')
router.register(r'comparisons', ProductComparisonViewSet, basename='product-comparison')
router.register(r'performance', StorePerformanceViewSet, basename='store-performance')
router.register(r'aggregation', ProductAggregationViewSet, basename='product-aggregation')
router.register(r'management', StoreIntegrationManagementViewSet, basename='integration-management')
router.register(r'webhooks', WebhookReceiverViewSet, basename='webhook-receiver')
router.register(r'realtime-sync', RealTimeSyncViewSet, basename='realtime-sync')
router.register(r'analytics', StoreAnalyticsViewSet, basename='store-analytics')

urlpatterns = [
    path('api/store-integration/', include(router.urls)),
]
