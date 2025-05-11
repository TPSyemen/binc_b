from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification


User = get_user_model()
# ----------------------------------------------------------
#               Register Serializer
# ----------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type')
        )
        return user

# ----------------------------------------------------------------------------
#                   Login Serializer
# -------------------------------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

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
    
