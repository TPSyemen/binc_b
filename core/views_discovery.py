"""
core/views_discovery.py
-----------------------
API views for smart product discovery and search functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.cache import cache
from django.utils import timezone
from .discovery_service import discovery_service
from .models import Product
from reviews.models import EngagementEvent
import logging

logger = logging.getLogger(__name__)


class ProductDiscoveryViewSet(viewsets.ViewSet):
    """
    ViewSet for smart product discovery and search functionality.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Intelligent product search across all stores.
        """
        try:
            query = request.query_params.get('q', '').strip()
            sort_by = request.query_params.get('sort_by', 'relevance')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Build filters from query parameters
            filters = {}
            
            if request.query_params.get('category_id'):
                filters['category_id'] = request.query_params.get('category_id')
            
            if request.query_params.get('brand_id'):
                filters['brand_id'] = request.query_params.get('brand_id')
            
            if request.query_params.get('shop_id'):
                filters['shop_id'] = request.query_params.get('shop_id')
            
            if request.query_params.get('min_price'):
                try:
                    filters['min_price'] = float(request.query_params.get('min_price'))
                except ValueError:
                    pass
            
            if request.query_params.get('max_price'):
                try:
                    filters['max_price'] = float(request.query_params.get('max_price'))
                except ValueError:
                    pass
            
            if request.query_params.get('min_rating'):
                try:
                    filters['min_rating'] = float(request.query_params.get('min_rating'))
                except ValueError:
                    pass
            
            if request.query_params.get('availability') == 'true':
                filters['availability'] = True
            
            if request.query_params.get('has_discount') == 'true':
                filters['has_discount'] = True
            
            # Perform search
            result = discovery_service.search_products(
                query=query,
                filters=filters,
                sort_by=sort_by,
                page=page,
                page_size=page_size
            )
            
            # Track search event if user is authenticated
            if request.user.is_authenticated and query:
                try:
                    EngagementEvent.objects.create(
                        user=request.user,
                        event_type='search',
                        session_id=request.session.session_key or 'anonymous',
                        event_data={
                            'query': query,
                            'filters': filters,
                            'sort_by': sort_by,
                            'results_count': result.get('pagination', {}).get('total_results', 0)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to track search event: {e}")
            
            return Response(result)
            
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
    def similar_products(self, request):
        """
        Find products similar to a given product.
        """
        try:
            product_id = request.query_params.get('product_id')
            limit = int(request.query_params.get('limit', 10))
            
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check cache first
            cache_key = f"similar_products_{product_id}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            result = discovery_service.discover_similar_products(product_id, limit)
            
            # Cache result for 1 hour
            if result['success']:
                cache.set(cache_key, result, 3600)
            
            # Track engagement event
            if request.user.is_authenticated:
                try:
                    EngagementEvent.objects.create(
                        user=request.user,
                        event_type='comparison_created',
                        product_id=product_id,
                        session_id=request.session.session_key or 'anonymous',
                        event_data={
                            'similar_products_found': len(result.get('similar_products', []))
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to track similar products event: {e}")
            
            return Response(result)
            
        except ValueError:
            return Response(
                {'error': 'Invalid limit parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return Response(
                {'error': 'Failed to find similar products'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending products based on engagement metrics.
        """
        try:
            category_id = request.query_params.get('category_id')
            time_period = request.query_params.get('time_period', 'week')
            limit = int(request.query_params.get('limit', 20))
            
            if time_period not in ['day', 'week', 'month']:
                return Response(
                    {'error': 'time_period must be day, week, or month'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check cache first
            cache_key = f"trending_products_{category_id or 'all'}_{time_period}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            result = discovery_service.get_trending_products(
                category_id=category_id,
                time_period=time_period,
                limit=limit
            )
            
            # Cache result for 30 minutes
            if result['success']:
                cache.set(cache_key, result, 1800)
            
            return Response(result)
            
        except ValueError:
            return Response(
                {'error': 'Invalid limit parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return Response(
                {'error': 'Failed to get trending products'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Get personalized product recommendations for the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required for personalized recommendations'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            limit = int(request.query_params.get('limit', 20))
            
            # Check cache first
            cache_key = f"user_recommendations_{request.user.id}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            result = discovery_service.get_personalized_recommendations(
                user_id=str(request.user.id),
                limit=limit
            )
            
            # Cache result for 1 hour
            if result['success']:
                cache.set(cache_key, result, 3600)
            
            # Track engagement event
            try:
                EngagementEvent.objects.create(
                    user=request.user,
                    event_type='recommendation_clicked',
                    session_id=request.session.session_key or 'anonymous',
                    event_data={
                        'recommendations_count': len(result.get('recommendations', []))
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to track recommendations event: {e}")
            
            return Response(result)
            
        except ValueError:
            return Response(
                {'error': 'Invalid limit parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return Response(
                {'error': 'Failed to get recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """
        Get search autocomplete suggestions.
        """
        try:
            query = request.query_params.get('q', '').strip()
            limit = int(request.query_params.get('limit', 10))
            
            if len(query) < 2:
                return Response({
                    'suggestions': [],
                    'message': 'Query too short'
                })
            
            # Check cache first
            cache_key = f"autocomplete_{query.lower()}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            # Get product name suggestions
            product_suggestions = Product.objects.filter(
                name__icontains=query,
                is_active=True
            ).values_list('name', flat=True).distinct()[:limit//2]
            
            # Get brand suggestions
            brand_suggestions = Product.objects.filter(
                brand__name__icontains=query,
                is_active=True
            ).values_list('brand__name', flat=True).distinct()[:limit//4]
            
            # Get category suggestions
            category_suggestions = Product.objects.filter(
                category__name__icontains=query,
                is_active=True
            ).values_list('category__name', flat=True).distinct()[:limit//4]
            
            # Combine and format suggestions
            suggestions = []
            
            for name in product_suggestions:
                suggestions.append({
                    'text': name,
                    'type': 'product',
                    'category': 'Products'
                })
            
            for brand in brand_suggestions:
                suggestions.append({
                    'text': brand,
                    'type': 'brand',
                    'category': 'Brands'
                })
            
            for category in category_suggestions:
                suggestions.append({
                    'text': category,
                    'type': 'category',
                    'category': 'Categories'
                })
            
            result = {
                'query': query,
                'suggestions': suggestions[:limit]
            }
            
            # Cache result for 1 hour
            cache.set(cache_key, result, 3600)
            
            return Response(result)
            
        except ValueError:
            return Response(
                {'error': 'Invalid limit parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {e}")
            return Response(
                {'error': 'Failed to get suggestions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def track_interaction(self, request):
        """
        Track user interaction with discovery results.
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
            
            # Create engagement event
            EngagementEvent.objects.create(
                user=request.user,
                event_type=event_type,
                product_id=product_id,
                session_id=request.session.session_key or 'anonymous',
                event_data=event_data
            )
            
            return Response({
                'success': True,
                'message': 'Interaction tracked successfully'
            })
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
            return Response(
                {'error': 'Failed to track interaction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
