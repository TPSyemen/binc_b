"""
api/frontend_views.py
---------------------
Comprehensive REST API endpoints for frontend integration, supporting all user experience flows.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.core.cache import cache
from django.db.models import Q, Avg, Count, F
from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import Product, Category, Brand, Shop, User
from core.discovery_service import discovery_service
from core.ai_rating_system import ai_rating_system
from store_integration.models import PriceHistory, ProductMapping
from store_integration.analytics_service import store_analytics_service
from store_integration.realtime_sync import realtime_sync_service
from reviews.models import Review, StoreReview, EngagementEvent
from reviews.services import SentimentAnalysisService
import logging

logger = logging.getLogger(__name__)


class FrontendAPIViewSet(viewsets.ViewSet):
    """
    Comprehensive API ViewSet for frontend integration with all platform features.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def home_feed(self, request):
        """
        Get personalized home feed with trending products, recommendations, and deals.
        """
        try:
            # Get user preferences if authenticated
            user_id = str(request.user.id) if request.user.is_authenticated else None
            
            # Check cache first
            cache_key = f"home_feed_{user_id or 'anonymous'}"
            cached_feed = cache.get(cache_key)
            if cached_feed:
                return Response(cached_feed)
            
            feed_data = {}
            
            # Get trending products
            trending_result = discovery_service.get_trending_products(
                time_period='week',
                limit=12
            )
            feed_data['trending_products'] = trending_result.get('trending_products', [])
            
            # Get personalized recommendations if user is authenticated
            if user_id:
                recommendations_result = discovery_service.get_personalized_recommendations(
                    user_id=user_id,
                    limit=10
                )
                feed_data['recommendations'] = recommendations_result.get('recommendations', [])
            else:
                # Get popular products for anonymous users
                popular_products = Product.objects.filter(
                    is_active=True
                ).order_by('-views', '-rating')[:10]
                
                feed_data['recommendations'] = [
                    discovery_service._enhance_product_data(product)
                    for product in popular_products
                ]
            
            # Get best deals (products with significant discounts)
            deals_products = Product.objects.filter(
                is_active=True,
                original_price__gt=models.F('price')
            ).annotate(
                discount_percentage=((models.F('original_price') - models.F('price')) / models.F('original_price')) * 100
            ).filter(discount_percentage__gte=20).order_by('-discount_percentage')[:8]
            
            feed_data['best_deals'] = [
                discovery_service._enhance_product_data(product)
                for product in deals_products
            ]
            
            # Get featured categories
            featured_categories = Category.objects.annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            ).filter(product_count__gt=0).order_by('-product_count')[:6]
            
            feed_data['featured_categories'] = [
                {
                    'id': str(category.id),
                    'name': category.name,
                    'description': category.description,
                    'product_count': category.product_count,
                    'image_url': getattr(category, 'image_url', '')
                }
                for category in featured_categories
            ]
            
            # Get platform statistics
            feed_data['platform_stats'] = {
                'total_products': Product.objects.filter(is_active=True).count(),
                'total_stores': Shop.objects.filter(is_active=True).count(),
                'total_brands': Brand.objects.count(),
                'total_categories': Category.objects.count()
            }
            
            # Cache for 15 minutes
            cache.set(cache_key, feed_data, 900)
            
            return Response({
                'success': True,
                'feed_data': feed_data,
                'user_authenticated': request.user.is_authenticated,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error generating home feed: {e}")
            return Response(
                {'error': 'Failed to generate home feed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def product_details(self, request):
        """
        Get comprehensive product details with cross-store comparisons and recommendations.
        """
        try:
            product_id = request.query_params.get('product_id')
            
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                product = Product.objects.select_related(
                    'shop', 'brand', 'category'
                ).get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get enhanced product data
            product_data = discovery_service._enhance_product_data(product)
            
            # Get AI rating breakdown
            ai_rating_result = ai_rating_system.calculate_ai_rating(product)
            product_data['ai_rating'] = ai_rating_result
            
            # Get price trends
            price_trends = realtime_sync_service.get_price_trends(product_id, days=30)
            product_data['price_trends'] = price_trends
            
            # Get similar products
            similar_result = discovery_service.discover_similar_products(product_id, limit=8)
            product_data['similar_products'] = similar_result.get('similar_products', [])
            
            # Get recent reviews
            recent_reviews = Review.objects.filter(
                product=product,
                status='approved'
            ).select_related('user').order_by('-created_at')[:10]
            
            product_data['recent_reviews'] = [
                {
                    'id': str(review.id),
                    'user_name': review.user.username,
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'pros': review.pros,
                    'cons': review.cons,
                    'verified_purchase': review.verified_purchase,
                    'sentiment_label': review.sentiment_label,
                    'helpfulness_score': review.helpfulness_score,
                    'created_at': review.created_at.isoformat()
                }
                for review in recent_reviews
            ]
            
            # Track product view event
            if request.user.is_authenticated:
                try:
                    EngagementEvent.objects.create(
                        user=request.user,
                        event_type='product_view',
                        product=product,
                        session_id=request.session.session_key or 'anonymous'
                    )
                except Exception as e:
                    logger.warning(f"Failed to track product view: {e}")
            
            return Response({
                'success': True,
                'product': product_data
            })
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return Response(
                {'error': 'Failed to get product details'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search_products(self, request):
        """
        Search products with intelligent filtering and sorting.
        """
        try:
            query = request.query_params.get('q', '').strip()
            category_id = request.query_params.get('category_id')
            brand_id = request.query_params.get('brand_id')
            shop_id = request.query_params.get('shop_id')
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            min_rating = request.query_params.get('min_rating')
            sort_by = request.query_params.get('sort_by', 'relevance')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Build filters
            filters = {}
            if category_id:
                filters['category_id'] = category_id
            if brand_id:
                filters['brand_id'] = brand_id
            if shop_id:
                filters['shop_id'] = shop_id
            if min_price:
                filters['min_price'] = float(min_price)
            if max_price:
                filters['max_price'] = float(max_price)
            if min_rating:
                filters['min_rating'] = float(min_rating)
            
            # Perform search
            search_result = discovery_service.search_products(
                query=query,
                filters=filters,
                sort_by=sort_by,
                page=page,
                page_size=page_size
            )
            
            return Response(search_result)
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid parameter: {e}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return Response(
                {'error': 'Search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def compare_products(self, request):
        """
        Compare multiple products side by side.
        """
        try:
            product_ids = request.query_params.getlist('product_ids')
            
            if not product_ids or len(product_ids) < 2:
                return Response(
                    {'error': 'At least 2 product_ids are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(product_ids) > 5:
                return Response(
                    {'error': 'Maximum 5 products can be compared'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get products
            products = Product.objects.filter(
                id__in=product_ids,
                is_active=True
            ).select_related('shop', 'brand', 'category')
            
            if products.count() != len(product_ids):
                return Response(
                    {'error': 'One or more products not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get enhanced data for each product
            comparison_data = []
            for product in products:
                product_data = discovery_service._enhance_product_data(product)
                
                # Get AI rating
                ai_rating = ai_rating_system.calculate_ai_rating(product)
                product_data['ai_rating_score'] = ai_rating.get('overall_rating', 0)
                
                comparison_data.append(product_data)
            
            # Generate comparison insights
            insights = self._generate_comparison_insights(comparison_data)
            
            # Track comparison event
            if request.user.is_authenticated:
                try:
                    EngagementEvent.objects.create(
                        user=request.user,
                        event_type='comparison_created',
                        session_id=request.session.session_key or 'anonymous',
                        event_data={
                            'product_ids': product_ids,
                            'comparison_count': len(product_ids)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to track comparison: {e}")
            
            return Response({
                'success': True,
                'products': comparison_data,
                'comparison_insights': insights,
                'total_compared': len(comparison_data)
            })
            
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            return Response(
                {'error': 'Failed to compare products'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def submit_review(self, request):
        """
        Submit a product review with sentiment analysis.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            product_id = request.data.get('product_id')
            rating = request.data.get('rating')
            title = request.data.get('title', '')
            comment = request.data.get('comment', '')
            pros = request.data.get('pros', '')
            cons = request.data.get('cons', '')

            if not all([product_id, rating]):
                return Response(
                    {'error': 'product_id and rating are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if user already reviewed this product
            existing_review = Review.objects.filter(
                user=request.user,
                product=product
            ).first()

            if existing_review:
                return Response(
                    {'error': 'You have already reviewed this product'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create review
            review = Review.objects.create(
                user=request.user,
                product=product,
                rating=int(rating),
                title=title,
                comment=comment,
                pros=pros,
                cons=cons
            )

            # Perform sentiment analysis
            try:
                sentiment_service = SentimentAnalysisService()
                sentiment_data = sentiment_service.analyze_review(review)

                review.sentiment_score = sentiment_data['score']
                review.sentiment_label = sentiment_data['label']
                review.save()
            except Exception as e:
                logger.warning(f"Failed to analyze sentiment: {e}")

            # Track engagement event
            try:
                EngagementEvent.objects.create(
                    user=request.user,
                    event_type='review_submitted',
                    product=product,
                    session_id=request.session.session_key or 'anonymous',
                    event_data={
                        'review_id': str(review.id),
                        'rating': rating
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to track review submission: {e}")

            return Response({
                'success': True,
                'review': {
                    'id': str(review.id),
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'sentiment_label': review.sentiment_label,
                    'created_at': review.created_at.isoformat()
                },
                'message': 'Review submitted successfully'
            })

        except ValueError:
            return Response(
                {'error': 'Invalid rating value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error submitting review: {e}")
            return Response(
                {'error': 'Failed to submit review'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def track_engagement(self, request):
        """
        Track user engagement events (likes, shares, saves, etc.).
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            event_type = request.data.get('event_type')
            product_id = request.data.get('product_id')
            event_data = request.data.get('event_data', {})

            if not event_type:
                return Response(
                    {'error': 'event_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate event type
            valid_events = [
                'product_like', 'product_dislike', 'add_to_cart', 'save_product',
                'share_product', 'product_view', 'search', 'comparison_created'
            ]

            if event_type not in valid_events:
                return Response(
                    {'error': f'Invalid event_type. Must be one of: {valid_events}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get product if specified
            product = None
            if product_id:
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                except Product.DoesNotExist:
                    return Response(
                        {'error': 'Product not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Create engagement event
            engagement_event = EngagementEvent.objects.create(
                user=request.user,
                event_type=event_type,
                product=product,
                session_id=request.session.session_key or 'anonymous',
                event_data=event_data
            )

            # Handle specific event types
            response_data = {'success': True, 'event_id': str(engagement_event.id)}

            if event_type == 'product_like' and product:
                product.likes += 1
                product.save()
                response_data['new_likes_count'] = product.likes

            elif event_type == 'product_dislike' and product:
                product.dislikes += 1
                product.save()
                response_data['new_dislikes_count'] = product.dislikes

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error tracking engagement: {e}")
            return Response(
                {'error': 'Failed to track engagement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def user_dashboard(self, request):
        """
        Get user dashboard data including activity, recommendations, and saved items.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = request.user

            # Get user's recent activity
            recent_events = EngagementEvent.objects.filter(
                user=user
            ).order_by('-timestamp')[:20]

            activity_data = []
            for event in recent_events:
                activity_item = {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp.isoformat(),
                    'event_data': event.event_data
                }

                if event.product:
                    activity_item['product'] = {
                        'id': str(event.product.id),
                        'name': event.product.name,
                        'price': float(event.product.price),
                        'image_url': event.product.image_url
                    }

                activity_data.append(activity_item)

            # Get user's reviews
            user_reviews = Review.objects.filter(
                user=user
            ).select_related('product').order_by('-created_at')[:10]

            reviews_data = [
                {
                    'id': str(review.id),
                    'product_name': review.product.name,
                    'rating': review.rating,
                    'title': review.title,
                    'sentiment_label': review.sentiment_label,
                    'created_at': review.created_at.isoformat()
                }
                for review in user_reviews
            ]

            # Get personalized recommendations
            recommendations_result = discovery_service.get_personalized_recommendations(
                user_id=str(user.id),
                limit=8
            )

            # Get user statistics
            user_stats = {
                'total_reviews': Review.objects.filter(user=user).count(),
                'total_likes': EngagementEvent.objects.filter(
                    user=user, event_type='product_like'
                ).count(),
                'total_saves': EngagementEvent.objects.filter(
                    user=user, event_type='save_product'
                ).count(),
                'total_comparisons': EngagementEvent.objects.filter(
                    user=user, event_type='comparison_created'
                ).count()
            }

            return Response({
                'success': True,
                'user_data': {
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.isoformat()
                },
                'recent_activity': activity_data,
                'recent_reviews': reviews_data,
                'recommendations': recommendations_result.get('recommendations', []),
                'user_statistics': user_stats
            })

        except Exception as e:
            logger.error(f"Error getting user dashboard: {e}")
            return Response(
                {'error': 'Failed to get user dashboard'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_comparison_insights(self, products_data):
        """
        Generate insights for product comparison.
        """
        insights = []

        if len(products_data) < 2:
            return insights

        # Find best price
        prices = [(p['price'], p['name']) for p in products_data if p['price']]
        if prices:
            best_price = min(prices)
            insights.append(f"Best price: {best_price[1]} at ${best_price[0]}")

        # Find highest rated
        ratings = [(p['rating'], p['name']) for p in products_data if p['rating']]
        if ratings:
            highest_rated = max(ratings)
            insights.append(f"Highest rated: {highest_rated[1]} with {highest_rated[0]}/5 stars")

        # Find best AI score
        ai_scores = [(p.get('ai_rating_score', 0), p['name']) for p in products_data]
        if ai_scores:
            best_ai_score = max(ai_scores)
            insights.append(f"Best AI score: {best_ai_score[1]} with {best_ai_score[0]}/5")

        # Check for significant price differences
        if prices and len(prices) > 1:
            price_diff = max(prices)[0] - min(prices)[0]
            if price_diff > 10:  # $10 difference
                insights.append(f"Price difference: ${price_diff:.2f} between highest and lowest")

        return insights
