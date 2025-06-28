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
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # دعم JSON أيضًا

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "يجب تسجيل الدخول أولاً."}, status=status.HTTP_401_UNAUTHORIZED)
        if getattr(user, 'user_type', None) != 'owner':
            return Response({"detail": "فقط المستخدم من نوع مالك (owner) يمكنه تسجيل متجر."}, status=status.HTTP_403_FORBIDDEN)

        # جلب أو إنشاء Owner profile
        owner, _ = Owner.objects.get_or_create(user=user, defaults={"email": user.email})
        # تحقق من وجود متجر سابق
        shop = getattr(owner, 'shop', None)
        if shop:
            return Response({"error": "لا يمكنك إنشاء أكثر من متجر واحد لهذا الحساب."}, status=status.HTTP_400_BAD_REQUEST)

        # إنشاء المتجر يدويًا بدون Serializer
        from core.models import Shop
        from django.core.exceptions import ValidationError
        data = request.data
        try:
            shop = Shop.objects.create(
                name=data.get('name'),
                owner=owner,
                address=data.get('address', ''),
                description=data.get('description', ''),
                url=data.get('url', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
            )
        except ValidationError as ve:
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "تم تسجيل المتجر بنجاح.", "shop_id": str(shop.id), "shop_name": shop.name}, status=status.HTTP_201_CREATED)

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
