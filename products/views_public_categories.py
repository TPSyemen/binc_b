from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser
from core.models import Category
from .serializers import CategorySerializer

class PublicCategoriesView(APIView):
    """
    API view for retrieving all categories without authentication.
    Also allows creating a new category (admin only).
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

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

    def post(self, request):
        """
        Create a new category (admin only).
        """
        user = request.user
        if not user.is_authenticated or getattr(user, 'user_type', None) != 'admin':
            return Response({"error": "Unauthorized. Admins only."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
