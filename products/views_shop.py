from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from core.models import Shop, Owner
from .serializers import ShopSerializer

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
    parser_classes = [MultiPartParser, FormParser]

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
