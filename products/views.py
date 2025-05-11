from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
from django.http import JsonResponse

from core.models import Product, Category
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer
from products.rating_service import rating_service


class ProductListView(APIView):
    """List all products based on user permissions."""
    permission_classes = [permissions.AllowAny]  # السماح بالوصول العام

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.user_type == 'owner':
                products = Product.objects.filter(shop__owner__user=request.user)
            elif request.user.user_type == 'admin':
                products = Product.objects.all()
            else:
                products = Product.objects.filter(is_active=True)
        else:
            # للمستخدمين غير المسجلين، عرض المنتجات النشطة فقط
            products = Product.objects.filter(is_active=True)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """Retrieve details of a specific product."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        if request.user.is_authenticated:
            product.log_behavior(request.user, 'view')
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


class ProductCreateView(APIView):
    """Create a new product."""
    permission_classes = [permissions.IsAuthenticated]

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
    """Update a product."""
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

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Convertir Decimal a float para operaciones matemáticas
        price_float = float(product.price)
        price_range = 0.2 * price_float  # 20% price range

        # Calcular los límites de precio
        min_price = price_float - price_range
        max_price = price_float + price_range

        similar_products = Product.objects.filter(
            Q(category=product.category) &
            Q(price__gte=min_price) &
            Q(price__lte=max_price) &
            Q(brand=product.brand) &
            ~Q(id=product.id)  # Exclude the current product
        ).order_by('-rating', '-views')[:10]  # Order by rating and views

        serializer = ProductListSerializer(similar_products, many=True)
        return Response({
            "current_product": ProductDetailSerializer(product).data,
            "similar_products": serializer.data
        })
