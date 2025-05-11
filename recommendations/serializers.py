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