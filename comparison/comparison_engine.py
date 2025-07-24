"""
comparison/comparison_engine.py
-------------------------------
Advanced comparison engine for cross-store product analysis.
"""

from typing import Dict, List, Optional, Tuple
from django.db.models import Avg, Count, Q
from decimal import Decimal
from core.models import Product, Shop
from store_integration.models import PriceHistory
from .models import (
    ProductComparison, ComparisonCriteria, ComparisonResult, 
    ComparisonTemplate, TemplateCriteria
)
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class AdvancedComparisonEngine:
    """
    Advanced engine for comparing products across multiple stores.
    """
    
    def __init__(self):
        self.criteria_calculators = {
            'price': self._calculate_price_score,
            'rating': self._calculate_rating_score,
            'delivery': self._calculate_delivery_score,
            'reliability': self._calculate_reliability_score,
            'customer_service': self._calculate_customer_service_score,
            'return_policy': self._calculate_return_policy_score,
            'availability': self._calculate_availability_score,
            'brand_reputation': self._calculate_brand_reputation_score,
        }
    
    def compare_products(
        self, 
        product_ids: List[str], 
        criteria_weights: Optional[Dict[str, float]] = None,
        template_id: Optional[str] = None
    ) -> Dict:
        """
        Compare multiple products using specified criteria and weights.
        """
        # Get products
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True
        ).select_related('shop', 'brand', 'category')
        
        if not products.exists():
            raise ValueError("No valid products found for comparison")
        
        # Get criteria weights
        if template_id:
            criteria_weights = self._get_template_weights(template_id)
        elif not criteria_weights:
            criteria_weights = self._get_default_weights()
        
        # Calculate scores for each product
        product_scores = {}
        criteria_breakdown = {}
        
        for product in products:
            scores = {}
            for criteria_type, weight in criteria_weights.items():
                if criteria_type in self.criteria_calculators:
                    score = self.criteria_calculators[criteria_type](product)
                    scores[criteria_type] = {
                        'score': score,
                        'weight': weight,
                        'weighted_score': score * weight
                    }
            
            # Calculate overall score
            total_weighted_score = sum(s['weighted_score'] for s in scores.values())
            total_weight = sum(s['weight'] for s in scores.values())
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            
            product_scores[str(product.id)] = {
                'product_id': str(product.id),
                'product_name': product.name,
                'shop_name': product.shop.name,
                'overall_score': round(overall_score, 2),
                'criteria_scores': scores
            }
            
            criteria_breakdown[str(product.id)] = scores
        
        # Determine winner
        winner_id = max(product_scores.keys(), key=lambda x: product_scores[x]['overall_score'])
        winner_product = products.get(id=winner_id)
        
        # Identify best deals
        best_deals = self._identify_best_deals(products, product_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(products, product_scores)
        
        return {
            'products': list(product_scores.values()),
            'winner': {
                'product_id': winner_id,
                'product_name': winner_product.name,
                'shop_name': winner_product.shop.name,
                'overall_score': product_scores[winner_id]['overall_score']
            },
            'criteria_breakdown': criteria_breakdown,
            'best_deals': best_deals,
            'recommendations': recommendations,
            'criteria_weights': criteria_weights,
            'comparison_summary': self._generate_summary(products, product_scores)
        }
    
    def _calculate_price_score(self, product: Product) -> float:
        """Calculate price competitiveness score (0-10, higher is better)."""
        # Get recent price history for context
        recent_prices = PriceHistory.objects.filter(
            product__category=product.category,
            recorded_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('price', flat=True)
        
        if not recent_prices:
            return 5.0  # Neutral score if no comparison data
        
        avg_price = sum(recent_prices) / len(recent_prices)
        
        if avg_price == 0:
            return 5.0
        
        # Lower price gets higher score
        price_ratio = float(product.price) / float(avg_price)
        
        if price_ratio <= 0.7:  # 30% below average
            return 10.0
        elif price_ratio <= 0.85:  # 15% below average
            return 8.0
        elif price_ratio <= 1.0:  # At or below average
            return 6.0
        elif price_ratio <= 1.15:  # 15% above average
            return 4.0
        elif price_ratio <= 1.3:  # 30% above average
            return 2.0
        else:
            return 1.0
    
    def _calculate_rating_score(self, product: Product) -> float:
        """Calculate rating score (0-10, based on product rating)."""
        return float(product.rating) * 2  # Convert 0-5 to 0-10
    
    def _calculate_delivery_score(self, product: Product) -> float:
        """Calculate delivery score (0-10, faster is better)."""
        delivery_days = product.shop.average_delivery_days
        
        if delivery_days <= 1:
            return 10.0
        elif delivery_days <= 2:
            return 8.0
        elif delivery_days <= 3:
            return 6.0
        elif delivery_days <= 5:
            return 4.0
        elif delivery_days <= 7:
            return 2.0
        else:
            return 1.0
    
    def _calculate_reliability_score(self, product: Product) -> float:
        """Calculate store reliability score (0-10)."""
        return float(product.shop.reliability_score) * 2  # Convert 0-5 to 0-10
    
    def _calculate_customer_service_score(self, product: Product) -> float:
        """Calculate customer service score (0-10)."""
        return float(product.shop.customer_service_rating) * 2  # Convert 0-5 to 0-10
    
    def _calculate_return_policy_score(self, product: Product) -> float:
        """Calculate return policy score (0-10, longer is better)."""
        return_days = product.shop.return_policy_days
        
        if return_days >= 90:
            return 10.0
        elif return_days >= 60:
            return 8.0
        elif return_days >= 30:
            return 6.0
        elif return_days >= 14:
            return 4.0
        elif return_days >= 7:
            return 2.0
        else:
            return 1.0
    
    def _calculate_availability_score(self, product: Product) -> float:
        """Calculate availability score (0-10)."""
        if not product.is_active:
            return 0.0
        
        # Check recent availability from price history
        recent_availability = PriceHistory.objects.filter(
            product=product,
            recorded_at__gte=timezone.now() - timedelta(days=7)
        ).aggregate(
            avg_availability=Avg('is_available')
        )['avg_availability']
        
        if recent_availability is None:
            return 8.0 if product.is_active else 0.0
        
        return float(recent_availability) * 10
    
    def _calculate_brand_reputation_score(self, product: Product) -> float:
        """Calculate brand reputation score (0-10)."""
        if not product.brand:
            return 5.0  # Neutral for no brand
        
        # Combine brand rating and popularity
        brand_score = (
            float(product.brand.rating) * 0.6 +  # 60% weight on rating
            (float(product.brand.popularity) / 10) * 0.4  # 40% weight on popularity
        )
        
        return brand_score * 2  # Convert to 0-10 scale
    
    def _get_template_weights(self, template_id: str) -> Dict[str, float]:
        """Get criteria weights from a template."""
        try:
            template = ComparisonTemplate.objects.get(id=template_id)
            template_criteria = TemplateCriteria.objects.filter(
                template=template
            ).select_related('criteria')
            
            weights = {}
            for tc in template_criteria:
                weights[tc.criteria.criteria_type] = float(tc.get_effective_weight())
            
            return weights
        except ComparisonTemplate.DoesNotExist:
            return self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default criteria weights."""
        return {
            'price': 3.0,
            'rating': 2.5,
            'delivery': 2.0,
            'reliability': 2.0,
            'customer_service': 1.5,
            'return_policy': 1.0,
            'availability': 2.5,
            'brand_reputation': 1.5
        }
    
    def _identify_best_deals(self, products, product_scores: Dict) -> List[Dict]:
        """Identify the best deals considering price and quality."""
        deals = []
        
        for product in products:
            product_id = str(product.id)
            score_data = product_scores[product_id]
            
            # Calculate value score (quality per dollar)
            price = float(product.price)
            quality_score = score_data['overall_score']
            
            if price > 0:
                value_score = quality_score / (price / 100)  # Normalize price
                
                deals.append({
                    'product_id': product_id,
                    'product_name': product.name,
                    'shop_name': product.shop.name,
                    'price': price,
                    'quality_score': quality_score,
                    'value_score': round(value_score, 2),
                    'savings_vs_highest': 0,  # Will be calculated below
                    'deal_type': 'standard'
                })
        
        # Calculate savings vs highest price
        if deals:
            highest_price = max(deal['price'] for deal in deals)
            for deal in deals:
                deal['savings_vs_highest'] = round(highest_price - deal['price'], 2)
                
                # Classify deal types
                if deal['value_score'] >= 8 and deal['savings_vs_highest'] > 0:
                    deal['deal_type'] = 'excellent_value'
                elif deal['price'] == min(d['price'] for d in deals):
                    deal['deal_type'] = 'lowest_price'
                elif deal['quality_score'] >= 8:
                    deal['deal_type'] = 'premium_quality'
        
        # Sort by value score
        deals.sort(key=lambda x: x['value_score'], reverse=True)
        
        return deals[:5]  # Return top 5 deals
    
    def _generate_recommendations(self, products, product_scores: Dict) -> List[str]:
        """Generate textual recommendations based on comparison results."""
        recommendations = []
        
        # Find best in each category
        best_price = min(products, key=lambda p: p.price)
        best_rated = max(products, key=lambda p: p.rating)
        best_delivery = min(products, key=lambda p: p.shop.average_delivery_days)
        
        recommendations.append(
            f"💰 Best Price: {best_price.name} at {best_price.shop.name} for ${best_price.price}"
        )
        
        recommendations.append(
            f"⭐ Highest Rated: {best_rated.name} with {best_rated.rating}/5 stars"
        )
        
        recommendations.append(
            f"🚚 Fastest Delivery: {best_delivery.name} from {best_delivery.shop.name} "
            f"({best_delivery.shop.average_delivery_days} days)"
        )
        
        # Overall recommendation
        winner_id = max(product_scores.keys(), key=lambda x: product_scores[x]['overall_score'])
        winner = products.get(id=winner_id)
        
        recommendations.append(
            f"🏆 Overall Best Choice: {winner.name} from {winner.shop.name} "
            f"(Score: {product_scores[winner_id]['overall_score']}/10)"
        )
        
        return recommendations
    
    def _generate_summary(self, products, product_scores: Dict) -> Dict:
        """Generate comparison summary statistics."""
        prices = [float(p.price) for p in products]
        scores = [data['overall_score'] for data in product_scores.values()]
        
        return {
            'total_products': len(products),
            'price_range': {
                'min': min(prices),
                'max': max(prices),
                'average': round(sum(prices) / len(prices), 2)
            },
            'score_range': {
                'min': min(scores),
                'max': max(scores),
                'average': round(sum(scores) / len(scores), 2)
            },
            'stores_involved': len(set(p.shop.name for p in products)),
            'categories_involved': len(set(p.category.name for p in products))
        }
