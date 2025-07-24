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
from rest_framework.permissions import IsAuthenticated
from core.models import Owner

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

            # تحديد رابط التوجيه حسب نوع المستخدم
            user_type = getattr(user, 'user_type', 'default')
            if user_type == 'admin':
                redirect_url = '/admin/dashboard/'
            elif user_type == 'owner':
                redirect_url = '/owner/dashboard/'
            else:
                redirect_url = '/'

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "user_type": user_type,
                },
                "permissions": list(user.get_all_permissions()),
                "redirect_url": redirect_url,
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

# ---------------------------------------------------------------------------------
#                   User Profile API View
# ---------------------------------------------------------------------------------
class UserProfileAPIView(APIView):
    """عرض بيانات المستخدم الحالي (البروفايل)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = RegisterSerializer(user)
        return Response(serializer.data)

# ---------------------------------------------------------------------------------
#                   Owner Profile API View
# ---------------------------------------------------------------------------------
class CreateOwnerProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if hasattr(user, 'owner_profile'):
            return Response({'detail': 'المالك موجود بالفعل.'}, status=status.HTTP_400_BAD_REQUEST)
        owner = Owner.objects.create(user=user, email=user.email)
        return Response({'detail': 'تم إنشاء ملف تعريف المالك بنجاح.', 'owner_id': owner.id}, status=status.HTTP_201_CREATED)

# ---------------------------------------------------------------------------------
#                   Shop Check API View
# ---------------------------------------------------------------------------------
class ShopCheckView(APIView):
    """Check if the authenticated owner has a shop. Creates Owner profile if missing."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # تحقق من وجود ملف تعريف المالك، إذا لم يوجد أنشئه تلقائياً
        if not hasattr(user, 'owner_profile'):
            owner = Owner.objects.create(user=user, email=user.email)
        else:
            owner = user.owner_profile
        # تحقق من وجود متجر مرتبط
        if not hasattr(owner, 'shop') or owner.shop is None:
            return Response({'has_owner': True, 'has_shop': False}, status=status.HTTP_200_OK)
        shop = owner.shop
        return Response({'has_owner': True, 'has_shop': True, 'shop_id': str(shop.id), 'shop_name': shop.name}, status=status.HTTP_200_OK)



import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Avg
from django.conf import settings # To access CURRENCY_SYMBOL
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.utils import timezone # For report date

from .models import Product, Shop, User, UserProductReaction, Category # Import all necessary models
from .forms import ProductForm # You'll need to create this form

@login_required
def owner_dashboard(request):
    """
    Owner dashboard view.
    Displays quick stats, product list, and report options.
    """
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner. Please contact the administrator.")
        return redirect('home') # Redirect to home or a suitable page

    owner_shop = request.user.owner_profile.shop # Assuming owner has a OneToOneField to Shop

    # 1. Quick Stats
    total_products = Product.objects.filter(shop=owner_shop).count()
    total_product_views = Product.objects.filter(shop=owner_shop).aggregate(total_views=Sum('views'))['total_views'] or 0

    # Get unique users who reacted (like/dislike/neutral) to the owner's products
    unique_interactors = UserProductReaction.objects.filter(
        product__shop=owner_shop,
        reaction_type__in=['like', 'dislike', 'neutral']
    ).values('user').distinct().count()

    # 2. Products List
    product_list = Product.objects.filter(shop=owner_shop).order_by('-created_at')
    paginator = Paginator(product_list, 10) # Show 10 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # 3. Chart Data (for Chart.js)
    # Top 5 Most Viewed Products
    top_products = Product.objects.filter(shop=owner_shop).order_by('-views')[:5]
    top_products_labels = json.dumps([p.name for p in top_products]) # No ensure_ascii=False needed for English
    top_products_views = json.dumps([p.views for p in top_products])

    # Average Product Rating by Category for owner's products
    category_ratings = Product.objects.filter(shop=owner_shop).values('category__name').annotate(
        avg_rating=Avg('rating')
    ).order_by('-avg_rating')

    category_rating_labels = json.dumps([item['category__name'] for item in category_ratings if item['category__name']])
    category_rating_values = json.dumps([float(item['avg_rating']) for item in category_ratings])

    context = {
        'total_products': total_products,
        'total_product_views': total_product_views,
        'unique_interactors': unique_interactors,
        'products': products,
        'settings': settings, # Pass settings to access CURRENCY_SYMBOL
        'top_products_labels': top_products_labels,
        'top_products_views': top_products_views,
        'category_rating_labels': category_rating_labels,
        'category_rating_values': category_rating_values,
    }
    return render(request, 'owner/owner_dashboard.html', context)

@login_required
def product_add(request):
    """View to add a new product."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = owner_shop # Assign the product to the owner's shop
            product.save()
            messages.success(request, f"Product '{product.name}' added successfully!")
            return redirect('core:owner_dashboard')
        else:
            messages.error(request, "There was an error adding the product. Please check the data.")
    else:
        form = ProductForm()
    return render(request, 'owner/product_form.html', {'form': form, 'form_title': 'Add New Product'})

@login_required
def product_edit(request, product_id):
    """View to edit an existing product."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop
    product = get_object_or_404(Product, id=product_id, shop=owner_shop) # Ensure product belongs to this owner

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('core:owner_dashboard')
        else:
            messages.error(request, "There was an error updating the product. Please check the data.")
    else:
        form = ProductForm(instance=product)
    return render(request, 'owner/product_form.html', {'form': form, 'product': product, 'form_title': 'Edit Product'})

@login_required
def product_detail(request, product_id):
    """View to display product details."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop
    product = get_object_or_404(Product, id=product_id, shop=owner_shop)

    # You might fetch more related data here, e.g., reviews, specific user reactions
    return render(request, 'owner/product_detail.html', {'product': product, 'settings': settings}) # Pass settings here too

@login_required
def product_delete(request, product_id):
    """View to delete a product."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop
    product = get_object_or_404(Product, id=product_id, shop=owner_shop)

    if request.method == 'POST':
        product_name = product.name # Store name before deletion for message
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully.")
        return redirect('core:owner_dashboard')
    # If accessed directly via GET, you might want to show a confirmation page or redirect
    messages.warning(request, "Invalid method to delete product.")
    return redirect('core:owner_dashboard')


# --- PDF Report Views ---
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # Note: For Arabic characters in PDF, 'xhtml2pdf' might require specific font configuration
    # or you might need to use a library like 'WeasyPrint' with proper font embedding.
    # For simplicity, default encoding is used here.
    pisa_status = pisa.CreatePDF(
        html, dest=response,
        encoding='UTF-8'
    )
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def report_product_interactions_pdf(request):
    """Generates a PDF report for product interactions."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop
    products = Product.objects.filter(shop=owner_shop).order_by('-views')

    # Aggregate interaction data
    product_interactions = []
    for product in products:
        likes = UserProductReaction.objects.filter(product=product, reaction_type='like').count()
        dislikes = UserProductReaction.objects.filter(product=product, reaction_type='dislike').count()
        neutrals = UserProductReaction.objects.filter(product=product, reaction_type='neutral').count()
        product_interactions.append({
            'name': product.name,
            'views': product.views,
            'likes': likes,
            'dislikes': dislikes,
            'neutrals': neutrals,
            'total_interactions': likes + dislikes + neutrals
        })

    context = {
        'shop_name': owner_shop.name,
        'report_title': 'Product Interaction Report',
        'report_date': timezone.now().strftime("%Y-%m-%d %H:%M"),
        'product_interactions': product_interactions,
    }
    return render_to_pdf('owner/reports/product_interactions_report_template.html', context)

@login_required
def report_product_performance_pdf(request):
    """Generates a PDF report for product performance."""
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, "You are not a registered store owner.")
        return redirect('home')

    owner_shop = request.user.owner_profile.shop
    products = Product.objects.filter(shop=owner_shop).order_by('-rating')

    context = {
        'shop_name': owner_shop.name,
        'report_title': 'Product Performance Report',
        'report_date': timezone.now().strftime("%Y-%m-%d %H:%M"),
        'products': products,
        'settings': settings,
    }
    return render_to_pdf('owner/reports/product_performance_report_template.html', context)