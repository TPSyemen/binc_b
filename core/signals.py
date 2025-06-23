from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Product, Brand

# تحديث تقييم المنتج تلقائيًا عند كل تغيير في الإعجابات أو عدم الإعجاب أو المشاهدات أو البراند
@receiver(post_save, sender=Product)
def update_product_rating_on_save(sender, instance, **kwargs):
    # لا تحدث إذا كان الحفظ فقط لحقل rating (لتفادي الحلقة اللانهائية)
    update_fields = kwargs.get('update_fields', None)
    if update_fields is not None and 'rating' in update_fields and len(update_fields) == 1:
        return
    instance.rating = instance.auto_rating
    instance.save(update_fields=["rating"])

@receiver(post_save, sender=Brand)
def update_brand_rating_on_save(sender, instance, **kwargs):
    # يمكن إضافة منطق خاص بتحديث تقييم البراند هنا إذا كان هناك دوال مشابهة
    pass
