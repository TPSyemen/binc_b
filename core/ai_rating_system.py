"""
core/ai_rating_system.py
------------------------
AI-driven product rating system that combines multiple data sources for intelligent scoring.
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Product, Shop, Brand
from reviews.models import Review, StoreReview, ProductEngagement, EngagementEvent
from reviews.services import SentimentAnalysisService
import math

logger = logging.getLogger(__name__)


class AIProductRatingSystem:
    """
    Comprehensive AI-driven product rating system that analyzes multiple factors
    to generate intelligent product scores and rankings.
    """
    
    def __init__(self):
        self.sentiment_service = SentimentAnalysisService()
        
        # Weights for different rating components (must sum to 1.0)
        self.weights = {
            'customer_reviews': 0.25,      # Customer review ratings and sentiment
            'engagement_metrics': 0.20,    # User engagement (views, likes, etc.)
            'store_reliability': 0.15,     # Store performance and reliability
            'brand_reputation': 0.10,      # Brand reputation and popularity
            'price_competitiveness': 0.10, # Price compared to similar products
            'availability_score': 0.10,    # Product availability and stock
            'historical_performance': 0.10 # Historical sales and performance
        }
    
    def calculate_ai_rating(self, product: Product, recalculate: bool = False) -> Dict:
        """
        Calculate comprehensive AI rating for a product.
        
        Args:
            product: Product instance to rate
            recalculate: Whether to force recalculation even if recent rating exists
            
        Returns:
            Dict containing overall rating and component breakdowns
        """
        try:
            # Check if we need to recalculate
            if not recalculate and self._has_recent_rating(product):
                return self._get_cached_rating(product)
            
            # Calculate individual components
            components = {
                'customer_reviews': self._calculate_review_score(product),
                'engagement_metrics': self._calculate_engagement_score(product),
                'store_reliability': self._calculate_store_score(product),
                'brand_reputation': self._calculate_brand_score(product),
                'price_competitiveness': self._calculate_price_score(product),
                'availability_score': self._calculate_availability_score(product),
                'historical_performance': self._calculate_historical_score(product)
            }
            
            # Calculate weighted overall score
            overall_score = sum(
                components[component] * self.weights[component]
                for component in components
            )
            
            # Normalize to 0-5 scale
            final_rating = max(0.0, min(5.0, overall_score))
            
            # Create rating breakdown
            rating_data = {
                'overall_rating': round(final_rating, 2),
                'components': {
                    component: {
                        'score': round(score, 2),
                        'weight': self.weights[component],
                        'weighted_contribution': round(score * self.weights[component], 2)
                    }
                    for component, score in components.items()
                },
                'confidence_level': self._calculate_confidence(components),
                'last_calculated': timezone.now(),
                'data_points_used': self._count_data_points(product),
                'recommendations': self._generate_improvement_recommendations(components)
            }
            
            # Update product rating
            product.rating = Decimal(str(final_rating))
            product.save()
            
            # Cache the rating data (you might want to store this in a separate model)
            self._cache_rating_data(product, rating_data)
            
            return rating_data
            
        except Exception as e:
            logger.error(f"Error calculating AI rating for product {product.id}: {e}")
            return {
                'overall_rating': float(product.rating) if product.rating else 3.0,
                'error': str(e),
                'fallback': True
            }
    
    def _calculate_review_score(self, product: Product) -> float:
        """
        Calculate score based on customer reviews and sentiment analysis.
        """
        try:
            reviews = Review.objects.filter(product=product, status='approved')
            
            if not reviews.exists():
                return 3.0  # Neutral score for no reviews
            
            # Basic rating average
            avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 3.0
            
            # Sentiment analysis boost/penalty
            sentiment_scores = []
            for review in reviews:
                if review.sentiment_score is not None:
                    sentiment_scores.append(float(review.sentiment_score))
                else:
                    # Calculate sentiment if not already done
                    sentiment_data = self.sentiment_service.analyze_review(review)
                    sentiment_scores.append(sentiment_data['score'])
            
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                # Convert sentiment (-1 to 1) to rating adjustment (-1 to 1)
                sentiment_adjustment = avg_sentiment * 0.5
            else:
                sentiment_adjustment = 0
            
            # Verified purchase bonus
            verified_count = reviews.filter(verified_purchase=True).count()
            verified_ratio = verified_count / reviews.count()
            verified_bonus = verified_ratio * 0.2  # Up to 0.2 bonus
            
            # Review helpfulness factor
            helpful_reviews = reviews.filter(helpfulness_score__gt=0).count()
            helpfulness_ratio = helpful_reviews / reviews.count() if reviews.count() > 0 else 0
            helpfulness_bonus = helpfulness_ratio * 0.1  # Up to 0.1 bonus
            
            # Combine factors
            final_score = avg_rating + sentiment_adjustment + verified_bonus + helpfulness_bonus
            
            return max(0.0, min(5.0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating review score: {e}")
            return 3.0
    
    def _calculate_engagement_score(self, product: Product) -> float:
        """
        Calculate score based on user engagement metrics.
        """
        try:
            engagement = ProductEngagement.objects.filter(product=product).first()
            
            if not engagement:
                return 2.5  # Below average for no engagement data
            
            # Normalize metrics to 0-5 scale
            view_score = min(5.0, math.log10(max(1, engagement.total_views)) / 2)
            like_ratio = engagement.total_likes / max(1, engagement.total_likes + engagement.total_dislikes)
            like_score = like_ratio * 5.0
            
            conversion_score = min(5.0, engagement.conversion_rate / 10)  # 10% conversion = 5.0
            share_score = min(5.0, math.log10(max(1, engagement.total_shares)))
            
            # Weighted combination
            engagement_score = (
                view_score * 0.3 +
                like_score * 0.4 +
                conversion_score * 0.2 +
                share_score * 0.1
            )
            
            return max(0.0, min(5.0, engagement_score))
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 2.5
    
    def _calculate_store_score(self, product: Product) -> float:
        """
        Calculate score based on store reliability and performance.
        """
        try:
            shop = product.shop
            
            # Base reliability score
            reliability = float(shop.reliability_score)
            
            # Customer service rating
            service_rating = float(shop.customer_service_rating)
            
            # Delivery performance (faster = better)
            delivery_score = max(0, 5 - (shop.average_delivery_days - 1) * 0.5)
            delivery_score = min(5.0, delivery_score)
            
            # Return policy (longer = better, up to a point)
            return_score = min(5.0, shop.return_policy_days / 30 * 5)
            
            # Store review sentiment
            store_reviews = StoreReview.objects.filter(shop=shop)
            if store_reviews.exists():
                avg_store_rating = store_reviews.aggregate(
                    avg_rating=Avg('overall_rating')
                )['avg_rating'] or 3.0
            else:
                avg_store_rating = reliability  # Fallback to reliability score
            
            # Weighted combination
            store_score = (
                reliability * 0.3 +
                service_rating * 0.2 +
                delivery_score * 0.2 +
                return_score * 0.1 +
                avg_store_rating * 0.2
            )
            
            return max(0.0, min(5.0, store_score))
            
        except Exception as e:
            logger.error(f"Error calculating store score: {e}")
            return 3.0
    
    def _calculate_brand_score(self, product: Product) -> float:
        """
        Calculate score based on brand reputation and popularity.
        """
        try:
            if not product.brand:
                return 3.0  # Neutral for no brand
            
            brand = product.brand
            
            # Brand rating and popularity
            brand_rating = float(brand.rating)
            brand_popularity = float(brand.popularity) / 20  # Normalize to 0-5 scale
            
            # Brand product performance
            brand_products = Product.objects.filter(brand=brand, is_active=True)
            if brand_products.exists():
                avg_brand_rating = brand_products.aggregate(
                    avg_rating=Avg('rating')
                )['avg_rating'] or 3.0
                avg_brand_rating = float(avg_brand_rating)
            else:
                avg_brand_rating = brand_rating
            
            # Brand review sentiment
            brand_reviews = Review.objects.filter(
                product__brand=brand,
                status='approved'
            )
            
            if brand_reviews.exists():
                avg_sentiment = brand_reviews.aggregate(
                    avg_sentiment=Avg('sentiment_score')
                )['avg_sentiment']
                
                if avg_sentiment is not None:
                    # Convert sentiment (-1 to 1) to 0-5 scale
                    sentiment_score = (float(avg_sentiment) + 1) * 2.5
                else:
                    sentiment_score = 3.0
            else:
                sentiment_score = 3.0
            
            # Weighted combination
            brand_score = (
                brand_rating * 0.4 +
                brand_popularity * 0.2 +
                avg_brand_rating * 0.3 +
                sentiment_score * 0.1
            )
            
            return max(0.0, min(5.0, brand_score))
            
        except Exception as e:
            logger.error(f"Error calculating brand score: {e}")
            return 3.0
    
    def _calculate_price_score(self, product: Product) -> float:
        """
        Calculate score based on price competitiveness.
        """
        try:
            # Get similar products in the same category
            similar_products = Product.objects.filter(
                category=product.category,
                is_active=True
            ).exclude(id=product.id)
            
            if not similar_products.exists():
                return 3.0  # Neutral if no comparison products
            
            # Calculate price percentile
            prices = list(similar_products.values_list('price', flat=True))
            prices.append(product.price)
            prices.sort()
            
            product_price_rank = prices.index(product.price)
            percentile = (len(prices) - product_price_rank - 1) / (len(prices) - 1)
            
            # Lower price = higher score (inverted percentile)
            price_score = percentile * 5.0
            
            # Bonus for having original_price (discount indication)
            if product.original_price and product.original_price > product.price:
                discount_ratio = (product.original_price - product.price) / product.original_price
                discount_bonus = min(1.0, discount_ratio * 2)  # Up to 1.0 bonus
                price_score += discount_bonus
            
            return max(0.0, min(5.0, price_score))
            
        except Exception as e:
            logger.error(f"Error calculating price score: {e}")
            return 3.0

    def _calculate_availability_score(self, product: Product) -> float:
        """
        Calculate score based on product availability and stock status.
        """
        try:
            if not product.is_active:
                return 0.0

            # Base availability score
            availability_score = 5.0 if product.is_active else 0.0

            # Check recent availability from price history
            from store_integration.models import PriceHistory

            recent_prices = PriceHistory.objects.filter(
                product=product,
                recorded_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-recorded_at')[:10]

            if recent_prices.exists():
                available_count = recent_prices.filter(is_available=True).count()
                availability_ratio = available_count / recent_prices.count()
                availability_score *= availability_ratio

            # Stock quantity bonus if available
            if hasattr(product, 'stock_quantity') and product.stock_quantity:
                if product.stock_quantity > 10:
                    stock_bonus = 0.5
                elif product.stock_quantity > 5:
                    stock_bonus = 0.3
                elif product.stock_quantity > 0:
                    stock_bonus = 0.1
                else:
                    stock_bonus = -1.0

                availability_score += stock_bonus

            return max(0.0, min(5.0, availability_score))

        except Exception as e:
            logger.error(f"Error calculating availability score: {e}")
            return 3.0

    def _calculate_historical_score(self, product: Product) -> float:
        """
        Calculate score based on historical performance and trends.
        """
        try:
            # View trends (last 30 days vs previous 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            sixty_days_ago = timezone.now() - timedelta(days=60)

            recent_views = EngagementEvent.objects.filter(
                product=product,
                event_type='product_view',
                timestamp__gte=thirty_days_ago
            ).count()

            previous_views = EngagementEvent.objects.filter(
                product=product,
                event_type='product_view',
                timestamp__gte=sixty_days_ago,
                timestamp__lt=thirty_days_ago
            ).count()

            # Calculate trend
            if previous_views > 0:
                view_trend = (recent_views - previous_views) / previous_views
            else:
                view_trend = 1.0 if recent_views > 0 else 0.0

            # Purchase trends
            recent_purchases = EngagementEvent.objects.filter(
                product=product,
                event_type='purchase_completed',
                timestamp__gte=thirty_days_ago
            ).count()

            previous_purchases = EngagementEvent.objects.filter(
                product=product,
                event_type='purchase_completed',
                timestamp__gte=sixty_days_ago,
                timestamp__lt=thirty_days_ago
            ).count()

            if previous_purchases > 0:
                purchase_trend = (recent_purchases - previous_purchases) / previous_purchases
            else:
                purchase_trend = 1.0 if recent_purchases > 0 else 0.0

            # Product age factor (newer products get slight bonus)
            product_age_days = (timezone.now() - product.created_at).days
            if product_age_days < 30:
                age_bonus = 0.5
            elif product_age_days < 90:
                age_bonus = 0.2
            else:
                age_bonus = 0.0

            # Combine factors
            base_score = 3.0
            trend_score = (view_trend + purchase_trend) / 2

            # Convert trend to score adjustment
            if trend_score > 0.5:
                trend_adjustment = 1.0
            elif trend_score > 0.1:
                trend_adjustment = 0.5
            elif trend_score > -0.1:
                trend_adjustment = 0.0
            elif trend_score > -0.5:
                trend_adjustment = -0.5
            else:
                trend_adjustment = -1.0

            historical_score = base_score + trend_adjustment + age_bonus

            return max(0.0, min(5.0, historical_score))

        except Exception as e:
            logger.error(f"Error calculating historical score: {e}")
            return 3.0

    def _calculate_confidence(self, components: Dict) -> float:
        """
        Calculate confidence level of the AI rating based on available data.
        """
        try:
            # Confidence factors
            confidence_factors = []

            # Review confidence (based on number of reviews)
            review_count = Review.objects.filter(
                product__id=components.get('product_id'),
                status='approved'
            ).count()

            if review_count >= 20:
                confidence_factors.append(1.0)
            elif review_count >= 10:
                confidence_factors.append(0.8)
            elif review_count >= 5:
                confidence_factors.append(0.6)
            elif review_count >= 1:
                confidence_factors.append(0.4)
            else:
                confidence_factors.append(0.2)

            # Engagement confidence (based on total interactions)
            # This would need to be calculated based on actual engagement data
            confidence_factors.append(0.7)  # Placeholder

            # Store confidence (established stores = higher confidence)
            confidence_factors.append(0.8)  # Placeholder

            # Overall confidence is the average
            overall_confidence = sum(confidence_factors) / len(confidence_factors)

            return round(overall_confidence, 2)

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _count_data_points(self, product: Product) -> Dict:
        """
        Count available data points for transparency.
        """
        try:
            return {
                'reviews': Review.objects.filter(product=product, status='approved').count(),
                'engagement_events': EngagementEvent.objects.filter(product=product).count(),
                'price_history_records': 0,  # Would need to import and count
                'store_reviews': StoreReview.objects.filter(shop=product.shop).count(),
                'similar_products': Product.objects.filter(
                    category=product.category,
                    is_active=True
                ).exclude(id=product.id).count()
            }
        except Exception as e:
            logger.error(f"Error counting data points: {e}")
            return {}

    def _generate_improvement_recommendations(self, components: Dict) -> List[str]:
        """
        Generate recommendations for improving product rating.
        """
        recommendations = []

        try:
            # Analyze weak components
            sorted_components = sorted(components.items(), key=lambda x: x[1])

            for component, score in sorted_components[:3]:  # Bottom 3 components
                if score < 3.0:
                    if component == 'customer_reviews':
                        recommendations.append(
                            "Encourage more customer reviews and address negative feedback"
                        )
                    elif component == 'engagement_metrics':
                        recommendations.append(
                            "Improve product visibility and marketing to increase engagement"
                        )
                    elif component == 'store_reliability':
                        recommendations.append(
                            "Focus on improving store reliability and customer service"
                        )
                    elif component == 'brand_reputation':
                        recommendations.append(
                            "Build brand reputation through quality and customer satisfaction"
                        )
                    elif component == 'price_competitiveness':
                        recommendations.append(
                            "Consider price optimization or highlight value proposition"
                        )
                    elif component == 'availability_score':
                        recommendations.append(
                            "Ensure consistent product availability and stock management"
                        )
                    elif component == 'historical_performance':
                        recommendations.append(
                            "Focus on marketing and promotion to improve sales trends"
                        )

            if not recommendations:
                recommendations.append("Product is performing well across all metrics")

            return recommendations[:5]  # Limit to top 5 recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations at this time"]

    def _has_recent_rating(self, product: Product) -> bool:
        """
        Check if product has a recent AI rating calculation.
        """
        # This would check a cache or rating history table
        # For now, return False to always recalculate
        return False

    def _get_cached_rating(self, product: Product) -> Dict:
        """
        Get cached rating data for a product.
        """
        # This would retrieve cached rating data
        # For now, return empty dict
        return {}

    def _cache_rating_data(self, product: Product, rating_data: Dict):
        """
        Cache rating data for future use.
        """
        # This would store rating data in cache or database
        # For now, just log
        logger.info(f"Caching rating data for product {product.id}: {rating_data['overall_rating']}")

    def bulk_calculate_ratings(self, products: List[Product] = None) -> Dict:
        """
        Calculate AI ratings for multiple products in bulk.
        """
        if products is None:
            products = Product.objects.filter(is_active=True)

        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        for product in products:
            try:
                rating_data = self.calculate_ai_rating(product, recalculate=True)
                if 'error' not in rating_data:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'product_id': str(product.id),
                        'error': rating_data['error']
                    })
                results['processed'] += 1

            except Exception as e:
                results['failed'] += 1
                results['processed'] += 1
                results['errors'].append({
                    'product_id': str(product.id),
                    'error': str(e)
                })
                logger.error(f"Error processing product {product.id}: {e}")

        return results


# Create singleton instance
ai_rating_system = AIProductRatingSystem()
