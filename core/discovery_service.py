"""
core/discovery_service.py
-------------------------
Smart product discovery service that aggregates and intelligently ranks products from all connected stores.
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, Avg, Count, Min, Max, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Product, Category, Brand, Shop
from store_integration.models import PriceHistory, ProductMapping
from reviews.models import Review, EngagementEvent
from .ai_rating_system import ai_rating_system
import re

logger = logging.getLogger(__name__)


class SmartProductDiscoveryService:
    """
    Service for intelligent product discovery and search across all connected stores.
    """
    
    def __init__(self):
        self.default_page_size = 20
        self.max_page_size = 100
        self.search_boost_factors = {
            'exact_match': 10.0,
            'title_match': 5.0,
            'description_match': 2.0,
            'brand_match': 3.0,
            'category_match': 1.5,
            'high_rating': 2.0,
            'popular': 1.5,
            'recent': 1.2
        }
    
    def search_products(self, query: str, filters: Dict = None, 
                       sort_by: str = 'relevance', page: int = 1, 
                       page_size: int = None) -> Dict:
        """
        Perform intelligent product search across all stores.
        
        Args:
            query: Search query string
            filters: Dictionary of filters to apply
            sort_by: Sorting method ('relevance', 'price_low', 'price_high', 'rating', 'popularity')
            page: Page number
            page_size: Number of results per page
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            # Validate and set page size
            if page_size is None:
                page_size = self.default_page_size
            page_size = min(page_size, self.max_page_size)
            
            # Build base queryset
            queryset = Product.objects.filter(is_active=True).select_related(
                'shop', 'brand', 'category'
            ).prefetch_related('reviews')
            
            # Apply search query
            if query:
                search_q = self._build_search_query(query)
                queryset = queryset.filter(search_q)
            
            # Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            # Get total count before pagination
            total_count = queryset.count()
            
            # Apply sorting
            queryset = self._apply_sorting(queryset, sort_by, query)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Enhance results with additional data
            enhanced_results = []
            for product in page_obj:
                enhanced_product = self._enhance_product_data(product, query)
                enhanced_results.append(enhanced_product)
            
            # Get aggregated data for filters
            filter_aggregations = self._get_filter_aggregations(
                Product.objects.filter(is_active=True), query, filters
            )
            
            return {
                'success': True,
                'query': query,
                'results': enhanced_results,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_results': total_count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'filters': filter_aggregations,
                'sort_by': sort_by,
                'search_metadata': {
                    'search_time': timezone.now().isoformat(),
                    'stores_searched': self._get_stores_count(),
                    'categories_found': self._get_categories_in_results(queryset)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'pagination': {},
                'filters': {}
            }
    
    def discover_similar_products(self, product_id: str, limit: int = 10) -> Dict:
        """
        Discover products similar to a given product across all stores.
        
        Args:
            product_id: ID of the reference product
            limit: Maximum number of similar products to return
            
        Returns:
            Dict containing similar products
        """
        try:
            reference_product = Product.objects.get(id=product_id, is_active=True)
            
            # Build similarity query
            similar_products = Product.objects.filter(
                is_active=True
            ).exclude(
                id=product_id
            ).select_related('shop', 'brand', 'category')
            
            # Apply similarity filters
            similarity_filters = Q()
            
            # Same category (high weight)
            if reference_product.category:
                similarity_filters |= Q(category=reference_product.category)
            
            # Same brand (medium weight)
            if reference_product.brand:
                similarity_filters |= Q(brand=reference_product.brand)
            
            # Similar price range (±30%)
            if reference_product.price:
                price_min = reference_product.price * Decimal('0.7')
                price_max = reference_product.price * Decimal('1.3')
                similarity_filters |= Q(price__gte=price_min, price__lte=price_max)
            
            # Similar name/description keywords
            name_keywords = self._extract_keywords(reference_product.name)
            if name_keywords:
                name_q = Q()
                for keyword in name_keywords:
                    name_q |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
                similarity_filters |= name_q
            
            similar_products = similar_products.filter(similarity_filters)
            
            # Calculate similarity scores and sort
            scored_products = []
            for product in similar_products[:limit * 3]:  # Get more to score and filter
                score = self._calculate_similarity_score(reference_product, product)
                if score > 0.1:  # Minimum similarity threshold
                    enhanced_product = self._enhance_product_data(product)
                    enhanced_product['similarity_score'] = round(score, 3)
                    scored_products.append(enhanced_product)
            
            # Sort by similarity score and limit results
            scored_products.sort(key=lambda x: x['similarity_score'], reverse=True)
            final_results = scored_products[:limit]
            
            return {
                'success': True,
                'reference_product': {
                    'id': str(reference_product.id),
                    'name': reference_product.name,
                    'price': float(reference_product.price),
                    'category': reference_product.category.name if reference_product.category else None,
                    'brand': reference_product.brand.name if reference_product.brand else None
                },
                'similar_products': final_results,
                'total_found': len(final_results)
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': f'Product {product_id} not found'
            }
        except Exception as e:
            logger.error(f"Error discovering similar products: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_trending_products(self, category_id: str = None, 
                            time_period: str = 'week', limit: int = 20) -> Dict:
        """
        Get trending products based on engagement metrics.
        
        Args:
            category_id: Optional category filter
            time_period: 'day', 'week', 'month'
            limit: Maximum number of products to return
            
        Returns:
            Dict containing trending products
        """
        try:
            # Calculate time range
            if time_period == 'day':
                start_date = timezone.now() - timedelta(days=1)
            elif time_period == 'week':
                start_date = timezone.now() - timedelta(weeks=1)
            elif time_period == 'month':
                start_date = timezone.now() - timedelta(days=30)
            else:
                start_date = timezone.now() - timedelta(weeks=1)
            
            # Get engagement events for the period
            engagement_query = EngagementEvent.objects.filter(
                timestamp__gte=start_date,
                product__is_active=True
            )
            
            if category_id:
                engagement_query = engagement_query.filter(product__category_id=category_id)
            
            # Calculate trending scores
            trending_data = engagement_query.values('product').annotate(
                view_count=Count('id', filter=Q(event_type='product_view')),
                like_count=Count('id', filter=Q(event_type='product_like')),
                cart_count=Count('id', filter=Q(event_type='add_to_cart')),
                purchase_count=Count('id', filter=Q(event_type='purchase_completed')),
                share_count=Count('id', filter=Q(event_type='share_product'))
            ).order_by('-view_count', '-like_count')
            
            # Calculate trending scores and get product details
            trending_products = []
            for data in trending_data[:limit * 2]:  # Get more to filter
                try:
                    product = Product.objects.select_related(
                        'shop', 'brand', 'category'
                    ).get(id=data['product'])
                    
                    # Calculate trending score
                    trending_score = (
                        data['view_count'] * 1.0 +
                        data['like_count'] * 3.0 +
                        data['cart_count'] * 5.0 +
                        data['purchase_count'] * 10.0 +
                        data['share_count'] * 4.0
                    )
                    
                    if trending_score > 0:
                        enhanced_product = self._enhance_product_data(product)
                        enhanced_product.update({
                            'trending_score': trending_score,
                            'engagement_metrics': {
                                'views': data['view_count'],
                                'likes': data['like_count'],
                                'cart_adds': data['cart_count'],
                                'purchases': data['purchase_count'],
                                'shares': data['share_count']
                            }
                        })
                        trending_products.append(enhanced_product)
                        
                except Product.DoesNotExist:
                    continue
            
            # Sort by trending score and limit
            trending_products.sort(key=lambda x: x['trending_score'], reverse=True)
            final_results = trending_products[:limit]
            
            return {
                'success': True,
                'trending_products': final_results,
                'time_period': time_period,
                'category_id': category_id,
                'total_found': len(final_results)
            }
            
        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_personalized_recommendations(self, user_id: str, limit: int = 20) -> Dict:
        """
        Get personalized product recommendations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            Dict containing personalized recommendations
        """
        try:
            from core.models import User
            user = User.objects.get(id=user_id)
            
            # Get user's interaction history
            user_events = EngagementEvent.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - timedelta(days=30)
            ).select_related('product', 'product__category', 'product__brand')
            
            # Analyze user preferences
            preferences = self._analyze_user_preferences(user_events)
            
            # Get candidate products
            candidates = Product.objects.filter(
                is_active=True
            ).exclude(
                id__in=user_events.filter(
                    event_type__in=['purchase_completed', 'product_view']
                ).values_list('product_id', flat=True)
            ).select_related('shop', 'brand', 'category')
            
            # Score and rank candidates
            scored_recommendations = []
            for product in candidates[:limit * 5]:  # Get more to score
                score = self._calculate_recommendation_score(product, preferences)
                if score > 0.1:
                    enhanced_product = self._enhance_product_data(product)
                    enhanced_product['recommendation_score'] = round(score, 3)
                    enhanced_product['recommendation_reasons'] = self._get_recommendation_reasons(
                        product, preferences
                    )
                    scored_recommendations.append(enhanced_product)
            
            # Sort and limit
            scored_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            final_recommendations = scored_recommendations[:limit]
            
            return {
                'success': True,
                'user_id': user_id,
                'recommendations': final_recommendations,
                'user_preferences': preferences,
                'total_found': len(final_recommendations)
            }
            
        except User.DoesNotExist:
            return {
                'success': False,
                'error': f'User {user_id} not found'
            }
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _build_search_query(self, query: str) -> Q:
        """
        Build Django Q object for search query.
        """
        search_terms = self._extract_keywords(query)
        search_q = Q()

        for term in search_terms:
            term_q = (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(brand__name__icontains=term) |
                Q(category__name__icontains=term) |
                Q(sku__icontains=term)
            )
            search_q &= term_q

        return search_q

    def _apply_filters(self, queryset, filters: Dict):
        """
        Apply filters to the queryset.
        """
        if 'category_id' in filters:
            queryset = queryset.filter(category_id=filters['category_id'])

        if 'brand_id' in filters:
            queryset = queryset.filter(brand_id=filters['brand_id'])

        if 'shop_id' in filters:
            queryset = queryset.filter(shop_id=filters['shop_id'])

        if 'min_price' in filters:
            queryset = queryset.filter(price__gte=filters['min_price'])

        if 'max_price' in filters:
            queryset = queryset.filter(price__lte=filters['max_price'])

        if 'min_rating' in filters:
            queryset = queryset.filter(rating__gte=filters['min_rating'])

        if 'availability' in filters and filters['availability']:
            queryset = queryset.filter(is_active=True)

        if 'has_discount' in filters and filters['has_discount']:
            queryset = queryset.filter(original_price__gt=F('price'))

        return queryset

    def _apply_sorting(self, queryset, sort_by: str, query: str = None):
        """
        Apply sorting to the queryset.
        """
        if sort_by == 'price_low':
            return queryset.order_by('price', '-rating')
        elif sort_by == 'price_high':
            return queryset.order_by('-price', '-rating')
        elif sort_by == 'rating':
            return queryset.order_by('-rating', '-views')
        elif sort_by == 'popularity':
            return queryset.order_by('-views', '-likes', '-rating')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'relevance' and query:
            # For relevance, we'd ideally use search ranking
            # For now, use a combination of factors
            return queryset.order_by('-rating', '-views', 'price')
        else:
            # Default sorting
            return queryset.order_by('-rating', '-views')

    def _enhance_product_data(self, product, query: str = None) -> Dict:
        """
        Enhance product data with additional information.
        """
        # Get latest price from other stores
        alternative_prices = PriceHistory.objects.filter(
            product=product
        ).exclude(
            shop=product.shop
        ).select_related('shop').order_by('shop', '-recorded_at').distinct('shop')

        price_comparison = []
        for price_record in alternative_prices:
            price_comparison.append({
                'shop_id': str(price_record.shop.id),
                'shop_name': price_record.shop.name,
                'price': float(price_record.price),
                'is_available': price_record.is_available,
                'last_updated': price_record.recorded_at.isoformat()
            })

        # Get review summary
        reviews = Review.objects.filter(product=product, status='approved')
        review_summary = {
            'total_reviews': reviews.count(),
            'average_rating': float(reviews.aggregate(avg=Avg('rating'))['avg'] or 0),
            'sentiment_distribution': {}
        }

        if reviews.exists():
            sentiment_counts = reviews.values('sentiment_label').annotate(count=Count('id'))
            for sentiment in sentiment_counts:
                if sentiment['sentiment_label']:
                    review_summary['sentiment_distribution'][sentiment['sentiment_label']] = sentiment['count']

        # Calculate discount percentage
        discount_percentage = 0
        if product.original_price and product.original_price > product.price:
            discount_percentage = ((product.original_price - product.price) / product.original_price) * 100

        enhanced_data = {
            'id': str(product.id),
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'original_price': float(product.original_price) if product.original_price else None,
            'discount_percentage': round(discount_percentage, 1),
            'currency': 'USD',  # You might want to make this dynamic
            'sku': product.sku,
            'image_url': product.image_url,
            'rating': float(product.rating),
            'views': product.views,
            'likes': product.likes,
            'is_active': product.is_active,
            'shop': {
                'id': str(product.shop.id),
                'name': product.shop.name,
                'reliability_score': float(product.shop.reliability_score)
            },
            'category': {
                'id': str(product.category.id),
                'name': product.category.name
            } if product.category else None,
            'brand': {
                'id': str(product.brand.id),
                'name': product.brand.name
            } if product.brand else None,
            'review_summary': review_summary,
            'price_comparison': price_comparison,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat()
        }

        # Add search relevance score if query provided
        if query:
            enhanced_data['relevance_score'] = self._calculate_relevance_score(product, query)

        return enhanced_data

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text.
        """
        if not text:
            return []

        # Remove special characters and split
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = cleaned_text.split()

        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }

        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Limit to 10 keywords

    def _calculate_similarity_score(self, reference_product, candidate_product) -> float:
        """
        Calculate similarity score between two products.
        """
        score = 0.0

        # Category match (high weight)
        if (reference_product.category and candidate_product.category and
            reference_product.category == candidate_product.category):
            score += 0.4

        # Brand match (medium weight)
        if (reference_product.brand and candidate_product.brand and
            reference_product.brand == candidate_product.brand):
            score += 0.3

        # Price similarity (medium weight)
        if reference_product.price and candidate_product.price:
            price_diff = abs(reference_product.price - candidate_product.price)
            max_price = max(reference_product.price, candidate_product.price)
            if max_price > 0:
                price_similarity = 1 - (price_diff / max_price)
                score += price_similarity * 0.2

        # Name similarity (low weight)
        ref_keywords = set(self._extract_keywords(reference_product.name))
        cand_keywords = set(self._extract_keywords(candidate_product.name))
        if ref_keywords and cand_keywords:
            name_similarity = len(ref_keywords & cand_keywords) / len(ref_keywords | cand_keywords)
            score += name_similarity * 0.1

        return min(score, 1.0)

    def _calculate_relevance_score(self, product, query: str) -> float:
        """
        Calculate relevance score for search query.
        """
        score = 0.0
        query_lower = query.lower()

        # Exact name match
        if query_lower in product.name.lower():
            score += self.search_boost_factors['exact_match']

        # Title word matches
        query_words = self._extract_keywords(query)
        name_words = self._extract_keywords(product.name)

        for query_word in query_words:
            if query_word in name_words:
                score += self.search_boost_factors['title_match']

        # Description matches
        if product.description and query_lower in product.description.lower():
            score += self.search_boost_factors['description_match']

        # Brand match
        if product.brand and query_lower in product.brand.name.lower():
            score += self.search_boost_factors['brand_match']

        # Category match
        if product.category and query_lower in product.category.name.lower():
            score += self.search_boost_factors['category_match']

        # Rating boost
        if product.rating >= 4.0:
            score += self.search_boost_factors['high_rating']

        # Popularity boost
        if product.views > 1000:
            score += self.search_boost_factors['popular']

        # Recent product boost
        if (timezone.now() - product.created_at).days < 30:
            score += self.search_boost_factors['recent']

        return score

    def _get_filter_aggregations(self, base_queryset, query: str = None, current_filters: Dict = None):
        """
        Get aggregated data for filters.
        """
        # Apply search query if provided
        if query:
            search_q = self._build_search_query(query)
            base_queryset = base_queryset.filter(search_q)

        # Remove current filters to show all available options
        filter_queryset = base_queryset.filter(is_active=True)

        aggregations = {
            'categories': list(filter_queryset.values(
                'category__id', 'category__name'
            ).annotate(
                count=Count('id')
            ).filter(category__isnull=False).order_by('category__name')),

            'brands': list(filter_queryset.values(
                'brand__id', 'brand__name'
            ).annotate(
                count=Count('id')
            ).filter(brand__isnull=False).order_by('brand__name')),

            'shops': list(filter_queryset.values(
                'shop__id', 'shop__name'
            ).annotate(
                count=Count('id')
            ).order_by('shop__name')),

            'price_range': filter_queryset.aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            ),

            'rating_distribution': list(filter_queryset.values(
                'rating'
            ).annotate(
                count=Count('id')
            ).order_by('-rating'))
        }

        return aggregations

    def _get_stores_count(self) -> int:
        """Get total number of active stores."""
        return Shop.objects.filter(is_active=True).count()

    def _get_categories_in_results(self, queryset) -> List[Dict]:
        """Get categories found in search results."""
        categories = queryset.values(
            'category__id', 'category__name'
        ).annotate(
            count=Count('id')
        ).filter(category__isnull=False).order_by('category__name')

        return list(categories)

    def _analyze_user_preferences(self, user_events) -> Dict:
        """
        Analyze user preferences from engagement events.
        """
        preferences = {
            'preferred_categories': {},
            'preferred_brands': {},
            'price_range': {'min': 0, 'max': 0},
            'interaction_patterns': {}
        }

        # Analyze category preferences
        category_interactions = user_events.filter(
            product__category__isnull=False
        ).values('product__category__name').annotate(count=Count('id'))

        for cat in category_interactions:
            preferences['preferred_categories'][cat['product__category__name']] = cat['count']

        # Analyze brand preferences
        brand_interactions = user_events.filter(
            product__brand__isnull=False
        ).values('product__brand__name').annotate(count=Count('id'))

        for brand in brand_interactions:
            preferences['preferred_brands'][brand['product__brand__name']] = brand['count']

        # Analyze price preferences
        price_interactions = user_events.filter(
            product__price__isnull=False
        ).aggregate(
            avg_price=Avg('product__price'),
            min_price=Min('product__price'),
            max_price=Max('product__price')
        )

        if price_interactions['avg_price']:
            preferences['price_range'] = {
                'min': float(price_interactions['min_price'] or 0),
                'max': float(price_interactions['max_price'] or 0),
                'average': float(price_interactions['avg_price'])
            }

        # Analyze interaction patterns
        interaction_types = user_events.values('event_type').annotate(count=Count('id'))
        for interaction in interaction_types:
            preferences['interaction_patterns'][interaction['event_type']] = interaction['count']

        return preferences

    def _calculate_recommendation_score(self, product, preferences: Dict) -> float:
        """
        Calculate recommendation score based on user preferences.
        """
        score = 0.0

        # Category preference match
        if product.category and product.category.name in preferences['preferred_categories']:
            category_weight = preferences['preferred_categories'][product.category.name]
            score += min(category_weight * 0.1, 0.4)  # Max 0.4 for category

        # Brand preference match
        if product.brand and product.brand.name in preferences['preferred_brands']:
            brand_weight = preferences['preferred_brands'][product.brand.name]
            score += min(brand_weight * 0.05, 0.3)  # Max 0.3 for brand

        # Price preference match
        if preferences['price_range'].get('average'):
            avg_price = preferences['price_range']['average']
            price_diff = abs(float(product.price) - avg_price)
            price_similarity = 1 - min(price_diff / avg_price, 1.0)
            score += price_similarity * 0.2

        # Product quality factors
        score += min(float(product.rating) / 5.0, 1.0) * 0.1  # Rating factor

        return min(score, 1.0)

    def _get_recommendation_reasons(self, product, preferences: Dict) -> List[str]:
        """
        Generate human-readable reasons for recommendation.
        """
        reasons = []

        if product.category and product.category.name in preferences['preferred_categories']:
            reasons.append(f"You've shown interest in {product.category.name}")

        if product.brand and product.brand.name in preferences['preferred_brands']:
            reasons.append(f"You've interacted with {product.brand.name} products before")

        if float(product.rating) >= 4.0:
            reasons.append("Highly rated product")

        if product.views > 1000:
            reasons.append("Popular among other users")

        # Check for discount
        if product.original_price and product.original_price > product.price:
            discount = ((product.original_price - product.price) / product.original_price) * 100
            reasons.append(f"On sale - {discount:.0f}% off")

        return reasons[:3]  # Limit to top 3 reasons


# Create singleton instance
discovery_service = SmartProductDiscoveryService()
