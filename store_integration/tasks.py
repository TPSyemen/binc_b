"""
store_integration/tasks.py
--------------------------
Celery tasks for real-time synchronization and background processing.
"""

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import StoreIntegrationConfig, PriceHistory, SyncLog, ProductMapping
from .services import StoreIntegrationService
from core.models import Product, Shop
from reviews.models import EngagementEvent
import logging
from datetime import timedelta
from typing import Dict, List, Optional
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_store_products(self, config_id: str, full_sync: bool = False):
    """
    Celery task to synchronize products from a specific store.
    """
    try:
        config = StoreIntegrationConfig.objects.get(id=config_id, is_active=True)
        integration = StoreIntegrationService.get_integration(config)
        
        result = integration.sync_products(full_sync=full_sync)
        
        logger.info(f"Sync completed for {config.shop.name}: {result}")
        return result
        
    except StoreIntegrationConfig.DoesNotExist:
        logger.error(f"Integration config {config_id} not found or inactive")
        return {'success': False, 'error': 'Configuration not found'}
    
    except Exception as e:
        logger.error(f"Sync task failed for config {config_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 60  # 1, 2, 4 minutes
            raise self.retry(countdown=countdown, exc=e)
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True)
def monitor_price_changes(self, config_id: str, product_ids: List[str] = None):
    """
    Monitor and record price changes for products in real-time.

    Args:
        config_id: StoreIntegrationConfig ID
        product_ids: Optional list of specific product IDs to monitor
    """
    try:
        config = StoreIntegrationConfig.objects.get(id=config_id, is_active=True)
        integration = StoreIntegrationService.get_integration(config)

        # Get products to monitor
        if product_ids:
            mappings = ProductMapping.objects.filter(
                integration_config=config,
                local_product_id__in=product_ids,
                is_active=True
            )
        else:
            mappings = ProductMapping.objects.filter(
                integration_config=config,
                is_active=True
            )

        price_changes = []

        for mapping in mappings:
            try:
                # Fetch current product data
                product_data = integration.fetch_product_details(
                    mapping.external_product_id
                )

                # Get latest price history
                latest_price = PriceHistory.objects.filter(
                    product=mapping.local_product,
                    shop=config.shop
                ).first()

                current_price = float(product_data.get('price', 0))
                current_availability = product_data.get('is_available', False)

                # Check for price or availability changes
                price_changed = (
                    not latest_price or
                    latest_price.price != current_price or
                    latest_price.is_available != current_availability
                )

                if price_changed:
                    # Record new price history
                    with transaction.atomic():
                        price_history = PriceHistory.objects.create(
                            product=mapping.local_product,
                            shop=config.shop,
                            price=current_price,
                            original_price=product_data.get('original_price'),
                            currency=product_data.get('currency', 'USD'),
                            is_available=current_availability,
                            stock_quantity=product_data.get('stock_quantity', 0)
                        )

                        # Calculate price change
                        if latest_price:
                            price_diff = current_price - latest_price.price
                            change_percentage = (price_diff / latest_price.price) * 100 if latest_price.price > 0 else 0
                        else:
                            price_diff = 0
                            change_percentage = 0

                        price_changes.append({
                            'product_id': str(mapping.local_product.id),
                            'product_name': mapping.local_product.name,
                            'old_price': latest_price.price if latest_price else 0,
                            'new_price': current_price,
                            'price_diff': price_diff,
                            'change_percentage': change_percentage,
                            'availability_changed': (
                                not latest_price or
                                latest_price.is_available != current_availability
                            ),
                            'new_availability': current_availability
                        })

                        # Update product price if it's the primary source
                        if config.shop == mapping.local_product.shop:
                            mapping.local_product.price = current_price
                            mapping.local_product.is_active = current_availability
                            mapping.local_product.save()

                        # Create engagement event for price change
                        EngagementEvent.objects.create(
                            product=mapping.local_product,
                            shop=config.shop,
                            event_type='price_change',
                            session_id='system',
                            event_data={
                                'old_price': latest_price.price if latest_price else 0,
                                'new_price': current_price,
                                'change_percentage': change_percentage,
                                'availability_changed': price_changes[-1]['availability_changed']
                            }
                        )

                # Update mapping sync status
                mapping.last_sync_at = timezone.now()
                mapping.sync_status = 'synced'
                mapping.save()

            except Exception as e:
                logger.error(f"Error monitoring price for product {mapping.local_product.id}: {e}")
                mapping.sync_status = 'error'
                mapping.save()

        # Trigger price alert notifications if there are significant changes
        if price_changes:
            send_price_alerts.delay(
                config_id=str(config.id),
                price_changes=price_changes
            )

        return {
            'success': True,
            'products_monitored': len(mappings),
            'price_changes_detected': len(price_changes),
            'changes': price_changes
        }

    except Exception as e:
        logger.error(f"Error monitoring price changes for config {config_id}: {e}")
        raise e


@shared_task
def send_price_alerts(config_id: str, price_changes: List[Dict]):
    """
    Send price alert notifications to relevant users.

    Args:
        config_id: StoreIntegrationConfig ID
        price_changes: List of price change data
    """
    try:
        config = StoreIntegrationConfig.objects.get(id=config_id)

        # Filter significant price changes (>5% change or availability changes)
        significant_changes = [
            change for change in price_changes
            if abs(change.get('change_percentage', 0)) > 5 or
               change.get('availability_changed', False)
        ]

        if not significant_changes:
            return {'success': True, 'message': 'No significant changes to alert'}

        # Here you would implement actual notification logic
        # (email, push notifications, etc.)
        logger.info(f"Price alerts sent for {len(significant_changes)} products from {config.shop.name}")

        return {
            'success': True,
            'alerts_sent': len(significant_changes),
            'shop': config.shop.name
        }

    except Exception as e:
        logger.error(f"Error sending price alerts: {e}")
        raise e


@shared_task
def sync_inventory_levels(config_id: str):
    """
    Synchronize inventory levels for products from a specific store.

    Args:
        config_id: StoreIntegrationConfig ID
    """
    try:
        config = StoreIntegrationConfig.objects.get(id=config_id, is_active=True)
        integration = StoreIntegrationService.get_integration(config)

        # Get all product mappings for this integration
        mappings = ProductMapping.objects.filter(
            integration_config=config,
            is_active=True
        )

        updated_count = 0

        for mapping in mappings:
            try:
                # Fetch current inventory data
                inventory_data = integration.fetch_inventory_data(
                    mapping.external_product_id
                )

                if inventory_data:
                    # Update local product inventory
                    product = mapping.local_product
                    old_stock = getattr(product, 'stock_quantity', 0)
                    new_stock = inventory_data.get('stock_quantity', 0)

                    if hasattr(product, 'stock_quantity'):
                        product.stock_quantity = new_stock
                        product.save()

                    # Record inventory change if significant
                    if abs(old_stock - new_stock) > 0:
                        EngagementEvent.objects.create(
                            product=product,
                            shop=config.shop,
                            event_type='inventory_update',
                            session_id='system',
                            event_data={
                                'old_stock': old_stock,
                                'new_stock': new_stock,
                                'stock_change': new_stock - old_stock
                            }
                        )

                    updated_count += 1

            except Exception as e:
                logger.error(f"Error syncing inventory for product {mapping.local_product.id}: {e}")

        return {
            'success': True,
            'products_updated': updated_count,
            'shop': config.shop.name
        }

    except Exception as e:
        logger.error(f"Error syncing inventory levels for config {config_id}: {e}")
        raise e


@shared_task
def sync_all_stores():
    """
    Celery task to synchronize all active store integrations.
    """
    configs = StoreIntegrationConfig.objects.filter(is_active=True)
    results = []
    
    for config in configs:
        try:
            # Check if it's time to sync based on frequency
            if should_sync_now(config):
                result = sync_store_products.delay(str(config.id))
                results.append({
                    'shop': config.shop.name,
                    'task_id': result.id,
                    'status': 'queued'
                })
            else:
                results.append({
                    'shop': config.shop.name,
                    'status': 'skipped',
                    'reason': 'not_due_for_sync'
                })
        except Exception as e:
            logger.error(f"Failed to queue sync for {config.shop.name}: {e}")
            results.append({
                'shop': config.shop.name,
                'status': 'error',
                'error': str(e)
            })
    
    return results


@shared_task
def update_price_history():
    """
    Task to update price history for all products across stores.
    """
    updated_count = 0
    error_count = 0
    
    # Get all active products
    products = Product.objects.filter(is_active=True).select_related('shop')
    
    for product in products:
        try:
            # Check if we need to record a new price entry
            latest_price = PriceHistory.objects.filter(
                product=product,
                shop=product.shop
            ).first()
            
            # Record new price if it's different or if it's been more than 24 hours
            should_record = False
            
            if not latest_price:
                should_record = True
            elif latest_price.price != product.price:
                should_record = True
            elif timezone.now() - latest_price.recorded_at > timedelta(hours=24):
                should_record = True
            
            if should_record:
                PriceHistory.objects.create(
                    product=product,
                    shop=product.shop,
                    price=product.price,
                    original_price=product.original_price,
                    is_available=product.is_active,
                    currency='USD'  # Default currency
                )
                updated_count += 1
                
        except Exception as e:
            logger.error(f"Failed to update price history for product {product.id}: {e}")
            error_count += 1
    
    return {
        'updated_count': updated_count,
        'error_count': error_count,
        'total_processed': products.count()
    }


@shared_task
def cleanup_old_price_history(days_to_keep: int = 90):
    """
    Task to clean up old price history records.
    """
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count, _ = PriceHistory.objects.filter(
        recorded_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old price history records")
    return {'deleted_count': deleted_count}


@shared_task
def cleanup_old_sync_logs(days_to_keep: int = 30):
    """
    Task to clean up old sync logs.
    """
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count, _ = SyncLog.objects.filter(
        started_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old sync logs")
    return {'deleted_count': deleted_count}


@shared_task
def update_shop_performance_metrics():
    """
    Task to update shop performance metrics based on recent data.
    """
    shops = Shop.objects.all()
    updated_count = 0
    
    for shop in shops:
        try:
            # Calculate reliability score based on sync success rate
            recent_syncs = SyncLog.objects.filter(
                integration_config__shop=shop,
                started_at__gte=timezone.now() - timedelta(days=30)
            )
            
            if recent_syncs.exists():
                success_rate = recent_syncs.filter(
                    status='completed'
                ).count() / recent_syncs.count()
                
                # Update reliability score (weighted average)
                new_reliability = (success_rate * 5)  # Convert to 0-5 scale
                shop.reliability_score = (
                    shop.reliability_score * 0.7 + new_reliability * 0.3
                )
                
                shop.save()
                updated_count += 1
                
        except Exception as e:
            logger.error(f"Failed to update performance metrics for shop {shop.id}: {e}")
    
    return {'updated_shops': updated_count}


@shared_task
def send_price_alerts():
    """
    Task to send price alerts to users for products they're watching.
    """
    # This would integrate with your notification system
    # For now, we'll just log significant price changes
    
    # Get recent price changes (last hour)
    recent_prices = PriceHistory.objects.filter(
        recorded_at__gte=timezone.now() - timedelta(hours=1)
    ).select_related('product', 'shop')
    
    alerts_sent = 0
    
    for price_record in recent_prices:
        # Get previous price
        previous_price = PriceHistory.objects.filter(
            product=price_record.product,
            shop=price_record.shop,
            recorded_at__lt=price_record.recorded_at
        ).first()
        
        if previous_price:
            price_change_percentage = (
                (price_record.price - previous_price.price) / previous_price.price
            ) * 100
            
            # Alert for significant price changes (>10% decrease or >20% increase)
            if price_change_percentage <= -10 or price_change_percentage >= 20:
                logger.info(
                    f"Price alert: {price_record.product.name} at {price_record.shop.name} "
                    f"changed by {price_change_percentage:.1f}% "
                    f"(${previous_price.price} -> ${price_record.price})"
                )
                alerts_sent += 1
                
                # Here you would send actual notifications to users
                # who are watching this product
    
    return {'alerts_sent': alerts_sent}


def should_sync_now(config: StoreIntegrationConfig) -> bool:
    """
    Determine if a store should be synced now based on its frequency setting.
    """
    if not config.last_sync_at:
        return True
    
    now = timezone.now()
    time_since_last_sync = now - config.last_sync_at
    
    frequency_intervals = {
        'realtime': timedelta(minutes=5),
        'hourly': timedelta(hours=1),
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'manual': timedelta(days=365)  # Effectively never auto-sync
    }
    
    required_interval = frequency_intervals.get(config.sync_frequency, timedelta(days=1))
    
    return time_since_last_sync >= required_interval


# Periodic task setup (would be configured in celery beat schedule)
CELERY_BEAT_SCHEDULE = {
    'sync-all-stores': {
        'task': 'store_integration.tasks.sync_all_stores',
        'schedule': 3600.0,  # Every hour
    },
    'update-price-history': {
        'task': 'store_integration.tasks.update_price_history',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'cleanup-old-data': {
        'task': 'store_integration.tasks.cleanup_old_price_history',
        'schedule': 86400.0,  # Daily
    },
    'update-performance-metrics': {
        'task': 'store_integration.tasks.update_shop_performance_metrics',
        'schedule': 21600.0,  # Every 6 hours
    },
    'send-price-alerts': {
        'task': 'store_integration.tasks.send_price_alerts',
        'schedule': 3600.0,  # Every hour
    },
}
