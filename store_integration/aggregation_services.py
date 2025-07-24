"""
store_integration/aggregation_services.py
-----------------------------------------
Services for aggregating and unifying products from multiple stores.
"""

from typing import Dict, List, Optional, Tuple
from django.db.models import Q, Count, Avg, Min, Max, F
from django.utils import timezone
from decimal import Decimal
from core.models import Product, Shop, Brand, Category
from .models import PriceHistory, ProductMapping, StoreIntegrationConfig
import logging
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class ProductAggregationService:
    """
    Service for aggregating products from multiple stores and identifying duplicates.
    """
    
    @staticmethod
    def find_similar_products(product: Product, similarity_threshold: float = 0.8) -> List[Dict]:
        """
        Find similar products across different stores that might be the same product.
        """
        # Get products from other stores
        other_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(
            shop=product.shop
        ).select_related('shop', 'brand')
        
        similar_products = []
        
        for other_product in other_products:
            similarity_score = ProductAggregationService._calculate_similarity(
                product, other_product
            )
            
            if similarity_score >= similarity_threshold:
                # Get latest price for comparison
                latest_price = PriceHistory.objects.filter(
                    product=other_product,
                    shop=other_product.shop
                ).first()
                
                similar_products.append({
                    'product': other_product,
                    'similarity_score': similarity_score,
                    'price_difference': float(other_product.price - product.price),
                    'price_difference_percentage': float(
                        ((other_product.price - product.price) / product.price) * 100
                    ) if product.price > 0 else 0,
                    'shop_reliability': float(other_product.shop.reliability_score),
                    'delivery_days': other_product.shop.average_delivery_days,
                    'latest_price_record': latest_price
                })
        
        # Sort by similarity score and price
        similar_products.sort(
            key=lambda x: (-x['similarity_score'], x['price_difference'])
        )
        
        return similar_products
    
    @staticmethod
    def _calculate_similarity(product1: Product, product2: Product) -> float:
        """
        Calculate similarity score between two products.
        """
        # Name similarity (40% weight)
        name_similarity = SequenceMatcher(
            None, 
            product1.name.lower(), 
            product2.name.lower()
        ).ratio()
        
        # Brand similarity (30% weight)
        brand_similarity = 0.0
        if product1.brand and product2.brand:
            if product1.brand == product2.brand:
                brand_similarity = 1.0
            else:
                brand_similarity = SequenceMatcher(
                    None,
                    product1.brand.name.lower(),
                    product2.brand.name.lower()
                ).ratio()
        elif not product1.brand and not product2.brand:
            brand_similarity = 1.0
        
        # Description similarity (20% weight)
        desc_similarity = 0.0
        if product1.description and product2.description:
            desc_similarity = SequenceMatcher(
                None,
                product1.description.lower()[:200],  # First 200 chars
                product2.description.lower()[:200]
            ).ratio()
        
        # Price similarity (10% weight) - closer prices get higher scores
        price_similarity = 0.0
        if product1.price > 0 and product2.price > 0:
            price_diff = abs(product1.price - product2.price)
            max_price = max(product1.price, product2.price)
            price_similarity = max(0, 1 - (price_diff / max_price))
        
        # Calculate weighted similarity
        total_similarity = (
            name_similarity * 0.4 +
            brand_similarity * 0.3 +
            desc_similarity * 0.2 +
            price_similarity * 0.1
        )
        
        return total_similarity
    
    @staticmethod
    def get_aggregated_product_data(product_id: str) -> Dict:
        """
        Get aggregated data for a product including all similar products from other stores.
        """
        try:
            main_product = Product.objects.select_related(
                'shop', 'brand', 'category'
            ).get(id=product_id)
        except Product.DoesNotExist:
            return None
        
        # Find similar products
        similar_products = ProductAggregationService.find_similar_products(main_product)
        
        # Get price history for the main product
        price_history = PriceHistory.objects.filter(
            product=main_product
        ).order_by('-recorded_at')[:30]  # Last 30 records
        
        # Calculate aggregated metrics
        all_products = [main_product] + [sp['product'] for sp in similar_products]
        prices = [float(p.price) for p in all_products]
        
        aggregated_data = {
            'main_product': {
                'id': str(main_product.id),
                'name': main_product.name,
                'description': main_product.description,
                'price': float(main_product.price),
                'original_price': float(main_product.original_price) if main_product.original_price else None,
                'brand': main_product.brand.name if main_product.brand else None,
                'category': main_product.category.name,
                'shop': {
                    'id': str(main_product.shop.id),
                    'name': main_product.shop.name,
                    'reliability_score': float(main_product.shop.reliability_score),
                    'delivery_days': main_product.shop.average_delivery_days,
                    'customer_service_rating': float(main_product.shop.customer_service_rating)
                },
                'rating': float(main_product.rating),
                'views': main_product.views,
                'likes': main_product.likes,
                'dislikes': main_product.dislikes,
                'image_url': main_product.image_url,
                'is_active': main_product.is_active
            },
            'similar_products': [],
            'price_comparison': {
                'lowest_price': min(prices) if prices else 0,
                'highest_price': max(prices) if prices else 0,
                'average_price': sum(prices) / len(prices) if prices else 0,
                'price_range': max(prices) - min(prices) if prices else 0,
                'stores_count': len(all_products)
            },
            'best_deals': [],
            'price_history': [
                {
                    'price': float(ph.price),
                    'original_price': float(ph.original_price) if ph.original_price else None,
                    'recorded_at': ph.recorded_at,
                    'is_available': ph.is_available
                }
                for ph in price_history
            ]
        }
        
        # Add similar products data
        for similar in similar_products:
            product_data = {
                'id': str(similar['product'].id),
                'name': similar['product'].name,
                'price': float(similar['product'].price),
                'original_price': float(similar['product'].original_price) if similar['product'].original_price else None,
                'shop': {
                    'id': str(similar['product'].shop.id),
                    'name': similar['product'].shop.name,
                    'reliability_score': similar['shop_reliability'],
                    'delivery_days': similar['delivery_days']
                },
                'similarity_score': similar['similarity_score'],
                'price_difference': similar['price_difference'],
                'price_difference_percentage': similar['price_difference_percentage'],
                'image_url': similar['product'].image_url,
                'rating': float(similar['product'].rating)
            }
            aggregated_data['similar_products'].append(product_data)
        
        # Identify best deals (considering price, reliability, and delivery)
        all_product_data = [aggregated_data['main_product']] + aggregated_data['similar_products']
        
        for product_data in all_product_data:
            # Calculate deal score (lower is better)
            price_score = product_data['price']
            reliability_penalty = (5 - product_data['shop']['reliability_score']) * 10
            delivery_penalty = max(0, product_data['shop']['delivery_days'] - 3) * 5
            
            deal_score = price_score + reliability_penalty + delivery_penalty
            product_data['deal_score'] = deal_score
        
        # Sort by deal score and take top 3
        best_deals = sorted(all_product_data, key=lambda x: x['deal_score'])[:3]
        aggregated_data['best_deals'] = best_deals
        
        return aggregated_data
    
    @staticmethod
    def get_unified_search_results(query: str, filters: Dict = None) -> List[Dict]:
        """
        Search products across all stores and return unified results.
        """
        filters = filters or {}
        
        # Build base queryset
        products = Product.objects.filter(
            is_active=True
        ).select_related('shop', 'brand', 'category')
        
        # Apply search query
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__name__icontains=query)
            )
        
        # Apply filters
        if filters.get('category_id'):
            products = products.filter(category_id=filters['category_id'])
        
        if filters.get('brand_id'):
            products = products.filter(brand_id=filters['brand_id'])
        
        if filters.get('min_price'):
            products = products.filter(price__gte=filters['min_price'])
        
        if filters.get('max_price'):
            products = products.filter(price__lte=filters['max_price'])
        
        if filters.get('shop_type'):
            products = products.filter(shop__shop_type=filters['shop_type'])
        
        # Group similar products
        grouped_results = {}
        processed_products = set()
        
        for product in products[:100]:  # Limit for performance
            if product.id in processed_products:
                continue
            
            # Find similar products for this one
            similar_products = ProductAggregationService.find_similar_products(
                product, similarity_threshold=0.7
            )
            
            # Create group key based on product name and brand
            group_key = f"{product.name.lower()}_{product.brand.name.lower() if product.brand else 'no_brand'}"
            group_key = re.sub(r'[^a-z0-9_]', '', group_key)
            
            if group_key not in grouped_results:
                # Get all prices for this product group
                group_products = [product] + [sp['product'] for sp in similar_products]
                prices = [float(p.price) for p in group_products]
                
                grouped_results[group_key] = {
                    'representative_product': {
                        'id': str(product.id),
                        'name': product.name,
                        'description': product.description[:200] + '...' if len(product.description) > 200 else product.description,
                        'brand': product.brand.name if product.brand else None,
                        'category': product.category.name,
                        'image_url': product.image_url,
                        'rating': float(product.rating)
                    },
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices),
                        'average': sum(prices) / len(prices)
                    },
                    'stores_count': len(group_products),
                    'stores': [
                        {
                            'shop_id': str(p.shop.id),
                            'shop_name': p.shop.name,
                            'price': float(p.price),
                            'reliability_score': float(p.shop.reliability_score),
                            'delivery_days': p.shop.average_delivery_days
                        }
                        for p in group_products
                    ],
                    'best_price': min(prices),
                    'best_deal_shop': min(group_products, key=lambda x: x.price).shop.name
                }
                
                # Mark all products in this group as processed
                for p in group_products:
                    processed_products.add(p.id)
        
        # Convert to list and sort by relevance
        results = list(grouped_results.values())
        
        # Sort by best price and store count
        results.sort(key=lambda x: (x['best_price'], -x['stores_count']))
        
        return results
    
    @staticmethod
    def get_category_aggregation(category_id: str) -> Dict:
        """
        Get aggregated data for all products in a category across stores.
        """
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None
        
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('shop', 'brand')
        
        # Group by store
        store_stats = {}
        for product in products:
            shop_id = str(product.shop.id)
            if shop_id not in store_stats:
                store_stats[shop_id] = {
                    'shop_name': product.shop.name,
                    'product_count': 0,
                    'avg_price': 0,
                    'min_price': float('inf'),
                    'max_price': 0,
                    'total_price': 0,
                    'reliability_score': float(product.shop.reliability_score)
                }
            
            stats = store_stats[shop_id]
            stats['product_count'] += 1
            stats['total_price'] += float(product.price)
            stats['min_price'] = min(stats['min_price'], float(product.price))
            stats['max_price'] = max(stats['max_price'], float(product.price))
        
        # Calculate averages
        for stats in store_stats.values():
            if stats['product_count'] > 0:
                stats['avg_price'] = stats['total_price'] / stats['product_count']
                if stats['min_price'] == float('inf'):
                    stats['min_price'] = 0
        
        return {
            'category': {
                'id': str(category.id),
                'name': category.name,
                'description': category.description
            },
            'total_products': products.count(),
            'total_stores': len(store_stats),
            'store_breakdown': list(store_stats.values()),
            'overall_price_range': {
                'min': min([s['min_price'] for s in store_stats.values()]) if store_stats else 0,
                'max': max([s['max_price'] for s in store_stats.values()]) if store_stats else 0,
                'average': sum([s['avg_price'] for s in store_stats.values()]) / len(store_stats) if store_stats else 0
            }
        }
