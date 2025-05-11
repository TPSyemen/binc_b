from django.urls import path
from .views import (
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView,
    ProductDeleteView, FeaturedProductsView, ProductSearchView, RecentlyViewedProductsView,
    SimilarProductsView
)
from .views_popular import PopularProductsView
from .views_public_categories import PublicCategoriesView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('recently-viewed/', RecentlyViewedProductsView.as_view(), name='recently-viewed-products'),
    path('<uuid:product_id>/similar/', SimilarProductsView.as_view(), name='similar-products'),
    path('popular/', PopularProductsView.as_view(), name='popular-products'),
    path('categories/', PublicCategoriesView.as_view(), name='public-categories'),
]
