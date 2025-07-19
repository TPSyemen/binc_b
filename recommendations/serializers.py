"""
recommendations/serializers.py
-----------------------------
Defines recommendation-related DRF serializers.
"""

from rest_framework import serializers
from .models import ProductRecommendation
from core.models import Product  # Correctly import Product from core.models

# ------------------------------------------------------------------
#                       Product Serializer
# ------------------------------------------------------------------

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image_url', 'likes', 'created_at']

# ------------------------------------------------------------------
#                  Product Recommendation Serializer
# ------------------------------------------------------------------
class ProductRecommendationSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = ProductRecommendation
        fields = ['product', 'score', 'created_at']


# ------------------------------------------------------------------
#                  Enhanced Recommendation Serializers
# ------------------------------------------------------------------

class EnhancedProductSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for Product model with shop and brand information.
    """
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'original_price', 'image_url',
            'rating', 'views', 'likes', 'dislikes', 'shop_name', 'brand_name', 'category_name'
        ]


class UserInteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserInteraction model.
    """
    product = EnhancedProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    interaction_type_display = serializers.CharField(source='get_interaction_type_display', read_only=True)

    class Meta:
        model = ProductRecommendation  # This will be updated when we import the new models
        fields = [
            'id', 'product', 'product_id', 'interaction_type', 'interaction_type_display',
            'last_interaction_type', 'interaction_count', 'context',
            'first_interaction_at', 'last_interaction_at'
        ]
        read_only_fields = ['first_interaction_at', 'last_interaction_at']


class CrossStoreRecommendationSerializer(serializers.Serializer):
    """
    Serializer for cross-store recommendation responses.
    """
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    shop_name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    price_difference = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_difference_percentage = serializers.FloatField()
    similarity_score = serializers.FloatField()
    shop_reliability = serializers.FloatField()
    delivery_days = serializers.IntegerField()
    recommendation_reason = serializers.CharField()


class InteractionTriggeredRecommendationSerializer(serializers.Serializer):
    """
    Serializer for interaction-triggered recommendation responses.
    """
    interaction_type = serializers.CharField()
    triggered_by = serializers.DictField()
    recommendations = serializers.DictField()
    session_id = serializers.UUIDField(required=False)


class EnhancedRecommendationRequestSerializer(serializers.Serializer):
    """
    Serializer for enhanced recommendation requests.
    """
    user_id = serializers.UUIDField(required=False)
    product_id = serializers.UUIDField(required=False)
    interaction_type = serializers.CharField(required=False)
    recommendation_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Types of recommendations to include"
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    include_cross_store = serializers.BooleanField(default=True)
    include_similar = serializers.BooleanField(default=True)
    include_complementary = serializers.BooleanField(default=False)
    include_alternatives = serializers.BooleanField(default=False)
    include_trending = serializers.BooleanField(default=True)
    include_better_deals = serializers.BooleanField(default=True)


class UserPreferencesSerializer(serializers.Serializer):
    """
    Serializer for user preferences based on interaction history.
    """
    preferred_brands = serializers.ListField(child=serializers.CharField())
    preferred_categories = serializers.ListField(child=serializers.CharField())
    price_range = serializers.DictField()
    preferred_shops = serializers.ListField(child=serializers.CharField())


class RecommendationAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for recommendation analytics and insights.
    """
    total_interactions = serializers.IntegerField()
    interaction_breakdown = serializers.DictField()
    user_preferences = UserPreferencesSerializer()
    most_interacted_products = serializers.ListField(child=serializers.DictField())
    recommendation_performance = serializers.DictField(required=False)
    cross_store_effectiveness = serializers.DictField(required=False)