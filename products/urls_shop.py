from django.urls import path
from .views_shop import ShopCheckView, ShopRegisterView

urlpatterns = [
    path('check/', ShopCheckView.as_view(), name='shop-check'),
    path('register/', ShopRegisterView.as_view(), name='shop-register'),
]
