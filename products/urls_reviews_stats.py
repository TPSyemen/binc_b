from django.urls import path
from .views_reviews_stats import ProductReviewsStatsView

urlpatterns = [
    path('<str:pk>/reviews-stats/', ProductReviewsStatsView.as_view(), name='product-reviews-stats'),
]
