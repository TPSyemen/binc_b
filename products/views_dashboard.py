from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from core.models import Shop, Product, User, Category
from .serializers import (
    ShopSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    DashboardStatsSerializer
)
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import json

class DashboardStatsView(APIView):
    """Get dashboard statistics for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على الإحصائيات
        now = timezone.now()
        last_month = now - timedelta(days=30)

        # إحصائيات المنتجات
        total_products = Product.objects.filter(shop=shop, is_active=True).count()

        # إحصائيات العملاء (تقديرية بدون طلبات)
        total_customers = 0
        customers_change = 0

        # المنتجات الأكثر شعبية (بناءً على المشاهدات بدلاً من المبيعات)
        top_products = Product.objects.filter(
            shop=shop,
            is_active=True
        ).order_by('-views')[:5]

        # تجميع البيانات
        stats = {
            'total_products': total_products,
            'total_customers': total_customers,
            'customers_change': customers_change,
            'top_products': ProductListSerializer(top_products, many=True).data
        }

        return Response(stats, status=status.HTTP_200_OK)

class OwnerProductsView(APIView):
    """Get, create, update and delete products for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def get(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على منتجات المتجر
        products = Product.objects.filter(shop=shop)

        # تطبيق التصفية إذا تم توفيرها
        category = request.query_params.get('category')
        if category:
            products = products.filter(category__name=category)

        search = request.query_params.get('search')
        if search:
            products = products.filter(name__icontains=search)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            products = products.filter(is_active=is_active_bool)

        in_stock = request.query_params.get('in_stock')
        if in_stock is not None:
            in_stock_bool = in_stock.lower() == 'true'
            products = products.filter(in_stock=in_stock_bool)

        # ترتيب المنتجات
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')

        if sort_order == 'desc':
            sort_by = f'-{sort_by}'

        products = products.order_by(sort_by)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        إنشاء منتج جديد للمالك الحالي فقط، مع ربطه بمتجره والتحقق من التصنيف.
        يقبل category كاسم أو category_id كـ UUID.
        يمنع تمرير shop أو owner في البيانات.
        """
        if request.user.user_type != 'owner':
            return Response({'error': 'يجب أن تكون مالكًا لإنشاء منتج.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            shop = request.user.owner_profile.shop
        except Exception:
            return Response({'error': 'لم يتم العثور على متجر مرتبط بهذا المالك.'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('shop', None)
        data.pop('owner', None)

        # معالجة التصنيف
        category_id = data.get('category_id')
        category_name = data.get('category')
        if not category_id and not category_name:
            return Response({'category_id': 'يجب تحديد التصنيف (category_id أو category).'}, status=status.HTTP_400_BAD_REQUEST)
        if category_name and not category_id:
            category_obj, _ = Category.objects.get_or_create(name=category_name)
            data['category_id'] = str(category_obj.id)
        if 'category' in data:
            data.pop('category')

        serializer = ProductDetailSerializer(data=data)
        if serializer.is_valid():
            product = serializer.save(shop=shop)
            return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OwnerProductDetailView(APIView):
    """Get, update and delete a specific product for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def get(self, request, product_id):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على المنتج
        try:
            product = Product.objects.get(id=product_id, shop=shop)
        except Product.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على المنتج."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, product_id):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على المنتج
        try:
            product = Product.objects.get(id=product_id, shop=shop)
        except Product.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على المنتج."},
                status=status.HTTP_404_NOT_FOUND
            )

        # تحديث المنتج
        data = request.data.copy()

        # التحقق من وجود الفئة
        if 'category_id' not in data and 'category' in data:
            # إذا كانت category UUID (وليس اسم نصي)
            import uuid
            try:
                uuid.UUID(str(data['category']))
                data['category_id'] = data['category']
            except Exception:
                try:
                    category = Category.objects.get(name=data['category'])
                    data['category_id'] = category.id
                except Category.DoesNotExist:
                    # إنشاء فئة جديدة إذا لم تكن موجودة
                    category = Category.objects.create(name=data['category'])
                    data['category_id'] = category.id
        # إذا أرسلت category_id مباشرة
        if 'category_id' not in data and 'category_id' in request.data:
            data['category_id'] = request.data['category_id']

        # معالجة release_date لقبول صيغ مختلفة وتحويلها إلى YYYY-MM-DD
        if 'release_date' in data and data['release_date']:
            from datetime import datetime
            date_val = data['release_date']
            if isinstance(date_val, str):
                # جرب تحويل الصيغة تلقائيًا
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y.%m.%d", "%d.%m.%Y"):
                    try:
                        data['release_date'] = datetime.strptime(date_val, fmt).strftime("%Y-%m-%d")
                        break
                    except Exception:
                        continue
                else:
                    # إذا لم تنجح أي صيغة، أزل الحقل لتفادي الخطأ
                    data.pop('release_date')

        serializer = ProductDetailSerializer(product, data=data, partial=True)
        if serializer.is_valid():
            try:
                updated_product = serializer.save()
                return Response(ProductDetailSerializer(updated_product).data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على المنتج
        try:
            product = Product.objects.get(id=product_id, shop=shop)
        except Product.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على المنتج."},
                status=status.HTTP_404_NOT_FOUND
            )

        # حذف المنتج
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class OwnerAnalyticsView(APIView):
    """Get analytics data for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # الحصول على نطاق التاريخ
        time_range = request.query_params.get('time_range', 'month')
        now = timezone.now()

        if time_range == 'week':
            start_date = now - timedelta(days=7)
            date_format = '%Y-%m-%d'
            group_by = 'day'
        elif time_range == 'month':
            start_date = now - timedelta(days=30)
            date_format = '%Y-%m-%d'
            group_by = 'day'
        elif time_range == 'year':
            start_date = now - timedelta(days=365)
            date_format = '%Y-%m'
            group_by = 'month'
        else:
            return Response(
                {"error": "نطاق التاريخ غير صالح. الخيارات المتاحة: week, month, year"},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        # تم تعطيل منطق المبيعات لعدم وجود Order
        sales_chart = []
        top_products_chart = []
        traffic_sources = [
            {'source': 'مباشر', 'visits': 120, 'percentage': 40},
            {'source': 'محركات البحث', 'visits': 90, 'percentage': 30},
            {'source': 'وسائل التواصل الاجتماعي', 'visits': 60, 'percentage': 20},
            {'source': 'مصادر أخرى', 'visits': 30, 'percentage': 10}
        ]
        analytics = {
            'sales_chart': sales_chart,
            'top_products_chart': top_products_chart,
            'traffic_sources': traffic_sources
        }

        return Response(analytics, status=status.HTTP_200_OK)

class OwnerShopSettingsView(APIView):
    """Get and update shop settings for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def get(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ShopSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # الحصول على متجر المالك
        try:
            shop = request.user.owner_profile.shop
        except:
            return Response(
                {"error": "لم يتم العثور على متجر مرتبط بهذا المالك."},
                status=status.HTTP_404_NOT_FOUND
            )

        # تحديث إعدادات المتجر
        serializer = ShopSerializer(shop, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AdminProductActivateView(View):
    def post(self, request, pk):
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'admin':
            return HttpResponseForbidden('Not allowed')
        product = get_object_or_404(Product, pk=pk)
        data = json.loads(request.body)
        product.is_active = data.get('is_active', True)
        product.save()
        return JsonResponse({'success': True, 'is_active': product.is_active})

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AdminProductNotifyOwnerView(View):
    def post(self, request, pk):
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'admin':
            return HttpResponseForbidden('Not allowed')
        product = get_object_or_404(Product, pk=pk)
        data = json.loads(request.body)
        message = data.get('message', '')
        # هنا من المفترض إرسال إشعار لصاحب المتجر (يمكنك ربطها بخدمة إشعارات حقيقية)
        # مثال: NotificationService.send(product.shop.owner.user, message)
        # الآن فقط نعيد رسالة نجاح وهمية
        return JsonResponse({'success': True, 'message': message, 'owner': str(product.shop.owner.user)})
