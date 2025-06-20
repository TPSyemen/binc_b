import os
import sys
import django
import json

# إضافة مسار المشروع لمسار بايثون
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')
django.setup()

from core.models import Product

def export_all_products_json():
    products = Product.objects.all()
    data = []
    for p in products:
        data.append({
            'id': str(p.id),
            'name': p.name,
            'price': str(p.price),
            'is_active': p.is_active,
            'category': str(p.category) if p.category else None,
            'shop': str(p.shop) if p.shop else None,
            'created_at': p.created_at.isoformat() if hasattr(p, 'created_at') and p.created_at else None,
        })
    with open('all_products_admin.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'تم تصدير {len(data)} منتجًا إلى all_products_admin.json')

if __name__ == '__main__':
    export_all_products_json()
