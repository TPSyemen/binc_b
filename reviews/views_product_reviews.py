from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from core.models import Product
from .models import Review
from .serializers import ReviewSerializer

class ProductReviewsView(APIView):
    """API view for retrieving and creating product reviews."""
    permission_classes = [permissions.AllowAny]  # Permitir acceso público para ver reseñas

    def get(self, request, product_id):
        """Get all reviews for a specific product."""
        product = get_object_or_404(Product, id=product_id)
        reviews = Review.objects.filter(product=product).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        """Create a new review for a product."""
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return Response(
                {"error": "يجب تسجيل الدخول لإضافة تقييم."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        product = get_object_or_404(Product, id=product_id)
        
        # Verificar si el usuario ya ha dejado una reseña para este producto
        existing_review = Review.objects.filter(product=product, user=request.user).first()
        if existing_review:
            return Response(
                {"error": "لقد قمت بالفعل بإضافة تقييم لهذا المنتج."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear una nueva reseña
        data = request.data.copy()
        serializer = ReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewDetailView(APIView):
    """API view for managing a specific product review."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id, review_id):
        """Get a specific review."""
        product = get_object_or_404(Product, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, product_id, review_id):
        """Update a specific review."""
        product = get_object_or_404(Product, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)
        
        # Verificar si el usuario es el autor de la reseña
        if review.user != request.user:
            return Response(
                {"error": "لا يمكنك تعديل تقييم لم تقم بكتابته."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, review_id):
        """Delete a specific review."""
        product = get_object_or_404(Product, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)
        
        # Verificar si el usuario es el autor de la reseña o un administrador
        if review.user != request.user and request.user.user_type != 'admin':
            return Response(
                {"error": "لا يمكنك حذف تقييم لم تقم بكتابته."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
