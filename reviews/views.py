"""
reviews/views.py
----------------
Defines review-related API views with enhanced customer feedback system.
"""

from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Review, StoreReview, ReviewHelpfulness, ProductEngagement,
    UserFeedback, EngagementEvent
)
from .serializers import (
    CreateReviewSerializer, ReviewSerializer, StoreReviewSerializer,
    ReviewHelpfulnessSerializer, ProductEngagementSerializer,
    UserFeedbackSerializer, EngagementEventSerializer
)
from .services import SentimentAnalysisService, EngagementTrackingService
import logging

logger = logging.getLogger(__name__)

class ReviewListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating reviews for a product أو عبر /reviews/add/"""

    def get_queryset(self):
        product_id = self.kwargs.get('product_id') or self.request.data.get('product_id')
        if product_id:
            return Review.objects.filter(product_id=product_id)
        return Review.objects.none()

    def get_serializer_class(self):
        return CreateReviewSerializer if self.request.method == 'POST' else ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # عند POST عبر /reviews/add/ يجب أخذ product_id من body
        if self.request.method == 'POST':
            product_id = self.request.data.get('product_id')
        else:
            product_id = self.kwargs.get('product_id')
        context['product_id'] = product_id
        return context

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class EnhancedReviewViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for product reviews with sentiment analysis and engagement tracking.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product', 'product__shop')

        # Filter by product if specified
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        # Filter by status
        status = self.request.query_params.get('status', 'approved')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by sentiment
        sentiment = self.request.query_params.get('sentiment')
        if sentiment:
            queryset = queryset.filter(sentiment_label=sentiment)

        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReviewSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Create review with sentiment analysis."""
        review = serializer.save(user=self.request.user)

        # Perform sentiment analysis (placeholder - will implement service)
        try:
            # This would call the sentiment analysis service
            # sentiment_service = SentimentAnalysisService()
            # sentiment_data = sentiment_service.analyze_review(review)
            # review.sentiment_score = sentiment_data['score']
            # review.sentiment_label = sentiment_data['label']
            # review.save()
            pass

        except Exception as e:
            logger.error(f"Error analyzing sentiment for review {review.id}: {e}")

        # Track engagement event (placeholder)
        try:
            # This would call the engagement tracking service
            pass
        except Exception as e:
            logger.error(f"Error tracking review submission event: {e}")

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark a review as helpful or not helpful."""
        review = self.get_object()
        vote = request.data.get('vote')  # 'helpful' or 'not_helpful'

        if vote not in ['helpful', 'not_helpful']:
            return Response(
                {'error': 'Vote must be "helpful" or "not_helpful"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update helpfulness vote
        helpfulness, created = ReviewHelpfulness.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'vote': vote}
        )

        if not created:
            helpfulness.vote = vote
            helpfulness.save()

        # Update review helpfulness score
        helpful_count = review.helpfulness_votes.filter(vote='helpful').count()
        review.helpfulness_score = helpful_count
        review.save()

        return Response({
            'message': f'Review marked as {vote}',
            'helpfulness_score': review.helpfulness_score
        })

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get review analytics for a product or overall."""
        product_id = request.query_params.get('product_id')

        queryset = self.get_queryset()
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        # Calculate analytics
        total_reviews = queryset.count()
        if total_reviews == 0:
            return Response({'message': 'No reviews found'})

        analytics = {
            'total_reviews': total_reviews,
            'average_rating': queryset.aggregate(avg_rating=Avg('rating'))['avg_rating'],
            'rating_distribution': {},
            'sentiment_distribution': {},
            'verified_purchase_percentage': 0,
            'recent_trends': {}
        }

        # Rating distribution
        for rating in range(1, 6):
            count = queryset.filter(rating=rating).count()
            analytics['rating_distribution'][f'{rating}_star'] = {
                'count': count,
                'percentage': (count / total_reviews) * 100
            }

        # Sentiment distribution
        sentiment_counts = queryset.values('sentiment_label').annotate(count=Count('id'))
        for sentiment in sentiment_counts:
            if sentiment['sentiment_label']:
                analytics['sentiment_distribution'][sentiment['sentiment_label']] = {
                    'count': sentiment['count'],
                    'percentage': (sentiment['count'] / total_reviews) * 100
                }

        # Verified purchase percentage
        verified_count = queryset.filter(verified_purchase=True).count()
        analytics['verified_purchase_percentage'] = (verified_count / total_reviews) * 100

        # Recent trends (last 30 days vs previous 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sixty_days_ago = timezone.now() - timedelta(days=60)

        recent_reviews = queryset.filter(created_at__gte=thirty_days_ago).count()
        previous_reviews = queryset.filter(
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago
        ).count()

        if previous_reviews > 0:
            trend_percentage = ((recent_reviews - previous_reviews) / previous_reviews) * 100
        else:
            trend_percentage = 100 if recent_reviews > 0 else 0

        analytics['recent_trends'] = {
            'last_30_days': recent_reviews,
            'previous_30_days': previous_reviews,
            'trend_percentage': round(trend_percentage, 2)
        }

        return Response(analytics)


class StoreReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for store/shop reviews and ratings.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = StoreReview.objects.select_related('user', 'shop')

        # Filter by shop if specified
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(overall_rating__gte=min_rating)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        return StoreReviewSerializer

    def perform_create(self, serializer):
        """Create store review and update shop metrics."""
        store_review = serializer.save(user=self.request.user)

        # Update shop's average ratings
        shop = store_review.shop
        shop_reviews = StoreReview.objects.filter(shop=shop)

        # Calculate new averages
        shop.reliability_score = shop_reviews.aggregate(
            avg_rating=Avg('overall_rating')
        )['avg_rating'] or 5.0

        shop.customer_service_rating = shop_reviews.aggregate(
            avg_rating=Avg('customer_service_rating')
        )['avg_rating'] or 5.0

        shop.save()

    @action(detail=False, methods=['get'])
    def shop_analytics(self, request):
        """Get analytics for a specific shop."""
        shop_id = request.query_params.get('shop_id')
        if not shop_id:
            return Response(
                {'error': 'shop_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviews = self.get_queryset().filter(shop_id=shop_id)
        total_reviews = reviews.count()

        if total_reviews == 0:
            return Response({'message': 'No reviews found for this shop'})

        analytics = {
            'total_reviews': total_reviews,
            'overall_rating': reviews.aggregate(avg=Avg('overall_rating'))['avg'],
            'delivery_rating': reviews.aggregate(avg=Avg('delivery_rating'))['avg'],
            'customer_service_rating': reviews.aggregate(avg=Avg('customer_service_rating'))['avg'],
            'product_quality_rating': reviews.aggregate(avg=Avg('product_quality_rating'))['avg'],
            'value_for_money_rating': reviews.aggregate(avg=Avg('value_for_money_rating'))['avg'],
            'rating_distribution': {},
            'recent_trends': {}
        }

        # Rating distribution
        for rating in range(1, 6):
            count = reviews.filter(overall_rating=rating).count()
            analytics['rating_distribution'][f'{rating}_star'] = {
                'count': count,
                'percentage': (count / total_reviews) * 100
            }

        return Response(analytics)


class EngagementTrackingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking and analyzing user engagement events.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EngagementEvent.objects.filter(user=self.request.user).order_by('-timestamp')

    def get_serializer_class(self):
        return EngagementEventSerializer

    def perform_create(self, serializer):
        """Create engagement event and update product metrics."""
        event = serializer.save(
            user=self.request.user,
            session_id=self.request.session.session_key or 'anonymous',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

        # Update product engagement metrics if product is involved
        if event.product:
            self.update_product_engagement(event)

    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def update_product_engagement(self, event):
        """Update product engagement metrics based on event."""
        try:
            engagement, created = ProductEngagement.objects.get_or_create(
                product=event.product
            )

            # Update metrics based on event type
            if event.event_type == 'product_view':
                engagement.total_views += 1
            elif event.event_type == 'product_like':
                engagement.total_likes += 1
            elif event.event_type == 'add_to_cart':
                engagement.add_to_cart_count += 1
            elif event.event_type == 'purchase_completed':
                engagement.purchase_count += 1
            elif event.event_type == 'share_product':
                engagement.total_shares += 1
            elif event.event_type == 'save_product':
                engagement.total_saves += 1

            # Recalculate conversion rate
            if engagement.total_views > 0:
                engagement.conversion_rate = (engagement.purchase_count / engagement.total_views) * 100

            engagement.save()

        except Exception as e:
            logger.error(f"Error updating product engagement: {e}")

    @action(detail=False, methods=['post'])
    def track_bulk(self, request):
        """Track multiple engagement events in bulk."""
        events_data = request.data.get('events', [])

        if not events_data:
            return Response(
                {'error': 'events array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_events = []
        errors = []

        for event_data in events_data:
            try:
                serializer = self.get_serializer(data=event_data)
                if serializer.is_valid():
                    event = serializer.save(
                        user=request.user,
                        session_id=request.session.session_key or 'anonymous',
                        ip_address=self.get_client_ip(),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    created_events.append(event.id)

                    # Update product engagement if applicable
                    if event.product:
                        self.update_product_engagement(event)
                else:
                    errors.append({
                        'event_data': event_data,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'event_data': event_data,
                    'error': str(e)
                })

        return Response({
            'created_events': len(created_events),
            'errors': errors,
            'event_ids': created_events
        })

    @action(detail=False, methods=['get'])
    def user_analytics(self, request):
        """Get engagement analytics for the current user."""
        events = self.get_queryset()

        # Calculate analytics
        total_events = events.count()
        if total_events == 0:
            return Response({'message': 'No engagement events found'})

        # Event type distribution
        event_types = events.values('event_type').annotate(count=Count('id'))

        # Recent activity (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_events = events.filter(timestamp__gte=seven_days_ago).count()

        # Most engaged products
        product_engagement = events.filter(product__isnull=False).values(
            'product__id', 'product__name'
        ).annotate(
            engagement_count=Count('id')
        ).order_by('-engagement_count')[:10]

        analytics = {
            'total_events': total_events,
            'recent_activity': recent_events,
            'event_type_distribution': list(event_types),
            'most_engaged_products': list(product_engagement),
            'engagement_score': self.calculate_user_engagement_score(events)
        }

        return Response(analytics)

    def calculate_user_engagement_score(self, events):
        """Calculate user engagement score based on event types and frequency."""
        event_weights = {
            'page_view': 1,
            'product_view': 2,
            'search': 2,
            'product_like': 3,
            'add_to_cart': 5,
            'purchase_completed': 10,
            'review_submitted': 8,
            'share_product': 4,
            'save_product': 3,
        }

        total_score = 0
        for event in events:
            weight = event_weights.get(event.event_type, 1)
            total_score += weight

        return total_score
