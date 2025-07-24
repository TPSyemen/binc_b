"""
comparison/models.py
-------------------
Defines comparison-related database models for advanced cross-store product comparison.
"""

from django.db import models
from django.conf import settings
from core.models import Product, Shop
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ProductComparison(models.Model):
    """
    Model to store user-created product comparisons.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_comparisons',
        null=True,
        blank=True,
        help_text="User who created this comparison (null for anonymous)"
    )
    name = models.CharField(
        max_length=200,
        default="Product Comparison",
        verbose_name="Comparison Name"
    )
    products = models.ManyToManyField(
        Product,
        related_name='comparisons',
        help_text="Products being compared"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Is Public",
        help_text="Whether this comparison can be viewed by others"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.products.count()} products)"


class ComparisonCriteria(models.Model):
    """
    Model to define comparison criteria and their weights.
    """
    CRITERIA_TYPES = (
        ('price', 'Price'),
        ('rating', 'Rating'),
        ('delivery', 'Delivery Time'),
        ('reliability', 'Store Reliability'),
        ('customer_service', 'Customer Service'),
        ('return_policy', 'Return Policy'),
        ('availability', 'Availability'),
        ('brand_reputation', 'Brand Reputation'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Criteria Name"
    )
    criteria_type = models.CharField(
        max_length=20,
        choices=CRITERIA_TYPES,
        verbose_name="Criteria Type"
    )
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.0'),
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('5.0'))],
        verbose_name="Weight",
        help_text="Importance weight for this criteria (0.1 to 5.0)"
    )
    is_higher_better = models.BooleanField(
        default=True,
        verbose_name="Is Higher Better",
        help_text="Whether higher values are better for this criteria"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )

    class Meta:
        verbose_name_plural = "Comparison Criteria"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (weight: {self.weight})"


class ComparisonResult(models.Model):
    """
    Model to store calculated comparison results.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    comparison = models.OneToOneField(
        ProductComparison,
        on_delete=models.CASCADE,
        related_name='result'
    )
    winner_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='won_comparisons',
        null=True,
        blank=True,
        verbose_name="Winner Product"
    )
    overall_scores = models.JSONField(
        default=dict,
        verbose_name="Overall Scores",
        help_text="Calculated scores for each product"
    )
    criteria_breakdown = models.JSONField(
        default=dict,
        verbose_name="Criteria Breakdown",
        help_text="Detailed breakdown by criteria"
    )
    best_deals = models.JSONField(
        default=list,
        verbose_name="Best Deals",
        help_text="Top deals identified in the comparison"
    )
    calculated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Calculated At"
    )

    def __str__(self):
        winner_name = self.winner_product.name if self.winner_product else "No winner"
        return f"Result for {self.comparison.name}: {winner_name}"


class ComparisonShare(models.Model):
    """
    Model for sharing comparison results.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    comparison = models.ForeignKey(
        ProductComparison,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    share_token = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="Share Token"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expires At"
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="View Count"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    def __str__(self):
        return f"Share for {self.comparison.name} (token: {self.share_token})"


class ComparisonTemplate(models.Model):
    """
    Model for predefined comparison templates.
    """
    TEMPLATE_CATEGORIES = (
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('home', 'Home & Garden'),
        ('sports', 'Sports & Outdoors'),
        ('books', 'Books'),
        ('general', 'General'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Template Name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    category = models.CharField(
        max_length=20,
        choices=TEMPLATE_CATEGORIES,
        default='general',
        verbose_name="Category"
    )
    criteria = models.ManyToManyField(
        ComparisonCriteria,
        through='TemplateCriteria',
        related_name='templates'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Is Default Template"
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Usage Count"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class TemplateCriteria(models.Model):
    """
    Through model for template criteria with custom weights.
    """
    template = models.ForeignKey(
        ComparisonTemplate,
        on_delete=models.CASCADE
    )
    criteria = models.ForeignKey(
        ComparisonCriteria,
        on_delete=models.CASCADE
    )
    custom_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('5.0'))],
        verbose_name="Custom Weight",
        help_text="Override the default criteria weight for this template"
    )

    class Meta:
        unique_together = ['template', 'criteria']

    def get_effective_weight(self):
        """Get the effective weight (custom or default)."""
        return self.custom_weight if self.custom_weight else self.criteria.weight
