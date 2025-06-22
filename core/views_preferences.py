from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models_preferences import UserPreference, BrandPreference
from .serializers_preferences import UserPreferenceSerializer, BrandPreferenceSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser

class UserPreferenceView(APIView):
    """API view for managing user preferences."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        """Get the authenticated user's preferences."""
        # Try to get existing preferences or create new ones
        user_preference, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(user_preference)
        return Response(serializer.data)

    def post(self, request):
        """Create or update the authenticated user's preferences."""
        # Try to get existing preferences or create new ones
        user_preference, created = UserPreference.objects.get_or_create(user=request.user)
        
        # Update with new data
        serializer = UserPreferenceSerializer(user_preference, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Reset the authenticated user's preferences to defaults."""
        # Try to get existing preferences
        try:
            user_preference = UserPreference.objects.get(user=request.user)
            
            # Reset to defaults
            user_preference.min_price = 0
            user_preference.max_price = 10000
            user_preference.save()
            
            # Remove all brand preferences
            user_preference.brand_preferences.all().delete()
            
            return Response(
                {"message": "تم إعادة تعيين التفضيلات بنجاح."},
                status=status.HTTP_200_OK
            )
        except UserPreference.DoesNotExist:
            return Response(
                {"message": "لا توجد تفضيلات لإعادة تعيينها."},
                status=status.HTTP_404_NOT_FOUND
            )


class BrandPreferenceToggleView(APIView):
    """API view for toggling a brand as preferred."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, brand_id):
        """Add or remove a brand from preferences."""
        # Get or create user preference
        user_preference, _ = UserPreference.objects.get_or_create(user=request.user)
        
        # Check if the brand is already in preferences
        brand_preference = BrandPreference.objects.filter(
            user_preference=user_preference,
            brand_id=brand_id
        ).first()
        
        if brand_preference:
            # If it already exists, remove it
            brand_preference.delete()
            return Response(
                {"message": "تمت إزالة العلامة التجارية من التفضيلات بنجاح."},
                status=status.HTTP_200_OK
            )
        else:
            # If it doesn't exist, add it
            brand_preference = BrandPreference.objects.create(
                user_preference=user_preference,
                brand_id=brand_id
            )
            serializer = BrandPreferenceSerializer(brand_preference)
            return Response(
                {
                    "message": "تمت إضافة العلامة التجارية إلى التفضيلات بنجاح.",
                    "brand_preference": serializer.data
                },
                status=status.HTTP_201_CREATED
            )


class BrandPreferenceStatusView(APIView):
    """API view for checking if a brand is in preferences."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, brand_id):
        """Check if a brand is in the user's preferences."""
        # Get user preference if it exists
        try:
            user_preference = UserPreference.objects.get(user=request.user)
            is_preferred = BrandPreference.objects.filter(
                user_preference=user_preference,
                brand_id=brand_id
            ).exists()
        except UserPreference.DoesNotExist:
            is_preferred = False
        
        return Response({"is_preferred": is_preferred})
