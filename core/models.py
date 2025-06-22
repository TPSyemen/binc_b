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
from django.conf import settings

#----------------------------------------------------------------
#           User model
#----------------------------------------------------------------
class User(AbstractUser):
    """
    Custom user model with user type and phone number.
    """
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('customer', 'Customer'),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer',
        verbose_name="User Type",
        help_text="نوع المستخدم: مدير، مالك، أو عميل."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Phone Number",
        help_text="رقم الجوال للمستخدم (اختياري)."
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
        help_text="البريد الإلكتروني للمستخدم. يجب أن يكون فريدًا."
    )
    # last_login و date_joined موروثة من AbstractUser

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

    def get_profile_data(self):
        """
        إرجاع بيانات البروفايل بشكل منسق للاستخدام في الواجهات أو API.
        """
        return {
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "user_type": self.user_type,
            "date_joined": self.date_joined,
            "last_login": self.last_login,
            "is_active": self.is_active,
        }

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

    @property
    def auto_rating(self):
        """
        تقييم المنتج تلقائيًا بناءً على الإعجابات، عدم الإعجاب، شهرة وتقييم البراند، والمحايدين.
        يمكن تعديل الأوزان حسب الحاجة.
        """
        like_score = self.likes * 1.0
        dislike_score = self.dislikes * -1.0
        neutral_score = self.neutrals * 0.2 if hasattr(self, 'neutrals') else 0
        brand_popularity_score = float(self.brand.popularity) * 0.1 if self.brand else 0
        brand_rating_score = float(self.brand.rating) * 1.0 if self.brand else 0

        score = (
            like_score +
            neutral_score +
            brand_popularity_score +
            brand_rating_score +
            dislike_score
        )
        # تحويل النتيجة إلى نطاق 0-5
        score = max(0, min(5, round(score / 10, 2)))
        return score

    def save(self, *args, **kwargs):
        """
        تحديث التقييم تلقائيًا عند كل عملية حفظ ليعكس auto_rating.
        إذا أصبح التقييم عاليًا جدًا (مثلاً >= 4.5)، يتم إرسال إشعار للمالك ولكل مستخدم أعجب بالمنتج.
        """
        self.rating = self.auto_rating
        super().save(*args, **kwargs)

        # إرسال إشعار إذا كان التقييم عاليًا جدًا
        if self.rating >= 4.5:
            # إشعار للمالك
            if self.shop and self.shop.owner and self.shop.owner.user:
                Notification.objects.create(
                    recipient=self.shop.owner.user,
                    content=f"🎉 منتجك '{self.name}' حصل على تقييم مرتفع جدًا!",
                    notification_type='general'
                )
            # إشعار لكل مستخدم أعجب بالمنتج
            for reaction in self.user_reactions.filter(reaction_type='like'):
                Notification.objects.create(
                    recipient=reaction.user,
                    content=f"🎉 المنتج '{self.name}' الذي أعجبت به أصبح من الأعلى تقييمًا!",
                    notification_type='general'
                )

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
    """
    Model for storing notifications.
    """
    NOTIFICATION_TYPES = (
        ('promotion', 'Promotion'),
        ('order', 'Order Update'),
        ('general', 'General'),
        ('inventory', 'Inventory Alert'),
        ('product_rating', 'Product Rating'),
        ('shop_status', 'Shop Status'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    content = models.TextField(verbose_name="Notification Content")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    related_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Related ID")
    action_url = models.URLField(blank=True, null=True, verbose_name="Action URL")
    extra_data = models.JSONField(blank=True, null=True, default=dict, verbose_name="Extra Data")

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.notification_type}"

# دوال مساعدة احترافية للإشعارات

def notify_user(user, content, notification_type='general', action_url=None, extra_data=None):
    Notification.objects.create(
        recipient=user,
        content=content,
        notification_type=notification_type,
        action_url=action_url,
        extra_data=extra_data or {}
    )

def notify_shop_owner(shop, content, notification_type='general', action_url=None, extra_data=None):
    if shop.owner and shop.owner.user:
        notify_user(shop.owner.user, content, notification_type, action_url, extra_data)
