"""
promotions/models.py
--------------------
Defines promotions-related database models.
"""

from django.db import models
from core.models import Product, User
from django.utils.timezone import now
# -----------------------------------------------------------------
#                   Promotion
# -----------------------------------------------------------------
class Promotion(models.Model):
    name = models.CharField(max_length=255, verbose_name="Promotion Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    start_date = models.DateTimeField(default=now, verbose_name="Start Date")
    end_date = models.DateTimeField(default=now, verbose_name="End Date")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    def __str__(self):
        return self.name
# -----------------------------------------------------------------
#                       Discount
# -----------------------------------------------------------------
class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Discount Code")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Discount Percentage")
    max_uses = models.PositiveIntegerField(default=1, verbose_name="Max Uses")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Used Count")
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="discount_codes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discount_codes", null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}%"
