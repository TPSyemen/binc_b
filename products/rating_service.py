import logging
from django.db.models import Avg, Count
from django.conf import settings
from core.models import Product
from recommendations.models import UserBehaviorLog
from recommendations.ai_services import recommendation_service

logger = logging.getLogger(__name__)

class AutomaticRatingService:
    """خدمة لحساب تقييم المنتج تلقائ<|im_start|> بناءً على سلوك المستخدم وتحليل الوصف والعلامة التجارية"""

    def __init__(self):
        self.recommendation_service = recommendation_service

    def calculate_product_rating(self, product_id):
        """
        حساب تقييم المنتج بناءً على:
        1. تفاعلات المستخدمين (إعجاب/عدم إعجاب/محايد)
        2. سمعة العلامة التجارية
        3. عدد المشاهدات
        4. تحليل وصف المنتج
        """
        try:
            product = Product.objects.get(id=product_id)

            # 1. حساب تقييم بناءً على تفاعلات المستخدمين (40% من التقييم النهائي)
            user_rating = self._calculate_user_reaction_rating(product)

            # 2. حساب تقييم بناءً على سمعة العلامة التجارية (20% من التقييم النهائي)
            brand_rating = self._calculate_brand_rating(product.brand)

            # 3. حساب تقييم بناءً على عدد المشاهدات (20% من التقييم النهائي)
            views_rating = self._calculate_views_rating(product.views)

            # 4. حساب تقييم بناءً على تحليل وصف المنتج (20% من التقييم النهائي)
            description_rating = self._analyze_product_description(product.description)

            # حساب التقييم النهائي (مرجح)
            final_rating = (user_rating * 0.4) + (brand_rating * 0.2) + (views_rating * 0.2) + (description_rating * 0.2)

            # تحديث تقييم المنتج (بدون إخطار المالك)
            product.rating = round(final_rating, 2)
            product.save(update_fields=['rating'])

            logger.info(f"تم تحديث تقييم المنتج {product.id} إلى {product.rating}")
            return product.rating

        except Exception as e:
            logger.error(f"خطأ في حساب تقييم المنتج {product_id}: {e}")
            return None

    def _calculate_user_reaction_rating(self, product):
        """حساب تقييم بناءً على تفاعلات المستخدمين"""
        total_reactions = product.likes + product.dislikes + product.neutrals

        if total_reactions == 0:
            return 2.5  # تقييم محايد افتراضي

        # حساب التقييم بناءً على نسبة الإعجابات وعدم الإعجابات
        # الإعجابات = 5 نجوم، عدم الإعجاب = 1 نجمة، محايد = 3 نجوم
        weighted_sum = (product.likes * 5) + (product.neutrals * 3) + (product.dislikes * 1)
        return weighted_sum / total_reactions

    def _calculate_brand_rating(self, brand):
        """حساب تقييم بناءً على سمعة العلامة التجارية"""
        # حساب متوسط تقييم منتجات العلامة التجارية
        brand_avg_rating = Product.objects.filter(
            brand=brand
        ).exclude(
            rating=0
        ).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 2.5

        return brand_avg_rating

    def _calculate_views_rating(self, views):
        """تحويل عدد المشاهدات إلى تقييم (1 إلى 5) بناءً على توزيع منطقي"""
        if views >= 1000:
            return 5.0
        elif views >= 500:
            return 4.0
        elif views >= 100:
            return 3.0
        elif views >= 10:
            return 2.0
        else:
            return 1.0

    def _analyze_product_description(self, description):
        """تحليل وصف المنتج لتقدير جودته"""
        if not description:
            return 2.5  # تقييم محايد للأوصاف الفارغة

        # تقييم طول الوصف (وصف أطول = تقييم أفضل، حتى حد معين)
        length_score = min(5, max(1, len(description) / 100))

        # يمكن استخدام تحليل المشاعر إذا كان متاحًا ومناسبًا
        # على سبيل المثال، إذا كانت هناك مكتبة لتحليل المشاعر، يمكن استخدامها هنا
        sentiment_score = 2.5  # افتراضي محايد

        # دمج تقييم الطول مع تقييم المشاعر
        return (length_score + sentiment_score) / 2

rating_service = AutomaticRatingService()