"""
store_integration/models.py
---------------------------
Models for multi-store integration and synchronization.
"""

from django.db import models
from django.conf import settings
from core.models import Shop, Product
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json


class StoreIntegrationConfig(models.Model):
    """
    Configuration for integrating with external stores.
    """
    PLATFORM_CHOICES = (
        ('shopify', 'Shopify'),
        ('woocommerce', 'WooCommerce'),
        ('magento', 'Magento'),
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('etsy', 'Etsy'),
        ('custom_api', 'Custom API'),
        ('csv_import', 'CSV Import'),
    )
    
    SYNC_FREQUENCY_CHOICES = (
        ('realtime', 'Real-time'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('manual', 'Manual'),
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name='integration_config'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name="Platform"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="API Key"
    )
    api_secret = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="API Secret"
    )
    access_token = models.TextField(
        blank=True,
        null=True,
        verbose_name="Access Token"
    )
    store_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Store URL"
    )
    webhook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webhook URL"
    )
    sync_frequency = models.CharField(
        max_length=20,
        choices=SYNC_FREQUENCY_CHOICES,
        default='daily',
        verbose_name="Sync Frequency"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Sync At"
    )
    sync_errors = models.TextField(
        blank=True,
        null=True,
        verbose_name="Sync Errors"
    )
    configuration = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Additional Configuration"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    def __str__(self):
        return f"{self.shop.name} - {self.get_platform_display()}"


class ProductMapping(models.Model):
    """
    Maps products between our system and external stores.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    local_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='external_mappings'
    )
    integration_config = models.ForeignKey(
        StoreIntegrationConfig,
        on_delete=models.CASCADE,
        related_name='product_mappings'
    )
    external_product_id = models.CharField(
        max_length=200,
        verbose_name="External Product ID"
    )
    external_sku = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="External SKU"
    )
    external_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="External Product URL"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Sync At"
    )
    sync_status = models.CharField(
        max_length=20,
        choices=(
            ('synced', 'Synced'),
            ('pending', 'Pending'),
            ('error', 'Error'),
            ('disabled', 'Disabled'),
        ),
        default='pending',
        verbose_name="Sync Status"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        unique_together = ['integration_config', 'external_product_id']

    def __str__(self):
        return f"{self.local_product.name} -> {self.external_product_id}"


class PriceHistory(models.Model):
    """
    Tracks price changes across different stores for comparison.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Price"
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Original Price"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name="Currency"
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="Is Available"
    )
    stock_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Stock Quantity"
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Recorded At"
    )

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product', 'shop', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.shop.name}: ${self.price}"


class SyncLog(models.Model):
    """
    Logs synchronization activities for monitoring and debugging.
    """
    SYNC_TYPE_CHOICES = (
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('product', 'Product Sync'),
        ('price', 'Price Sync'),
        ('inventory', 'Inventory Sync'),
    )
    
    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    integration_config = models.ForeignKey(
        StoreIntegrationConfig,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        verbose_name="Sync Type"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Status"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Started At"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At"
    )
    products_processed = models.PositiveIntegerField(
        default=0,
        verbose_name="Products Processed"
    )
    products_updated = models.PositiveIntegerField(
        default=0,
        verbose_name="Products Updated"
    )
    products_created = models.PositiveIntegerField(
        default=0,
        verbose_name="Products Created"
    )
    errors_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Errors Count"
    )
    error_details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Error Details"
    )
    summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Sync Summary"
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.integration_config.shop.name} - {self.get_sync_type_display()} ({self.status})"
