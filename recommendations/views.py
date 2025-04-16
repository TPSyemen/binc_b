from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Product, User
from .serializers import ProductSerializer
from .models import ProductRecommendation

# ai lib
import pandas as pd
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Preferred products based on previous interactions
        preferred_products = Product.objects.filter(
            reviews__user=user
        ).distinct()

        # Liked products
        liked_products = Product.objects.filter(
            likes__gt=0, reviews__user=user
        ).distinct()

        # New products (last 30 days)
        new_products = Product.objects.filter(
            created_at__gte=now() - timedelta(days=30)
        )

        # Most liked products
        popular_products = Product.objects.order_by('-likes')[:10]

        # Serialize each category
        preferred_serializer = ProductSerializer(preferred_products, many=True)
        liked_serializer = ProductSerializer(liked_products, many=True)
        new_serializer = ProductSerializer(new_products, many=True)
        popular_serializer = ProductSerializer(popular_products, many=True)

        # Return categorized recommendations
        return Response({
            "preferred": preferred_serializer.data,
            "liked": liked_serializer.data,
            "new": new_serializer.data,
            "popular": popular_serializer.data
        })

class HybridRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Step 1: Fetch user-product interactions
        interactions = ProductRecommendation.objects.all().values('user_id', 'product_id', 'score')
        df = pd.DataFrame(interactions)

        # Step 2: Collaborative Filtering using implicit
        user_item_matrix = csr_matrix(
            (df['score'], (df['user_id'], df['product_id']))
        )
        model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)
        model.fit(user_item_matrix)

        # Predict scores for all products for the current user
        user_index = user.id
        recommendations = model.recommend(
            user_index, user_item_matrix[user_index], N=10
        )

        # Step 3: Fetch recommended products
        recommended_product_ids = [product_id for product_id, _ in recommendations]
        recommended_products = Product.objects.filter(id__in=recommended_product_ids)

        serializer = ProductSerializer(recommended_products, many=True)
        return Response(serializer.data)
