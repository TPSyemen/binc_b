"""
reviews/urls.py
--------------
Defines review-related API endpoints for products.
"""

from django.urls import path
from .views import ReviewListCreateView
from .views_product_reviews import ProductReviewsView, ProductReviewDetailView

urlpatterns = [
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='product-reviews-old'),
    path('products/<uuid:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/<uuid:product_id>/reviews/<int:review_id>/', ProductReviewDetailView.as_view(), name='product-review-detail'),
    path('add/', ReviewListCreateView.as_view(), name='add-review'),
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
]
