from django.urls import path
from .views_favorites import FavoriteListView, FavoriteToggleView, FavoriteStatusView

urlpatterns = [
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/toggle/<uuid:product_id>/', FavoriteToggleView.as_view(), name='favorite-toggle'),
    path('favorites/status/<uuid:product_id>/', FavoriteStatusView.as_view(), name='favorite-status'),
]
