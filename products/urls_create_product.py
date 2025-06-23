from django.urls import path
from products.views import ProductCreateView

urlpatterns = [
    path('', ProductCreateView.as_view(), name='product-create-noapi'),
]
