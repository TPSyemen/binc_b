"""
core/models.py
--------------
Defines core database models (User, Category, etc.).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.apps import apps  # Use apps.get_model to resolve circular imports
from .models_favorites import Favorite  # Import the Favorite model
from .models_verification import EmailVerificationToken, ActionVerificationToken  # Import verification models
from .models_preferences import UserPreference, BrandPreference  # Import preferences models

#----------------------------------------------------------------
#           User model
#----------------------------------------------------------------
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('customer', 'Customer'),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer',
        verbose_name="User Type"
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',  # Added related_name to avoid conflict
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_set',  # Added related_name to avoid conflict
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name="Is Banned",
        help_text="Indicates whether the user is banned."
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Is Email Verified",
        help_text="Indicates whether the user's email has been verified."
    )

    def has_permission(self, permission):
        """Check if the user has a specific permission based on user_type."""
        if self.user_type == 'admin':
            return True
        elif self.user_type == 'owner':
            return permission in ['manage_shop', 'manage_products']
        elif self.user_type == 'customer':
            return permission in ['view_products', 'write_reviews']
        return False

#----------------------------------------------------------------
#                   Owner Role
#----------------------------------------------------------------
class Owner(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    email = models.EmailField(unique=True, verbose_name="Email")
    password = models.CharField(max_length=255, verbose_name="Password")

    last_login_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Last Login Date"
    )

    def __str__(self):
        return self.user.username

#----------------------------------------------------------------
#                       Shop module
#----------------------------------------------------------------
class Shop(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Shop Name"
    )
    owner = models.OneToOneField(Owner, on_delete=models.CASCADE, related_name='shop')

    address = models.CharField(
        max_length=500,
        verbose_name="Shop Address",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Shop Description"
    )
    logo = models.ImageField(
        upload_to='shop_logos/',
        null=True,
        verbose_name="Shop Logo"
    )
    banner = models.ImageField(
        upload_to='shop_banners/',
        verbose_name="Shop Banner",
        blank=True,
        null=True
    )
    url = models.URLField(
        verbose_name="Shop URL"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Shop Phone"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Shop Email"
    )
    social_media = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Social Media Links"
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name="Is Banned",
        help_text="Indicates whether the shop is banned."
    )

    def __str__(self):
        return self.name

#----------------------------------------------------------------
#                           Brand models
#----------------------------------------------------------------
class Brand(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Brand Name"
    )
    popularity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name="Popularity Score"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))],
        verbose_name="Brand Rating"
    )
    likes = models.PositiveIntegerField(
        default=0,
        verbose_name="Likes"
    )
    dislikes = models.PositiveIntegerField(
        default=0,
        verbose_name="Dislikes"
    )

    def __str__(self):
        return self.name

#----------------------------------------------------------------
#                       Category models
#----------------------------------------------------------------
class Category(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Category Name"
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description"
    )

    def __str__(self):
        return self.name

#----------------------------------------------------------------
#                       Product models
#----------------------------------------------------------------
class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=4000,
        unique=True,
        verbose_name="Product Name"
    )
    brand = models.ForeignKey(
        Brand,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name="Brand",
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name="Category"
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Price (USD)"
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Original Price (USD)",
        null=True,
        blank=True
    )
    is_featured = models.BooleanField(default=False)
    release_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Release Date"
    )
    last_price_update = models.DateField(
        null=True,
        blank=True,
        verbose_name="Last Price Update"
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Image URL"
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Video URL"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))],
        verbose_name="Product Rating"
    )
    likes = models.PositiveIntegerField(
        default=0,
        verbose_name="Likes"
    )
    dislikes = models.PositiveIntegerField(
        default=0,
        verbose_name="Dislikes"
    )
    neutrals = models.PositiveIntegerField(
        default=0,
        verbose_name="Neutrals"
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name="Views",
        help_text="Number of times the product has been viewed."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Indicates whether the product is active and visible."
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name="In Stock",
        help_text="Indicates whether the product is currently in stock."
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name="Is Banned",
        help_text="Indicates whether the product is banned."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    def __str__(self):
        return f"{self.name} ({self.brand.name})"

    def log_behavior(self, user, action):
        UserBehaviorLog = apps.get_model('recommendations', 'UserBehaviorLog')  # Dynamically get the model
        UserBehaviorLog.objects.create(user=user, product=self, action=action)

    @property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if hasattr(self, 'original_price') and self.original_price and self.original_price > self.price:
            return round(((self.original_price - self.price) / self.original_price) * 100, 2)
        return 0

#----------------------------------------------------------------
#                    Specification models
#----------------------------------------------------------------
class SpecificationCategory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="المعرف الفريد لتصنيف المواصفات"
    )
    category_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="اسم تصنيف المواصفات"
    )

    def __str__(self):
        return self.category_name

#----------------------------------------------------------------
#                       Specification model
#----------------------------------------------------------------
class Specification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="المعرف الفريد للمواصفة"
    )
    category = models.ForeignKey(
        SpecificationCategory,
        on_delete=models.CASCADE,
        help_text="تصنيف المواصفة"
    )
    specification_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="اسم المواصفة"
    )

    def __str__(self):
        return self.specification_name

#----------------------------------------------------------------
#                   Product Speci fication
#----------------------------------------------------------------
class ProductSpecification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="المعرف الفريد لربط المنتج بالمواصفة"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        help_text="المنتج المرتبط بالمواصفة"
    )
    specification = models.ForeignKey(
        Specification, on_delete=models.CASCADE,
        help_text="المواصفة المرتبطة بالمنتج"
    )
    specification_value = models.CharField(
        max_length=255,
        help_text="قيمة المواصفة للمنتج"
    )

    class Meta:
        unique_together = ('product', 'specification')
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specification"

    def __str__(self):
        return f"{self.product.name} - {self.specification.specification_name}: {self.specification_value}"

#----------------------------------------------------------------
#                       Seller Rating model
#----------------------------------------------------------------
class SellerRating(models.Model):
    """Model for storing seller ratings."""
    seller = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_ratings')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Rating"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Comment")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        unique_together = ('seller', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Rating for {self.seller.name} by {self.user.username}"

#----------------------------------------------------------------
#                   Customer model
#----------------------------------------------------------------
class Customer(models.Model):
    """Model for storing customer information."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Customer Name")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return self.name

#----------------------------------------------------------------
#                   Notification model
#----------------------------------------------------------------
class Notification(models.Model):
    """Model for storing notifications."""
    NOTIFICATION_TYPES = (
        ('promotion', 'Promotion'),
        ('order', 'Order Update'),
        ('general', 'General'),
        ('inventory', 'Inventory Alert'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    content = models.TextField(verbose_name="Notification Content")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    related_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Related ID")

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.notification_type}"

#----------------------------------------------------------------
#                   User Product Reaction model
#----------------------------------------------------------------
class UserProductReaction(models.Model):
    """Model for storing user reactions to products (like, dislike, neutral)."""
    REACTION_TYPES = (
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('neutral', 'Neutral'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='neutral')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "User Product Reaction"
        verbose_name_plural = "User Product Reactions"

    def __str__(self):
        return f"{self.user.username}'s {self.reaction_type} reaction to {self.product.name}"
