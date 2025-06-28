from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Owner

@receiver(post_save, sender=User)
def create_owner_for_user(sender, instance, created, **kwargs):
    if created and instance.user_type == 'owner':
        # إذا لم يوجد Owner مرتبط بهذا المستخدم، أنشئه تلقائيًا
        if not hasattr(instance, 'owner_profile'):
            Owner.objects.create(user=instance, email=instance.email, password=instance.password)
