"""
store_integration/serializers.py
--------------------------------
Serializers for store integration API endpoints.
"""

from rest_framework import serializers
from .models import StoreIntegrationConfig, ProductMapping, PriceHistory, SyncLog
from core.serializers import ShopSerializer, ProductSerializer


class StoreIntegrationConfigSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    sync_frequency_display = serializers.CharField(source='get_sync_frequency_display', read_only=True)
    
    class Meta:
        model = StoreIntegrationConfig
        fields = [
            'id', 'shop', 'shop_name', 'platform', 'platform_display',
            'sync_frequency', 'sync_frequency_display', 'is_active',
            'last_sync_at', 'sync_errors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'created_at', 'updated_at']


class StoreIntegrationConfigDetailSerializer(StoreIntegrationConfigSerializer):
    shop = ShopSerializer(read_only=True)
    
    class Meta(StoreIntegrationConfigSerializer.Meta):
        fields = StoreIntegrationConfigSerializer.Meta.fields + [
            'api_key', 'store_url', 'webhook_url', 'configuration'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'access_token': {'write_only': True},
        }


class ProductMappingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='local_product.name', read_only=True)
    shop_name = serializers.CharField(source='integration_config.shop.name', read_only=True)
    platform = serializers.CharField(source='integration_config.platform', read_only=True)
    
    class Meta:
        model = ProductMapping
        fields = [
            'id', 'local_product', 'product_name', 'integration_config',
            'shop_name', 'platform', 'external_product_id', 'external_sku',
            'external_url', 'is_active', 'sync_status', 'last_sync_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'created_at', 'updated_at']


class PriceHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PriceHistory
        fields = [
            'id', 'product', 'product_name', 'shop', 'shop_name',
            'price', 'original_price', 'discount_percentage', 'currency',
            'is_available', 'stock_quantity', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']
    
    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return round(((obj.original_price - obj.price) / obj.original_price) * 100, 2)
        return 0


class SyncLogSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='integration_config.shop.name', read_only=True)
    platform = serializers.CharField(source='integration_config.platform', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncLog
        fields = [
            'id', 'integration_config', 'shop_name', 'platform',
            'sync_type', 'sync_type_display', 'status', 'status_display',
            'started_at', 'completed_at', 'duration', 'products_processed',
            'products_created', 'products_updated', 'errors_count',
            'error_details', 'summary'
        ]
        read_only_fields = ['id']
    
    def get_duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        return None


class ProductComparisonSerializer(serializers.Serializer):
    """
    Serializer for product comparison across multiple stores.
    """
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    stores = serializers.ListField(
        child=serializers.DictField(), 
        read_only=True
    )
    best_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    best_deal_shop = serializers.CharField(read_only=True)
    price_range = serializers.DictField(read_only=True)
    availability_count = serializers.IntegerField(read_only=True)


class StorePerformanceSerializer(serializers.Serializer):
    """
    Serializer for store performance metrics.
    """
    shop_id = serializers.UUIDField()
    shop_name = serializers.CharField()
    reliability_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    average_delivery_days = serializers.IntegerField()
    customer_service_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    average_price_competitiveness = serializers.DecimalField(max_digits=5, decimal_places=2)
    last_sync_status = serializers.CharField()
    sync_frequency = serializers.CharField()
