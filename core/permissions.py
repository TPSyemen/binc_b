from rest_framework.permissions import BasePermission

class IsOwnerUser(BasePermission):
    """
    يسمح فقط للمستخدمين من نوع owner بالوصول.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'owner'
