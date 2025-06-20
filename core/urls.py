"""
core/urls.py
--------------
Defines authentication and admin-related API endpoints for the core app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    AccessPointLoginAPIView,
)
from .views_site_admin import ensure_site_view

app_name = 'core'

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('ensure-site/', ensure_site_view, name='ensure-site'),
]
