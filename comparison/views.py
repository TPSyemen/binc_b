from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from core.models import Product
from products.serializers import ProductDetailSerializer

# Create your views here.
# ------------------------------------------------------------------------
#                       Comparison View
# --------------------------------------------------------------------------------
class ComparisonView(APIView):
    """Compare a product with similar products."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        similar_products = Product.objects.filter(
            category=product.category,
            price__range=(product.price * 0.8, product.price * 1.2),
            is_active=True
        ).exclude(id=product.id).order_by('-rating', '-views')[:5]

        return Response({
            "product": ProductDetailSerializer(product).data,
            "similar_products": ProductDetailSerializer(similar_products, many=True).data
        })
