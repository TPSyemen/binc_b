from django.urls import path
from .views import ReviewListCreateView
from .views_product_reviews import ProductReviewsView, ProductReviewDetailView

urlpatterns = [
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='product-reviews-old'),
    # Nuevas URLs para reseñas de productos con UUID
    path('products/<uuid:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/<uuid:product_id>/reviews/<int:review_id>/', ProductReviewDetailView.as_view(), name='product-review-detail'),
    # ... otras URLs si es necesario ...
]


urlpatterns = [
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='product-reviews'),
]
