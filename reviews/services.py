"""
reviews/services.py
-------------------
Services for sentiment analysis and engagement tracking in the customer feedback system.
"""

import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import Review, StoreReview, EngagementEvent, ProductEngagement
import re

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """
    Service for analyzing sentiment in reviews and feedback.
    """
    
    def __init__(self):
        self.positive_words = [
            'excellent', 'amazing', 'great', 'fantastic', 'wonderful', 'perfect',
            'outstanding', 'superb', 'brilliant', 'awesome', 'love', 'best',
            'good', 'nice', 'happy', 'satisfied', 'recommend', 'quality',
            'fast', 'quick', 'helpful', 'friendly', 'professional', 'reliable'
        ]
        
        self.negative_words = [
            'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'disappointed',
            'poor', 'slow', 'expensive', 'cheap', 'broken', 'defective', 'useless',
            'waste', 'scam', 'fraud', 'rude', 'unprofessional', 'unreliable',
            'delayed', 'damaged', 'wrong', 'missing', 'never', 'not'
        ]
        
        self.intensifiers = [
            'very', 'extremely', 'really', 'absolutely', 'completely', 'totally',
            'quite', 'rather', 'pretty', 'so', 'too', 'highly'
        ]
    
    def analyze_review(self, review: Review) -> Dict:
        """
        Analyze sentiment of a review and return score and label.
        """
        try:
            text = self._prepare_text(review.comment, review.pros, review.cons)
            
            # Calculate sentiment score
            score = self._calculate_sentiment_score(text)
            
            # Determine sentiment label
            label = self._get_sentiment_label(score)
            
            # Consider rating in final score
            rating_influence = (review.rating - 3) * 0.2  # -0.4 to +0.4
            final_score = max(-1.0, min(1.0, score + rating_influence))
            
            return {
                'score': round(final_score, 2),
                'label': label,
                'confidence': self._calculate_confidence(text, score),
                'details': {
                    'text_sentiment': score,
                    'rating_influence': rating_influence,
                    'word_count': len(text.split()),
                    'positive_words_found': self._count_sentiment_words(text, self.positive_words),
                    'negative_words_found': self._count_sentiment_words(text, self.negative_words)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for review {review.id}: {e}")
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'details': {}
            }
    
    def analyze_store_review(self, store_review: StoreReview) -> Dict:
        """
        Analyze sentiment of a store review.
        """
        try:
            text = self._prepare_text(store_review.comment)
            score = self._calculate_sentiment_score(text)
            
            # Consider overall rating
            rating_influence = (store_review.overall_rating - 3) * 0.2
            final_score = max(-1.0, min(1.0, score + rating_influence))
            
            return {
                'score': round(final_score, 2),
                'label': self._get_sentiment_label(final_score),
                'confidence': self._calculate_confidence(text, score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for store review {store_review.id}: {e}")
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
    
    def analyze_bulk_reviews(self, reviews: List[Review]) -> Dict:
        """
        Analyze sentiment for multiple reviews and return aggregated results.
        """
        results = []
        total_score = 0
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for review in reviews:
            analysis = self.analyze_review(review)
            results.append({
                'review_id': str(review.id),
                'analysis': analysis
            })
            
            total_score += analysis['score']
            sentiment_counts[analysis['label']] += 1
        
        if not reviews:
            return {
                'results': [],
                'summary': {
                    'average_sentiment': 0.0,
                    'sentiment_distribution': sentiment_counts,
                    'total_reviews': 0
                }
            }
        
        return {
            'results': results,
            'summary': {
                'average_sentiment': round(total_score / len(reviews), 2),
                'sentiment_distribution': sentiment_counts,
                'total_reviews': len(reviews),
                'positive_percentage': (sentiment_counts['positive'] / len(reviews)) * 100,
                'negative_percentage': (sentiment_counts['negative'] / len(reviews)) * 100
            }
        }
    
    def _prepare_text(self, *texts) -> str:
        """
        Prepare text for sentiment analysis by combining and cleaning.
        """
        combined_text = ' '.join(filter(None, texts))
        # Clean and normalize text
        cleaned_text = re.sub(r'[^\w\s]', ' ', combined_text.lower())
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score using word-based approach.
        """
        words = text.split()
        if not words:
            return 0.0
        
        score = 0
        word_count = len(words)
        
        for i, word in enumerate(words):
            word_score = 0
            
            # Check for positive words
            if word in self.positive_words:
                word_score = 1
            # Check for negative words
            elif word in self.negative_words:
                word_score = -1
            
            # Apply intensifier if present
            if i > 0 and words[i-1] in self.intensifiers:
                word_score *= 1.5
            
            # Apply negation if present
            if i > 0 and words[i-1] in ['not', 'no', 'never', 'none']:
                word_score *= -1
            
            score += word_score
        
        # Normalize score
        if word_count > 0:
            normalized_score = score / word_count
            return max(-1.0, min(1.0, normalized_score))
        
        return 0.0
    
    def _get_sentiment_label(self, score: float) -> str:
        """
        Convert sentiment score to label.
        """
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(self, text: str, score: float) -> float:
        """
        Calculate confidence level of sentiment analysis.
        """
        words = text.split()
        if not words:
            return 0.0
        
        sentiment_word_count = (
            self._count_sentiment_words(text, self.positive_words) +
            self._count_sentiment_words(text, self.negative_words)
        )
        
        # Confidence based on sentiment word density and score magnitude
        word_density = sentiment_word_count / len(words)
        score_magnitude = abs(score)
        
        confidence = min(1.0, (word_density * 2 + score_magnitude) / 2)
        return round(confidence, 2)
    
    def _count_sentiment_words(self, text: str, word_list: List[str]) -> int:
        """
        Count occurrences of sentiment words in text.
        """
        words = text.split()
        return sum(1 for word in words if word in word_list)


class EngagementTrackingService:
    """
    Service for tracking and analyzing user engagement events.
    """
    
    @staticmethod
    def track_event(user, event_type: str, product=None, shop=None, 
                   session_id: str = None, event_data: Dict = None, 
                   page_url: str = None, referrer_url: str = None) -> EngagementEvent:
        """
        Track a user engagement event.
        """
        try:
            event = EngagementEvent.objects.create(
                user=user,
                session_id=session_id or 'anonymous',
                event_type=event_type,
                product=product,
                shop=shop,
                event_data=event_data or {},
                page_url=page_url or '',
                referrer_url=referrer_url or ''
            )
            
            # Update product engagement metrics if product is involved
            if product:
                EngagementTrackingService.update_product_engagement(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error tracking engagement event: {e}")
            return None
    
    @staticmethod
    def update_product_engagement(event: EngagementEvent):
        """
        Update product engagement metrics based on event.
        """
        try:
            engagement, created = ProductEngagement.objects.get_or_create(
                product=event.product
            )
            
            # Update metrics based on event type
            if event.event_type == 'product_view':
                engagement.total_views += 1
            elif event.event_type == 'product_like':
                engagement.total_likes += 1
            elif event.event_type == 'product_dislike':
                engagement.total_dislikes += 1
            elif event.event_type == 'add_to_cart':
                engagement.add_to_cart_count += 1
            elif event.event_type == 'purchase_completed':
                engagement.purchase_count += 1
            elif event.event_type == 'share_product':
                engagement.total_shares += 1
            elif event.event_type == 'save_product':
                engagement.total_saves += 1
            elif event.event_type == 'comparison_created':
                engagement.comparison_count += 1
            
            # Recalculate conversion rate
            if engagement.total_views > 0:
                engagement.conversion_rate = (engagement.purchase_count / engagement.total_views) * 100
            
            engagement.save()
            
        except Exception as e:
            logger.error(f"Error updating product engagement: {e}")
    
    @staticmethod
    def get_engagement_analytics(product=None, user=None, days: int = 30) -> Dict:
        """
        Get engagement analytics for a product or user.
        """
        try:
            from datetime import timedelta
            
            # Build queryset
            queryset = EngagementEvent.objects.all()
            
            if product:
                queryset = queryset.filter(product=product)
            
            if user:
                queryset = queryset.filter(user=user)
            
            # Filter by date range
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=start_date)
            
            # Calculate analytics
            total_events = queryset.count()
            
            if total_events == 0:
                return {'message': 'No engagement events found'}
            
            # Event type distribution
            event_types = queryset.values('event_type').annotate(
                count=models.Count('id')
            ).order_by('-count')
            
            # Daily engagement trends
            daily_events = queryset.extra(
                select={'day': 'date(timestamp)'}
            ).values('day').annotate(
                count=models.Count('id')
            ).order_by('day')
            
            return {
                'total_events': total_events,
                'event_type_distribution': list(event_types),
                'daily_trends': list(daily_events),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement analytics: {e}")
            return {'error': str(e)}
