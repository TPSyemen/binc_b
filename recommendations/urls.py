from django.urls import path
from .views import RecommendationView, HybridRecommendationView, UserBehaviorView

urlpatterns = [
    path('', RecommendationView.as_view(), name='recommendations'),
    path('hybrid/', HybridRecommendationView.as_view(), name='hybrid-recommendations'),
    path('track-behavior/', UserBehaviorView.as_view(), name='track-user-behavior'),
]
