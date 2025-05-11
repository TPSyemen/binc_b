from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models_verification import EmailVerificationToken, ActionVerificationToken

def send_verification_email(user):
    """Send a verification email to the user."""
    # Create or get a verification token
    token, created = EmailVerificationToken.objects.get_or_create(user=user)
    
    # If the token already exists but is used or expired, create a new one
    if not created and not token.is_valid:
        token.delete()
        token = EmailVerificationToken.objects.create(user=user)
    
    # Create the verification URL
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"
    
    # Render the email template
    html_message = render_to_string('email/verify_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    plain_message = strip_tags(html_message)
    
    # Send the email
    send_mail(
        subject='تأكيد البريد الإلكتروني - منصة المقارنة',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )
    
    return token


def send_action_verification_email(user, action_type, object_id=None):
    """Send an action verification email to the user."""
    # Create a verification token
    token = ActionVerificationToken.objects.create(
        user=user,
        action_type=action_type,
        object_id=object_id
    )
    
    # Create the verification URL
    verification_url = f"{settings.FRONTEND_URL}/verify-action/{token.token}"
    
    # Get action description
    action_descriptions = {
        'delete_product': 'حذف منتج',
        'bulk_delete': 'حذف متعدد للمنتجات',
        'update_stock': 'تحديث المخزون',
        'change_password': 'تغيير كلمة المرور'
    }
    action_description = action_descriptions.get(action_type, action_type)
    
    # Render the email template
    html_message = render_to_string('email/verify_action.html', {
        'user': user,
        'verification_url': verification_url,
        'action_description': action_description,
        'object_id': object_id
    })
    plain_message = strip_tags(html_message)
    
    # Send the email
    send_mail(
        subject=f'تأكيد إجراء: {action_description} - منصة المقارنة',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )
    
    return token
