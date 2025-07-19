"""
recommendations/models.py
------------------------
Defines recommendation-related database models.
"""

from django.db import models
from django.apps import apps  # Use apps.get_model to resolve circular imports
from django.conf import settings


# -------------------------------------------------------------------------------------------------
#                   Product Recommendation
# -------------------------------------------------------------------------------------------------------
class ProductRecommendation(models.Model):
    """
    Represents a recommendation of a product for a specific user.
    """
    RECOMMENDATION_TYPE_CHOICES = (
        ('preferred', 'Preferred'),
        ('liked', 'Liked'),
        ('new', 'New'),
        ('popular', 'Popular'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='recommendations',
        help_text="The user who receives the recommendation."
    )
    product = models.ForeignKey(
        'core.Product',  # Use string reference to avoid circular import
        on_delete=models.CASCADE, 
        related_name='recommended_to',
        help_text="The product being recommended."
    )
    score = models.FloatField(
        default=0.0, 
        help_text="The recommendation score for the product."
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        default='preferred',
        help_text="Type of recommendation."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="The timestamp when the recommendation was created."
    )

    def __str__(self):
        return f"Recommendation for {self.user.username} - {self.product.name}"

    class Meta:
        verbose_name = "Product Recommendation"
        verbose_name_plural = "Product Recommendations"
        ordering = ['-created_at']


# -------------------------------------------------------------------------------------------------
#                   User Behavior Log
# -------------------------------------------------------------------------------------------------------
class UserBehaviorLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='behavior_logs')
    product = models.ForeignKey(
        'core.Product',  # Use string reference to avoid circular import
        on_delete=models.CASCADE,
        related_name='behavior_logs'
    )
    action = models.CharField(max_length=50, choices=[('view', 'View'), ('like', 'Like'), ('purchase', 'Purchase')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.product.name}"


# -------------------------------------------------------------------------------------------------
#                   Enhanced Recommendation Models
# -------------------------------------------------------------------------------------------------------

class UserInteraction(models.Model):
    """
    Model to track user interactions with products for recommendation improvements.
    """
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('share', 'Share'),
        ('compare', 'Compare'),
        ('wishlist_add', 'Add to Wishlist'),
        ('wishlist_remove', 'Remove from Wishlist'),
        ('search', 'Search'),
        ('click', 'Click'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_interactions'
    )
    product = models.ForeignKey(
        'core.Product',
        on_delete=models.CASCADE,
        related_name='user_interactions'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES,
        verbose_name="Interaction Type"
    )
    last_interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES,
        null=True,
        blank=True,
        verbose_name="Last Interaction Type"
    )
    interaction_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Interaction Count"
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Interaction Context",
        help_text="Additional context about the interaction"
    )
    first_interaction_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="First Interaction At"
    )
    last_interaction_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Interaction At"
    )

    class Meta:
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['user', 'last_interaction_at']),
            models.Index(fields=['product', 'interaction_type']),
            models.Index(fields=['interaction_type', 'last_interaction_at']),
        ]
        ordering = ['-last_interaction_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.interaction_type})"


class UserProductWeight(models.Model):
    """
    Model to store calculated weights for user-product pairs based on interactions.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_weights'
    )
    product = models.ForeignKey(
        'core.Product',
        on_delete=models.CASCADE,
        related_name='user_weights'
    )
    weight = models.FloatField(
        default=0.0,
        verbose_name="Weight",
        help_text="Calculated weight based on user interactions"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )

    class Meta:
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['user', '-weight']),
            models.Index(fields=['product', '-weight']),
        ]
        ordering = ['-weight']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}: {self.weight}"


class RecommendationSession(models.Model):
    """
    Model to track recommendation sessions and their effectiveness.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendation_sessions',
        null=True,
        blank=True
    )
    session_id = models.CharField(
        max_length=100,
        verbose_name="Session ID",
        help_text="Browser session ID for anonymous users"
    )
    trigger_product = models.ForeignKey(
        'core.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_sessions',
        verbose_name="Trigger Product"
    )
    trigger_interaction = models.CharField(
        max_length=20,
        choices=UserInteraction.INTERACTION_TYPES,
        null=True,
        blank=True,
        verbose_name="Trigger Interaction"
    )
    recommended_products = models.JSONField(
        default=list,
        verbose_name="Recommended Products",
        help_text="List of recommended product IDs"
    )
    recommendation_types = models.JSONField(
        default=dict,
        verbose_name="Recommendation Types",
        help_text="Types of recommendations provided"
    )
    clicks = models.PositiveIntegerField(
        default=0,
        verbose_name="Clicks",
        help_text="Number of recommended products clicked"
    )
    conversions = models.PositiveIntegerField(
        default=0,
        verbose_name="Conversions",
        help_text="Number of recommended products purchased"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_id', '-created_at']),
            models.Index(fields=['trigger_product', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.username if self.user else f"Session {self.session_id[:8]}"
        return f"Recommendations for {user_info} at {self.created_at}"

    @property
    def click_through_rate(self):
        """Calculate click-through rate."""
        if not self.recommended_products:
            return 0.0
        return (self.clicks / len(self.recommended_products)) * 100

    @property
    def conversion_rate(self):
        """Calculate conversion rate."""
        if not self.recommended_products:
            return 0.0
        return (self.conversions / len(self.recommended_products)) * 100