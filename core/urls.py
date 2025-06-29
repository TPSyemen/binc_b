"""
core/urls.py
--------------
Defines authentication and admin-related API endpoints for the core app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    AccessPointLoginAPIView,
    UserViewSet,
    UserProfileAPIView,
    CustomTokenObtainPairView,  # أضف هذا
)
from .views_site_admin import ensure_site_view

app_name = 'core'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # استخدم الكلاس المخصص
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenObtainPairView.as_view(), name='token_verify'),
    path('ensure-site/', ensure_site_view, name='ensure-site'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
]

urlpatterns += router.urls
