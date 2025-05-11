"""
نظام الإشعارات الذكية المعزز بالذكاء الاصطناعي
يقوم بتحليل بيانات المستخدم وسلوكه لتوليد إشعارات مخصصة وذكية
"""

import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q, F
from .models import User, Notification
from products.models import Product

logger = logging.getLogger(__name__)

class AINotificationGenerator:
    """مولد الإشعارات الذكية باستخدام الذكاء الاصطناعي."""
    
    def __init__(self, user):
        """
        تهيئة مولد الإشعارات الذكية.
        
        Args:
            user (User): المستخدم الذي سيتم توليد الإشعارات له
        """
        self.user = user
        self.generated_notifications = []
    
    def generate_notifications(self):
        """
        توليد إشعارات ذكية بناءً على بيانات المستخدم وسلوكه.
        
        Returns:
            list: قائمة بالإشعارات المولدة
        """
        if not self.user.is_authenticated:
            logger.warning("Cannot generate notifications for unauthenticated user")
            return []
        
        # تنظيف الإشعارات القديمة المشابهة
        self._clean_old_similar_notifications()
        
        # توليد الإشعارات حسب نوع المستخدم
        if self.user.user_type == 'owner':
            self._generate_owner_notifications()
        elif self.user.user_type == 'customer':
            self._generate_customer_notifications()
        elif self.user.user_type == 'admin':
            self._generate_admin_notifications()
        
        return self.generated_notifications
    
    def _clean_old_similar_notifications(self):
        """حذف الإشعارات القديمة المشابهة لتجنب التكرار."""
        # حذف الإشعارات المشابهة التي تم إنشاؤها في آخر 24 ساعة
        yesterday = timezone.now() - timedelta(days=1)
        Notification.objects.filter(
            recipient=self.user,
            created_at__gte=yesterday,
            notification_type__in=['inventory', 'general']
        ).delete()
    
    def _generate_owner_notifications(self):
        """توليد إشعارات ذكية لمالكي المتاجر."""
        try:
            # الحصول على متجر المالك
            shop = self.user.owner_profile.shop
            
            # 1. إشعارات المنتجات غير النشطة
            self._generate_inactive_products_notification(shop)
            
            # 2. إشعارات المنتجات الأكثر مشاهدة
            self._generate_top_viewed_products_notification(shop)
            
            # 3. إشعارات التقييمات الجديدة
            self._generate_recent_reviews_notification(shop)
            
            # 4. إشعارات اكتمال ملف المتجر
            self._generate_shop_profile_completion_notification(shop)
            
            # 5. إشعارات تحليل المنافسين
            self._generate_competitor_analysis_notification(shop)
            
            # 6. إشعارات اقتراحات تحسين المنتجات
            self._generate_product_improvement_suggestions(shop)
            
        except Exception as e:
            logger.error(f"Error generating owner notifications: {str(e)}")
    
    def _generate_customer_notifications(self):
        """توليد إشعارات ذكية للعملاء."""
        try:
            # 1. إشعارات المنتجات الموصى بها
            self._generate_recommended_products_notification()
            
            # 2. إشعارات المنتجات المشابهة للمنتجات المشاهدة مؤخرًا
            self._generate_similar_products_notification()
            
            # 3. إشعارات المنتجات الجديدة في الفئات المفضلة
            self._generate_new_products_in_favorite_categories()
            
        except Exception as e:
            logger.error(f"Error generating customer notifications: {str(e)}")
    
    def _generate_admin_notifications(self):
        """توليد إشعارات ذكية للمسؤولين."""
        try:
            # 1. إشعارات المستخدمين الجدد
            self._generate_new_users_notification()
            
            # 2. إشعارات المتاجر الجديدة
            self._generate_new_shops_notification()
            
            # 3. إشعارات المنتجات المبلغ عنها
            self._generate_reported_products_notification()
            
        except Exception as e:
            logger.error(f"Error generating admin notifications: {str(e)}")
    
    def _generate_inactive_products_notification(self, shop):
        """توليد إشعار للمنتجات غير النشطة."""
        inactive_products = shop.products.filter(is_active=False)
        
        if inactive_products.exists():
            count = inactive_products.count()
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"لديك {count} منتج غير نشط. قم بتفعيلها لزيادة ظهورها في نتائج البحث والمقارنات.",
                notification_type='inventory',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_top_viewed_products_notification(self, shop):
        """توليد إشعار للمنتجات الأكثر مشاهدة."""
        top_viewed_products = shop.products.filter(
            is_active=True
        ).order_by('-views')[:3]
        
        if top_viewed_products.exists():
            product_names = ", ".join([p.name[:30] + "..." if len(p.name) > 30 else p.name for p in top_viewed_products])
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"منتجاتك الأكثر مشاهدة: {product_names}. استفد من شعبيتها بإضافة المزيد من المعلومات والمواصفات!",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_recent_reviews_notification(self, shop):
        """توليد إشعار للتقييمات الجديدة."""
        recent_reviews = []
        
        for product in shop.products.all():
            product_reviews = product.reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            )
            recent_reviews.extend(product_reviews)
        
        if recent_reviews:
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"لديك {len(recent_reviews)} تقييم جديد في الأسبوع الماضي. اطلع عليها الآن للتعرف على آراء العملاء!",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_shop_profile_completion_notification(self, shop):
        """توليد إشعار لاكتمال ملف المتجر."""
        required_fields = ['name', 'address', 'description', 'logo', 'url', 'phone', 'email', 'social_media']
        completed = sum(1 for field in required_fields if getattr(shop, field))
        completion_percentage = int((completed / len(required_fields)) * 100)
        
        if completion_percentage < 100:
            missing_fields = [field for field in required_fields if not getattr(shop, field)]
            missing_fields_str = ", ".join(missing_fields)
            
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"ملف متجرك مكتمل بنسبة {completion_percentage}%. أضف {missing_fields_str} لتحسين ظهور متجرك في نتائج البحث.",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_competitor_analysis_notification(self, shop):
        """توليد إشعار لتحليل المنافسين."""
        # الحصول على فئات منتجات المتجر
        shop_categories = set(shop.products.values_list('category_id', flat=True))
        
        if not shop_categories:
            return
        
        # البحث عن المتاجر المنافسة (التي لديها منتجات في نفس الفئات)
        competitor_shops = Product.objects.filter(
            category_id__in=shop_categories
        ).exclude(
            shop=shop
        ).values('shop').annotate(
            product_count=Count('id')
        ).order_by('-product_count')[:3]
        
        if competitor_shops:
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"تم تحديد {len(competitor_shops)} متجر منافس في فئات منتجاتك. قم بتحليل منتجاتهم لتحسين عروضك!",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_product_improvement_suggestions(self, shop):
        """توليد إشعار لاقتراحات تحسين المنتجات."""
        # البحث عن المنتجات التي تفتقر إلى المواصفات الكافية
        products_without_specs = shop.products.annotate(
            spec_count=Count('specifications')
        ).filter(
            spec_count__lt=3,  # أقل من 3 مواصفات
            is_active=True
        )[:5]
        
        if products_without_specs:
            product_names = ", ".join([p.name[:20] + "..." if len(p.name) > 20 else p.name for p in products_without_specs])
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"يمكنك تحسين منتجاتك التالية بإضافة المزيد من المواصفات: {product_names}",
                notification_type='inventory',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_recommended_products_notification(self):
        """توليد إشعار للمنتجات الموصى بها للعملاء."""
        # هذه الوظيفة تحتاج إلى تكامل مع نظام التوصيات
        pass
    
    def _generate_similar_products_notification(self):
        """توليد إشعار للمنتجات المشابهة للمنتجات المشاهدة مؤخرًا."""
        # هذه الوظيفة تحتاج إلى تكامل مع نظام التوصيات
        pass
    
    def _generate_new_products_in_favorite_categories(self):
        """توليد إشعار للمنتجات الجديدة في الفئات المفضلة."""
        # هذه الوظيفة تحتاج إلى تكامل مع نظام التفضيلات
        pass
    
    def _generate_new_users_notification(self):
        """توليد إشعار للمستخدمين الجدد."""
        # الحصول على المستخدمين الجدد في آخر 24 ساعة
        yesterday = timezone.now() - timedelta(days=1)
        new_users = User.objects.filter(date_joined__gte=yesterday)
        
        if new_users.exists():
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"انضم {new_users.count()} مستخدم جديد إلى المنصة في آخر 24 ساعة.",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_new_shops_notification(self):
        """توليد إشعار للمتاجر الجديدة."""
        # الحصول على المتاجر الجديدة في آخر أسبوع
        last_week = timezone.now() - timedelta(days=7)
        from core.models import Shop
        new_shops = Shop.objects.filter(created_at__gte=last_week)
        
        if new_shops.exists():
            notification = Notification.objects.create(
                recipient=self.user,
                content=f"تم إضافة {new_shops.count()} متجر جديد إلى المنصة في آخر أسبوع.",
                notification_type='general',
                is_read=False
            )
            self.generated_notifications.append(notification)
    
    def _generate_reported_products_notification(self):
        """توليد إشعار للمنتجات المبلغ عنها."""
        # هذه الوظيفة تحتاج إلى تكامل مع نظام الإبلاغ عن المنتجات
        pass
