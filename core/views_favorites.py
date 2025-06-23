from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from core.models import Product
from .models_favorites import Favorite
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from recommendations.serializers import ProductSerializer

class FavoriteListView(APIView):
    """API view for listing user's favorite products."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        """Get all favorite products for the authenticated user."""
        favorites = Favorite.objects.filter(user=request.user)
        
        # Get the product data
        favorite_products = [favorite.product for favorite in favorites]
        
        # Use the ProductListSerializer to serialize the products
        from products.serializers import ProductListSerializer
        serializer = ProductListSerializer(favorite_products, many=True)
        
        return Response(serializer.data)


class FavoriteToggleView(APIView):
    """API view for toggling a product as favorite."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, product_id):
        """Add or remove a product from favorites."""
        product = get_object_or_404(Product, id=product_id)
        
        # Check if the product is already in favorites
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            # If it already exists, remove it
            favorite.delete()
            return Response(
                {"message": "تمت إزالة المنتج من المفضلة بنجاح."},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": "تمت إضافة المنتج إلى المفضلة بنجاح."},
            status=status.HTTP_201_CREATED
        )


class FavoriteStatusView(APIView):
    """API view for checking if a product is in favorites."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, product_id):
        """Check if a product is in the user's favorites."""
        is_favorite = Favorite.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()
        
        return Response({"is_favorite": is_favorite})


class FavoriteProductsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        favorite_ids = Favorite.objects.filter(user=user).values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=favorite_ids)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
