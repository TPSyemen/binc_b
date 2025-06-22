"""
comparison/views.py
------------------
Defines comparison-related API views.
"""

from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import JSONParser
from core.models import Product
from products.serializers import ProductDetailSerializer

# Create your views here.
# ------------------------------------------------------------------------
#                       Comparison View
# --------------------------------------------------------------------------------
class ComparisonView(APIView):
    """Compare a product with similar products or compare multiple products or get the best product."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request, product_id=None):
        """
        GET /api/comparison/<product_id>/compare/ : مقارنة منتج مع المتشابهة
        GET /api/comparison/?best=1 : مقارنة جميع المنتجات وإرجاع الأفضل
        """
        best = request.query_params.get('best')
        if best == '1':
            # مقارنة جميع المنتجات وإرجاع الأفضل
            products = Product.objects.filter(is_active=True)
            if not products.exists():
                return Response({"detail": "لا توجد منتجات للمقارنة."}, status=404)
            # يمكن تخصيص منطق اختيار الأفضل (هنا حسب أعلى rating ثم views)
            best_product = products.order_by('-rating', '-views').first()
            return Response({
                "best_product": ProductDetailSerializer(best_product).data,
                "note": "تم اختيار هذا المنتج كأفضل منتج بناءً على التقييم وعدد المشاهدات."
            })
        if product_id:
            # مقارنة منتج مع المتشابهة
            product = get_object_or_404(Product, id=product_id, is_active=True)
            price_float = float(product.price)
            min_price = price_float * 0.8
            max_price = price_float * 1.2
            similar_products = Product.objects.filter(
                category=product.category,
                price__gte=min_price,
                price__lte=max_price,
                is_active=True
            ).exclude(id=product.id).order_by('-rating', '-views')[:5]
            return Response({
                "product": ProductDetailSerializer(product).data,
                "similar_products": ProductDetailSerializer(similar_products, many=True).data
            })
        return Response({"detail": "يرجى تحديد نوع المقارنة أو معرف المنتج."}, status=400)

    def post(self, request):
        """
        POST /api/comparison/ : مقارنة بين عدة منتجات
        Body: {"product_ids": ["id1", "id2", ...]}
        """
        product_ids = request.data.get("product_ids", [])
        if not product_ids or len(product_ids) < 2:
            return Response({"detail": "يجب اختيار منتجين أو أكثر للمقارنة."}, status=400)
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        if products.count() != len(product_ids):
            return Response({"detail": "منتج واحد أو أكثر غير موجود أو غير نشط."}, status=404)
        categories = set([str(p.category_id) for p in products])
        if len(categories) > 1:
            return Response({
                "detail": "لا يمكن مقارنة منتجات من فئات مختلفة. يرجى اختيار منتجات من نفس الفئة فقط."
            }, status=400)
        # منطق المقارنة (يمكن تخصيصه)
        comparison = {"fields": [
            "name", "brand", "price", "rating", "likes", "dislikes", "views", "is_featured"
        ]}
        # اختيار الأفضل بينهم
        best_product = sorted(products, key=lambda p: (p.rating, p.views), reverse=True)[0]
        return Response({
            "products": ProductDetailSerializer(products, many=True).data,
            "comparison": comparison,
            "best_product": ProductDetailSerializer(best_product).data,
            "note": "تم وسم المنتج الأفضل بناءً على التقييم وعدد المشاهدات."
        })
