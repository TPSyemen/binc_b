"""
comparison/serializers.py
-------------------------
Serializers for comparison models and API responses.
"""

from rest_framework import serializers
from .models import (
    ProductComparison, ComparisonCriteria, ComparisonResult,
    ComparisonTemplate, ComparisonShare, TemplateCriteria
)
from core.models import Product
from products.serializers import ProductSerializer


class ComparisonCriteriaSerializer(serializers.ModelSerializer):
    criteria_type_display = serializers.CharField(source='get_criteria_type_display', read_only=True)
    
    class Meta:
        model = ComparisonCriteria
        fields = [
            'id', 'name', 'criteria_type', 'criteria_type_display',
            'weight', 'is_higher_better', 'is_active'
        ]


class TemplateCriteriaSerializer(serializers.ModelSerializer):
    criteria = ComparisonCriteriaSerializer(read_only=True)
    effective_weight = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateCriteria
        fields = ['criteria', 'custom_weight', 'effective_weight']
    
    def get_effective_weight(self, obj):
        return float(obj.get_effective_weight())


class ComparisonTemplateSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    criteria_details = TemplateCriteriaSerializer(
        source='templatecriteria_set', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = ComparisonTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'is_default', 'usage_count', 'created_at', 'criteria_details'
        ]
        read_only_fields = ['usage_count', 'created_at']


class ProductComparisonSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    products_count = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProductComparison
        fields = [
            'id', 'name', 'products', 'product_ids', 'products_count',
            'user', 'user_name', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.count()
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids')
        comparison = ProductComparison.objects.create(**validated_data)
        
        # Add products to the comparison
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        comparison.products.set(products)
        
        return comparison


class ComparisonResultSerializer(serializers.ModelSerializer):
    comparison = ProductComparisonSerializer(read_only=True)
    winner_product = ProductSerializer(read_only=True)
    
    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'comparison', 'winner_product', 'overall_scores',
            'criteria_breakdown', 'best_deals', 'calculated_at'
        ]


class ComparisonShareSerializer(serializers.ModelSerializer):
    comparison = ProductComparisonSerializer(read_only=True)
    share_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonShare
        fields = [
            'id', 'comparison', 'share_token', 'share_url',
            'expires_at', 'is_expired', 'view_count', 'created_at'
        ]
        read_only_fields = ['share_token', 'view_count', 'created_at']
    
    def get_share_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/comparison/shared/{obj.share_token}/')
        return f'/api/comparison/shared/{obj.share_token}/'
    
    def get_is_expired(self, obj):
        if not obj.expires_at:
            return False
        return timezone.now() > obj.expires_at


class AdvancedComparisonRequestSerializer(serializers.Serializer):
    """
    Serializer for advanced comparison requests.
    """
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        max_length=10,
        help_text="List of product IDs to compare (2-10 products)"
    )
    criteria_weights = serializers.DictField(
        child=serializers.FloatField(min_value=0.1, max_value=5.0),
        required=False,
        help_text="Custom weights for comparison criteria"
    )
    template_id = serializers.UUIDField(
        required=False,
        help_text="ID of comparison template to use"
    )
    save_comparison = serializers.BooleanField(
        default=False,
        help_text="Whether to save this comparison for future reference"
    )
    comparison_name = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Name for saved comparison"
    )
    is_public = serializers.BooleanField(
        default=False,
        help_text="Whether saved comparison should be public"
    )


class AdvancedComparisonResponseSerializer(serializers.Serializer):
    """
    Serializer for advanced comparison responses.
    """
    products = serializers.ListField(
        child=serializers.DictField(),
        help_text="Detailed product comparison data"
    )
    winner = serializers.DictField(
        help_text="Overall winner of the comparison"
    )
    criteria_breakdown = serializers.DictField(
        help_text="Detailed breakdown by criteria"
    )
    best_deals = serializers.ListField(
        child=serializers.DictField(),
        help_text="Best deals identified"
    )
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Textual recommendations"
    )
    criteria_weights = serializers.DictField(
        help_text="Criteria weights used in comparison"
    )
    comparison_summary = serializers.DictField(
        help_text="Summary statistics"
    )
    saved_comparison_id = serializers.UUIDField(
        required=False,
        help_text="ID of saved comparison if requested"
    )


class SimilarProductsRequestSerializer(serializers.Serializer):
    """
    Serializer for similar products search requests.
    """
    product_id = serializers.UUIDField(
        help_text="ID of the product to find similar products for"
    )
    similarity_threshold = serializers.FloatField(
        default=0.8,
        min_value=0.1,
        max_value=1.0,
        help_text="Similarity threshold (0.1-1.0)"
    )
    max_results = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum number of similar products to return"
    )
    include_same_store = serializers.BooleanField(
        default=False,
        help_text="Whether to include products from the same store"
    )


class CrossStoreComparisonSerializer(serializers.Serializer):
    """
    Serializer for cross-store product comparison.
    """
    product_name = serializers.CharField()
    category = serializers.CharField()
    brand = serializers.CharField(allow_null=True)
    stores = serializers.ListField(
        child=serializers.DictField()
    )
    price_analysis = serializers.DictField()
    availability_analysis = serializers.DictField()
    delivery_analysis = serializers.DictField()
    reliability_analysis = serializers.DictField()
    best_overall_deal = serializers.DictField()
    recommendations = serializers.ListField(
        child=serializers.CharField()
    )


class ComparisonInsightsSerializer(serializers.Serializer):
    """
    Serializer for comparison insights and analytics.
    """
    total_comparisons = serializers.IntegerField()
    popular_categories = serializers.ListField(
        child=serializers.DictField()
    )
    average_price_savings = serializers.DecimalField(max_digits=10, decimal_places=2)
    most_compared_products = serializers.ListField(
        child=serializers.DictField()
    )
    store_performance_summary = serializers.DictField()
    trending_comparisons = serializers.ListField(
        child=serializers.DictField()
    )
