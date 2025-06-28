from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_shop import ShopViewSet, ShopRegisterView, ShopCheckView

router = DefaultRouter()
router.register(r'', ShopViewSet, basename='shop')

urlpatterns = [
    path('create/', ShopRegisterView.as_view(), name='shop-create'),
    path('check/', ShopCheckView.as_view(), name='shop-check'),
    path('<uuid:pk>/update/', ShopViewSet.as_view({'put': 'update'}), name='shop-update'),
    path('<uuid:pk>/delete/', ShopViewSet.as_view({'delete': 'destroy'}), name='shop-delete'),
]

urlpatterns += router.urls
