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


class StoreIntegrationManagementViewSet(viewsets.ViewSet):
    """
    ViewSet for comprehensive store integration management.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def supported_platforms(self, request):
        """
        Get list of supported e-commerce platforms.
        """
        try:
            platforms = StoreIntegrationService.get_supported_platforms()
            return Response({
                'platforms': platforms,
                'total_supported': len(platforms)
            })
        except Exception as e:
            logger.error(f"Error getting supported platforms: {e}")
            return Response(
                {'error': 'Failed to get supported platforms'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def validate_config(self, request):
        """
        Validate store integration configuration.
        """
        try:
            platform = request.data.get('platform')
            config_data = request.data.get('config', {})

            if not platform:
                return Response(
                    {'error': 'Platform is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validation_result = StoreIntegrationService.validate_config(platform, config_data)

            return Response(validation_result)

        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return Response(
                {'error': 'Configuration validation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """
        Test connection to a store without saving configuration.
        """
        try:
            platform = request.data.get('platform')
            config_data = request.data.get('config', {})
            shop_id = request.data.get('shop_id')

            if not all([platform, config_data, shop_id]):
                return Response(
                    {'error': 'Platform, config, and shop_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate user has access to the shop
            try:
                shop = Shop.objects.get(id=shop_id)
                if not request.user.is_staff and shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this shop'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Shop.DoesNotExist:
                return Response(
                    {'error': 'Shop not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create temporary config for testing
            temp_config = StoreIntegrationConfig(
                shop=shop,
                platform=platform,
                api_key=config_data.get('api_key', ''),
                api_secret=config_data.get('api_secret', ''),
                access_token=config_data.get('access_token', ''),
                store_url=config_data.get('store_url', ''),
                is_active=False  # Don't activate during test
            )

            # Test the integration
            test_result = StoreIntegrationService.test_integration(temp_config)

            return Response(test_result)

        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return Response(
                {'error': 'Connection test failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def setup_webhooks(self, request):
        """
        Setup webhooks for a store integration.
        """
        try:
            config_id = request.data.get('config_id')
            webhook_events = request.data.get('events', [])

            if not config_id:
                return Response(
                    {'error': 'config_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                config = StoreIntegrationConfig.objects.get(id=config_id)

                # Check user permissions
                if not request.user.is_staff and config.shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this integration'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            except StoreIntegrationConfig.DoesNotExist:
                return Response(
                    {'error': 'Integration config not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Setup webhooks based on platform
            integration = StoreIntegrationService.get_integration(config)
            webhook_result = integration.setup_webhooks(webhook_events)

            # Update config with webhook URL
            if webhook_result.get('success'):
                config.webhook_url = webhook_result.get('webhook_url', '')
                config.save()

            return Response(webhook_result)

        except Exception as e:
            logger.error(f"Error setting up webhooks: {e}")
            return Response(
                {'error': 'Webhook setup failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookReceiverViewSet(viewsets.ViewSet):
    """
    ViewSet for receiving webhooks from integrated stores.
    """
    permission_classes = []  # Webhooks don't use standard auth

    @action(detail=False, methods=['post'])
    def shopify(self, request):
        """
        Receive Shopify webhooks.
        """
        try:
            # Verify Shopify webhook signature
            if not self._verify_shopify_webhook(request):
                return Response(
                    {'error': 'Invalid webhook signature'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get shop domain from headers
            shop_domain = request.META.get('HTTP_X_SHOPIFY_SHOP_DOMAIN')
            if not shop_domain:
                return Response(
                    {'error': 'Missing shop domain'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find integration config
            try:
                config = StoreIntegrationConfig.objects.get(
                    platform='shopify',
                    store_url__icontains=shop_domain,
                    is_active=True
                )
            except StoreIntegrationConfig.DoesNotExist:
                return Response(
                    {'error': 'Integration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Process webhook
            webhook_data = {
                'topic': request.META.get('HTTP_X_SHOPIFY_TOPIC'),
                **request.data
            }

            from .services import WebhookHandler
            result = WebhookHandler.handle_shopify_webhook(webhook_data, config)

            return Response(result)

        except Exception as e:
            logger.error(f"Error processing Shopify webhook: {e}")
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def woocommerce(self, request):
        """
        Receive WooCommerce webhooks.
        """
        try:
            # Verify WooCommerce webhook signature
            if not self._verify_woocommerce_webhook(request):
                return Response(
                    {'error': 'Invalid webhook signature'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get source URL from webhook data or headers
            source_url = request.data.get('source_url') or request.META.get('HTTP_REFERER', '')

            if not source_url:
                return Response(
                    {'error': 'Missing source URL'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find integration config
            try:
                config = StoreIntegrationConfig.objects.get(
                    platform='woocommerce',
                    store_url__icontains=source_url.split('/')[2],  # Extract domain
                    is_active=True
                )
            except StoreIntegrationConfig.DoesNotExist:
                return Response(
                    {'error': 'Integration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Process webhook
            from .services import WebhookHandler
            result = WebhookHandler.handle_woocommerce_webhook(request.data, config)

            return Response(result)

        except Exception as e:
            logger.error(f"Error processing WooCommerce webhook: {e}")
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _verify_shopify_webhook(self, request) -> bool:
        """
        Verify Shopify webhook signature.
        """
        try:
            import hmac
            import hashlib
            import base64

            signature = request.META.get('HTTP_X_SHOPIFY_HMAC_SHA256')
            if not signature:
                return False

            # Get webhook secret from config (you'd need to store this)
            webhook_secret = settings.SHOPIFY_WEBHOOK_SECRET.encode('utf-8')

            # Calculate expected signature
            body = request.body
            expected_signature = base64.b64encode(
                hmac.new(webhook_secret, body, hashlib.sha256).digest()
            ).decode()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying Shopify webhook: {e}")
            return False

    def _verify_woocommerce_webhook(self, request) -> bool:
        """
        Verify WooCommerce webhook signature.
        """
        try:
            import hmac
            import hashlib

            signature = request.META.get('HTTP_X_WC_WEBHOOK_SIGNATURE')
            if not signature:
                return False

            # Get webhook secret from config
            webhook_secret = settings.WOOCOMMERCE_WEBHOOK_SECRET.encode('utf-8')

            # Calculate expected signature
            body = request.body
            expected_signature = base64.b64encode(
                hmac.new(webhook_secret, body, hashlib.sha256).digest()
            ).decode()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying WooCommerce webhook: {e}")
            return False


class RealTimeSyncViewSet(viewsets.ViewSet):
    """
    ViewSet for real-time synchronization management and monitoring.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def trigger_product_sync(self, request):
        """
        Trigger real-time synchronization for a specific product.
        """
        try:
            product_id = request.data.get('product_id')
            source_config_id = request.data.get('source_config_id')

            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user has access to the product
            try:
                product = Product.objects.get(id=product_id)
                if not request.user.is_staff and product.shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this product'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            from .realtime_sync import realtime_sync_service
            result = realtime_sync_service.trigger_product_sync(product_id, source_config_id)

            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error triggering product sync: {e}")
            return Response(
                {'error': 'Failed to trigger product sync'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def trigger_store_sync(self, request):
        """
        Trigger real-time synchronization for all products in a store.
        """
        try:
            config_id = request.data.get('config_id')
            product_ids = request.data.get('product_ids', [])

            if not config_id:
                return Response(
                    {'error': 'config_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user has access to the integration config
            try:
                config = StoreIntegrationConfig.objects.get(id=config_id)
                if not request.user.is_staff and config.shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this integration'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except StoreIntegrationConfig.DoesNotExist:
                return Response(
                    {'error': 'Integration config not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            from .realtime_sync import realtime_sync_service
            result = realtime_sync_service.trigger_store_sync(config_id, product_ids)

            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error triggering store sync: {e}")
            return Response(
                {'error': 'Failed to trigger store sync'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def price_trends(self, request):
        """
        Get price trends for a product across all stores.
        """
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 30))

            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            from .realtime_sync import realtime_sync_service
            result = realtime_sync_service.get_price_trends(product_id, days)

            return Response(result)

        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting price trends: {e}")
            return Response(
                {'error': 'Failed to get price trends'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def price_anomalies(self, request):
        """
        Detect price anomalies for a product.
        """
        try:
            product_id = request.query_params.get('product_id')
            threshold = float(request.query_params.get('threshold', 0.2))

            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            from .realtime_sync import realtime_sync_service
            result = realtime_sync_service.detect_price_anomalies(product_id, threshold)

            return Response(result)

        except ValueError:
            return Response(
                {'error': 'Invalid threshold parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error detecting price anomalies: {e}")
            return Response(
                {'error': 'Failed to detect price anomalies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """
        Get current synchronization status for stores.
        """
        try:
            config_id = request.query_params.get('config_id')

            from .realtime_sync import realtime_sync_service
            result = realtime_sync_service.get_sync_status(config_id)

            return Response(result)

        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return Response(
                {'error': 'Failed to get sync status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def price_comparison(self, request):
        """
        Get real-time price comparison for a product across all stores.
        """
        try:
            product_id = request.query_params.get('product_id')

            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get latest prices from all stores
            latest_prices = PriceHistory.objects.filter(
                product_id=product_id
            ).select_related('shop').order_by('shop', '-recorded_at').distinct('shop')

            if not latest_prices.exists():
                return Response({
                    'product_id': product_id,
                    'message': 'No price data found',
                    'stores': []
                })

            stores_data = []
            for price_record in latest_prices:
                stores_data.append({
                    'shop_id': str(price_record.shop.id),
                    'shop_name': price_record.shop.name,
                    'price': float(price_record.price),
                    'original_price': float(price_record.original_price) if price_record.original_price else None,
                    'currency': price_record.currency,
                    'is_available': price_record.is_available,
                    'stock_quantity': price_record.stock_quantity,
                    'last_updated': price_record.recorded_at.isoformat(),
                    'discount_percentage': (
                        ((price_record.original_price - price_record.price) / price_record.original_price) * 100
                        if price_record.original_price and price_record.original_price > price_record.price
                        else 0
                    )
                })

            # Sort by price (lowest first)
            stores_data.sort(key=lambda x: x['price'] if x['is_available'] else float('inf'))

            # Find best deal
            available_stores = [store for store in stores_data if store['is_available']]
            best_deal = available_stores[0] if available_stores else None

            return Response({
                'product_id': product_id,
                'total_stores': len(stores_data),
                'available_stores': len(available_stores),
                'best_deal': best_deal,
                'stores': stores_data,
                'price_range': {
                    'min': min(store['price'] for store in available_stores) if available_stores else 0,
                    'max': max(store['price'] for store in available_stores) if available_stores else 0
                }
            })

        except Exception as e:
            logger.error(f"Error getting price comparison: {e}")
            return Response(
                {'error': 'Failed to get price comparison'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


class StoreAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for comprehensive store performance analytics.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """
        Get comprehensive performance metrics for a store.
        """
        try:
            shop_id = request.query_params.get('shop_id')
            days = int(request.query_params.get('days', 30))

            if not shop_id:
                return Response(
                    {'error': 'shop_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user has access to the shop
            try:
                shop = Shop.objects.get(id=shop_id)
                if not request.user.is_staff and shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this shop'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Shop.DoesNotExist:
                return Response(
                    {'error': 'Shop not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            from .analytics_service import store_analytics_service
            result = store_analytics_service.calculate_store_performance(shop_id, days)

            return Response(result)

        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return Response(
                {'error': 'Failed to get performance metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def comparative_analytics(self, request):
        """
        Get comparative analytics for multiple stores.
        """
        try:
            shop_ids = request.query_params.getlist('shop_ids')
            days = int(request.query_params.get('days', 30))

            if not shop_ids:
                return Response(
                    {'error': 'shop_ids are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user has access to all shops (for non-staff users)
            if not request.user.is_staff:
                accessible_shops = Shop.objects.filter(
                    id__in=shop_ids,
                    owner__user=request.user
                ).values_list('id', flat=True)

                if len(accessible_shops) != len(shop_ids):
                    return Response(
                        {'error': 'Access denied to one or more shops'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            from .analytics_service import store_analytics_service
            result = store_analytics_service.get_comparative_analytics(shop_ids, days)

            return Response(result)

        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting comparative analytics: {e}")
            return Response(
                {'error': 'Failed to get comparative analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def reliability_dashboard(self, request):
        """
        Get reliability dashboard data for a store.
        """
        try:
            shop_id = request.query_params.get('shop_id')

            if not shop_id:
                return Response(
                    {'error': 'shop_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check access permissions
            try:
                shop = Shop.objects.get(id=shop_id)
                if not request.user.is_staff and shop.owner.user != request.user:
                    return Response(
                        {'error': 'Access denied to this shop'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Shop.DoesNotExist:
                return Response(
                    {'error': 'Shop not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get integration config
            config = StoreIntegrationConfig.objects.filter(
                shop_id=shop_id,
                is_active=True
            ).first()

            if not config:
                return Response({
                    'shop_id': shop_id,
                    'shop_name': shop.name,
                    'message': 'No active integration found',
                    'reliability_data': {}
                })

            # Get recent sync logs
            recent_logs = SyncLog.objects.filter(
                integration_config=config
            ).order_by('-started_at')[:20]

            # Calculate reliability metrics
            total_syncs = recent_logs.count()
            successful_syncs = recent_logs.filter(status='completed').count()
            failed_syncs = recent_logs.filter(status='failed').count()

            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0

            # Get sync history for chart
            sync_history = []
            for log in recent_logs:
                sync_history.append({
                    'date': log.started_at.isoformat(),
                    'status': log.status,
                    'duration': (
                        (log.completed_at - log.started_at).total_seconds()
                        if log.completed_at and log.started_at else 0
                    ),
                    'products_processed': log.products_processed,
                    'errors_count': log.errors_count
                })

            reliability_data = {
                'success_rate': round(success_rate, 2),
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'last_sync': config.last_sync_at.isoformat() if config.last_sync_at else None,
                'sync_frequency': config.sync_frequency,
                'current_errors': config.sync_errors or None,
                'sync_history': sync_history
            }

            return Response({
                'shop_id': shop_id,
                'shop_name': shop.name,
                'platform': config.platform,
                'reliability_data': reliability_data
            })

        except Exception as e:
            logger.error(f"Error getting reliability dashboard: {e}")
            return Response(
                {'error': 'Failed to get reliability dashboard'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
