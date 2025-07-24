"""
store_integration/admin.py
--------------------------
Admin interface for store integration models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import StoreIntegrationConfig, ProductMapping, PriceHistory, SyncLog
from .services import StoreIntegrationService
import json


@admin.register(StoreIntegrationConfig)
class StoreIntegrationConfigAdmin(admin.ModelAdmin):
    list_display = [
        'shop', 'platform', 'is_active', 'sync_frequency', 
        'last_sync_at', 'integration_status'
    ]
    list_filter = ['platform', 'is_active', 'sync_frequency', 'created_at']
    search_fields = ['shop__name', 'store_url']
    readonly_fields = ['created_at', 'updated_at', 'last_sync_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shop', 'platform', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'access_token', 'store_url', 'webhook_url'),
            'classes': ('collapse',)
        }),
        ('Sync Settings', {
            'fields': ('sync_frequency', 'configuration')
        }),
        ('Status', {
            'fields': ('last_sync_at', 'sync_errors', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['test_connection', 'trigger_sync', 'activate_configs', 'deactivate_configs']

    def integration_status(self, obj):
        if obj.sync_errors:
            return format_html(
                '<span style="color: red;">Error</span>'
            )
        elif obj.last_sync_at:
            return format_html(
                '<span style="color: green;">Synced</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">Pending</span>'
            )
    integration_status.short_description = 'Status'

    def test_connection(self, request, queryset):
        """Test connection for selected integrations."""
        results = []
        for config in queryset:
            try:
                result = StoreIntegrationService.test_integration(config)
                if result['success']:
                    results.append(f"✓ {config.shop.name}: Connection successful")
                else:
                    results.append(f"✗ {config.shop.name}: {result['error']}")
            except Exception as e:
                results.append(f"✗ {config.shop.name}: {str(e)}")

        self.message_user(request, "\n".join(results))
    test_connection.short_description = "Test connection for selected integrations"

    def trigger_sync(self, request, queryset):
        """Trigger synchronization for selected integrations."""
        results = []
        for config in queryset:
            if config.is_active:
                try:
                    integration = StoreIntegrationService.get_integration(config)
                    result = integration.sync_products()
                    if result['success']:
                        results.append(f"✓ {config.shop.name}: Sync completed")
                    else:
                        results.append(f"✗ {config.shop.name}: {result['error']}")
                except Exception as e:
                    results.append(f"✗ {config.shop.name}: {str(e)}")
            else:
                results.append(f"⚠ {config.shop.name}: Integration not active")

        self.message_user(request, "\n".join(results))
    trigger_sync.short_description = "Trigger sync for selected integrations"

    def activate_configs(self, request, queryset):
        """Activate selected integrations."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} integrations")
    activate_configs.short_description = "Activate selected integrations"

    def deactivate_configs(self, request, queryset):
        """Deactivate selected integrations."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} integrations")
    deactivate_configs.short_description = "Deactivate selected integrations"


@admin.register(ProductMapping)
class ProductMappingAdmin(admin.ModelAdmin):
    list_display = [
        'local_product', 'integration_config', 'external_product_id', 
        'sync_status', 'is_active', 'last_sync_at'
    ]
    list_filter = ['sync_status', 'is_active', 'integration_config__platform']
    search_fields = [
        'local_product__name', 'external_product_id', 'external_sku'
    ]
    readonly_fields = ['created_at', 'updated_at', 'last_sync_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'local_product', 'integration_config', 'integration_config__shop'
        )


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'shop', 'price', 'original_price', 
        'is_available', 'recorded_at'
    ]
    list_filter = ['is_available', 'currency', 'recorded_at', 'shop']
    search_fields = ['product__name', 'shop__name']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'shop')


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'integration_config', 'sync_type', 'status', 
        'products_processed', 'errors_count', 'started_at'
    ]
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['integration_config__shop__name']
    readonly_fields = [
        'started_at', 'completed_at', 'products_processed', 
        'products_updated', 'products_created', 'errors_count'
    ]
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('integration_config', 'sync_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': (
                'products_processed', 'products_created', 
                'products_updated', 'errors_count'
            )
        }),
        ('Details', {
            'fields': ('error_details', 'summary'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'integration_config', 'integration_config__shop'
        )
