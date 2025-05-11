from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from core.models import Product, Notification, User
from products.serializers import ProductDetailSerializer
from core.models_verification import ActionVerificationToken
from core.email_service import send_action_verification_email

class InventoryUpdateView(APIView):
    """API view for updating product inventory status."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        """Update the inventory status of a product."""
        # Check if user is owner
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the product
        product = get_object_or_404(Product, id=product_id)
        
        # Check if user owns the product's shop
        if product.shop.owner.user != request.user:
            return Response(
                {"error": "لا يمكنك تحديث مخزون منتج لا تملكه."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the new in_stock status
        in_stock = request.data.get('in_stock')
        if in_stock is None:
            return Response(
                {"error": "يجب تحديد حالة المخزون."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the product
        product.in_stock = in_stock
        product.save()
        
        # Create notification for the owner
        Notification.objects.create(
            recipient=request.user,
            content=f"تم تحديث حالة مخزون المنتج '{product.name}' إلى {'متوفر' if in_stock else 'غير متوفر'}.",
            notification_type='inventory',
            related_id=str(product.id)
        )
        
        return Response({
            "message": f"تم تحديث حالة المخزون بنجاح إلى {'متوفر' if in_stock else 'غير متوفر'}.",
            "in_stock": product.in_stock
        })


class BulkInventoryUpdateView(APIView):
    """API view for updating multiple products' inventory status."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Update the inventory status of multiple products."""
        # Check if user is owner
        if request.user.user_type != 'owner':
            return Response(
                {"error": "يجب أن تكون مالكًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the product IDs and new status
        product_ids = request.data.get('product_ids', [])
        in_stock = request.data.get('in_stock')
        
        if not product_ids:
            return Response(
                {"error": "يجب تحديد معرفات المنتجات."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if in_stock is None:
            return Response(
                {"error": "يجب تحديد حالة المخزون."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if verification is required
        require_verification = request.data.get('require_verification', False)
        if require_verification:
            # Send verification email
            token = send_action_verification_email(
                request.user,
                'update_stock',
                ','.join(product_ids)
            )
            
            return Response({
                "message": "تم إرسال رابط التحقق إلى بريدك الإلكتروني.",
                "require_verification": True
            })
        
        # Get the products owned by the user
        updated_products = []
        not_found = []
        not_owned = []
        
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check if user owns the product's shop
                if product.shop.owner.user != request.user:
                    not_owned.append(product_id)
                    continue
                
                # Update the product
                product.in_stock = in_stock
                product.save()
                updated_products.append(product_id)
                
            except Product.DoesNotExist:
                not_found.append(product_id)
        
        # Create notification for the owner
        if updated_products:
            Notification.objects.create(
                recipient=request.user,
                content=f"تم تحديث حالة مخزون {len(updated_products)} منتج إلى {'متوفر' if in_stock else 'غير متوفر'}.",
                notification_type='inventory',
                related_id=','.join(updated_products)
            )
        
        return Response({
            "message": f"تم تحديث حالة المخزون لـ {len(updated_products)} منتج بنجاح.",
            "updated_products": updated_products,
            "not_found": not_found,
            "not_owned": not_owned
        })


class VerifiedInventoryUpdateView(APIView):
    """API view for updating inventory after verification."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token_id):
        """Update inventory after verification."""
        # Get the verification token
        token = get_object_or_404(ActionVerificationToken, token=token_id)
        
        # Check if the token is valid
        if not token.is_valid:
            return Response(
                {"error": "رمز التحقق غير صالح أو منتهي الصلاحية."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the token is for the correct action
        if token.action_type != 'update_stock':
            return Response(
                {"error": "رمز التحقق غير صالح لهذا الإجراء."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the token belongs to the user
        if token.user != request.user:
            return Response(
                {"error": "رمز التحقق غير صالح لهذا المستخدم."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the product IDs and new status
        product_ids = token.object_id.split(',')
        in_stock = request.data.get('in_stock')
        
        if in_stock is None:
            return Response(
                {"error": "يجب تحديد حالة المخزون."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark the token as used
        token.is_used = True
        token.save()
        
        # Get the products owned by the user
        updated_products = []
        not_found = []
        not_owned = []
        
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check if user owns the product's shop
                if product.shop.owner.user != request.user:
                    not_owned.append(product_id)
                    continue
                
                # Update the product
                product.in_stock = in_stock
                product.save()
                updated_products.append(product_id)
                
            except Product.DoesNotExist:
                not_found.append(product_id)
        
        # Create notification for the owner
        if updated_products:
            Notification.objects.create(
                recipient=request.user,
                content=f"تم تحديث حالة مخزون {len(updated_products)} منتج إلى {'متوفر' if in_stock else 'غير متوفر'}.",
                notification_type='inventory',
                related_id=','.join(updated_products)
            )
        
        return Response({
            "message": f"تم تحديث حالة المخزون لـ {len(updated_products)} منتج بنجاح بعد التحقق.",
            "updated_products": updated_products,
            "not_found": not_found,
            "not_owned": not_owned
        })
