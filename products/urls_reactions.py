from django.urls import path
from .views_reactions import ProductReactionView

urlpatterns = [
    path('<uuid:product_id>/reaction/', ProductReactionView.as_view(), name='product-reaction'),
]
