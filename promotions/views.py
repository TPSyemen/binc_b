"""
promotions/views.py
-------------------
Defines promotions-related API views.
"""

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Promotion, DiscountCode
from .serializers import PromotionSerializer, DiscountCodeSerializer
from core.models import User
from rest_framework.parsers import JSONParser

class PromotionListCreateView(generics.ListCreateAPIView):
    queryset = Promotion.objects.filter(is_active=True)
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DiscountCodeListCreateView(generics.ListCreateAPIView):
    queryset = DiscountCode.objects.all()
    serializer_class = DiscountCodeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class PromotionListView(APIView):
    """Retrieve all active promotions."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request):
        promotions = Promotion.objects.filter(is_active=True)
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)

class PromotionDetailView(APIView):
    """Retrieve details of a specific promotion."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request, promotionId):
        promotion = get_object_or_404(Promotion, id=promotionId)
        serializer = PromotionSerializer(promotion)
        return Response(serializer.data)

class PromotionCreateView(APIView):
    """Create a new promotion."""
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data  # Ensure JSON data is read correctly
            serializer = PromotionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PromotionUpdateView(APIView):
    """Update an existing promotion."""
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser]

    def put(self, request, promotionId):
        promotion = get_object_or_404(Promotion, id=promotionId)
        serializer = PromotionSerializer(promotion, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PromotionDeleteView(APIView):
    """Delete a promotion."""
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser]

    def delete(self, request, promotionId):
        promotion = get_object_or_404(Promotion, id=promotionId)
        promotion.delete()
        return Response({"message": "Promotion deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class CustomerPromotionRecommendationsView(APIView):
    """Retrieve personalized promotions for a specific customer."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, customerId):
        customer = get_object_or_404(User, id=customerId)
        # Example logic for recommendations (can be replaced with AI-based logic)
        promotions = Promotion.objects.filter(is_active=True)[:5]
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)

class PromotionForecastView(APIView):
    """Retrieve demand forecasts for promotions."""
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser]

    def get(self, request):
        # Example response for forecast (replace with actual ML-based logic)
        forecast_data = {
            "holiday_season": {"expected_demand": 1200, "recommended_discount": "20%"},
            "weekend_sales": {"expected_demand": 800, "recommended_discount": "15%"}
        }
        return Response(forecast_data)
