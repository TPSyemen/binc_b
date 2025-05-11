from django.urls import path
from .views_preferences import UserPreferenceView, BrandPreferenceToggleView, BrandPreferenceStatusView

urlpatterns = [
    path('', UserPreferenceView.as_view(), name='user-preferences'),
    path('brands/toggle/<uuid:brand_id>/', BrandPreferenceToggleView.as_view(), name='brand-preference-toggle'),
    path('brands/status/<uuid:brand_id>/', BrandPreferenceStatusView.as_view(), name='brand-preference-status'),
]
