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