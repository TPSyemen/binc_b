"""
products/serializers.py
----------------------
Defines product-related DRF serializers.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from reviews.serializers import ReviewSerializer
from core.models import Category, Product, Shop, Customer, Brand, SpecificationCategory, Specification, ProductSpecification
# from .serializers import ShopOwnerSerializer  # تم التعليق لمنع الاستيراد الدائري

User = get_user_model()

#----------------------------------------------------------------
#                   Shop Owner Serializer
#----------------------------------------------------------------
class ShopOwnerSerializer(serializers.ModelSerializer):
    owner_username = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    class Meta:
        model = Shop
        fields = ('id', 'name', 'owner_username', 'owner_email')
    def get_owner_username(self, obj):
        return obj.owner.user.username if obj.owner and obj.owner.user else None
    def get_owner_email(self, obj):
        return obj.owner.user.email if obj.owner and obj.owner.user else None

#----------------------------------------------------------------
#                 Category Serializer
#----------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'product_count')

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

#----------------------------------------------------------------

#                   ProductList Serializer
#----------------------------------------------------------------
class ProductListSerializer(serializers.ModelSerializer):

    category = CategorySerializer(read_only=True)
    discount = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'original_price', 'discount',
                  'category', 'image_url', 'rating', 'in_stock', 'is_active')

    def get_discount(self, obj):
        return obj.discount_percentage

#----------------------------------------------------------------
#                   Brand Serializer
#----------------------------------------------------------------
class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'name', 'popularity', 'rating', 'likes', 'dislikes', 'product_count')

    def get_product_count(self, obj):
        return obj.products.count()

#----------------------------------------------------------------
#                   Product Detail Serializer
#----------------------------------------------------------------
class ProductDetailSerializer(serializers.ModelSerializer):

    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    shop = ShopOwnerSerializer(read_only=True)
    discount = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True, required=False)
    in_stock = serializers.BooleanField(read_only=True, required=False)
    stock = serializers.IntegerField(required=False)

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'original_price',
                  'discount', 'category', 'brand', 'shop', 'image_url', 'in_stock', 'rating', 'is_active', 'created_at', 'stock',
                  'reviews', 'video_url', 'release_date', 'likes', 'dislikes', 'neutrals',
                  'views', 'is_banned')
        extra_kwargs = {
            'brand': {'required': False},
            'rating': {'required': False, 'default': 0},
            'original_price': {'required': False},
            'is_active': {'default': True}
        }

    def get_discount(self, obj):
        return obj.discount_percentage

    def create(self, validated_data):
        # Asignar valores predeterminados si no están presentes
        if 'rating' not in validated_data:
            validated_data['rating'] = 0
        if 'in_stock' not in validated_data:
            validated_data['in_stock'] = True

        # Eliminar el campo stock si está presente, ya que no existe en el modelo
        if 'stock' in validated_data:
            validated_data.pop('stock')

        # Crear el producto
        return super().create(validated_data)

#----------------------------------------------------------------
#                   Shop Serializer
#----------------------------------------------------------------
class ShopSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'address', 'description', 'logo', 'banner', 'url',
                 'phone', 'email', 'social_media', 'owner_name', 'product_count',
                 'completion_percentage')
        read_only_fields = ('id', 'owner_name', 'product_count', 'completion_percentage')

    def get_owner_name(self, obj):
        if obj.owner and obj.owner.user:
            return obj.owner.user.username
        return None

    def get_product_count(self, obj):
        return obj.products.count()

    def get_completion_percentage(self, obj):
        required_fields = ['name', 'address', 'description', 'logo', 'url', 'phone', 'email']
        completed = sum(1 for field in required_fields if getattr(obj, field))
        return int((completed / len(required_fields)) * 100)


#----------------------------------------------------------------
#                   ProductList Serializer
#----------------------------------------------------------------
class ProductListSerializer(serializers.ModelSerializer):

    category = CategorySerializer(read_only=True)
    discount = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    shop_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'original_price', 'discount',
                  'category', 'image_url', 'rating', 'likes','dislikes',
                  'neutrals', 'is_active', 'shop_name', 'in_stock', 'views')

    def get_discount(self, obj):
        if obj.original_price and obj.price and obj.original_price > obj.price:
            return int(((obj.original_price - obj.price) / obj.original_price) * 100)
        return 0

    def get_shop_name(self, obj):
        if obj.shop:
            return obj.shop.name
        return None

#----------------------------------------------------------------
#                   Brand Serializer
#----------------------------------------------------------------
class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'name', 'popularity', 'rating', 'likes', 'dislikes', 'product_count')

    def get_product_count(self, obj):
        return obj.products.count()

#----------------------------------------------------------------
#                   Product Detail Serializer
#----------------------------------------------------------------
class ProductDetailSerializer(serializers.ModelSerializer):

    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    shop = ShopOwnerSerializer(read_only=True)
    discount = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True, required=False)
    in_stock = serializers.BooleanField(read_only=True, required=False)
    stock = serializers.IntegerField(required=False)

    def get_shop_name(self, obj):
        if obj.shop:
            return obj.shop.name
        return None

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'original_price',
                  'discount', 'category', 'brand', 'shop', 'image_url', 'in_stock', 'rating', 'is_active', 'created_at', 'stock',
                  'reviews', 'video_url', 'release_date', 'likes', 'dislikes', 'neutrals',
                  'views', 'is_banned')
        extra_kwargs = {
            'brand': {'required': False},
            'rating': {'read_only': True},  # جعل حقل التقييم للقراءة فقط
            'original_price': {'required': False},
            'is_active': {'default': True}
        }

    def get_discount(self, obj):
        if obj.original_price and obj.price and obj.original_price > obj.price:
            return int(((obj.original_price - obj.price) / obj.original_price) * 100)
        return 0

    def create(self, validated_data):
        # Asignar valores predeterminados si no están presentes
        if 'rating' not in validated_data:
            validated_data['rating'] = 0
        if 'in_stock' not in validated_data:
            validated_data['in_stock'] = True

        # Eliminar el campo stock si está presente, ya que no existe en el modelo
        if 'stock' in validated_data:
            validated_data.pop('stock')

        # Crear el producto
        return super().create(validated_data)

#----------------------------------------------------------------
#                   Customer Serializer
#----------------------------------------------------------------
class CustomerSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'address', 'user_email')

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return None



#----------------------------------------------------------------
#                   Dashboard Stats Serializer
#----------------------------------------------------------------
class DashboardStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    customers_change = serializers.FloatField()
    top_products = ProductListSerializer(many=True)

#----------------------------------------------------------------
#                   Specification Category Serializer
#----------------------------------------------------------------
class SpecificationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationCategory
        fields = ('id', 'category_name')

#----------------------------------------------------------------
#                   Specification Serializer
#----------------------------------------------------------------
class SpecificationSerializer(serializers.ModelSerializer):
    category = SpecificationCategorySerializer(read_only=True)

    class Meta:
        model = Specification
        fields = ('id', 'category', 'specification_name')

#----------------------------------------------------------------
#                   Product Specification Serializer
#----------------------------------------------------------------
class ProductSpecificationSerializer(serializers.ModelSerializer):
    specification = SpecificationSerializer(read_only=True)
    specification_id = serializers.PrimaryKeyRelatedField(
        queryset=Specification.objects.all(),
        source='specification',
        write_only=True
    )

    class Meta:
        model = ProductSpecification
        fields = ('id', 'specification', 'specification_id', 'specification_value')
        read_only_fields = ('id',)
