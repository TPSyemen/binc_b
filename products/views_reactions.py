from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from core.models import Product, User, UserProductReaction
from products.rating_service import rating_service

class ProductReactionView(APIView):
    """
    API view for handling product reactions (like, dislike, neutral).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        """
        Handle user reaction to a product.

        Reaction types:
        - 'like': User likes the product
        - 'dislike': User dislikes the product
        - 'neutral': User has a neutral opinion (default)
        """
        # التحقق من وجود المنتج
        product = get_object_or_404(Product, id=product_id)

        # الحصول على نوع التفاعل من البيانات المرسلة
        reaction_type = request.data.get('reaction_type', 'neutral')

        if reaction_type not in ['like', 'dislike', 'neutral']:
            return Response(
                {"error": "نوع التفاعل غير صالح. يجب أن يكون 'like'، 'dislike'، أو 'neutral'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # الحصول على التفاعل الحالي للمستخدم مع المنتج (إن وجد)
        user_reaction = self._get_user_reaction(request.user, product)

        # إذا كان التفاعل الجديد هو نفس التفاعل الحالي، فلا نقوم بأي تغيير
        if user_reaction == reaction_type:
            return Response(
                {"message": f"لم يتم تغيير التفاعل، المستخدم بالفعل {reaction_type} هذا المنتج."},
                status=status.HTTP_200_OK
            )

        # تحديث عدادات التفاعل في المنتج
        self._update_product_reaction_counts(product, user_reaction, reaction_type)

        # تحديث تفاعل المستخدم في قاعدة البيانات
        self._save_user_reaction(request.user, product, reaction_type)

        # تحديث تقييم المنتج تلقائيًا
        updated_rating = rating_service.calculate_product_rating(product.id)

        return Response(
            {
                "message": f"تم تحديث التفاعل إلى {reaction_type} بنجاح.",
                "product_id": str(product.id),
                "reaction_type": reaction_type,
                "likes": product.likes,
                "dislikes": product.dislikes,
                "neutrals": product.neutrals,
                "rating": updated_rating
            },
            status=status.HTTP_200_OK
        )

    def get(self, request, product_id):
        """
        Get the current user's reaction to a product.
        """
        # التحقق من وجود المنتج
        product = get_object_or_404(Product, id=product_id)

        # الحصول على التفاعل الحالي للمستخدم مع المنتج
        user_reaction = self._get_user_reaction(request.user, product)

        return Response(
            {
                "product_id": str(product.id),
                "reaction_type": user_reaction,
                "likes": product.likes,
                "dislikes": product.dislikes,
                "neutrals": product.neutrals
            },
            status=status.HTTP_200_OK
        )

    def _get_user_reaction(self, user, product):
        """
        Get the current user's reaction to a product.

        Returns:
            str: 'like', 'dislike', or 'neutral'
        """
        try:
            reaction = UserProductReaction.objects.get(user=user, product=product)
            return reaction.reaction_type
        except UserProductReaction.DoesNotExist:
            return 'neutral'

    def _save_user_reaction(self, user, product, reaction_type):
        """
        Save or update the user's reaction to a product.
        """
        reaction, created = UserProductReaction.objects.get_or_create(
            user=user,
            product=product,
            defaults={'reaction_type': reaction_type}
        )

        if not created:
            reaction.reaction_type = reaction_type
            reaction.save()

    def _update_product_reaction_counts(self, product, old_reaction, new_reaction):
        """
        Update the reaction counts on the product.
        """
        # إذا كان هناك تفاعل سابق، نقوم بتقليل العداد المناسب
        if old_reaction == 'like':
            product.likes = max(0, product.likes - 1)
        elif old_reaction == 'dislike':
            product.dislikes = max(0, product.dislikes - 1)
        elif old_reaction == 'neutral':
            product.neutrals = max(0, product.neutrals - 1)

        # زيادة العداد المناسب للتفاعل الجديد
        if new_reaction == 'like':
            product.likes += 1
        elif new_reaction == 'dislike':
            product.dislikes += 1
        elif new_reaction == 'neutral':
            product.neutrals += 1

        product.save()

