from django.contrib import admin
from django.urls import path, include
from core.views import LoginAPIView, LogoutAPIView, RegisterAPIView  # Import authentication views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),  
    path('products/', include('products.urls')),
    path('categories/', include('products.urls_categories')),
    path('promotions/', include('promotions.urls')),
    path('reviews/', include('reviews.urls')),
    path('recommendations/', include('recommendations.urls')),
]
