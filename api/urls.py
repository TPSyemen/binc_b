"""
api/urls.py
-----------
URL configuration for frontend integration APIs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .frontend_views import FrontendAPIViewSet
from .documentation_views import APIDocumentationViewSet

# Create router for API endpoints
router = DefaultRouter()
router.register(r'frontend', FrontendAPIViewSet, basename='frontend-api')
router.register(r'docs', APIDocumentationViewSet, basename='api-docs')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
]
