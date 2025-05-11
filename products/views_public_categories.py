from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from core.models import Category
from .serializers import CategorySerializer

class PublicCategoriesView(APIView):
    """
    API view for retrieving all categories without authentication.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get all categories.
        """
        try:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving categories: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
