from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import JSONParser
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Notification, User
from .serializers import NotificationSerializer
from .ai_notifications import AINotificationGenerator

class NotificationListView(APIView):
    """API view for listing and managing notifications."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        """Get all notifications for the authenticated user."""
        # الحصول على إشعارات المستخدم
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

        # تطبيق التصفية إذا تم توفيرها
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        # تصفية حسب حالة القراءة
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            notifications = notifications.filter(is_read=is_read_bool)

        # تحديد عدد الإشعارات المطلوبة
        limit = request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                notifications = notifications[:limit]
            except ValueError:
                pass

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def delete(self, request):
        """Delete all notifications for the authenticated user."""
        Notification.objects.filter(recipient=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationDetailView(APIView):
    """API view for managing a specific notification."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, notification_id):
        """Get a specific notification."""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response(
                {"error": "الإشعار غير موجود."},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response(
                {"error": "الإشعار غير موجود."},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, notification_id):
        """Delete a specific notification."""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response(
                {"error": "الإشعار غير موجود."},
                status=status.HTTP_404_NOT_FOUND
            )

class NotificationMarkAllReadView(APIView):
    """API view for marking all notifications as read."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def put(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"message": "تم تعيين جميع الإشعارات كمقروءة."})

class NotificationAIGeneratorView(APIView):
    """API view for generating AI-powered notifications."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        """Generate AI-powered notifications based on user behavior and system events."""
        user = request.user

        # التحقق من نوع المستخدم
        if user.user_type not in ['owner', 'admin', 'customer']:
            return Response(
                {"error": "يجب أن تكون مالكًا أو مسؤولًا أو عميلًا للوصول إلى هذه الميزة."},
                status=status.HTTP_403_FORBIDDEN
            )

        # استخدام مولد الإشعارات الذكية
        ai_generator = AINotificationGenerator(user)
        generated_notifications = ai_generator.generate_notifications()

        return Response({
            "message": "تم توليد الإشعارات بنجاح.",
            "count": len(generated_notifications),
            "notifications": NotificationSerializer(generated_notifications, many=True).data
        })
