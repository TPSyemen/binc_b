"""
comparison/views.py
------------------
Defines comparison-related API views with advanced cross-store comparison capabilities.
"""

from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from core.models import Product
from products.serializers import ProductDetailSerializer
from .comparison_engine import AdvancedComparisonEngine
from .models import (
    ProductComparison, ComparisonCriteria, ComparisonResult,
    ComparisonTemplate, ComparisonShare
)
from .serializers import (
    ProductComparisonSerializer, ComparisonCriteriaSerializer,
    ComparisonResultSerializer, ComparisonTemplateSerializer
)
import secrets
from datetime import timedelta
from django.utils import timezone

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


class AdvancedComparisonViewSet(viewsets.ViewSet):
    """
    Advanced comparison functionality with cross-store analysis.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comparison_engine = AdvancedComparisonEngine()

    @action(detail=False, methods=['post'])
    def advanced_compare(self, request):
        """
        Perform advanced comparison using the comparison engine.
        """
        from .serializers import (
            AdvancedComparisonRequestSerializer,
            AdvancedComparisonResponseSerializer
        )

        serializer = AdvancedComparisonRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            # Perform comparison
            result = self.comparison_engine.compare_products(
                product_ids=data['product_ids'],
                criteria_weights=data.get('criteria_weights'),
                template_id=data.get('template_id')
            )

            # Save comparison if requested
            saved_comparison_id = None
            if data.get('save_comparison') and request.user.is_authenticated:
                comparison = ProductComparison.objects.create(
                    user=request.user,
                    name=data.get('comparison_name', 'Product Comparison'),
                    is_public=data.get('is_public', False)
                )

                # Add products to comparison
                products = Product.objects.filter(id__in=data['product_ids'])
                comparison.products.set(products)

                # Save result
                ComparisonResult.objects.create(
                    comparison=comparison,
                    winner_product_id=result['winner']['product_id'],
                    overall_scores=result['products'],
                    criteria_breakdown=result['criteria_breakdown'],
                    best_deals=result['best_deals']
                )

                saved_comparison_id = str(comparison.id)

            # Add saved comparison ID to result
            if saved_comparison_id:
                result['saved_comparison_id'] = saved_comparison_id

            response_serializer = AdvancedComparisonResponseSerializer(result)
            return Response(response_serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def find_similar(self, request):
        """
        Find similar products across different stores.
        """
        from .serializers import SimilarProductsRequestSerializer
        from store_integration.aggregation_services import ProductAggregationService

        serializer = SimilarProductsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            product = Product.objects.get(id=data['product_id'])
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Find similar products
        similar_products = ProductAggregationService.find_similar_products(
            product,
            similarity_threshold=data['similarity_threshold']
        )

        # Filter out same store if requested
        if not data['include_same_store']:
            similar_products = [
                sp for sp in similar_products
                if sp['product'].shop != product.shop
            ]

        # Limit results
        similar_products = similar_products[:data['max_results']]

        return Response({
            'original_product': {
                'id': str(product.id),
                'name': product.name,
                'price': float(product.price),
                'shop': product.shop.name,
                'rating': float(product.rating)
            },
            'similar_products': [
                {
                    'id': str(sp['product'].id),
                    'name': sp['product'].name,
                    'price': float(sp['product'].price),
                    'shop': sp['product'].shop.name,
                    'rating': float(sp['product'].rating),
                    'similarity_score': sp['similarity_score'],
                    'price_difference': sp['price_difference'],
                    'price_difference_percentage': sp['price_difference_percentage'],
                    'shop_reliability': sp['shop_reliability'],
                    'delivery_days': sp['delivery_days']
                }
                for sp in similar_products
            ],
            'search_parameters': data,
            'total_found': len(similar_products)
        })

    @action(detail=False, methods=['get'])
    def cross_store_analysis(self, request):
        """
        Analyze products across different stores for the same item.
        """
        product_name = request.query_params.get('product_name')
        category_id = request.query_params.get('category_id')

        if not product_name and not category_id:
            return Response(
                {'error': 'Either product_name or category_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build query
        products = Product.objects.filter(is_active=True).select_related('shop', 'brand')

        if product_name:
            products = products.filter(name__icontains=product_name)

        if category_id:
            products = products.filter(category_id=category_id)

        if not products.exists():
            return Response(
                {'error': 'No products found matching criteria'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Group by similar products
        from store_integration.aggregation_services import ProductAggregationService

        # For simplicity, take first product and find similar ones
        base_product = products.first()
        similar_products = ProductAggregationService.find_similar_products(
            base_product, similarity_threshold=0.7
        )

        all_products = [base_product] + [sp['product'] for sp in similar_products]

        # Analyze across stores
        stores_data = []
        prices = []
        delivery_times = []
        reliability_scores = []

        for product in all_products:
            store_data = {
                'product_id': str(product.id),
                'product_name': product.name,
                'shop_id': str(product.shop.id),
                'shop_name': product.shop.name,
                'price': float(product.price),
                'original_price': float(product.original_price) if product.original_price else None,
                'rating': float(product.rating),
                'delivery_days': product.shop.average_delivery_days,
                'reliability_score': float(product.shop.reliability_score),
                'customer_service_rating': float(product.shop.customer_service_rating),
                'return_policy_days': product.shop.return_policy_days,
                'is_available': product.is_active
            }
            stores_data.append(store_data)
            prices.append(float(product.price))
            delivery_times.append(product.shop.average_delivery_days)
            reliability_scores.append(float(product.shop.reliability_score))

        # Calculate best deal
        best_deal = min(stores_data, key=lambda x: x['price'])

        from .serializers import CrossStoreComparisonSerializer

        analysis_data = {
            'product_name': base_product.name,
            'category': base_product.category.name,
            'brand': base_product.brand.name if base_product.brand else None,
            'stores': stores_data,
            'price_analysis': {
                'lowest_price': min(prices),
                'highest_price': max(prices),
                'average_price': sum(prices) / len(prices),
                'price_range': max(prices) - min(prices),
                'savings_potential': max(prices) - min(prices)
            },
            'availability_analysis': {
                'total_stores': len(stores_data),
                'available_stores': len([s for s in stores_data if s['is_available']]),
                'availability_rate': len([s for s in stores_data if s['is_available']]) / len(stores_data)
            },
            'delivery_analysis': {
                'fastest_delivery': min(delivery_times),
                'slowest_delivery': max(delivery_times),
                'average_delivery': sum(delivery_times) / len(delivery_times)
            },
            'reliability_analysis': {
                'highest_reliability': max(reliability_scores),
                'lowest_reliability': min(reliability_scores),
                'average_reliability': sum(reliability_scores) / len(reliability_scores)
            },
            'best_overall_deal': best_deal,
            'recommendations': [
                f"💰 Save ${max(prices) - min(prices):.2f} by choosing the lowest price option",
                f"🚚 Get fastest delivery in {min(delivery_times)} days",
                f"⭐ Highest reliability score: {max(reliability_scores)}/5",
                f"🏆 Best overall deal: {best_deal['shop_name']} at ${best_deal['price']}"
            ]
        }

        serializer = CrossStoreComparisonSerializer(analysis_data)
        return Response(serializer.data)
