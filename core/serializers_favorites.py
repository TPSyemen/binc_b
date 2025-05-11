from rest_framework import serializers
from .models_favorites import Favorite
from products.serializers import ProductListSerializer

class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model."""
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'product', 'created_at')
        read_only_fields = ('user',)
