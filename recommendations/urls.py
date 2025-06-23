"""
recommendations/urls.py
----------------------
Defines recommendation-related API endpoints.
"""

from django.urls import path
from .views import RecommendationView, HybridRecommendationView, UserBehaviorView, ExternalHybridRecommendationView

urlpatterns = [
    path('', RecommendationView.as_view(), name='recommendations'),
    path('hybrid/', HybridRecommendationView.as_view(), name='hybrid-recommendations'),
    path('track-behavior/', UserBehaviorView.as_view(), name='track-user-behavior'),
    path('external-hybrid/', ExternalHybridRecommendationView.as_view(), name='external-hybrid-recommendations'),
    path('foryou/', ExternalHybridRecommendationView.as_view(), name='foryou-recommendation'),
]
