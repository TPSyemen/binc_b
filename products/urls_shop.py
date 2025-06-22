from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_shop import ShopViewSet, ShopRegisterView

router = DefaultRouter()
router.register(r'', ShopViewSet, basename='shop')

urlpatterns = [
    path('create/', ShopRegisterView.as_view(), name='shop-create'),
]

urlpatterns += router.urls
