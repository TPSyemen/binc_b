from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models_verification import EmailVerificationToken, ActionVerificationToken
from .email_service import send_verification_email, send_action_verification_email
from django.contrib.auth import get_user_model
from rest_framework.parsers import JSONParser

User = get_user_model()

class EmailVerificationSendView(APIView):
    """API view for sending email verification."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        """Send a verification email to the authenticated user."""
        user = request.user
        
        # Check if email is already verified
        if user.is_email_verified:
            return Response(
                {"message": "البريد الإلكتروني مفعل بالفعل."},
                status=status.HTTP_200_OK
            )
        
        # Send verification email
        token = send_verification_email(user)
        
        return Response(
            {"message": "تم إرسال رسالة التحقق إلى بريدك الإلكتروني."},
            status=status.HTTP_200_OK
        )


class EmailVerificationConfirmView(APIView):
    """API view for confirming email verification."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request, token):
        """Verify the email using the token."""
        # Get the token
        verification_token = get_object_or_404(EmailVerificationToken, token=token)
        
        # Check if the token is valid
        if not verification_token.is_valid:
            return Response(
                {"error": "رمز التحقق غير صالح أو منتهي الصلاحية."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark the token as used
        verification_token.is_used = True
        verification_token.save()
        
        # Mark the user's email as verified
        user = verification_token.user
        user.is_email_verified = True
        user.save()
        
        return Response(
            {"message": "تم تفعيل البريد الإلكتروني بنجاح."},
            status=status.HTTP_200_OK
        )


class ActionVerificationSendView(APIView):
    """API view for sending action verification."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        """Send an action verification email."""
        user = request.user
        action_type = request.data.get('action_type')
        object_id = request.data.get('object_id')
        
        # Validate action type
        valid_action_types = [choice[0] for choice in ActionVerificationToken.ACTION_TYPES]
        if action_type not in valid_action_types:
            return Response(
                {"error": "نوع الإجراء غير صالح."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send verification email
        token = send_action_verification_email(user, action_type, object_id)
        
        return Response(
            {"message": "تم إرسال رسالة التحقق إلى بريدك الإلكتروني."},
            status=status.HTTP_200_OK
        )


class ActionVerificationConfirmView(APIView):
    """API view for confirming action verification."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request, token):
        """Verify the action using the token."""
        # Get the token
        verification_token = get_object_or_404(ActionVerificationToken, token=token)
        
        # Check if the token is valid
        if not verification_token.is_valid:
            return Response(
                {"error": "رمز التحقق غير صالح أو منتهي الصلاحية."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark the token as used
        verification_token.is_used = True
        verification_token.save()
        
        return Response({
            "message": "تم تأكيد الإجراء بنجاح.",
            "action_type": verification_token.action_type,
            "object_id": verification_token.object_id,
            "user_id": verification_token.user.id
        }, status=status.HTTP_200_OK)
