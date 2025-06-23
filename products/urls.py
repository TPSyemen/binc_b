"""
products/urls.py
----------------
Defines product-related API endpoints (list, detail, create, update, etc.).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductListView,
    ProductDetailView,
    ProductUpdateView,
    ProductDeleteView,
    FeaturedProductsView,
    ProductSearchView,
    RecentlyViewedProductsView,
    SimilarProductsView,
    ProductPriceHistoryView,
)
from .views_popular import PopularProductsView
from .views_public_categories import PublicCategoriesView
from .views import BrandViewSet
from .views_reviews_stats import ProductReviewsStatsView

router = DefaultRouter()
router.register(r"brands", BrandViewSet, basename="brand")

urlpatterns = [
    path("", ProductListView.as_view(), name="product-list"),
    path("<str:pk>/reviews-stats/", ProductReviewsStatsView.as_view(), name="product-reviews-stats"),
    path("<str:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("<uuid:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("<uuid:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    path("featured/", FeaturedProductsView.as_view(), name="featured-products"),
    path("search/", ProductSearchView.as_view(), name="product-search"),
    path(
        "recently-viewed/",
        RecentlyViewedProductsView.as_view(),
        name="recently-viewed-products",
    ),
    path("<uuid:pk>/similar/", SimilarProductsView.as_view(), name="similar-products"),
    path("popular/", PopularProductsView.as_view(), name="popular-products"),
    path("categories/", include("products.urls_categories")),
    path(
        "<uuid:pk>/price-history/",
        ProductPriceHistoryView.as_view(),
        name="product-price-history",
    ),
]

urlpatterns += router.urls
