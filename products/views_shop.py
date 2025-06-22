from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from core.models import Shop, Owner, Product
from .serializers import ShopSerializer
from rest_framework import viewsets
from rest_framework.decorators import action

class ShopCheckView(APIView):
    """Check if the authenticated owner has a shop."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # التحقق من وجود ملف تعريف المالك
        try:
            owner = request.user.owner_profile
        except Owner.DoesNotExist:
            return Response(
                {"error": "ملف تعريف المالك غير موجود."},
                status=status.HTTP_404_NOT_FOUND
            )

        # التحقق من وجود متجر للمالك
        try:
            shop = owner.shop
            serializer = ShopSerializer(shop)
            return Response(
                {"has_shop": True, "shop": serializer.data},
                status=status.HTTP_200_OK
            )
        except Shop.DoesNotExist:
            return Response(
                {"has_shop": False},
                status=status.HTTP_404_NOT_FOUND
            )

class ShopRegisterView(APIView):
    """Register a new shop for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def post(self, request):
        # التحقق من أن المستخدم هو مالك
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # التحقق من وجود ملف تعريف المالك
        try:
            owner = request.user.owner_profile
        except Owner.DoesNotExist:
            # إنشاء ملف تعريف المالك إذا لم يكن موجودًا
            owner = Owner.objects.create(
                user=request.user,
                email=request.user.email,
                password=request.user.password  # ملاحظة: هذا ليس آمنًا، ولكن نستخدمه للتبسيط
            )

        # التحقق من أن المالك ليس لديه متجر بالفعل
        try:
            shop = owner.shop
            return Response(
                {"error": "لديك متجر بالفعل."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Shop.DoesNotExist:
            # إنشاء متجر جديد
            serializer = ShopSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=owner)
                return Response(
                    {"message": "تم تسجيل المتجر بنجاح.", "shop": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShopListView(APIView):
    """عرض جميع المتاجر مع بيانات مختصرة (id, name, logo)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from core.models import Shop
        shops = Shop.objects.all()
        data = [
            {
                "id": str(shop.id),
                "name": shop.name,
                "logo": shop.logo.url if shop.logo else None
            }
            for shop in shops
        ]
        return Response(data)

class ShopDetailView(APIView):
    """عرض تفاصيل متجر بناءً على معرف المتجر."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        from core.models import Shop
        shop = get_object_or_404(Shop, pk=pk)
        from .serializers import ShopSerializer
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='toggle-products')
    def toggle_products(self, request, pk=None):
        """تفعيل أو تعطيل جميع المنتجات المرتبطة بمتجر معين"""
        shop = self.get_object()
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'error': 'يرجى تحديد الحالة is_active.'}, status=400)
        products = Product.objects.filter(shop=shop)
        updated = products.update(is_active=bool(is_active))
        return Response({'updated': updated, 'is_active': bool(is_active)})
