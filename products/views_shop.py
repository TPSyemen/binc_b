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
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        # تحقق فقط من user_type
        if getattr(request.user, 'user_type', None) != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )
        # جلب المتجر بناءً على علاقة Shop مع Owner عبر user_type فقط
        owner = Owner.objects.filter(user=request.user).first()
        if not owner:
            return Response({"has_shop": False, "detail": "لا يوجد متجر مرتبط بهذا المالك بعد."}, status=status.HTTP_200_OK)
        shop = getattr(owner, 'shop', None)
        if shop:
            serializer = ShopSerializer(shop)
            return Response({"has_shop": True, "shop": serializer.data}, status=status.HTTP_200_OK)
        return Response({"has_shop": False, "detail": "لا يوجد متجر مرتبط بهذا المالك بعد."}, status=status.HTTP_200_OK)

class ShopRegisterView(APIView):
    """Register a new shop for the authenticated owner."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def post(self, request):
        # تحقق فقط من نوع المستخدم
        if getattr(request.user, 'user_type', None) != 'owner':
            return Response(
                {"detail": "ليس لديك صلاحية للقيام بهذا الإجراء. فقط المستخدم من نوع مالك (owner) يمكنه تسجيل متجر."},
                status=status.HTTP_403_FORBIDDEN
            )
        # السماح للمالك بمتجر واحد فقط
        owner, _ = Owner.objects.get_or_create(user=request.user, defaults={"email": request.user.email})
        if hasattr(owner, 'shop') and owner.shop is not None:
            return Response({"error": "لديك متجر بالفعل."}, status=status.HTTP_400_BAD_REQUEST)
        # إنشاء متجر جديد بدون أي شروط إضافية
        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=owner)
            return Response({"message": "تم تسجيل المتجر بنجاح.", "shop": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShopListView(APIView):
    """عرض جميع المتاجر مع بيانات مختصرة (id, name, logo)."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

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
    parser_classes = [JSONParser]

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
