from django.urls import path
from .views_product_reviews import ProductReviewsView, ProductReviewDetailView

urlpatterns = [
    path('<uuid:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('<uuid:product_id>/reviews/<int:review_id>/', ProductReviewDetailView.as_view(), name='product-review-detail'),
]
