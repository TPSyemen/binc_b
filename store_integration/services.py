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


class WooCommerceIntegration(BaseStoreIntegration):
    """
    Integration with WooCommerce stores.
    """

    def authenticate(self) -> bool:
        """
        Authenticate with WooCommerce API.
        """
        try:
            import base64

            # WooCommerce uses basic auth with consumer key and secret
            credentials = base64.b64encode(
                f"{self.config.api_key}:{self.config.api_secret}".encode()
            ).decode()

            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.config.store_url}/wp-json/wc/v3/system_status",
                headers=headers,
                timeout=30
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"WooCommerce authentication failed: {e}")
            return False

    def fetch_products(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch products from WooCommerce.
        """
        import base64

        credentials = base64.b64encode(
            f"{self.config.api_key}:{self.config.api_secret}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }

        params = {
            'per_page': min(limit, 100),  # WooCommerce max is 100
            'page': (offset // limit) + 1,
            'status': 'publish'
        }

        response = requests.get(
            f"{self.config.store_url}/wp-json/wc/v3/products",
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            products = response.json()
            transformed_products = []

            for product in products:
                transformed = self.transform_woocommerce_product(product)
                transformed_products.append(transformed)

            return transformed_products
        else:
            raise Exception(f"Failed to fetch products: {response.status_code}")

    def transform_woocommerce_product(self, wc_product: Dict) -> Dict:
        """
        Transform WooCommerce product data to our format.
        """
        # Get the first image
        image_url = ''
        if wc_product.get('images'):
            image_url = wc_product['images'][0].get('src', '')

        # Calculate average rating
        rating = float(wc_product.get('average_rating', 0))

        return {
            'id': wc_product.get('id'),
            'name': wc_product.get('name', ''),
            'description': wc_product.get('description', ''),
            'price': float(wc_product.get('price', 0)),
            'original_price': float(wc_product.get('regular_price', 0)) if wc_product.get('regular_price') else None,
            'sku': wc_product.get('sku', ''),
            'brand': '',  # WooCommerce doesn't have built-in brand field
            'category': wc_product.get('categories', [{}])[0].get('name', 'Uncategorized'),
            'image_url': image_url,
            'is_active': wc_product.get('status') == 'publish',
            'is_available': wc_product.get('stock_status') == 'instock',
            'stock_quantity': wc_product.get('stock_quantity', 0),
            'rating': rating,
            'url': wc_product.get('permalink', '')
        }


class MagentoIntegration(BaseStoreIntegration):
    """
    Integration with Magento stores.
    """

    def authenticate(self) -> bool:
        """
        Authenticate with Magento API.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.config.store_url}/rest/V1/modules",
                headers=headers,
                timeout=30
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Magento authentication failed: {e}")
            return False

    def fetch_products(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch products from Magento.
        """
        headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'searchCriteria[pageSize]': min(limit, 100),
            'searchCriteria[currentPage]': (offset // limit) + 1,
            'searchCriteria[filterGroups][0][filters][0][field]': 'status',
            'searchCriteria[filterGroups][0][filters][0][value]': '1',  # Enabled
            'searchCriteria[filterGroups][0][filters][0][conditionType]': 'eq'
        }

        response = requests.get(
            f"{self.config.store_url}/rest/V1/products",
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            products = data.get('items', [])
            transformed_products = []

            for product in products:
                transformed = self.transform_magento_product(product)
                transformed_products.append(transformed)

            return transformed_products
        else:
            raise Exception(f"Failed to fetch products: {response.status_code}")

    def transform_magento_product(self, magento_product: Dict) -> Dict:
        """
        Transform Magento product data to our format.
        """
        # Extract custom attributes
        custom_attrs = {attr['attribute_code']: attr['value']
                       for attr in magento_product.get('custom_attributes', [])}

        # Get image URL
        image_url = ''
        media_gallery = custom_attrs.get('media_gallery')
        if media_gallery and isinstance(media_gallery, dict):
            images = media_gallery.get('images', [])
            if images:
                image_url = f"{self.config.store_url}/media/catalog/product{images[0].get('file', '')}"

        return {
            'id': magento_product.get('id'),
            'name': magento_product.get('name', ''),
            'description': custom_attrs.get('description', ''),
            'price': float(magento_product.get('price', 0)),
            'original_price': None,  # Would need special price logic
            'sku': magento_product.get('sku', ''),
            'brand': custom_attrs.get('manufacturer', ''),
            'category': 'Uncategorized',  # Would need category lookup
            'image_url': image_url,
            'is_active': magento_product.get('status') == 1,
            'is_available': custom_attrs.get('quantity_and_stock_status', {}).get('is_in_stock', False),
            'stock_quantity': 0,  # Would need inventory lookup
            'rating': 0,  # Would need review lookup
            'url': f"{self.config.store_url}/catalog/product/view/id/{magento_product.get('id')}"
        }


class StoreIntegrationService:
    """
    Enhanced service for managing store integrations with multiple platforms.
    """

    INTEGRATION_CLASSES = {
        'shopify': ShopifyIntegration,
        'woocommerce': WooCommerceIntegration,
        'magento': MagentoIntegration,
        # Add more integrations here
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

    @classmethod
    def test_integration(cls, config: StoreIntegrationConfig) -> Dict:
        """
        Test integration connectivity and authentication.
        """
        try:
            integration = cls.get_integration(config)

            # Test authentication
            auth_success = integration.authenticate()

            if not auth_success:
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'details': 'Unable to authenticate with store API'
                }

            # Test product fetch (small sample)
            try:
                sample_products = integration.fetch_products(limit=5)
                product_count = len(sample_products)
            except Exception as e:
                return {
                    'success': False,
                    'error': 'Product fetch failed',
                    'details': str(e)
                }

            return {
                'success': True,
                'message': 'Integration test successful',
                'details': {
                    'authentication': 'passed',
                    'product_fetch': 'passed',
                    'sample_product_count': product_count,
                    'platform': config.platform,
                    'store_url': config.store_url
                }
            }

        except Exception as e:
            logger.error(f"Integration test failed for {config.shop.name}: {e}")
            return {
                'success': False,
                'error': 'Integration test failed',
                'details': str(e)
            }

    @classmethod
    def validate_config(cls, platform: str, config_data: Dict) -> Dict:
        """
        Validate integration configuration for a specific platform.
        """
        validation_rules = {
            'shopify': {
                'required_fields': ['store_url', 'access_token'],
                'url_format': r'^https://[\w-]+\.myshopify\.com$',
                'test_endpoint': '/admin/api/2023-10/shop.json'
            },
            'woocommerce': {
                'required_fields': ['store_url', 'api_key', 'api_secret'],
                'url_format': r'^https?://[\w.-]+',
                'test_endpoint': '/wp-json/wc/v3/system_status'
            },
            'magento': {
                'required_fields': ['store_url', 'access_token'],
                'url_format': r'^https?://[\w.-]+',
                'test_endpoint': '/rest/V1/modules'
            }
        }

        if platform not in validation_rules:
            return {
                'valid': False,
                'errors': [f'Unsupported platform: {platform}']
            }

        rules = validation_rules[platform]
        errors = []

        # Check required fields
        for field in rules['required_fields']:
            if not config_data.get(field):
                errors.append(f'Missing required field: {field}')

        # Validate URL format
        import re
        store_url = config_data.get('store_url', '')
        if store_url and not re.match(rules['url_format'], store_url):
            errors.append(f'Invalid store URL format for {platform}')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'platform': platform
        }

    @classmethod
    def get_supported_platforms(cls) -> List[Dict]:
        """
        Get list of supported e-commerce platforms with their requirements.
        """
        platforms = []

        for platform_key, integration_class in cls.INTEGRATION_CLASSES.items():
            platform_info = {
                'key': platform_key,
                'name': platform_key.title(),
                'description': f'Integration with {platform_key.title()} stores',
                'auth_type': cls._get_auth_type(platform_key),
                'required_fields': cls._get_required_fields(platform_key),
                'features': cls._get_platform_features(platform_key)
            }
            platforms.append(platform_info)

        return platforms

    @classmethod
    def _get_auth_type(cls, platform: str) -> str:
        """Get authentication type for platform."""
        auth_types = {
            'shopify': 'access_token',
            'woocommerce': 'api_key_secret',
            'magento': 'bearer_token'
        }
        return auth_types.get(platform, 'unknown')

    @classmethod
    def _get_required_fields(cls, platform: str) -> List[str]:
        """Get required configuration fields for platform."""
        required_fields = {
            'shopify': ['store_url', 'access_token'],
            'woocommerce': ['store_url', 'api_key', 'api_secret'],
            'magento': ['store_url', 'access_token']
        }
        return required_fields.get(platform, [])

    @classmethod
    def _get_platform_features(cls, platform: str) -> List[str]:
        """Get supported features for platform."""
        features = {
            'shopify': [
                'Product sync', 'Inventory tracking', 'Order management',
                'Customer data', 'Webhook support', 'Real-time updates'
            ],
            'woocommerce': [
                'Product sync', 'Inventory tracking', 'Order management',
                'Customer data', 'Category management'
            ],
            'magento': [
                'Product sync', 'Inventory tracking', 'Order management',
                'Customer data', 'Advanced catalog management'
            ]
        }
        return features.get(platform, [])


class WebhookHandler:
    """
    Service for handling webhooks from integrated stores.
    """

    @staticmethod
    def handle_shopify_webhook(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """
        Handle Shopify webhook events.
        """
        try:
            topic = webhook_data.get('topic', '')

            if topic == 'products/create':
                return WebhookHandler._handle_product_create(webhook_data, config)
            elif topic == 'products/update':
                return WebhookHandler._handle_product_update(webhook_data, config)
            elif topic == 'products/delete':
                return WebhookHandler._handle_product_delete(webhook_data, config)
            elif topic == 'inventory_levels/update':
                return WebhookHandler._handle_inventory_update(webhook_data, config)
            else:
                return {'success': True, 'message': f'Unhandled topic: {topic}'}

        except Exception as e:
            logger.error(f"Error handling Shopify webhook: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_woocommerce_webhook(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """
        Handle WooCommerce webhook events.
        """
        try:
            action = webhook_data.get('action', '')

            if action in ['product.created', 'product.updated']:
                return WebhookHandler._handle_product_update(webhook_data, config)
            elif action == 'product.deleted':
                return WebhookHandler._handle_product_delete(webhook_data, config)
            else:
                return {'success': True, 'message': f'Unhandled action: {action}'}

        except Exception as e:
            logger.error(f"Error handling WooCommerce webhook: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _handle_product_create(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """Handle product creation webhook."""
        try:
            integration = StoreIntegrationService.get_integration(config)

            # Get product details from webhook data
            external_id = str(webhook_data.get('id'))

            # Fetch full product details
            product_details = integration.fetch_product_details(external_id)

            # Process the product
            result = integration.process_product(product_details)

            return {
                'success': True,
                'message': 'Product created successfully',
                'product_id': str(result['product'].id),
                'created': result['created']
            }

        except Exception as e:
            logger.error(f"Error handling product create webhook: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _handle_product_update(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """Handle product update webhook."""
        try:
            integration = StoreIntegrationService.get_integration(config)
            external_id = str(webhook_data.get('id'))

            # Check if we have this product mapped
            try:
                mapping = ProductMapping.objects.get(
                    integration_config=config,
                    external_product_id=external_id
                )

                # Update the product
                product_details = integration.fetch_product_details(external_id)
                integration.update_product_from_data(mapping.local_product, product_details)
                integration.record_price_history(mapping.local_product, product_details)

                mapping.last_sync_at = timezone.now()
                mapping.save()

                return {
                    'success': True,
                    'message': 'Product updated successfully',
                    'product_id': str(mapping.local_product.id)
                }

            except ProductMapping.DoesNotExist:
                # Product not in our system, create it
                return WebhookHandler._handle_product_create(webhook_data, config)

        except Exception as e:
            logger.error(f"Error handling product update webhook: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _handle_product_delete(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """Handle product deletion webhook."""
        try:
            external_id = str(webhook_data.get('id'))

            # Find and deactivate the product
            try:
                mapping = ProductMapping.objects.get(
                    integration_config=config,
                    external_product_id=external_id
                )

                # Deactivate instead of deleting
                mapping.local_product.is_active = False
                mapping.local_product.save()

                mapping.is_active = False
                mapping.save()

                return {
                    'success': True,
                    'message': 'Product deactivated successfully',
                    'product_id': str(mapping.local_product.id)
                }

            except ProductMapping.DoesNotExist:
                return {
                    'success': True,
                    'message': 'Product not found in our system'
                }

        except Exception as e:
            logger.error(f"Error handling product delete webhook: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _handle_inventory_update(webhook_data: Dict, config: StoreIntegrationConfig) -> Dict:
        """Handle inventory update webhook."""
        try:
            # This would handle inventory/stock updates
            # Implementation depends on webhook data structure
            return {
                'success': True,
                'message': 'Inventory update processed'
            }

        except Exception as e:
            logger.error(f"Error handling inventory update webhook: {e}")
            return {'success': False, 'error': str(e)}
