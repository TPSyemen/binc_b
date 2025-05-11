from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.models import Brand
from .serializers import BrandSerializer

class BrandListCreateView(APIView):
    """
    API view for listing and creating brands.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all brands."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new brand."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BrandDetailView(APIView):
    """
    API view for retrieving, updating and deleting a brand.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, brand_id):
        """Get brand object."""
        try:
            return Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return None

    def get(self, request, brand_id):
        """Get a specific brand."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        brand = self.get_object(brand_id)
        if not brand:
            return Response(
                {"error": "Brand not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BrandSerializer(brand)
        return Response(serializer.data)

    def put(self, request, brand_id):
        """Update a brand."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        brand = self.get_object(brand_id)
        if not brand:
            return Response(
                {"error": "Brand not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BrandSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, brand_id):
        """Delete a brand."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        brand = self.get_object(brand_id)
        if not brand:
            return Response(
                {"error": "Brand not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
