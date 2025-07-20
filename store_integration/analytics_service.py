"""
store_integration/analytics_service.py
-------------------------------------
Comprehensive analytics service for tracking store performance, reliability, and customer satisfaction.
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Avg, Count, Sum, Q, F, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from .models import StoreIntegrationConfig, PriceHistory, SyncLog, ProductMapping
from reviews.models import StoreReview, Review, EngagementEvent
from core.models import Shop, Product
import statistics

logger = logging.getLogger(__name__)


class StorePerformanceAnalyticsService:
    """
    Service for comprehensive store performance analytics and reliability scoring.
    """
    
    def __init__(self):
        self.performance_weights = {
            'reliability_score': 0.25,      # Technical reliability
            'customer_satisfaction': 0.30,  # Customer reviews and ratings
            'delivery_performance': 0.20,   # Delivery speed and accuracy
            'price_competitiveness': 0.15,  # Price comparison with competitors
            'product_availability': 0.10    # Stock availability and consistency
        }
    
    def calculate_store_performance(self, shop_id: str, days: int = 30) -> Dict:
        """
        Calculate comprehensive store performance metrics.
        
        Args:
            shop_id: Shop ID to analyze
            days: Number of days to analyze (default 30)
            
        Returns:
            Dict containing performance metrics and scores
        """
        try:
            shop = Shop.objects.get(id=shop_id)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Calculate individual performance components
            reliability_metrics = self._calculate_reliability_metrics(shop, start_date, end_date)
            satisfaction_metrics = self._calculate_satisfaction_metrics(shop, start_date, end_date)
            delivery_metrics = self._calculate_delivery_metrics(shop, start_date, end_date)
            price_metrics = self._calculate_price_competitiveness(shop, start_date, end_date)
            availability_metrics = self._calculate_availability_metrics(shop, start_date, end_date)
            
            # Calculate weighted overall score
            component_scores = {
                'reliability_score': reliability_metrics['score'],
                'customer_satisfaction': satisfaction_metrics['score'],
                'delivery_performance': delivery_metrics['score'],
                'price_competitiveness': price_metrics['score'],
                'product_availability': availability_metrics['score']
            }
            
            overall_score = sum(
                component_scores[component] * self.performance_weights[component]
                for component in component_scores
            )
            
            # Generate performance insights
            insights = self._generate_performance_insights(component_scores, shop)
            
            # Calculate trends
            trends = self._calculate_performance_trends(shop, days)
            
            return {
                'success': True,
                'shop_id': shop_id,
                'shop_name': shop.name,
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'overall_score': round(overall_score, 2),
                'component_scores': {
                    component: {
                        'score': round(score, 2),
                        'weight': self.performance_weights[component],
                        'weighted_contribution': round(score * self.performance_weights[component], 2)
                    }
                    for component, score in component_scores.items()
                },
                'detailed_metrics': {
                    'reliability': reliability_metrics,
                    'customer_satisfaction': satisfaction_metrics,
                    'delivery_performance': delivery_metrics,
                    'price_competitiveness': price_metrics,
                    'product_availability': availability_metrics
                },
                'performance_insights': insights,
                'trends': trends,
                'last_calculated': timezone.now().isoformat()
            }
            
        except Shop.DoesNotExist:
            return {
                'success': False,
                'error': f'Shop {shop_id} not found'
            }
        except Exception as e:
            logger.error(f"Error calculating store performance for {shop_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_reliability_metrics(self, shop: Shop, start_date: datetime, end_date: datetime) -> Dict:
        """
        Calculate technical reliability metrics.
        """
        try:
            # Get integration config for this shop
            config = StoreIntegrationConfig.objects.filter(shop=shop, is_active=True).first()
            
            if not config:
                return {
                    'score': 5.0,  # Default score if no integration
                    'sync_success_rate': 100.0,
                    'uptime_percentage': 100.0,
                    'error_rate': 0.0,
                    'message': 'No integration data available'
                }
            
            # Get sync logs for the period
            sync_logs = SyncLog.objects.filter(
                integration_config=config,
                started_at__gte=start_date,
                started_at__lte=end_date
            )
            
            if not sync_logs.exists():
                return {
                    'score': 5.0,
                    'sync_success_rate': 100.0,
                    'uptime_percentage': 100.0,
                    'error_rate': 0.0,
                    'message': 'No sync activity in period'
                }
            
            # Calculate sync success rate
            total_syncs = sync_logs.count()
            successful_syncs = sync_logs.filter(status='completed').count()
            sync_success_rate = (successful_syncs / total_syncs) * 100 if total_syncs > 0 else 100
            
            # Calculate error rate
            failed_syncs = sync_logs.filter(status='failed').count()
            error_rate = (failed_syncs / total_syncs) * 100 if total_syncs > 0 else 0
            
            # Calculate average sync duration
            completed_syncs = sync_logs.filter(
                status='completed',
                completed_at__isnull=False
            )
            
            avg_sync_duration = 0
            if completed_syncs.exists():
                durations = []
                for log in completed_syncs:
                    if log.completed_at and log.started_at:
                        duration = (log.completed_at - log.started_at).total_seconds()
                        durations.append(duration)
                
                if durations:
                    avg_sync_duration = statistics.mean(durations)
            
            # Calculate reliability score (0-5 scale)
            reliability_score = 5.0
            
            # Penalize for low success rate
            if sync_success_rate < 95:
                reliability_score -= (95 - sync_success_rate) * 0.05
            
            # Penalize for high error rate
            if error_rate > 5:
                reliability_score -= (error_rate - 5) * 0.02
            
            # Penalize for slow syncs (>5 minutes)
            if avg_sync_duration > 300:
                reliability_score -= min((avg_sync_duration - 300) / 300, 1.0)
            
            reliability_score = max(0.0, min(5.0, reliability_score))
            
            return {
                'score': reliability_score,
                'sync_success_rate': round(sync_success_rate, 2),
                'error_rate': round(error_rate, 2),
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'average_sync_duration_seconds': round(avg_sync_duration, 2),
                'uptime_percentage': round(sync_success_rate, 2)  # Simplified uptime calculation
            }
            
        except Exception as e:
            logger.error(f"Error calculating reliability metrics: {e}")
            return {
                'score': 3.0,  # Default middle score on error
                'error': str(e)
            }
    
    def _calculate_satisfaction_metrics(self, shop: Shop, start_date: datetime, end_date: datetime) -> Dict:
        """
        Calculate customer satisfaction metrics.
        """
        try:
            # Get store reviews for the period
            store_reviews = StoreReview.objects.filter(
                shop=shop,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Get product reviews for products from this shop
            product_reviews = Review.objects.filter(
                product__shop=shop,
                created_at__gte=start_date,
                created_at__lte=end_date,
                status='approved'
            )
            
            # Calculate store review metrics
            store_metrics = {
                'total_store_reviews': store_reviews.count(),
                'average_overall_rating': 0.0,
                'average_delivery_rating': 0.0,
                'average_service_rating': 0.0,
                'average_quality_rating': 0.0
            }
            
            if store_reviews.exists():
                store_aggregates = store_reviews.aggregate(
                    avg_overall=Avg('overall_rating'),
                    avg_delivery=Avg('delivery_rating'),
                    avg_service=Avg('customer_service_rating'),
                    avg_quality=Avg('product_quality_rating')
                )
                
                store_metrics.update({
                    'average_overall_rating': float(store_aggregates['avg_overall'] or 0),
                    'average_delivery_rating': float(store_aggregates['avg_delivery'] or 0),
                    'average_service_rating': float(store_aggregates['avg_service'] or 0),
                    'average_quality_rating': float(store_aggregates['avg_quality'] or 0)
                })
            
            # Calculate product review metrics
            product_metrics = {
                'total_product_reviews': product_reviews.count(),
                'average_product_rating': 0.0,
                'positive_sentiment_percentage': 0.0
            }
            
            if product_reviews.exists():
                product_aggregates = product_reviews.aggregate(
                    avg_rating=Avg('rating')
                )
                product_metrics['average_product_rating'] = float(product_aggregates['avg_rating'] or 0)
                
                # Calculate sentiment distribution
                positive_reviews = product_reviews.filter(sentiment_label='positive').count()
                if product_reviews.count() > 0:
                    product_metrics['positive_sentiment_percentage'] = (positive_reviews / product_reviews.count()) * 100
            
            # Calculate overall satisfaction score
            satisfaction_score = 0.0
            
            if store_reviews.exists():
                # Weight store ratings more heavily
                satisfaction_score = store_metrics['average_overall_rating'] * 0.6
                satisfaction_score += store_metrics['average_service_rating'] * 0.4
            elif product_reviews.exists():
                # Fallback to product ratings
                satisfaction_score = product_metrics['average_product_rating']
            else:
                # No reviews available, use shop's base rating
                satisfaction_score = float(shop.reliability_score)
            
            return {
                'score': satisfaction_score,
                'store_reviews': store_metrics,
                'product_reviews': product_metrics,
                'total_reviews': store_metrics['total_store_reviews'] + product_metrics['total_product_reviews']
            }
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction metrics: {e}")
            return {
                'score': 3.0,
                'error': str(e)
            }

    def _calculate_price_competitiveness(self, shop: Shop, start_date: datetime, end_date: datetime) -> Dict:
        """
        Calculate price competitiveness metrics.
        """
        try:
            # Get products from this shop
            shop_products = Product.objects.filter(shop=shop, is_active=True)

            if not shop_products.exists():
                return {
                    'score': 3.0,
                    'message': 'No products found for price comparison'
                }

            competitive_scores = []
            price_comparisons = []

            for product in shop_products[:50]:  # Limit to 50 products for performance
                # Get price history for this product from other shops
                other_prices = PriceHistory.objects.filter(
                    product=product,
                    recorded_at__gte=start_date,
                    recorded_at__lte=end_date,
                    is_available=True
                ).exclude(shop=shop).values('shop').annotate(
                    avg_price=Avg('price')
                )

                if other_prices.exists():
                    # Get current price from our shop
                    current_price = PriceHistory.objects.filter(
                        product=product,
                        shop=shop,
                        is_available=True
                    ).first()

                    if current_price:
                        competitor_prices = [float(p['avg_price']) for p in other_prices]
                        our_price = float(current_price.price)

                        if competitor_prices:
                            avg_competitor_price = statistics.mean(competitor_prices)
                            min_competitor_price = min(competitor_prices)

                            # Calculate competitiveness score
                            if our_price <= min_competitor_price:
                                score = 5.0  # Best price
                            elif our_price <= avg_competitor_price:
                                score = 4.0  # Better than average
                            elif our_price <= avg_competitor_price * 1.1:
                                score = 3.0  # Close to average
                            elif our_price <= avg_competitor_price * 1.2:
                                score = 2.0  # Above average
                            else:
                                score = 1.0  # Significantly higher

                            competitive_scores.append(score)
                            price_comparisons.append({
                                'product_id': str(product.id),
                                'product_name': product.name,
                                'our_price': our_price,
                                'avg_competitor_price': round(avg_competitor_price, 2),
                                'min_competitor_price': round(min_competitor_price, 2),
                                'competitiveness_score': score
                            })

            # Calculate overall price competitiveness
            if competitive_scores:
                overall_score = statistics.mean(competitive_scores)

                return {
                    'score': round(overall_score, 2),
                    'products_compared': len(competitive_scores),
                    'average_competitiveness': round(overall_score, 2),
                    'price_comparisons': price_comparisons[:10],  # Return top 10 for display
                    'competitive_products_percentage': (
                        len([s for s in competitive_scores if s >= 4.0]) / len(competitive_scores) * 100
                    )
                }
            else:
                return {
                    'score': 3.0,
                    'message': 'No price comparisons available'
                }

        except Exception as e:
            logger.error(f"Error calculating price competitiveness: {e}")
            return {
                'score': 3.0,
                'error': str(e)
            }

    def _calculate_availability_metrics(self, shop: Shop, start_date: datetime, end_date: datetime) -> Dict:
        """
        Calculate product availability metrics.
        """
        try:
            # Get price history records for this shop (which include availability)
            availability_records = PriceHistory.objects.filter(
                shop=shop,
                recorded_at__gte=start_date,
                recorded_at__lte=end_date
            )

            if not availability_records.exists():
                return {
                    'score': 3.0,
                    'message': 'No availability data found'
                }

            # Calculate availability metrics
            total_records = availability_records.count()
            available_records = availability_records.filter(is_available=True).count()
            availability_percentage = (available_records / total_records) * 100 if total_records > 0 else 0

            # Calculate stock consistency
            products_with_stock = availability_records.filter(
                stock_quantity__gt=0
            ).values('product').distinct().count()

            total_products = availability_records.values('product').distinct().count()
            stock_consistency = (products_with_stock / total_products) * 100 if total_products > 0 else 0

            # Calculate availability score
            availability_score = 5.0

            if availability_percentage < 90:
                availability_score -= (90 - availability_percentage) * 0.05

            if stock_consistency < 80:
                availability_score -= (80 - stock_consistency) * 0.02

            availability_score = max(0.0, min(5.0, availability_score))

            return {
                'score': round(availability_score, 2),
                'availability_percentage': round(availability_percentage, 2),
                'stock_consistency_percentage': round(stock_consistency, 2),
                'total_availability_checks': total_records,
                'products_monitored': total_products
            }

        except Exception as e:
            logger.error(f"Error calculating availability metrics: {e}")
            return {
                'score': 3.0,
                'error': str(e)
            }

    def _generate_performance_insights(self, component_scores: Dict, shop: Shop) -> List[str]:
        """
        Generate actionable insights based on performance scores.
        """
        insights = []

        # Reliability insights
        if component_scores['reliability_score'] < 3.0:
            insights.append("Technical reliability needs improvement. Consider optimizing API integration and sync processes.")
        elif component_scores['reliability_score'] > 4.5:
            insights.append("Excellent technical reliability. Integration is performing optimally.")

        # Customer satisfaction insights
        if component_scores['customer_satisfaction'] < 3.0:
            insights.append("Customer satisfaction is below average. Focus on improving service quality and addressing customer concerns.")
        elif component_scores['customer_satisfaction'] > 4.5:
            insights.append("Outstanding customer satisfaction. Continue maintaining high service standards.")

        # Delivery performance insights
        if component_scores['delivery_performance'] < 3.0:
            insights.append("Delivery performance needs attention. Consider optimizing logistics and setting realistic delivery expectations.")
        elif component_scores['delivery_performance'] > 4.5:
            insights.append("Excellent delivery performance. Fast and reliable delivery is a competitive advantage.")

        # Price competitiveness insights
        if component_scores['price_competitiveness'] < 3.0:
            insights.append("Prices are less competitive compared to other stores. Consider price optimization strategies.")
        elif component_scores['price_competitiveness'] > 4.5:
            insights.append("Highly competitive pricing. This is a strong selling point for customers.")

        # Availability insights
        if component_scores['product_availability'] < 3.0:
            insights.append("Product availability issues detected. Improve inventory management and stock monitoring.")
        elif component_scores['product_availability'] > 4.5:
            insights.append("Excellent product availability. Consistent stock levels enhance customer experience.")

        # Overall performance insights
        overall_avg = sum(component_scores.values()) / len(component_scores)
        if overall_avg > 4.0:
            insights.append("Overall performance is excellent. This store is highly recommended for customers.")
        elif overall_avg < 3.0:
            insights.append("Overall performance needs improvement across multiple areas. Consider a comprehensive review of operations.")

        return insights

    def _calculate_performance_trends(self, shop: Shop, days: int) -> Dict:
        """
        Calculate performance trends over time.
        """
        try:
            # Compare current period with previous period
            current_end = timezone.now()
            current_start = current_end - timedelta(days=days)
            previous_end = current_start
            previous_start = previous_end - timedelta(days=days)

            # Get basic metrics for both periods
            current_metrics = self._get_basic_metrics(shop, current_start, current_end)
            previous_metrics = self._get_basic_metrics(shop, previous_start, previous_end)

            # Calculate trends
            trends = {}
            for metric in current_metrics:
                current_value = current_metrics[metric]
                previous_value = previous_metrics.get(metric, 0)

                if previous_value > 0:
                    change_percentage = ((current_value - previous_value) / previous_value) * 100
                    trends[metric] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change_percentage': round(change_percentage, 2),
                        'trend': 'improving' if change_percentage > 0 else 'declining' if change_percentage < 0 else 'stable'
                    }
                else:
                    trends[metric] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change_percentage': 0,
                        'trend': 'new_data'
                    }

            return trends

        except Exception as e:
            logger.error(f"Error calculating performance trends: {e}")
            return {}

    def _get_basic_metrics(self, shop: Shop, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get basic metrics for a time period.
        """
        try:
            # Store reviews
            store_reviews = StoreReview.objects.filter(
                shop=shop,
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # Product reviews
            product_reviews = Review.objects.filter(
                product__shop=shop,
                created_at__gte=start_date,
                created_at__lte=end_date,
                status='approved'
            )

            # Sync logs
            config = StoreIntegrationConfig.objects.filter(shop=shop, is_active=True).first()
            sync_logs = SyncLog.objects.filter(
                integration_config=config,
                started_at__gte=start_date,
                started_at__lte=end_date
            ) if config else SyncLog.objects.none()

            return {
                'store_reviews_count': store_reviews.count(),
                'average_store_rating': float(store_reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0),
                'product_reviews_count': product_reviews.count(),
                'average_product_rating': float(product_reviews.aggregate(avg=Avg('rating'))['avg'] or 0),
                'sync_success_rate': (
                    sync_logs.filter(status='completed').count() / sync_logs.count() * 100
                    if sync_logs.count() > 0 else 100
                )
            }

        except Exception as e:
            logger.error(f"Error getting basic metrics: {e}")
            return {}

    def get_comparative_analytics(self, shop_ids: List[str], days: int = 30) -> Dict:
        """
        Get comparative analytics for multiple shops.

        Args:
            shop_ids: List of shop IDs to compare
            days: Number of days to analyze

        Returns:
            Dict containing comparative analytics
        """
        try:
            comparative_data = []

            for shop_id in shop_ids:
                performance_data = self.calculate_store_performance(shop_id, days)
                if performance_data['success']:
                    comparative_data.append({
                        'shop_id': shop_id,
                        'shop_name': performance_data['shop_name'],
                        'overall_score': performance_data['overall_score'],
                        'component_scores': {
                            component: data['score']
                            for component, data in performance_data['component_scores'].items()
                        }
                    })

            # Calculate rankings
            if comparative_data:
                # Sort by overall score
                comparative_data.sort(key=lambda x: x['overall_score'], reverse=True)

                # Add rankings
                for i, shop_data in enumerate(comparative_data):
                    shop_data['overall_rank'] = i + 1

                # Calculate component rankings
                for component in ['reliability_score', 'customer_satisfaction', 'delivery_performance',
                                'price_competitiveness', 'product_availability']:
                    sorted_by_component = sorted(
                        comparative_data,
                        key=lambda x: x['component_scores'][component],
                        reverse=True
                    )

                    for i, shop_data in enumerate(sorted_by_component):
                        if 'component_rankings' not in shop_data:
                            shop_data['component_rankings'] = {}
                        shop_data['component_rankings'][component] = i + 1

            return {
                'success': True,
                'shops_compared': len(comparative_data),
                'analysis_period_days': days,
                'comparative_data': comparative_data,
                'summary': {
                    'best_overall': comparative_data[0] if comparative_data else None,
                    'average_score': (
                        sum(shop['overall_score'] for shop in comparative_data) / len(comparative_data)
                        if comparative_data else 0
                    )
                }
            }

        except Exception as e:
            logger.error(f"Error in comparative analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
store_analytics_service = StorePerformanceAnalyticsService()
