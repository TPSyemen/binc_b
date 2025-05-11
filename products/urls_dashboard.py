from django.urls import path
from .views_dashboard import (
    DashboardStatsView,
    OwnerProductsView,
    OwnerProductDetailView,
    OwnerAnalyticsView,
    OwnerShopSettingsView
)
from .views_brands import BrandListCreateView, BrandDetailView
from .views_specifications import SpecificationCategoryListView, ProductSpecificationsView

urlpatterns = [
    # Dashboard stats
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),

    # Products management
    path('products/', OwnerProductsView.as_view(), name='owner-products'),
    path('products/<uuid:product_id>/', OwnerProductDetailView.as_view(), name='owner-product-detail'),

    # Orders management has been removed

    # Analytics
    path('analytics/', OwnerAnalyticsView.as_view(), name='owner-analytics'),

    # Shop settings
    path('settings/', OwnerShopSettingsView.as_view(), name='owner-shop-settings'),

    # Brands management
    path('brands/', BrandListCreateView.as_view(), name='owner-brands'),
    path('brands/<uuid:brand_id>/', BrandDetailView.as_view(), name='owner-brand-detail'),

    # Specifications management
    path('specifications/categories/', SpecificationCategoryListView.as_view(), name='owner-specification-categories'),
    path('products/<uuid:product_id>/specifications/', ProductSpecificationsView.as_view(), name='owner-product-specifications'),
]
