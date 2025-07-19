"""
store_integration/views.py
--------------------------
API views for store integration functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Min, Max
from django.utils import timezone
from datetime import timedelta
from .models import StoreIntegrationConfig, ProductMapping, PriceHistory, SyncLog
from .serializers import (
    StoreIntegrationConfigSerializer, StoreIntegrationConfigDetailSerializer,
    ProductMappingSerializer, PriceHistorySerializer, SyncLogSerializer,
    ProductComparisonSerializer, StorePerformanceSerializer
)
from .services import StoreIntegrationService
from .aggregation_services import ProductAggregationService
from core.models import Product, Shop
import logging

logger = logging.getLogger(__name__)


class StoreIntegrationConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing store integration configurations.
    """
    queryset = StoreIntegrationConfig.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return StoreIntegrationConfigDetailSerializer
        return StoreIntegrationConfigSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user's shops if not admin
        if not self.request.user.is_staff:
            user_shops = Shop.objects.filter(owner__user=self.request.user)
            queryset = queryset.filter(shop__in=user_shops)
        
        return queryset.select_related('shop')
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Trigger synchronization for a specific store integration.
        """
        config = self.get_object()
        
        try:
            integration = StoreIntegrationService.get_integration(config)
            result = integration.sync_products(full_sync=request.data.get('full_sync', False))
            
            return Response({
                'success': True,
                'message': 'Synchronization completed',
                'result': result
            })
        except Exception as e:
            logger.error(f"Sync failed for config {pk}: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """
        Get synchronization status for a store integration.
        """
        config = self.get_object()
        
        # Get latest sync log
        latest_sync = SyncLog.objects.filter(
            integration_config=config
        ).first()
        
        sync_data = None
        if latest_sync:
            sync_data = SyncLogSerializer(latest_sync).data
        
        return Response({
            'config': StoreIntegrationConfigSerializer(config).data,
            'latest_sync': sync_data,
            'product_mappings_count': config.product_mappings.count(),
            'active_mappings_count': config.product_mappings.filter(is_active=True).count()
        })


class ProductMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product mappings between local and external products.
    """
    queryset = ProductMapping.objects.all()
    serializer_class = ProductMappingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user's shops if not admin
        if not self.request.user.is_staff:
            user_shops = Shop.objects.filter(owner__user=self.request.user)
            queryset = queryset.filter(integration_config__shop__in=user_shops)
        
        # Filter by integration config if provided
        config_id = self.request.query_params.get('config')
        if config_id:
            queryset = queryset.filter(integration_config_id=config_id)
        
        # Filter by sync status if provided
        sync_status = self.request.query_params.get('sync_status')
        if sync_status:
            queryset = queryset.filter(sync_status=sync_status)
        
        return queryset.select_related('local_product', 'integration_config', 'integration_config__shop')


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing price history across stores.
    """
    queryset = PriceHistory.objects.all()
    serializer_class = PriceHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product if provided
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by shop if provided
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Filter by date range if provided
        days = self.request.query_params.get('days')
        if days:
            try:
                days_int = int(days)
                start_date = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(recorded_at__gte=start_date)
            except ValueError:
                pass
        
        return queryset.select_related('product', 'shop').order_by('-recorded_at')


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing synchronization logs.
    """
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user's shops if not admin
        if not self.request.user.is_staff:
            user_shops = Shop.objects.filter(owner__user=self.request.user)
            queryset = queryset.filter(integration_config__shop__in=user_shops)
        
        # Filter by integration config if provided
        config_id = self.request.query_params.get('config')
        if config_id:
            queryset = queryset.filter(integration_config_id=config_id)
        
        # Filter by status if provided
        sync_status = self.request.query_params.get('status')
        if sync_status:
            queryset = queryset.filter(status=sync_status)
        
        return queryset.select_related('integration_config', 'integration_config__shop')


class ProductComparisonViewSet(viewsets.ViewSet):
    """
    ViewSet for comparing products across multiple stores.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Get product comparisons across stores.
        """
        # Get products that exist in multiple stores
        products_with_multiple_stores = Product.objects.annotate(
            store_count=Count('shop', distinct=True)
        ).filter(store_count__gt=1)
        
        comparisons = []
        
        for product in products_with_multiple_stores[:20]:  # Limit for performance
            # Get price history for this product across all stores
            price_data = PriceHistory.objects.filter(
                product=product
            ).select_related('shop').order_by('shop', '-recorded_at').distinct('shop')
            
            stores_data = []
            prices = []
            
            for price_record in price_data:
                store_info = {
                    'shop_id': str(price_record.shop.id),
                    'shop_name': price_record.shop.name,
                    'price': float(price_record.price),
                    'original_price': float(price_record.original_price) if price_record.original_price else None,
                    'is_available': price_record.is_available,
                    'stock_quantity': price_record.stock_quantity,
                    'recorded_at': price_record.recorded_at,
                    'reliability_score': float(price_record.shop.reliability_score),
                    'delivery_days': price_record.shop.average_delivery_days
                }
                stores_data.append(store_info)
                prices.append(float(price_record.price))
            
            if prices:
                comparison = {
                    'product_id': str(product.id),
                    'product_name': product.name,
                    'stores': stores_data,
                    'best_price': min(prices),
                    'best_deal_shop': min(stores_data, key=lambda x: x['price'])['shop_name'],
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices),
                        'average': sum(prices) / len(prices)
                    },
                    'availability_count': sum(1 for store in stores_data if store['is_available'])
                }
                comparisons.append(comparison)
        
        serializer = ProductComparisonSerializer(comparisons, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Get detailed comparison for a specific product.
        """
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all stores that have this product
        price_data = PriceHistory.objects.filter(
            product=product
        ).select_related('shop').order_by('shop', '-recorded_at').distinct('shop')
        
        stores_data = []
        for price_record in price_data:
            store_info = {
                'shop_id': str(price_record.shop.id),
                'shop_name': price_record.shop.name,
                'price': float(price_record.price),
                'original_price': float(price_record.original_price) if price_record.original_price else None,
                'is_available': price_record.is_available,
                'stock_quantity': price_record.stock_quantity,
                'recorded_at': price_record.recorded_at,
                'reliability_score': float(price_record.shop.reliability_score),
                'delivery_days': price_record.shop.average_delivery_days,
                'customer_service_rating': float(price_record.shop.customer_service_rating),
                'return_policy_days': price_record.shop.return_policy_days
            }
            stores_data.append(store_info)
        
        if not stores_data:
            return Response({'error': 'No price data found for this product'}, status=status.HTTP_404_NOT_FOUND)
        
        prices = [store['price'] for store in stores_data]
        
        comparison = {
            'product_id': str(product.id),
            'product_name': product.name,
            'stores': stores_data,
            'best_price': min(prices),
            'best_deal_shop': min(stores_data, key=lambda x: x['price'])['shop_name'],
            'price_range': {
                'min': min(prices),
                'max': max(prices),
                'average': sum(prices) / len(prices)
            },
            'availability_count': sum(1 for store in stores_data if store['is_available'])
        }
        
        serializer = ProductComparisonSerializer(comparison)
        return Response(serializer.data)


class StorePerformanceViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing store performance analytics.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Get performance metrics for all stores.
        """
        shops = Shop.objects.annotate(
            total_products=Count('products'),
            active_products=Count('products', filter=Q(products__is_active=True))
        ).prefetch_related('integration_config')
        
        performance_data = []
        
        for shop in shops:
            # Calculate average price competitiveness
            # This is a simplified metric - you might want to make it more sophisticated
            avg_price = PriceHistory.objects.filter(shop=shop).aggregate(
                avg_price=Avg('price')
            )['avg_price'] or 0
            
            # Get latest sync status
            latest_sync = SyncLog.objects.filter(
                integration_config__shop=shop
            ).first()
            
            sync_status = 'never_synced'
            if latest_sync:
                sync_status = latest_sync.status
            
            performance = {
                'shop_id': str(shop.id),
                'shop_name': shop.name,
                'reliability_score': float(shop.reliability_score),
                'average_delivery_days': shop.average_delivery_days,
                'customer_service_rating': float(shop.customer_service_rating),
                'total_products': shop.total_products,
                'active_products': shop.active_products,
                'average_price_competitiveness': float(avg_price),
                'last_sync_status': sync_status,
                'sync_frequency': getattr(shop.integration_config, 'sync_frequency', 'manual') if hasattr(shop, 'integration_config') else 'manual'
            }
            performance_data.append(performance)
        
        serializer = StorePerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)


class ProductAggregationViewSet(viewsets.ViewSet):
    """
    ViewSet for product aggregation across multiple stores.
    """
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """
        Get aggregated data for a specific product including similar products from other stores.
        """
        aggregated_data = ProductAggregationService.get_aggregated_product_data(pk)

        if not aggregated_data:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(aggregated_data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Unified search across all stores with product aggregation.
        """
        query = request.query_params.get('q', '')

        filters = {
            'category_id': request.query_params.get('category'),
            'brand_id': request.query_params.get('brand'),
            'min_price': request.query_params.get('min_price'),
            'max_price': request.query_params.get('max_price'),
            'shop_type': request.query_params.get('shop_type')
        }

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        results = ProductAggregationService.get_unified_search_results(query, filters)

        return Response({
            'query': query,
            'filters': filters,
            'results': results,
            'total_groups': len(results)
        })

    @action(detail=False, methods=['get'])
    def category_aggregation(self, request):
        """
        Get aggregated data for products in a specific category.
        """
        category_id = request.query_params.get('category_id')

        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        aggregated_data = ProductAggregationService.get_category_aggregation(category_id)

        if not aggregated_data:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(aggregated_data)

    @action(detail=True, methods=['get'])
    def similar_products(self, request, pk=None):
        """
        Find similar products across different stores for a given product.
        """
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        similarity_threshold = float(request.query_params.get('threshold', 0.8))
        similar_products = ProductAggregationService.find_similar_products(
            product, similarity_threshold
        )

        return Response({
            'product': {
                'id': str(product.id),
                'name': product.name,
                'price': float(product.price),
                'shop': product.shop.name
            },
            'similar_products': similar_products,
            'threshold_used': similarity_threshold,
            'total_found': len(similar_products)
        })
