from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_shop import ShopViewSet

router = DefaultRouter()
router.register(r'', ShopViewSet, basename='shop')

urlpatterns = [
]

urlpatterns += router.urls
