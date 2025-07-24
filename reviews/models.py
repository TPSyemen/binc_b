"""
reviews/models.py
-----------------
Defines review-related database models with enhanced customer feedback system.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Product, Shop
import uuid
from decimal import Decimal


class Review(models.Model):
    """Enhanced model for product reviews with sentiment analysis."""

    REVIEW_STATUS_CHOICES = (
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Product Rating"
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Review Comment"
    )

    # Enhanced feedback fields
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Review Title"
    )
    pros = models.TextField(
        blank=True,
        verbose_name="Pros",
        help_text="What did you like about this product?"
    )
    cons = models.TextField(
        blank=True,
        verbose_name="Cons",
        help_text="What didn't you like about this product?"
    )

    # Purchase verification
    verified_purchase = models.BooleanField(
        default=False,
        verbose_name="Verified Purchase",
        help_text="Whether this review is from a verified purchase"
    )
    purchase_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Purchase Date"
    )

    # AI-generated sentiment analysis
    sentiment_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-1')), MaxValueValidator(Decimal('1'))],
        verbose_name="Sentiment Score",
        help_text="AI-calculated sentiment score (-1 to 1)"
    )
    sentiment_label = models.CharField(
        max_length=20,
        choices=(
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative'),
        ),
        null=True,
        blank=True,
        verbose_name="Sentiment Label"
    )

    # Moderation and quality
    status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default='pending',
        verbose_name="Review Status"
    )
    helpfulness_score = models.PositiveIntegerField(
        default=0,
        verbose_name="Helpfulness Score",
        help_text="Number of users who found this review helpful"
    )

    # Engagement metrics
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    reports = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['sentiment_label', '-created_at']),
        ]

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name} - {self.rating} stars"

    @property
    def engagement_ratio(self):
        """Calculate engagement ratio (likes vs dislikes)."""
        total_engagement = self.likes + self.dislikes
        if total_engagement == 0:
            return 0.5  # Neutral
        return self.likes / total_engagement


class StoreReview(models.Model):
    """Model for store/shop reviews and ratings."""

    DELIVERY_RATING_CHOICES = [(i, i) for i in range(1, 6)]
    SERVICE_RATING_CHOICES = [(i, i) for i in range(1, 6)]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='store_reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store_reviews'
    )

    # Overall store rating
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Overall Rating"
    )

    # Specific aspect ratings
    delivery_rating = models.PositiveIntegerField(
        choices=DELIVERY_RATING_CHOICES,
        verbose_name="Delivery Rating"
    )
    customer_service_rating = models.PositiveIntegerField(
        choices=SERVICE_RATING_CHOICES,
        verbose_name="Customer Service Rating"
    )
    product_quality_rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Product Quality Rating"
    )
    value_for_money_rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Value for Money Rating"
    )

    # Review content
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Review Title"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Review Comment"
    )

    # Purchase context
    order_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Order Reference"
    )
    purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Purchase Amount"
    )

    # AI analysis
    sentiment_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-1')), MaxValueValidator(Decimal('1'))],
        verbose_name="Sentiment Score"
    )

    # Engagement
    helpfulness_score = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('shop', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['overall_rating', '-created_at']),
        ]

    def __str__(self):
        return f"Store review by {self.user.username} for {self.shop.name} - {self.overall_rating} stars"


class ReviewHelpfulness(models.Model):
    """Model to track review helpfulness votes."""

    VOTE_CHOICES = (
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpfulness_votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_helpfulness_votes'
    )
    vote = models.CharField(
        max_length=20,
        choices=VOTE_CHOICES,
        verbose_name="Vote"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')
        indexes = [
            models.Index(fields=['review', 'vote']),
        ]

    def __str__(self):
        return f"{self.user.username} found review {self.vote}"


class ProductEngagement(models.Model):
    """Model to track detailed product engagement metrics."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='engagement_metrics'
    )

    # View metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    average_view_duration = models.DurationField(null=True, blank=True)

    # Interaction metrics
    total_likes = models.PositiveIntegerField(default=0)
    total_dislikes = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_saves = models.PositiveIntegerField(default=0)

    # Conversion metrics
    add_to_cart_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Conversion Rate (%)"
    )

    # Review metrics
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Average Rating"
    )
    review_sentiment_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.0'),
        verbose_name="Average Sentiment Score"
    )

    # Comparison metrics
    comparison_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Times Compared"
    )
    won_comparisons = models.PositiveIntegerField(
        default=0,
        verbose_name="Won Comparisons"
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', '-last_updated']),
            models.Index(fields=['-total_views']),
            models.Index(fields=['-conversion_rate']),
            models.Index(fields=['-average_rating']),
        ]

    def __str__(self):
        return f"Engagement metrics for {self.product.name}"

    @property
    def engagement_score(self):
        """Calculate overall engagement score."""
        # Weighted score based on different engagement types
        score = (
            self.total_views * 0.1 +
            self.total_likes * 2.0 +
            self.total_shares * 3.0 +
            self.total_saves * 2.5 +
            self.add_to_cart_count * 5.0 +
            self.purchase_count * 10.0 +
            self.total_reviews * 4.0
        )
        return round(score, 2)


class UserFeedback(models.Model):
    """Model for general user feedback about the platform."""

    FEEDBACK_TYPES = (
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('general_feedback', 'General Feedback'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('suggestion', 'Suggestion'),
    )

    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_feedback',
        null=True,
        blank=True
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Contact Email",
        help_text="For anonymous feedback"
    )

    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPES,
        verbose_name="Feedback Type"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name="Priority"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Status"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Title"
    )
    description = models.TextField(
        verbose_name="Description"
    )

    # Context information
    page_url = models.URLField(
        blank=True,
        verbose_name="Page URL",
        help_text="URL where the feedback was submitted"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )

    # AI analysis
    sentiment_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-1')), MaxValueValidator(Decimal('1'))],
        verbose_name="Sentiment Score"
    )
    category_prediction = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="AI Category Prediction"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else self.email
        return f"{self.feedback_type} from {user_info}: {self.title}"


class EngagementEvent(models.Model):
    """Model to track real-time engagement events for analytics."""

    EVENT_TYPES = (
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('search', 'Search'),
        ('filter_applied', 'Filter Applied'),
        ('sort_applied', 'Sort Applied'),
        ('product_like', 'Product Like'),
        ('product_dislike', 'Product Dislike'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_started', 'Checkout Started'),
        ('purchase_completed', 'Purchase Completed'),
        ('review_submitted', 'Review Submitted'),
        ('comparison_created', 'Comparison Created'),
        ('recommendation_clicked', 'Recommendation Clicked'),
        ('share_product', 'Share Product'),
        ('save_product', 'Save Product'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_events',
        null=True,
        blank=True
    )
    session_id = models.CharField(
        max_length=100,
        verbose_name="Session ID"
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        verbose_name="Event Type"
    )

    # Related objects
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='engagement_events'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='engagement_events'
    )

    # Event data
    event_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Event Data"
    )

    # Context
    page_url = models.URLField(blank=True)
    referrer_url = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['session_id', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['product', '-timestamp']),
            models.Index(fields=['shop', '-timestamp']),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else f"Session {self.session_id[:8]}"
        return f"{self.event_type} by {user_info} at {self.timestamp}"
