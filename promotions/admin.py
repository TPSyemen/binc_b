"""
promotions/admin.py
-------------------
Admin configuration for promotions models.
"""

from django.contrib import admin

from .models import Promotion, DiscountCode

admin.site.register(Promotion)
admin.site.register(DiscountCode)
