"""
store_integration/services.py
-----------------------------
Services for integrating with external stores and synchronizing data.
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import StoreIntegrationConfig, ProductMapping, PriceHistory, SyncLog
from core.models import Product, Shop, Brand, Category
import json

logger = logging.getLogger(__name__)


class BaseStoreIntegration:
    """
    Base class for store integrations.
    """
    
    def __init__(self, config: StoreIntegrationConfig):
        self.config = config
        self.shop = config.shop
        
    def authenticate(self) -> bool:
        """
        Authenticate with the external store API.
        """
        raise NotImplementedError("Subclasses must implement authenticate method")
    
    def fetch_products(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch products from external store.
        """
        raise NotImplementedError("Subclasses must implement fetch_products method")
    
    def fetch_product_details(self, external_id: str) -> Dict:
        """
        Fetch detailed product information.
        """
        raise NotImplementedError("Subclasses must implement fetch_product_details method")
    
    def sync_products(self, full_sync: bool = False) -> Dict:
        """
        Synchronize products from external store.
        """
        sync_log = SyncLog.objects.create(
            integration_config=self.config,
            sync_type='full' if full_sync else 'incremental',
            status='started'
        )
        
        try:
            if not self.authenticate():
                raise Exception("Authentication failed")
            
            products_data = self.fetch_products()
            processed = 0
            created = 0
            updated = 0
            errors = []
            
            for product_data in products_data:
                try:
                    result = self.process_product(product_data)
                    processed += 1
                    if result['created']:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f"Product {product_data.get('id', 'unknown')}: {str(e)}")
                    logger.error(f"Error processing product: {e}")
            
            sync_log.status = 'completed' if not errors else 'partial'
            sync_log.products_processed = processed
            sync_log.products_created = created
            sync_log.products_updated = updated
            sync_log.errors_count = len(errors)
            sync_log.error_details = '\n'.join(errors) if errors else None
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update shop's last sync time
            self.shop.last_sync_at = timezone.now()
            self.shop.save()
            
            return {
                'success': True,
                'processed': processed,
                'created': created,
                'updated': updated,
                'errors': len(errors)
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_details = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            logger.error(f"Sync failed for {self.shop.name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_product(self, product_data: Dict) -> Dict:
        """
        Process a single product from external store.
        """
        external_id = str(product_data.get('id'))
        
        # Check if product mapping exists
        try:
            mapping = ProductMapping.objects.get(
                integration_config=self.config,
                external_product_id=external_id
            )
            product = mapping.local_product
            created = False
        except ProductMapping.DoesNotExist:
            # Create new product
            product = self.create_product_from_data(product_data)
            mapping = ProductMapping.objects.create(
                local_product=product,
                integration_config=self.config,
                external_product_id=external_id,
                external_sku=product_data.get('sku', ''),
                external_url=product_data.get('url', '')
            )
            created = True
        
        # Update product data
        self.update_product_from_data(product, product_data)
        
        # Record price history
        self.record_price_history(product, product_data)
        
        # Update mapping
        mapping.last_sync_at = timezone.now()
        mapping.sync_status = 'synced'
        mapping.save()
        
        return {'created': created, 'product': product}
    
    def create_product_from_data(self, product_data: Dict) -> Product:
        """
        Create a new product from external store data.
        """
        # Get or create category
        category_name = product_data.get('category', 'Uncategorized')
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'description': f'Category for {category_name}'}
        )
        
        # Get or create brand
        brand = None
        brand_name = product_data.get('brand')
        if brand_name:
            brand, _ = Brand.objects.get_or_create(
                name=brand_name,
                defaults={
                    'popularity': Decimal('50.0'),
                    'rating': Decimal('3.0'),
                }
            )
        
        # Create product
        product = Product.objects.create(
            name=product_data.get('name', 'Unnamed Product'),
            description=product_data.get('description', ''),
            price=Decimal(str(product_data.get('price', 0))),
            original_price=Decimal(str(product_data.get('original_price', 0))) if product_data.get('original_price') else None,
            category=category,
            brand=brand,
            shop=self.shop,
            image_url=product_data.get('image_url', ''),
            rating=Decimal(str(product_data.get('rating', 0))),
            is_active=product_data.get('is_active', True)
        )
        
        return product
    
    def update_product_from_data(self, product: Product, product_data: Dict):
        """
        Update existing product with data from external store.
        """
        # Update basic fields
        product.name = product_data.get('name', product.name)
        product.description = product_data.get('description', product.description)
        product.price = Decimal(str(product_data.get('price', product.price)))
        
        if product_data.get('original_price'):
            product.original_price = Decimal(str(product_data.get('original_price')))
        
        product.image_url = product_data.get('image_url', product.image_url)
        product.is_active = product_data.get('is_active', product.is_active)
        
        # Update rating if provided
        if product_data.get('rating'):
            product.rating = Decimal(str(product_data.get('rating')))
        
        product.save()
    
    def record_price_history(self, product: Product, product_data: Dict):
        """
        Record price history for comparison purposes.
        """
        price = Decimal(str(product_data.get('price', 0)))
        original_price = None
        
        if product_data.get('original_price'):
            original_price = Decimal(str(product_data.get('original_price')))
        
        # Only record if price has changed or it's the first record
        latest_price = PriceHistory.objects.filter(
            product=product,
            shop=self.shop
        ).first()
        
        if not latest_price or latest_price.price != price:
            PriceHistory.objects.create(
                product=product,
                shop=self.shop,
                price=price,
                original_price=original_price,
                is_available=product_data.get('is_available', True),
                stock_quantity=product_data.get('stock_quantity')
            )


class ShopifyIntegration(BaseStoreIntegration):
    """
    Integration with Shopify stores.
    """
    
    def authenticate(self) -> bool:
        """
        Authenticate with Shopify API.
        """
        try:
            headers = {
                'X-Shopify-Access-Token': self.config.access_token,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.config.store_url}/admin/api/2023-10/shop.json",
                headers=headers,
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Shopify authentication failed: {e}")
            return False
    
    def fetch_products(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch products from Shopify.
        """
        headers = {
            'X-Shopify-Access-Token': self.config.access_token,
            'Content-Type': 'application/json'
        }
        
        params = {
            'limit': min(limit, 250),  # Shopify max is 250
            'page_info': offset if offset else None
        }
        
        response = requests.get(
            f"{self.config.store_url}/admin/api/2023-10/products.json",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            products = []
            
            for product in data.get('products', []):
                # Transform Shopify product to our format
                transformed = self.transform_shopify_product(product)
                products.append(transformed)
            
            return products
        else:
            raise Exception(f"Failed to fetch products: {response.status_code}")
    
    def transform_shopify_product(self, shopify_product: Dict) -> Dict:
        """
        Transform Shopify product data to our format.
        """
        # Get the first variant for pricing
        variant = shopify_product.get('variants', [{}])[0]
        
        # Get the first image
        image_url = ''
        if shopify_product.get('images'):
            image_url = shopify_product['images'][0].get('src', '')
        
        return {
            'id': shopify_product.get('id'),
            'name': shopify_product.get('title', ''),
            'description': shopify_product.get('body_html', ''),
            'price': float(variant.get('price', 0)),
            'original_price': float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else None,
            'sku': variant.get('sku', ''),
            'brand': shopify_product.get('vendor', ''),
            'category': shopify_product.get('product_type', 'Uncategorized'),
            'image_url': image_url,
            'is_active': shopify_product.get('status') == 'active',
            'is_available': variant.get('inventory_quantity', 0) > 0,
            'stock_quantity': variant.get('inventory_quantity', 0),
            'url': f"{self.config.store_url}/products/{shopify_product.get('handle', '')}"
        }


class StoreIntegrationService:
    """
    Main service for managing store integrations.
    """
    
    INTEGRATION_CLASSES = {
        'shopify': ShopifyIntegration,
        # Add more integrations here
        # 'woocommerce': WooCommerceIntegration,
        # 'magento': MagentoIntegration,
    }
    
    @classmethod
    def get_integration(cls, config: StoreIntegrationConfig):
        """
        Get the appropriate integration class for a configuration.
        """
        integration_class = cls.INTEGRATION_CLASSES.get(config.platform)
        if not integration_class:
            raise ValueError(f"Unsupported platform: {config.platform}")
        
        return integration_class(config)
    
    @classmethod
    def sync_all_stores(cls):
        """
        Sync all active store integrations.
        """
        configs = StoreIntegrationConfig.objects.filter(is_active=True)
        results = []
        
        for config in configs:
            try:
                integration = cls.get_integration(config)
                result = integration.sync_products()
                results.append({
                    'shop': config.shop.name,
                    'platform': config.platform,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to sync {config.shop.name}: {e}")
                results.append({
                    'shop': config.shop.name,
                    'platform': config.platform,
                    'result': {'success': False, 'error': str(e)}
                })
        
        return results
    
    @classmethod
    def sync_store(cls, shop_id: str):
        """
        Sync a specific store.
        """
        try:
            config = StoreIntegrationConfig.objects.get(shop_id=shop_id, is_active=True)
            integration = cls.get_integration(config)
            return integration.sync_products()
        except StoreIntegrationConfig.DoesNotExist:
            raise ValueError(f"No active integration found for shop {shop_id}")
