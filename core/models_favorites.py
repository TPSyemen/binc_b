from django.db import models
from django.conf import settings
from django.apps import apps  # Use apps.get_model to resolve circular imports

class Favorite(models.Model):
    """Model for storing user favorite products."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text="The user who favorited the product."
    )
    product = models.ForeignKey(
        'core.Product',  # Use string reference to avoid circular import
        on_delete=models.CASCADE,
        related_name='favorited_by',
        help_text="The product that was favorited."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
