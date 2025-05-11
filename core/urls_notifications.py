from django.urls import path
from .views_notifications import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkAllReadView,
    NotificationAIGeneratorView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('generate-ai/', NotificationAIGeneratorView.as_view(), name='notification-generate-ai'),
]
