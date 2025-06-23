from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from core.models import Product
from .serializers import ProductListSerializer

class PopularProductsView(APIView):
    """
    API view for retrieving popular products.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get popular products based on views, likes, and rating.
        """
        try:
            # Get products with high views, likes, and rating
            popular_products = Product.objects.filter(
                is_active=True,
                in_stock=True
            ).order_by('-rating')[:10]
            
            serializer = ProductListSerializer(popular_products, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving popular products: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
