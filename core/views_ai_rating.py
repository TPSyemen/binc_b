"""
core/views_ai_rating.py
-----------------------
API views for the AI-driven product rating system.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import Product, Shop, Brand
from .ai_rating_system import ai_rating_system
from .serializers import ProductSerializer
import logging

logger = logging.getLogger(__name__)


class AIRatingViewSet(viewsets.ViewSet):
    """
    ViewSet for AI-driven product rating functionality.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def product_rating(self, request):
        """
        Get AI rating for a specific product.
        """
        product_id = request.query_params.get('product_id')
        recalculate = request.query_params.get('recalculate', 'false').lower() == 'true'
        
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            rating_data = ai_rating_system.calculate_ai_rating(product, recalculate=recalculate)
            
            # Add product basic info
            rating_data['product'] = {
                'id': str(product.id),
                'name': product.name,
                'current_rating': float(product.rating),
                'shop_name': product.shop.name,
                'brand_name': product.brand.name if product.brand else None,
                'category_name': product.category.name,
                'price': float(product.price)
            }
            
            return Response(rating_data)
            
        except Exception as e:
            logger.error(f"Error getting AI rating for product {product_id}: {e}")
            return Response(
                {'error': 'Failed to calculate AI rating'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_calculate(self, request):
        """
        Calculate AI ratings for multiple products in bulk.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        product_ids = request.data.get('product_ids', [])
        category_id = request.data.get('category_id')
        shop_id = request.data.get('shop_id')
        limit = min(int(request.data.get('limit', 100)), 1000)  # Max 1000 products
        
        # Build queryset
        queryset = Product.objects.filter(is_active=True)
        
        if product_ids:
            queryset = queryset.filter(id__in=product_ids)
        elif category_id:
            queryset = queryset.filter(category_id=category_id)
        elif shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        products = queryset[:limit]
        
        try:
            results = ai_rating_system.bulk_calculate_ratings(products)
            return Response({
                'message': f'Bulk rating calculation completed',
                'results': results,
                'total_products': len(products)
            })
            
        except Exception as e:
            logger.error(f"Error in bulk rating calculation: {e}")
            return Response(
                {'error': 'Bulk calculation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def top_rated_products(self, request):
        """
        Get top-rated products based on AI ratings.
        """
        category_id = request.query_params.get('category_id')
        shop_id = request.query_params.get('shop_id')
        limit = min(int(request.query_params.get('limit', 20)), 100)
        
        # Build queryset
        queryset = Product.objects.filter(is_active=True).select_related(
            'shop', 'brand', 'category'
        )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Order by AI rating (stored in rating field)
        top_products = queryset.order_by('-rating', '-views')[:limit]
        
        results = []
        for product in top_products:
            try:
                # Get detailed AI rating breakdown
                rating_data = ai_rating_system.calculate_ai_rating(product, recalculate=False)
                
                product_data = {
                    'id': str(product.id),
                    'name': product.name,
                    'price': float(product.price),
                    'ai_rating': rating_data.get('overall_rating', float(product.rating)),
                    'shop_name': product.shop.name,
                    'brand_name': product.brand.name if product.brand else None,
                    'category_name': product.category.name,
                    'image_url': product.image_url,
                    'views': product.views,
                    'likes': product.likes,
                    'rating_components': rating_data.get('components', {}),
                    'confidence_level': rating_data.get('confidence_level', 0.5)
                }
                results.append(product_data)
                
            except Exception as e:
                logger.error(f"Error getting rating data for product {product.id}: {e}")
                # Fallback to basic data
                results.append({
                    'id': str(product.id),
                    'name': product.name,
                    'price': float(product.price),
                    'ai_rating': float(product.rating),
                    'shop_name': product.shop.name,
                    'brand_name': product.brand.name if product.brand else None,
                    'category_name': product.category.name,
                    'image_url': product.image_url,
                    'error': 'Failed to get detailed rating data'
                })
        
        return Response({
            'top_products': results,
            'total_found': len(results),
            'filters_applied': {
                'category_id': category_id,
                'shop_id': shop_id,
                'limit': limit
            }
        })
    
    @action(detail=False, methods=['get'])
    def rating_analytics(self, request):
        """
        Get analytics about AI ratings across the platform.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Overall statistics
            total_products = Product.objects.filter(is_active=True).count()
            
            # Rating distribution
            rating_ranges = [
                (0, 1), (1, 2), (2, 3), (3, 4), (4, 5)
            ]
            
            rating_distribution = {}
            for min_rating, max_rating in rating_ranges:
                count = Product.objects.filter(
                    is_active=True,
                    rating__gte=min_rating,
                    rating__lt=max_rating
                ).count()
                rating_distribution[f'{min_rating}-{max_rating}'] = count
            
            # Top categories by average rating
            from django.db.models import Avg
            top_categories = Product.objects.filter(
                is_active=True
            ).values(
                'category__name'
            ).annotate(
                avg_rating=Avg('rating'),
                product_count=Count('id')
            ).order_by('-avg_rating')[:10]
            
            # Top shops by average rating
            top_shops = Product.objects.filter(
                is_active=True
            ).values(
                'shop__name'
            ).annotate(
                avg_rating=Avg('rating'),
                product_count=Count('id')
            ).order_by('-avg_rating')[:10]
            
            # Recent rating trends (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_products = Product.objects.filter(
                is_active=True,
                created_at__gte=thirty_days_ago
            )
            
            if recent_products.exists():
                recent_avg_rating = recent_products.aggregate(
                    avg_rating=Avg('rating')
                )['avg_rating']
            else:
                recent_avg_rating = None
            
            # Overall platform average
            platform_avg_rating = Product.objects.filter(
                is_active=True
            ).aggregate(avg_rating=Avg('rating'))['avg_rating']
            
            analytics = {
                'total_products': total_products,
                'platform_average_rating': round(float(platform_avg_rating), 2) if platform_avg_rating else 0,
                'rating_distribution': rating_distribution,
                'top_categories': list(top_categories),
                'top_shops': list(top_shops),
                'recent_trends': {
                    'last_30_days_avg': round(float(recent_avg_rating), 2) if recent_avg_rating else None,
                    'new_products_count': recent_products.count()
                },
                'rating_system_info': {
                    'components': list(ai_rating_system.weights.keys()),
                    'weights': ai_rating_system.weights,
                    'last_updated': timezone.now()
                }
            }
            
            return Response(analytics)
            
        except Exception as e:
            logger.error(f"Error getting rating analytics: {e}")
            return Response(
                {'error': 'Failed to get rating analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def rating_explanation(self, request):
        """
        Get explanation of how AI ratings are calculated.
        """
        explanation = {
            'overview': 'AI ratings combine multiple data sources to provide comprehensive product scores',
            'components': {
                'customer_reviews': {
                    'weight': ai_rating_system.weights['customer_reviews'],
                    'description': 'Customer review ratings, sentiment analysis, verified purchases, and review helpfulness',
                    'factors': [
                        'Average review rating',
                        'Sentiment analysis of review text',
                        'Percentage of verified purchases',
                        'Review helpfulness scores'
                    ]
                },
                'engagement_metrics': {
                    'weight': ai_rating_system.weights['engagement_metrics'],
                    'description': 'User engagement including views, likes, shares, and conversion rates',
                    'factors': [
                        'Total product views',
                        'Like to dislike ratio',
                        'Conversion rate (views to purchases)',
                        'Social sharing activity'
                    ]
                },
                'store_reliability': {
                    'weight': ai_rating_system.weights['store_reliability'],
                    'description': 'Store performance, reliability, and customer service quality',
                    'factors': [
                        'Store reliability score',
                        'Customer service rating',
                        'Delivery performance',
                        'Return policy terms',
                        'Store review ratings'
                    ]
                },
                'brand_reputation': {
                    'weight': ai_rating_system.weights['brand_reputation'],
                    'description': 'Brand reputation, popularity, and overall brand product performance',
                    'factors': [
                        'Brand rating and popularity',
                        'Average rating of brand products',
                        'Brand review sentiment'
                    ]
                },
                'price_competitiveness': {
                    'weight': ai_rating_system.weights['price_competitiveness'],
                    'description': 'Price competitiveness compared to similar products',
                    'factors': [
                        'Price percentile in category',
                        'Discount availability',
                        'Value for money perception'
                    ]
                },
                'availability_score': {
                    'weight': ai_rating_system.weights['availability_score'],
                    'description': 'Product availability and stock consistency',
                    'factors': [
                        'Current availability status',
                        'Historical availability trends',
                        'Stock level indicators'
                    ]
                },
                'historical_performance': {
                    'weight': ai_rating_system.weights['historical_performance'],
                    'description': 'Historical sales trends and performance indicators',
                    'factors': [
                        'View trends over time',
                        'Purchase trends',
                        'Product age factor'
                    ]
                }
            },
            'rating_scale': {
                'range': '0.0 to 5.0',
                'interpretation': {
                    '4.5-5.0': 'Excellent',
                    '4.0-4.4': 'Very Good',
                    '3.5-3.9': 'Good',
                    '3.0-3.4': 'Average',
                    '2.5-2.9': 'Below Average',
                    '2.0-2.4': 'Poor',
                    '0.0-1.9': 'Very Poor'
                }
            },
            'confidence_levels': {
                'high': 'Based on substantial data from multiple sources',
                'medium': 'Based on moderate amount of data',
                'low': 'Based on limited data, rating may be less reliable'
            },
            'update_frequency': 'Ratings are recalculated when new data becomes available or manually triggered'
        }
        
        return Response(explanation)
