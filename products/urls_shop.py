from django.urls import path
from .views_shop import ShopCheckView, ShopRegisterView, ShopListView, ShopDetailView

urlpatterns = [
    path('check/', ShopCheckView.as_view(), name='shop-check'),
    path('register/', ShopRegisterView.as_view(), name='shop-register'),
    path('', ShopListView.as_view(), name='shop-list'),
    path('<uuid:pk>/', ShopDetailView.as_view(), name='shop-detail'),
]
