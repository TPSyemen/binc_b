"""
reviews/models.py
-----------------
Defines review-related database models.
"""

from django.db import models
from django.conf import settings
from core.models import Product  # Assuming Product is defined in core.models

class Review(models.Model):
    """Model for product reviews."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user} for {self.product} - {self.rating} stars"
