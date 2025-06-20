import os
import sys
import django

def setup_django_environment():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')
    django.setup()

def promote_admin():
    from core.models import User
    user = User.objects.filter(email='admin@gmail.com').first()
    if user:
        user.is_superuser = True
        user.is_staff = True
        user.user_type = 'admin'
        user.save()
        print('admin@gmail.com تمت ترقيته كأدمن كامل الصلاحيات.')
    else:
        print('لم يتم العثور على مستخدم admin@gmail.com')

if __name__ == "__main__":
    setup_django_environment()
    promote_admin()
