from rest_framework import serializers
from .models_preferences import UserPreference, BrandPreference
from products.serializers import BrandSerializer

class BrandPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for the BrandPreference model."""
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = BrandPreference
        fields = ('id', 'brand', 'brand_id', 'created_at')
        read_only_fields = ('id', 'created_at')


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for the UserPreference model."""
    brand_preferences = BrandPreferenceSerializer(many=True, read_only=True)
    preferred_brands = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = UserPreference
        fields = ('id', 'min_price', 'max_price', 'brand_preferences', 'preferred_brands', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        preferred_brands = validated_data.pop('preferred_brands', [])
        user_preference = UserPreference.objects.create(**validated_data)
        
        # Create brand preferences
        for brand_id in preferred_brands:
            BrandPreference.objects.create(
                user_preference=user_preference,
                brand_id=brand_id
            )
        
        return user_preference
    
    def update(self, instance, validated_data):
        preferred_brands = validated_data.pop('preferred_brands', None)
        
        # Update user preference fields
        instance.min_price = validated_data.get('min_price', instance.min_price)
        instance.max_price = validated_data.get('max_price', instance.max_price)
        instance.save()
        
        # Update brand preferences if provided
        if preferred_brands is not None:
            # Remove existing brand preferences
            instance.brand_preferences.all().delete()
            
            # Create new brand preferences
            for brand_id in preferred_brands:
                BrandPreference.objects.create(
                    user_preference=instance,
                    brand_id=brand_id
                )
        
        return instance
