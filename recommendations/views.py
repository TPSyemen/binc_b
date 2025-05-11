from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.models import Product, User
from reviews.models import Review
from .serializers import ProductSerializer
from .models import ProductRecommendation, UserBehaviorLog

# AI services
from .ai_services import recommendation_service
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)
# -----------------------------------------------------------------------
#                          Recommendation View
# -----------------------------------------------------------------------
class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            # Get user behavior data
            viewed_products = list(UserBehaviorLog.objects.filter(
                user=user, action='view'
            ).values_list('product_id', flat=True).order_by('-timestamp')[:20])

            liked_products = list(UserBehaviorLog.objects.filter(
                user=user, action='like'
            ).values_list('product_id', flat=True).order_by('-timestamp')[:10])

            # Prepare user data for recommendations
            user_data = {
                'viewed_products': viewed_products,
                'liked_products': liked_products
            }

            # Ensure models are trained
            self._ensure_models_trained()

            # Get AI-powered personalized recommendations
            ai_recommendations = recommendation_service.get_personalized_recommendations(
                user.id, user_data, n=20
            )

            # Fetch preferred products from AI recommendations
            preferred_product_ids = ai_recommendations.get('preferred', [])
            preferred_products = Product.objects.filter(id__in=preferred_product_ids)

            # Fetch liked products from AI recommendations
            liked_product_ids = ai_recommendations.get('liked', [])
            liked_products = Product.objects.filter(id__in=liked_product_ids)

            # If AI recommendations are insufficient, fall back to basic recommendations
            if len(preferred_products) < 5:
                # Fallback: Preferred products based on previous interactions
                fallback_preferred = Product.objects.filter(
                    reviews__user=user
                ).distinct()[:10]
                preferred_products = list(preferred_products) + list(fallback_preferred)

            if len(liked_products) < 5:
                # Fallback: Liked products
                fallback_liked = Product.objects.filter(
                    likes__gt=0, reviews__user=user
                ).distinct()[:10]
                liked_products = list(liked_products) + list(fallback_liked)

            # New products (last 30 days)
            new_products = Product.objects.filter(
                created_at__gte=now() - timedelta(days=30)
            )[:10]

            # Most popular products (based on views)
            popular_products = Product.objects.order_by('-views')[:10]

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
        except Exception as e:
            logger.error(f"Error in recommendations: {e}")
            # Fallback to basic recommendations if AI fails
            return self._get_basic_recommendations(user)

    def _ensure_models_trained(self):
        """Ensure that recommendation models are trained."""
        try:
            # Check if we need to train the collaborative filtering model
            if not hasattr(recommendation_service, 'als_model') or recommendation_service.als_model is None:
                # Get all user-product interactions
                interactions = ProductRecommendation.objects.all().values('user_id', 'product_id', 'score')
                if interactions.exists():
                    df = pd.DataFrame(list(interactions))
                    recommendation_service.train_collaborative_filtering(df)

            # Check if we need to train the content-based filtering model
            if not hasattr(recommendation_service, 'tfidf_vectorizer') or recommendation_service.tfidf_vectorizer is None:
                # Get all products with their descriptions
                products = Product.objects.all().values('id', 'name', 'description', 'category__name', 'brand__name')
                if products.exists():
                    # Prepare data for content-based filtering
                    products_df = pd.DataFrame(list(products))
                    products_df.rename(columns={'category__name': 'category', 'brand__name': 'brand'}, inplace=True)
                    recommendation_service.train_content_based_filtering(products_df)
        except Exception as e:
            logger.error(f"Error ensuring models are trained: {e}")

    def _get_basic_recommendations(self, user):
        """Get basic recommendations without AI."""
        # Preferred products based on previous interactions
        preferred_products = Product.objects.filter(
            reviews__user=user
        ).distinct()[:10]

        # Liked products
        liked_products = Product.objects.filter(
            likes__gt=0, reviews__user=user
        ).distinct()[:10]

        # New products (last 30 days)
        new_products = Product.objects.filter(
            created_at__gte=now() - timedelta(days=30)
        )[:10]

        # Most popular products
        popular_products = Product.objects.order_by('-views')[:10]

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

# -----------------------------------------------------------------------
#                 User Behavior Tracking View
# -----------------------------------------------------------------------
class UserBehaviorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        action = request.data.get('action')  # 'view', 'like', 'purchase'

        if not product_id or not action:
            return Response(
                {"error": "Product ID and action are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the product
            product = Product.objects.get(id=product_id)

            # Log the behavior
            UserBehaviorLog.objects.create(
                user=user,
                product=product,
                action=action
            )

            # Update product metrics
            if action == 'view':
                product.views = product.views + 1
                product.save(update_fields=['views'])
            elif action == 'like':
                product.likes = product.likes + 1
                product.save(update_fields=['likes'])

            # Update recommendation score
            score_mapping = {
                'view': 1.0,
                'like': 3.0,
                'purchase': 5.0
            }

            # Create or update recommendation
            recommendation, created = ProductRecommendation.objects.update_or_create(
                user=user,
                product=product,
                defaults={
                    'score': score_mapping.get(action, 1.0),
                    'recommendation_type': 'preferred'
                }
            )

            return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error logging user behavior: {e}")
            return Response(
                {"error": "An error occurred while logging behavior"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# -----------------------------------------------------------------------
#                 Hybrid Recommendation View
# -----------------------------------------------------------------------
class HybridRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            # Get user behavior data
            viewed_products = list(UserBehaviorLog.objects.filter(
                user=user, action='view'
            ).values_list('product_id', flat=True).order_by('-timestamp')[:20])

            liked_products = list(UserBehaviorLog.objects.filter(
                user=user, action='like'
            ).values_list('product_id', flat=True).order_by('-timestamp')[:10])

            # Prepare user data for recommendations
            user_data = {
                'viewed_products': viewed_products,
                'liked_products': liked_products
            }

            # Train models if needed
            self._ensure_models_trained()

            # Get hybrid recommendations
            recommended_product_ids = recommendation_service.get_hybrid_recommendations(
                user.id, viewed_products, n=10
            )

            # Fetch recommended products
            recommended_products = Product.objects.filter(id__in=recommended_product_ids)

            # Log this recommendation event
            self._log_recommendation_event(user, recommended_products)

            serializer = ProductSerializer(recommended_products, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {e}")
            # Fallback to popular products
            popular_products = Product.objects.order_by('-views')[:10]
            serializer = ProductSerializer(popular_products, many=True)
            return Response(serializer.data)

    def _ensure_models_trained(self):
        """Ensure that recommendation models are trained."""
        try:
            # Check if we need to train the collaborative filtering model
            if not hasattr(recommendation_service, 'als_model') or recommendation_service.als_model is None:
                # Get all user-product interactions
                interactions = ProductRecommendation.objects.all().values('user_id', 'product_id', 'score')
                if interactions.exists():
                    df = pd.DataFrame(list(interactions))
                    recommendation_service.train_collaborative_filtering(df)

            # Check if we need to train the content-based filtering model
            if not hasattr(recommendation_service, 'tfidf_vectorizer') or recommendation_service.tfidf_vectorizer is None:
                # Get all products with their descriptions
                products = Product.objects.all().values('id', 'name', 'description', 'category__name', 'brand__name')
                if products.exists():
                    # Prepare data for content-based filtering
                    products_df = pd.DataFrame(list(products))
                    products_df.rename(columns={'category__name': 'category', 'brand__name': 'brand'}, inplace=True)
                    recommendation_service.train_content_based_filtering(products_df)
        except Exception as e:
            logger.error(f"Error ensuring models are trained: {e}")

    def _log_recommendation_event(self, user, recommended_products):
        """Log recommendation events for future analysis."""
        try:
            for product in recommended_products:
                # Create or update recommendation
                ProductRecommendation.objects.update_or_create(
                    user=user,
                    product=product,
                    defaults={
                        'score': 1.0,  # Default score
                        'recommendation_type': 'hybrid'
                    }
                )
        except Exception as e:
            logger.error(f"Error logging recommendation event: {e}")
