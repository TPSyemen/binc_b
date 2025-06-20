import os
import sys
import django

def setup_django_environment():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')
    django.setup()

def create_admin_gmail():
    from core.models import User
    email = 'admin@gmail.com'
    username = 'admin'
    password = 'adminadmin'
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        print('تم إنشاء مستخدم أدمن admin@gmail.com بنجاح.')
    else:
        print('المستخدم admin@gmail.com موجود بالفعل.')

def print_all_product_ids():
    from core.models import Product
    print('--- جميع معرفات المنتجات في قاعدة البيانات ---')
    for p in Product.objects.all():
        print(f'id: {p.id}, name: {p.name}, is_active: {p.is_active}')

if __name__ == "__main__":
    setup_django_environment()
    create_admin_gmail()
    print_all_product_ids()
