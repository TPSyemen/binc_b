from django.urls import path
from .views_verification import (
    EmailVerificationSendView, 
    EmailVerificationConfirmView,
    ActionVerificationSendView,
    ActionVerificationConfirmView
)

urlpatterns = [
    path('verify-email/send/', EmailVerificationSendView.as_view(), name='verify-email-send'),
    path('verify-email/confirm/<uuid:token>/', EmailVerificationConfirmView.as_view(), name='verify-email-confirm'),
    path('verify-action/send/', ActionVerificationSendView.as_view(), name='verify-action-send'),
    path('verify-action/confirm/<uuid:token>/', ActionVerificationConfirmView.as_view(), name='verify-action-confirm'),
]
