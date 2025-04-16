from django.urls import path
from .views import (
    PromotionListView, PromotionDetailView, PromotionCreateView,
    PromotionUpdateView, PromotionDeleteView, CustomerPromotionRecommendationsView,
    PromotionForecastView, DiscountCodeListCreateView
)

urlpatterns = [
    path('promotions/', PromotionListView.as_view(), name='promotion-list'),
    path('promotions/<uuid:promotionId>/', PromotionDetailView.as_view(), name='promotion-detail'),
    path('promotions/create/', PromotionCreateView.as_view(), name='promotion-create'),
    path('promotions/<uuid:promotionId>/update/', PromotionUpdateView.as_view(), name='promotion-update'),
    path('promotions/<uuid:promotionId>/delete/', PromotionDeleteView.as_view(), name='promotion-delete'),
    path('promotions/customer/<uuid:customerId>/recommendations/', CustomerPromotionRecommendationsView.as_view(), name='promotion-recommendations'),
    path('promotions/forecast/', PromotionForecastView.as_view(), name='promotion-forecast'),
    path('discount-codes/', DiscountCodeListCreateView.as_view(), name='discount-code-list-create'),  # List and create discount codes
]
