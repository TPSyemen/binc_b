"""
promotions/serializers.py
------------------------
Defines promotions-related DRF serializers.
"""

from rest_framework import serializers
from .models import Promotion, DiscountCode

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = '__all__'
