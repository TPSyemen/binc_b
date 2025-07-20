"""
core/serializers.py
------------------
Defines core DRF serializers (User, Category, etc.).
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django import forms
from .models import Notification, Product, Shop, Brand, Category


User = get_user_model()
# ----------------------------------------------------------
#               Register Serializer
# ----------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل.")
        return value

    def validate(self, data):
        # تحقق من تطابق كلمة المرور
        if data.get('password1') != data.get('password2'):
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            user_type=validated_data.get('user_type')
        )
        return user

# ----------------------------------------------------------------------------
#                   Login Serializer
# -------------------------------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

# Django Forms for HTML templates
class CustomLoginForm(forms.Form):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your username or email',
            'autofocus': True,
            'id': 'username'
        }),
        label='Username or Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'id': 'password'
        }),
        label='Password'
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'rememberMe'
        }),
        label='Remember me'
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Try to authenticate with username first, then email
            user = authenticate(username=username, password=password)

            if user is None:
                raise forms.ValidationError("Invalid username/email or password.")

            if hasattr(user, 'is_banned') and user.is_banned:
                raise forms.ValidationError("This account has been banned.")

            cleaned_data['user'] = user

        return cleaned_data

# ----------------------------------------------------------------------------
#                   Notification Serializer
# -------------------------------------------------------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    recipient_username = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'recipient_username', 'content', 'notification_type',
                  'is_read', 'created_at', 'related_id']
        read_only_fields = ['id', 'recipient', 'created_at']

    def get_recipient_username(self, obj):
        return obj.recipient.username if obj.recipient else None


# ----------------------------------------------------------------------------
#                   Shop Serializer
# -------------------------------------------------------------------------------
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'platform', 'reliability_score', 'is_active']


# ----------------------------------------------------------------------------
#                   Brand Serializer
# -------------------------------------------------------------------------------
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description']


# ----------------------------------------------------------------------------
#                   Category Serializer
# -------------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent']


# ----------------------------------------------------------------------------
#                   Product Serializer
# -------------------------------------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'original_price',
            'discount_percentage', 'image_url', 'product_url', 'sku',
            'is_available', 'stock_quantity', 'rating', 'review_count',
            'shop', 'brand', 'category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

