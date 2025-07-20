"""
core/urls.py
--------------
Defines authentication and admin-related API endpoints for the core app.
"""

from django import views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from rest_framework.routers import DefaultRouter
from . import views

from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    AccessPointLoginAPIView,
    UserViewSet,
    UserProfileAPIView,
    CreateOwnerProfileView,
    ShopCheckView,
)
from .views_site_admin import ensure_site_view
from .views_ai_rating import AIRatingViewSet
from .views_discovery import ProductDiscoveryViewSet

app_name = 'core'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ai-ratings', AIRatingViewSet, basename='ai-rating')
router.register(r'discovery', ProductDiscoveryViewSet, basename='product-discovery')

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenObtainPairView.as_view(), name='token_verify'),
    path('ensure-site/', ensure_site_view, name='ensure-site'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('owner/profile/create/', CreateOwnerProfileView.as_view(), name='create-owner-profile'),
    path('shop/check/', ShopCheckView.as_view(), name='shop-check'),

    
 path('dashboard/owner/', views.owner_dashboard, name='owner_dashboard'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/<uuid:product_id>/', views.product_edit, name='product_edit'),
    path('products/detail/<uuid:product_id>/', views.product_detail, name='product_detail'),
    path('products/delete/<uuid:product_id>/', views.product_delete, name='product_delete'), # Use POST for deletion!

    # Report URLs
    path('reports/product_interactions/', views.report_product_interactions_pdf, name='report_product_interactions_pdf'),
    path('reports/product_performance/', views.report_product_performance_pdf, name='report_product_performance_pdf'),
]

urlpatterns += router.urls
