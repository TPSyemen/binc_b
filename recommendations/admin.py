"""
recommendations/admin.py
-----------------------
Admin configuration for recommendation models.
"""

from django.contrib import admin

from .models import UserBehaviorLog

# Register your models here.
admin.site.register(UserBehaviorLog)
