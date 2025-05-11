from celery import shared_task
from core.models import Product
from products.rating_service import rating_service
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_all_product_ratings():
    """مهمة دورية لتحديث تقييمات جميع المنتجات"""
    products = Product.objects.all()
    updated_count = 0
    
    for product in products:
        try:
            rating_service.calculate_product_rating(product.id)
            updated_count += 1
        except Exception as e:
            logger.error(f"فشل تحديث تقييم المنتج {product.id}: {e}")
    
    logger.info(f"تم تحديث تقييمات {updated_count} منتج بنجاح")
    return updated_count