"""
core/views.py
-------------
Defines core API views (authentication, user management, etc.).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import RegisterSerializer, LoginSerializer
from .email_service import send_verification_email
from rest_framework import viewsets

User = get_user_model()

# ---------------------------------------------------------------------------
#                   Register API View
# ---------------------------------------------------------------------------------
class RegisterAPIView(APIView):
    """
    Register a new user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "user_type": getattr(user, 'user_type', 'default'),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------------------------------------------------------
#                   Login API View
#-------------------------------------------------------------------------------------
class LoginAPIView(APIView):
    """
    Login using email and password.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "بيانات الاعتماد غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)
        if user:
            if getattr(user, 'is_banned', False):
                return Response({"error": "User is banned."}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "user_type": getattr(user, 'user_type', 'default'),
                },
                "permissions": list(user.get_all_permissions()),
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# ---------------------------------------------------------------------------------
#                       Logout API View
# ---------------------------------------------------------------------------------------
class LogoutAPIView(APIView):
    """
    Logout and invalidate the token.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]  # تأكد من استخدام JWTAuthentication

    def post(self, request):
        try:
            # التحقق من أن المستخدم مسجل الدخول
            if not request.user.is_authenticated:
                return Response({"error": "User is not logged in or token is missing."}, status=status.HTTP_401_UNAUTHORIZED)

            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # إبطال صلاحية رمز التحديث
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # التحقق من حالة تسجيل الدخول
        if request.user.is_authenticated:
            return Response({"message": "User is logged in."}, status=status.HTTP_200_OK)
        return Response({"error": "User is not logged in."}, status=status.HTTP_401_UNAUTHORIZED)

# ---------------------------------------------------------------------------------
#                   Access Point Login API View
# ---------------------------------------------------------------------------------
class AccessPointLoginAPIView(APIView):
    """
    Login using Access Point (e.g., MAC address or device ID).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mac_address = request.data.get("mac_address")
        device_id = request.data.get("device_id")

        if not mac_address and not device_id:
            return Response({"error": "MAC address or Device ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(mac_address=mac_address) if mac_address else User.objects.get(device_id=device_id)

            if user.is_banned:
                return Response({"error": "User is banned."}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "user_type": user.user_type,
                },
                "permissions": list(user.get_all_permissions()),
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        return Response({"error": "Only POST method is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# ---------------------------------------------------------------------------------
#                   User API ViewSet
# ---------------------------------------------------------------------------------
class UserSerializer(RegisterSerializer):
    class Meta(RegisterSerializer.Meta):
        fields = ['id', 'username', 'email', 'user_type', 'is_active']
        read_only_fields = ['id']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        # فقط الأدمن يمكنه أي عملية (عرض، إضافة، تعديل، حذف)
        return [permissions.IsAdminUser()]

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True  # دعم التحديث الجزئي دائماً
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        password = self.request.data.get('password')
        user = serializer.save()
        if password:
            user.set_password(password)
            user.save()

    def perform_update(self, serializer):
        password = self.request.data.get('password')
        user = serializer.save()
        if password:
            user.set_password(password)
            user.save()
