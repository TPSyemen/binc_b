"""
recommendations/views.py
-----------------------
Defines recommendation-related API views.
"""

from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from core.models import Product, User
from reviews.models import Review
from .serializers import ProductSerializer
from .models import ProductRecommendation, UserBehaviorLog
from rest_framework import permissions

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
    parser_classes = [JSONParser]

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

            # إضافة المنتجات التي قام المستخدم بتقييمها
            from reviews.models import Review
            rated_products = list(Review.objects.filter(
                user=user
            ).values_list('product_id', flat=True).order_by('-created_at')[:10])

            # إضافة المنتجات المفضلة (Favorites) إلى بيانات الذكاء الاصطناعي
            from core.models_favorites import Favorite
            favorite_products = Product.objects.filter(id__in=Favorite.objects.filter(user=user).values_list('product_id', flat=True))
            favorite_serializer = ProductSerializer(favorite_products, many=True)

            # Prepare user data for recommendations
            user_data = {
                'viewed_products': viewed_products,
                'liked_products': liked_products,
                'rated_products': rated_products,
                'favorite_products': favorite_products
            }

            # استدعاء خدمة التوصيات بالبيانات الصحيحة
            ai_recommendations = recommendation_service.get_personalized_recommendations(
                user.id, user_data, n=20
            )

            # Fetch preferred products from AI recommendations
            preferred_product_ids = ai_recommendations.get('preferred', [])
            preferred_products = list(Product.objects.filter(id__in=preferred_product_ids))
            # fallback إذا بقيت القائمة فارغة بعد الفلترة
            if not preferred_products:
                fallback_qs = Product.objects.order_by('-views')[:10]
                if not fallback_qs:
                    fallback_qs = Product.objects.all().order_by('?')[:10]
                preferred_products = list(fallback_qs)

            # Fetch liked products from AI recommendations
            liked_product_ids = ai_recommendations.get('liked', [])
            # إضافة جميع المنتجات التي أعجب بها المستخدم حتى لو لم تظهر في الذكاء الاصطناعي
            # liked_products هنا عبارة عن قائمة معرفات من السطر السابق (وليس كويري)
            all_liked_ids = set(liked_product_ids)
            if liked_products:
                all_liked_ids = all_liked_ids.union(set(liked_products))
            liked_products = list(Product.objects.filter(id__in=all_liked_ids))
            # fallback إذا بقيت القائمة فارغة بعد الفلترة
            if not liked_products:
                fallback_qs = Product.objects.order_by('-views')[:10]
                if not fallback_qs:
                    fallback_qs = Product.objects.all().order_by('?')[:10]
                liked_products = list(fallback_qs)

            # New products (last 30 days), ordered from newest to oldest
            new_products = Product.objects.filter(
                created_at__gte=now() - timedelta(days=30)
            ).order_by('-created_at')[:10]

            # Most popular products (based on views), ordered from most to least
            popular_products = Product.objects.order_by('-views')[:30]

            # Hybrid recommendations: 30% new, 70% popular (من أصل 10 منتجات)
            hybrid_count = 10
            new_count = max(1, int(hybrid_count * 0.3))  # 3 منتجات جديدة
            popular_count = hybrid_count - new_count     # 7 منتجات شهيرة
            new_list = list(new_products)[:new_count]
            popular_list = [p for p in popular_products if p.id not in {n.id for n in new_list}][:popular_count]
            hybrid_products = new_list + popular_list

            hybrid_serializer = ProductSerializer(hybrid_products, many=True)

            # Serialize each category
            preferred_serializer = ProductSerializer(preferred_products, many=True)
            liked_serializer = ProductSerializer(liked_products, many=True)
            new_serializer = ProductSerializer(new_products, many=True)
            popular_serializer = ProductSerializer(popular_products, many=True)
            # Favorites
            favorite_serializer = ProductSerializer(favorite_products, many=True)

            response_data = {
                "preferred": preferred_serializer.data,
                "liked": liked_serializer.data,
                "new": new_serializer.data,
                "popular": popular_serializer.data,
                "favorites": favorite_serializer.data,
            }
            if hybrid_serializer is not None:
                response_data["hybrid"] = hybrid_serializer.data
            # إضافة نتائج الذكاء الاصطناعي الخام في الاستجابة النهائية دائماً
            response_data["ai_raw"] = ai_recommendations
            return Response(response_data)
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
        # Favorites
        from core.models_favorites import Favorite
        favorite_products = Product.objects.filter(id__in=Favorite.objects.filter(user=user).values_list('product_id', flat=True))
        favorite_serializer = ProductSerializer(favorite_products, many=True)
        # Hybrid (optional fallback)
        hybrid_products = []
        hybrid_serializer = None
        try:
            hybrid_count = 10
            new_count = max(1, int(hybrid_count * 0.3))
            popular_count = hybrid_count - new_count
            new_list = list(new_products)[:new_count]
            popular_list = [p for p in popular_products if p.id not in {n.id for n in new_list}][:popular_count]
            hybrid_products = new_list + popular_list
            hybrid_serializer = ProductSerializer(hybrid_products, many=True)
        except Exception:
            pass
        response_data = {
            "preferred": preferred_serializer.data,
            "liked": liked_serializer.data,
            "new": new_serializer.data,
            "popular": popular_serializer.data,
            "favorites": favorite_serializer.data,
        }
        if hybrid_serializer is not None:
            response_data["hybrid"] = hybrid_serializer.data
        # إصلاح نهائي: إذا لم يكن ai_recommendations معرفًا، لا تضف ai_raw
        # أو يمكن حذف هذا السطر نهائيًا من fallback لأن ai_recommendations غير متاح في هذا السياق.
        return Response(response_data)


# -----------------------------------------------------------------------
#                 User Behavior Tracking View
# -----------------------------------------------------------------------
class UserBehaviorView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

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
    parser_classes = [JSONParser]

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

# -----------------------------------------------------------------------
#        External Hybrid Recommendation View (AI + Exclude Input)
# -----------------------------------------------------------------------
class ExternalHybridRecommendationView(APIView):
    permission_classes = [permissions.AllowAny]  # السماح للجميع بالوصول
    parser_classes = [JSONParser]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        try:
            viewed_products = []
            liked_products = []
            rated_products = []
            favorite_products = []
            if user:
                viewed_products = list(UserBehaviorLog.objects.filter(
                    user=user, action='view'
                ).values_list('product_id', flat=True).order_by('-timestamp')[:20])
                liked_products = list(UserBehaviorLog.objects.filter(
                    user=user, action='like'
                ).values_list('product_id', flat=True).order_by('-timestamp')[:10])
                from reviews.models import Review
                rated_products = list(Review.objects.filter(
                    user=user
                ).values_list('product_id', flat=True).order_by('-created_at')[:10])
                from core.models_favorites import Favorite
                favorite_products = list(Favorite.objects.filter(user=user).values_list('product_id', flat=True))
            # دمج كل المنتجات الأصلية بدون تكرار
            product_ids = list(set(viewed_products + liked_products + rated_products + favorite_products))
            original_products = list(Product.objects.filter(id__in=product_ids))
            # استدعاء الذكاء الاصطناعي لجلب توصيات جديدة ليست ضمن القائمة
            user_data = {
                'viewed_products': viewed_products,
                'liked_products': liked_products,
                'rated_products': rated_products,
                'favorite_products': favorite_products
            }
            ai_recommendations = recommendation_service.get_personalized_recommendations(
                user.id if user else None, user_data, n=30
            )
            ai_ids = ai_recommendations.get('preferred', [])
            # استبعاد المنتجات الأصلية
            new_ids = [pid for pid in ai_ids if pid not in product_ids]
            new_products = list(Product.objects.filter(id__in=new_ids))
            # حساب النسب
            total_count = min(10, len(original_products) + len(new_products))
            orig_count = max(1, int(total_count * 0.3))
            new_count = total_count - orig_count
            # اختيار المنتجات
            selected_originals = original_products[:orig_count]
            selected_new = new_products[:new_count]
            # fallback إذا بقيت ai_new فارغة بعد الفلترة
            if not selected_new:
                fallback_qs = Product.objects.filter(is_active=True).order_by('-views')[:new_count]
                if not fallback_qs:
                    fallback_qs = Product.objects.filter(is_active=True).order_by('?')[:new_count]
                selected_new = list(fallback_qs)
            final_products = selected_originals + selected_new
            serializer = ProductSerializer(final_products, many=True)
            return Response({
                "results": serializer.data,
                "source": {
                    "original": ProductSerializer(selected_originals, many=True).data,
                    "ai_new": ProductSerializer(selected_new, many=True).data,
                    "ai_raw": ai_recommendations
                }
            })
        except Exception as e:
            logger.error(f"Error in external hybrid recommendations: {e}")
            return Response({"error": "An error occurred while generating recommendations"}, status=500)


# -----------------------------------------------------------------------
#                    Enhanced Recommendation Views
# -----------------------------------------------------------------------

class InteractionTriggeredRecommendationView(APIView):
    """
    API view for triggering recommendations based on user interactions.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Trigger recommendations based on user interaction with a product.

        Expected payload:
        {
            "product_id": "uuid",
            "interaction_type": "view|like|add_to_cart|etc",
            "context": {...}  // optional
        }
        """
        try:
            product_id = request.data.get('product_id')
            interaction_type = request.data.get('interaction_type')
            context = request.data.get('context', {})

            if not product_id or not interaction_type:
                return Response(
                    {'error': 'product_id and interaction_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate product exists
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Trigger recommendations
            recommendations = recommendation_service.trigger_recommendations_on_interaction(
                user_id=str(request.user.id),
                product_id=product_id,
                interaction_type=interaction_type,
                context=context
            )

            # Create recommendation session for tracking
            session = RecommendationSession.objects.create(
                user=request.user,
                session_id=request.session.session_key or 'anonymous',
                trigger_product=product,
                trigger_interaction=interaction_type,
                recommended_products=[
                    rec['product_id'] for rec_type in recommendations.get('recommendations', {}).values()
                    for rec in rec_type if isinstance(rec, dict) and 'product_id' in rec
                ],
                recommendation_types=list(recommendations.get('recommendations', {}).keys())
            )

            # Add session ID to response
            recommendations['session_id'] = str(session.id)

            return Response(recommendations)

        except Exception as e:
            logger.error(f"Error in interaction-triggered recommendations: {e}")
            return Response(
                {'error': 'An error occurred while generating recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossStoreRecommendationView(APIView):
    """
    API view for getting cross-store recommendations for a specific product.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        """
        Get cross-store recommendations for a specific product.
        """
        try:
            # Validate product exists
            try:
                product = Product.objects.select_related('shop', 'brand', 'category').get(
                    id=product_id, is_active=True
                )
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get cross-store recommendations
            cross_store_recs = recommendation_service.get_cross_store_recommendations(product)

            return Response({
                'original_product': {
                    'id': str(product.id),
                    'name': product.name,
                    'price': float(product.price),
                    'shop_name': product.shop.name,
                    'rating': float(product.rating)
                },
                'cross_store_recommendations': cross_store_recs,
                'total_alternatives': len(cross_store_recs)
            })

        except Exception as e:
            logger.error(f"Error in cross-store recommendations: {e}")
            return Response(
                {'error': 'An error occurred while getting cross-store recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserInteractionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user interactions with products.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserInteraction.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return UserInteractionSerializer

    def create(self, request, *args, **kwargs):
        """
        Create or update a user interaction.
        """
        try:
            product_id = request.data.get('product_id')
            interaction_type = request.data.get('interaction_type')
            context = request.data.get('context', {})

            if not product_id or not interaction_type:
                return Response(
                    {'error': 'product_id and interaction_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate product exists
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get or create interaction
            interaction, created = UserInteraction.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={
                    'interaction_type': interaction_type,
                    'context': context
                }
            )

            if not created:
                # Update existing interaction
                interaction.interaction_count += 1
                interaction.last_interaction_type = interaction_type
                interaction.context.update(context)
                interaction.save()

            # Record interaction for recommendations
            recommendation_service.record_user_interaction(
                str(request.user.id), product_id, interaction_type, context
            )

            serializer = self.get_serializer(interaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error creating user interaction: {e}")
            return Response(
                {'error': 'An error occurred while recording interaction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get user interaction analytics.
        """
        try:
            interactions = self.get_queryset()

            # Calculate analytics
            total_interactions = interactions.count()
            interaction_types = {}

            for interaction in interactions:
                interaction_type = interaction.interaction_type
                if interaction_type not in interaction_types:
                    interaction_types[interaction_type] = {
                        'count': 0,
                        'unique_products': set()
                    }

                interaction_types[interaction_type]['count'] += interaction.interaction_count
                interaction_types[interaction_type]['unique_products'].add(str(interaction.product.id))

            # Convert sets to counts
            for interaction_type in interaction_types:
                interaction_types[interaction_type]['unique_products'] = len(
                    interaction_types[interaction_type]['unique_products']
                )

            # Get user preferences
            preferences = recommendation_service.get_user_preferences(str(request.user.id))

            return Response({
                'total_interactions': total_interactions,
                'interaction_breakdown': interaction_types,
                'user_preferences': preferences,
                'most_interacted_products': [
                    {
                        'product_id': str(interaction.product.id),
                        'product_name': interaction.product.name,
                        'interaction_count': interaction.interaction_count,
                        'last_interaction': interaction.last_interaction_at
                    }
                    for interaction in interactions.order_by('-interaction_count')[:10]
                ]
            })

        except Exception as e:
            logger.error(f"Error getting interaction analytics: {e}")
            return Response(
                {'error': 'An error occurred while getting analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
