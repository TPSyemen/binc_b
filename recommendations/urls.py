from django.urls import path
from .views import RecommendationView, HybridRecommendationView

urlpatterns = [
    path('', RecommendationView.as_view(), name='recommendations'),
    path('recommendations/hybrid/', HybridRecommendationView.as_view(), name='hybrid-recommendations'),
]
