"""
reviews/serializers.py
---------------------
Defines review-related DRF serializers.
"""

from rest_framework import serializers
from core.models import User
from .models import Review
from nltk.sentiment.vader import SentimentIntensityAnalyzer
# ----------------------------------------------------------------
#                       Review User Serializer
# ----------------------------------------------------------------
class ReviewUserSerializer(serializers.ModelSerializer):
    """Serializer for user information in reviews."""
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'name')  # حذف avatar لأنه غير موجود في نموذج User

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
# ----------------------------------------------------------------
#                   Review Serializer
# ----------------------------------------------------------------
class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for the Review model."""
    user = ReviewUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
# ----------------------------------------------------------------
#                   Create Review Serializer
# ----------------------------------------------------------------
class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating a review. التقييم يتم توليده تلقائياً من التعليق."""

    class Meta:
        model = Review
        fields = ('comment',)  # لا نسمح للمستخدم بإرسال rating

    def create(self, validated_data):
        product_id = self.context['product_id']
        user = self.context['request'].user
        comment = validated_data.get('comment', '')

        from core.models import Product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Invalid product_id.")

        if Review.objects.filter(product=product, user=user).exists():
            raise serializers.ValidationError("You have already reviewed this product.")

        # تحليل المشاعر للتعليق وتوليد rating تلقائي
        sia = SentimentIntensityAnalyzer()
        sentiment = sia.polarity_scores(comment)
        compound = sentiment['compound']
        # تحويل compound score إلى تقييم من 1 إلى 5
        if compound >= 0.6:
            rating = 5
        elif compound >= 0.2:
            rating = 4
        elif compound > -0.2:
            rating = 3
        elif compound > -0.6:
            rating = 2
        else:
            rating = 1

        return Review.objects.create(product=product, user=user, comment=comment, rating=rating)


# ----------------------------------------------------------------
#                   Enhanced Feedback Serializers
# ----------------------------------------------------------------

class EnhancedReviewSerializer(serializers.ModelSerializer):
    """Enhanced serializer for displaying reviews with sentiment analysis."""
    user = ReviewUserSerializer(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='product.shop.name', read_only=True)
    sentiment_label_display = serializers.CharField(source='get_sentiment_label_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    engagement_ratio = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product_name', 'shop_name', 'rating', 'title',
            'comment', 'pros', 'cons', 'verified_purchase', 'sentiment_score',
            'sentiment_label', 'sentiment_label_display', 'status', 'status_display',
            'helpfulness_score', 'likes', 'dislikes', 'engagement_ratio', 'created_at'
        ]


class StoreReviewSerializer(serializers.ModelSerializer):
    """Serializer for store reviews."""
    user = ReviewUserSerializer(read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    shop_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Review  # This will be updated when we import the new models
        fields = [
            'id', 'shop_id', 'shop_name', 'user', 'overall_rating',
            'delivery_rating', 'customer_service_rating', 'product_quality_rating',
            'value_for_money_rating', 'title', 'comment', 'order_reference',
            'purchase_amount', 'sentiment_score', 'helpfulness_score',
            'likes', 'dislikes', 'created_at'
        ]


class ReviewHelpfulnessSerializer(serializers.ModelSerializer):
    """Serializer for review helpfulness votes."""
    user = ReviewUserSerializer(read_only=True)

    class Meta:
        model = Review  # This will be updated when we import the new models
        fields = ['id', 'review', 'user', 'vote', 'created_at']


class ProductEngagementSerializer(serializers.ModelSerializer):
    """Serializer for product engagement metrics."""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review  # This will be updated when we import the new models
        fields = [
            'id', 'product', 'product_name', 'total_views', 'unique_views',
            'total_likes', 'total_dislikes', 'total_shares', 'total_saves',
            'add_to_cart_count', 'purchase_count', 'conversion_rate',
            'total_reviews', 'average_rating', 'review_sentiment_score',
            'comparison_count', 'won_comparisons', 'last_updated'
        ]


class EngagementEventSerializer(serializers.ModelSerializer):
    """Serializer for engagement events."""
    user = ReviewUserSerializer(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = Review  # This will be updated when we import the new models
        fields = [
            'id', 'user', 'session_id', 'event_type', 'event_type_display',
            'product', 'product_name', 'shop', 'shop_name', 'event_data',
            'page_url', 'referrer_url', 'timestamp'
        ]


class UserFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for user platform feedback."""
    user = ReviewUserSerializer(read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Review  # This will be updated when we import the new models
        fields = [
            'id', 'user', 'email', 'feedback_type', 'feedback_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'title', 'description', 'page_url', 'sentiment_score',
            'category_prediction', 'created_at', 'updated_at', 'resolved_at'
        ]


class ReviewAnalyticsSerializer(serializers.Serializer):
    """Serializer for review analytics responses."""
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    sentiment_distribution = serializers.DictField()
    verified_purchase_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    recent_trends = serializers.DictField()


class StoreAnalyticsSerializer(serializers.Serializer):
    """Serializer for store analytics responses."""
    total_reviews = serializers.IntegerField()
    overall_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    delivery_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    customer_service_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    product_quality_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    value_for_money_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    recent_trends = serializers.DictField()


class EngagementAnalyticsSerializer(serializers.Serializer):
    """Serializer for engagement analytics responses."""
    total_events = serializers.IntegerField()
    recent_activity = serializers.IntegerField()
    event_type_distribution = serializers.ListField(child=serializers.DictField())
    most_engaged_products = serializers.ListField(child=serializers.DictField())
    engagement_score = serializers.IntegerField()
