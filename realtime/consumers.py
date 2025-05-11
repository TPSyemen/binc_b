import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from core.models import Notification
from core.serializers import NotificationSerializer

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        
        # التحقق من تسجيل دخول المستخدم
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # إنشاء اسم المجموعة الخاصة بالمستخدم
        self.notification_group_name = f"notifications_{self.user.id}"
        
        # الانضمام إلى مجموعة المستخدم
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        # قبول الاتصال
        await self.accept()
        
        # إرسال الإشعارات غير المقروءة عند الاتصال
        unread_notifications = await self.get_unread_notifications()
        if unread_notifications:
            await self.send(text_data=json.dumps({
                'type': 'unread_notifications',
                'notifications': unread_notifications,
                'count': len(unread_notifications)
            }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # مغادرة مجموعة المستخدم
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'mark_as_read':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.mark_notification_as_read(notification_id)
                await self.channel_layer.group_send(
                    self.notification_group_name,
                    {
                        'type': 'notification_read',
                        'notification_id': notification_id
                    }
                )
        
        elif action == 'mark_all_as_read':
            await self.mark_all_notifications_as_read()
            await self.channel_layer.group_send(
                self.notification_group_name,
                {
                    'type': 'all_notifications_read'
                }
            )
    
    async def notification_message(self, event):
        """Send notification message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
    
    async def notification_read(self, event):
        """Send notification read status to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'notification_id': event['notification_id']
        }))
    
    async def all_notifications_read(self, event):
        """Send all notifications read status to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'all_notifications_read'
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Get unread notifications for the user."""
        notifications = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).order_by('-created_at')
        
        serializer = NotificationSerializer(notifications, many=True)
        return serializer.data
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_as_read(self):
        """Mark all notifications as read."""
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True)
        return True
