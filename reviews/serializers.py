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
