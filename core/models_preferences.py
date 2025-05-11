from django.db import models
from django.conf import settings
import uuid

class UserPreference(models.Model):
    """Model for storing user preferences for brands and price ranges."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='preferences',
        help_text="The user who owns these preferences."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    
    # Price range preferences
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Minimum Price"
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10000,
        verbose_name="Maximum Price"
    )
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class BrandPreference(models.Model):
    """Model for storing user brand preferences."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user_preference = models.ForeignKey(
        UserPreference,
        on_delete=models.CASCADE,
        related_name='brand_preferences',
        help_text="The user preference this brand preference belongs to."
    )
    brand = models.ForeignKey(
        'core.Brand',
        on_delete=models.CASCADE,
        related_name='preferred_by',
        help_text="The brand that is preferred."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    class Meta:
        unique_together = ('user_preference', 'brand')
        ordering = ['brand__name']
        verbose_name = "Brand Preference"
        verbose_name_plural = "Brand Preferences"
    
    def __str__(self):
        return f"{self.user_preference.user.username} - {self.brand.name}"
