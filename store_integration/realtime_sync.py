"""
store_integration/realtime_sync.py
----------------------------------
Real-time synchronization service for coordinating price and availability updates.
"""

import logging
from typing import Dict, List, Optional, Set
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
from .models import StoreIntegrationConfig, ProductMapping, PriceHistory
from .tasks import monitor_price_changes, sync_inventory_levels, send_price_alerts
from core.models import Product
import json

logger = logging.getLogger(__name__)


class RealTimeSyncService:
    """
    Service for managing real-time synchronization of product data across stores.
    """
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'REALTIME_SYNC_CACHE_TIMEOUT', 300)  # 5 minutes
        self.price_change_threshold = getattr(settings, 'PRICE_CHANGE_THRESHOLD', 0.05)  # 5%
        self.sync_batch_size = getattr(settings, 'SYNC_BATCH_SIZE', 50)
    
    def trigger_product_sync(self, product_id: str, source_config_id: str = None) -> Dict:
        """
        Trigger real-time synchronization for a specific product across all stores.
        
        Args:
            product_id: Product ID to sync
            source_config_id: Optional source integration config ID
            
        Returns:
            Dict with sync results
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Get all active mappings for this product
            mappings = ProductMapping.objects.filter(
                local_product=product,
                is_active=True,
                integration_config__is_active=True
            ).select_related('integration_config')
            
            if source_config_id:
                # Exclude the source config to avoid circular updates
                mappings = mappings.exclude(integration_config_id=source_config_id)
            
            sync_tasks = []
            
            # Group mappings by integration config
            config_groups = {}
            for mapping in mappings:
                config_id = str(mapping.integration_config.id)
                if config_id not in config_groups:
                    config_groups[config_id] = []
                config_groups[config_id].append(str(mapping.local_product.id))
            
            # Trigger monitoring tasks for each config
            for config_id, product_ids in config_groups.items():
                task = monitor_price_changes.delay(config_id, product_ids)
                sync_tasks.append({
                    'config_id': config_id,
                    'task_id': task.id,
                    'product_count': len(product_ids)
                })
            
            # Cache the sync request to prevent duplicate triggers
            cache_key = f"product_sync_{product_id}"
            cache.set(cache_key, timezone.now().isoformat(), self.cache_timeout)
            
            return {
                'success': True,
                'product_id': product_id,
                'sync_tasks': sync_tasks,
                'configs_triggered': len(config_groups)
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': f'Product {product_id} not found'
            }
        except Exception as e:
            logger.error(f"Error triggering product sync for {product_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_store_sync(self, config_id: str, product_ids: List[str] = None) -> Dict:
        """
        Trigger real-time synchronization for all products in a store.
        
        Args:
            config_id: StoreIntegrationConfig ID
            product_ids: Optional list of specific product IDs
            
        Returns:
            Dict with sync results
        """
        try:
            config = StoreIntegrationConfig.objects.get(id=config_id, is_active=True)
            
            # Check if sync is already in progress
            cache_key = f"store_sync_{config_id}"
            if cache.get(cache_key):
                return {
                    'success': False,
                    'error': 'Sync already in progress for this store'
                }
            
            # Set sync in progress flag
            cache.set(cache_key, True, self.cache_timeout)
            
            try:
                # Trigger price monitoring
                price_task = monitor_price_changes.delay(config_id, product_ids)
                
                # Trigger inventory sync
                inventory_task = sync_inventory_levels.delay(config_id)
                
                return {
                    'success': True,
                    'config_id': config_id,
                    'shop_name': config.shop.name,
                    'price_task_id': price_task.id,
                    'inventory_task_id': inventory_task.id
                }
                
            finally:
                # Clear sync in progress flag after a delay
                cache.set(cache_key, True, 60)  # Keep flag for 1 minute
            
        except StoreIntegrationConfig.DoesNotExist:
            return {
                'success': False,
                'error': f'Store integration config {config_id} not found'
            }
        except Exception as e:
            logger.error(f"Error triggering store sync for {config_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_price_trends(self, product_id: str, days: int = 30) -> Dict:
        """
        Get price trends for a product across all stores.
        
        Args:
            product_id: Product ID
            days: Number of days to analyze
            
        Returns:
            Dict with price trend data
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Get price history for the last N days
            start_date = timezone.now() - timedelta(days=days)
            price_history = PriceHistory.objects.filter(
                product=product,
                recorded_at__gte=start_date
            ).select_related('shop').order_by('recorded_at')
            
            if not price_history.exists():
                return {
                    'success': True,
                    'product_id': product_id,
                    'message': 'No price history found',
                    'trends': {}
                }
            
            # Group by shop and calculate trends
            shop_trends = {}
            
            for record in price_history:
                shop_id = str(record.shop.id)
                if shop_id not in shop_trends:
                    shop_trends[shop_id] = {
                        'shop_name': record.shop.name,
                        'prices': [],
                        'availability': [],
                        'current_price': None,
                        'lowest_price': None,
                        'highest_price': None,
                        'price_changes': 0
                    }
                
                trend = shop_trends[shop_id]
                trend['prices'].append({
                    'price': float(record.price),
                    'date': record.recorded_at.isoformat(),
                    'available': record.is_available
                })
                
                # Update statistics
                if trend['current_price'] is None or record.recorded_at > timezone.now() - timedelta(hours=24):
                    trend['current_price'] = float(record.price)
                
                if trend['lowest_price'] is None or record.price < trend['lowest_price']:
                    trend['lowest_price'] = float(record.price)
                
                if trend['highest_price'] is None or record.price > trend['highest_price']:
                    trend['highest_price'] = float(record.price)
            
            # Calculate price change frequency
            for shop_id, trend in shop_trends.items():
                prices = [p['price'] for p in trend['prices']]
                if len(prices) > 1:
                    changes = sum(1 for i in range(1, len(prices)) if prices[i] != prices[i-1])
                    trend['price_changes'] = changes
                    trend['volatility'] = self._calculate_volatility(prices)
                else:
                    trend['volatility'] = 0
            
            # Find best deals
            current_prices = {
                shop_id: trend['current_price'] 
                for shop_id, trend in shop_trends.items() 
                if trend['current_price'] is not None
            }
            
            best_deal = None
            if current_prices:
                best_shop_id = min(current_prices, key=current_prices.get)
                best_deal = {
                    'shop_id': best_shop_id,
                    'shop_name': shop_trends[best_shop_id]['shop_name'],
                    'price': current_prices[best_shop_id]
                }
            
            return {
                'success': True,
                'product_id': product_id,
                'product_name': product.name,
                'analysis_period_days': days,
                'shop_trends': shop_trends,
                'best_current_deal': best_deal,
                'total_shops': len(shop_trends)
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': f'Product {product_id} not found'
            }
        except Exception as e:
            logger.error(f"Error getting price trends for {product_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """
        Calculate price volatility (standard deviation).
        """
        if len(prices) < 2:
            return 0.0
        
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        return variance ** 0.5
    
    def detect_price_anomalies(self, product_id: str, threshold: float = 0.2) -> Dict:
        """
        Detect unusual price changes that might indicate errors or special deals.
        
        Args:
            product_id: Product ID
            threshold: Percentage threshold for anomaly detection (default 20%)
            
        Returns:
            Dict with anomaly detection results
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Get recent price history (last 7 days)
            start_date = timezone.now() - timedelta(days=7)
            recent_prices = PriceHistory.objects.filter(
                product=product,
                recorded_at__gte=start_date
            ).select_related('shop').order_by('shop', 'recorded_at')
            
            anomalies = []
            
            # Group by shop and check for anomalies
            shop_prices = {}
            for record in recent_prices:
                shop_id = str(record.shop.id)
                if shop_id not in shop_prices:
                    shop_prices[shop_id] = []
                shop_prices[shop_id].append(record)
            
            for shop_id, prices in shop_prices.items():
                if len(prices) < 2:
                    continue
                
                # Sort by date
                prices.sort(key=lambda x: x.recorded_at)
                
                # Check for sudden price changes
                for i in range(1, len(prices)):
                    prev_price = prices[i-1].price
                    curr_price = prices[i].price
                    
                    if prev_price > 0:
                        change_percentage = abs(curr_price - prev_price) / prev_price
                        
                        if change_percentage > threshold:
                            anomalies.append({
                                'shop_id': shop_id,
                                'shop_name': prices[i].shop.name,
                                'previous_price': float(prev_price),
                                'current_price': float(curr_price),
                                'change_percentage': change_percentage * 100,
                                'change_type': 'increase' if curr_price > prev_price else 'decrease',
                                'detected_at': prices[i].recorded_at.isoformat(),
                                'severity': 'high' if change_percentage > 0.5 else 'medium'
                            })
            
            return {
                'success': True,
                'product_id': product_id,
                'product_name': product.name,
                'anomalies_detected': len(anomalies),
                'anomalies': anomalies,
                'threshold_used': threshold * 100
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': f'Product {product_id} not found'
            }
        except Exception as e:
            logger.error(f"Error detecting price anomalies for {product_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sync_status(self, config_id: str = None) -> Dict:
        """
        Get current synchronization status for stores.
        
        Args:
            config_id: Optional specific config ID
            
        Returns:
            Dict with sync status information
        """
        try:
            if config_id:
                configs = StoreIntegrationConfig.objects.filter(id=config_id, is_active=True)
            else:
                configs = StoreIntegrationConfig.objects.filter(is_active=True)
            
            status_info = []
            
            for config in configs:
                # Check if sync is in progress
                cache_key = f"store_sync_{config.id}"
                sync_in_progress = bool(cache.get(cache_key))
                
                # Get latest sync log
                from .models import SyncLog
                latest_log = SyncLog.objects.filter(
                    integration_config=config
                ).first()
                
                # Get product mapping count
                mapping_count = ProductMapping.objects.filter(
                    integration_config=config,
                    is_active=True
                ).count()
                
                status_info.append({
                    'config_id': str(config.id),
                    'shop_name': config.shop.name,
                    'platform': config.platform,
                    'sync_in_progress': sync_in_progress,
                    'last_sync_at': config.last_sync_at.isoformat() if config.last_sync_at else None,
                    'sync_frequency': config.sync_frequency,
                    'active_mappings': mapping_count,
                    'latest_sync_status': latest_log.status if latest_log else 'never',
                    'sync_errors': config.sync_errors or None
                })
            
            return {
                'success': True,
                'total_configs': len(status_info),
                'configs': status_info
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
realtime_sync_service = RealTimeSyncService()
