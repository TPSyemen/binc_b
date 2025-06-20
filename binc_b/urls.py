"""
binc_b/urls.py
--------------
Main URL configuration for the project. Includes all app endpoints and admin.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import api_index

urlpatterns = [
    path('', api_index, name='api-index'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/shop/', include('products.urls_shop')),
    path('api/products/', include('products.urls')),
    path('api/products/', include('products.urls_reactions')),
    path('api/products/', include('products.urls_inventory')),
    path('api/products/', include('reviews.urls_product_reviews')),
    path('api/comparison/', include('comparison.urls')),
    path('api/dashboard/', include('products.urls_dashboard')),
    path('products/', include('products.urls')),
    path('categories/', include('products.urls_categories')),
    path('promotions/', include('promotions.urls')),
    path('reviews/', include('reviews.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/notifications/', include('core.urls_notifications')),
    path('api/user/', include('core.urls_favorites')),
    path('api/user/preferences/', include('core.urls_preferences')),
    path('api/verification/', include('core.urls_verification')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
