"""
store_integration/tasks.py
--------------------------
Celery tasks for real-time synchronization and background processing.
"""

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import StoreIntegrationConfig, PriceHistory, SyncLog
from .services import StoreIntegrationService
from core.models import Product, Shop
import logging
from datetime import timedelta

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
