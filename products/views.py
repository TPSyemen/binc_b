"""
products/views.py
-----------------
Defines product-related API views (list, detail, create, update, etc.).
"""

from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.parsers import JSONParser

from core.models import Product, Category, Brand
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer, BrandSerializer
from products.rating_service import rating_service


class ProductListView(APIView):
    """List all products based on user permissions."""
    permission_classes = [permissions.IsAuthenticated]  # السماح بالوصول العام

    def get(self, request):
        print('--- ProductListView.get ---')
        print('User:', request.user)
        print('User type:', getattr(request.user, 'user_type', None))
        print('is_superuser:', getattr(request.user, 'is_superuser', None))
        print('is_staff:', getattr(request.user, 'is_staff', None))
        print('is_authenticated:', request.user.is_authenticated)
        shop_id = request.GET.get('shop_id')
        if request.user.is_authenticated:
            if request.user.user_type == 'owner':
                products = Product.objects.filter(shop__owner__user=request.user)
            elif request.user.user_type == 'admin':
                products = Product.objects.all()  # جميع المنتجات نشطة وغير نشطة
            else:
                products = Product.objects.filter(is_active=True)
        else:
            # للمستخدمين غير المسجلين، عرض المنتجات النشطة فقط
            products = Product.objects.filter(is_active=True)
        # دعم فلترة المنتجات حسب shop_id إذا تم تمريره في الكويري
        if shop_id:
            products = products.filter(shop__id=shop_id)
        print('عدد المنتجات المسترجعة:', products.count())
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """Retrieve details of a specific product."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        # إذا كان المستخدم أدمن أو سوبر يوزر، اعرض المنتج بغض النظر عن is_active
        if request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'admin':
            product = get_object_or_404(Product, pk=pk)
        else:
            product = get_object_or_404(Product, pk=pk, is_active=True)
        if request.user.is_authenticated:
            product.log_behavior(request.user, 'view')
        serializer = ProductDetailSerializer(product)
        print('--- بيانات المنتج قبل الإرسال ---')
        print(serializer.data)
        return Response(serializer.data)


class ProductCreateView(APIView):
    """Create a new product."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        if request.user.user_type not in ['owner', 'admin']:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(shop=request.user.owner_profile.shop)
            
            # حساب التقييم الأولي للمنتج
            rating_service.calculate_product_rating(product.id)
            
            # إعادة تحميل المنتج بعد تحديث التقييم
            product.refresh_from_db()
            
            return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(APIView):
    """Update a product (يدعم التحديث الجزئي لحالة is_active)."""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.user.user_type == 'owner' and product.shop.owner.user != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductDetailSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.user.user_type == 'owner' and product.shop.owner.user != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductDetailSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDeleteView(APIView):
    """Delete a product."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.user.user_type == 'owner' and product.shop.owner.user != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class FeaturedProductsView(APIView):
    """Retrieve featured products."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.filter(is_featured=True, is_active=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSearchView(APIView):
    """Search for products with filters."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            query = request.GET.get('query', '')
            category_id = request.GET.get('category', None)
            brand = request.GET.get('brand', None)

            products = Product.objects.filter(is_active=True)
            if query:
                products = products.filter(name__icontains=query)
            if category_id:
                products = products.filter(category_id=category_id)
            if brand:
                products = products.filter(brand__name__icontains=brand)

            serializer = ProductListSerializer(products, many=True)
            return Response({"products": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecentlyViewedProductsView(View):
    def get(self, request, *args, **kwargs):
        # Example response for recently viewed products
        return JsonResponse({"recently_viewed": []})


class SimilarProductsView(APIView):
    """Retrieve similar products based on category, price, brand, and popularity."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, id=pk, is_active=True)

            # تحقق من وجود جميع الحقول المطلوبة
            if product.price is None or not product.category or not product.brand:
                return Response({
                    "detail": "المنتج يفتقد بيانات ضرورية (السعر أو التصنيف أو العلامة التجارية)."
                }, status=400)

            # تحقق من أن الكائنات المرتبطة موجودة فعليًا
            if not hasattr(product.brand, 'id') or not hasattr(product.category, 'id'):
                return Response({
                    "detail": "المنتج مرتبط بعلامة تجارية أو تصنيف غير موجود فعليًا."
                }, status=400)

            price_float = float(product.price)
            price_range = 0.2 * price_float  # 20% price range
            min_price = price_float - price_range
            max_price = price_float + price_range

            similar_products = Product.objects.filter(
                Q(category=product.category) &
                Q(price__gte=min_price) &
                Q(price__lte=max_price) &
                Q(brand=product.brand) &
                ~Q(id=product.id)
            ).order_by('-rating', '-views')[:10]

            serializer = ProductListSerializer(similar_products, many=True)
            return Response({
                "current_product": ProductDetailSerializer(product).data,
                "similar_products": serializer.data
            })
        except Exception as e:
            return Response({
                "detail": f"حدث خطأ غير متوقع: {str(e)}"
            }, status=500)


class ProductPriceHistoryView(APIView):
    """عرض تاريخ أسعار المنتج حسب التغييرات المسجلة (إن وجدت)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        # يفترض وجود علاقة أو جدول لتخزين تاريخ الأسعار، هنا مثال مبسط:
        if hasattr(product, 'price_history'):
            history = product.price_history.all().order_by('-date')
            data = [
                {"date": h.date, "price": float(h.price)} for h in history
            ]
        else:
            # إذا لم يوجد تاريخ أسعار، أعد السعر الحالي فقط
            data = [{"date": str(product.last_price_update), "price": float(product.price)}]
        return Response({"product_id": pk, "price_history": data})


class BrandViewSet(viewsets.ModelViewSet):
    """Manage product brands (CRUD)."""
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]
