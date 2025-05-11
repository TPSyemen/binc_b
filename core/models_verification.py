from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta

class EmailVerificationToken(models.Model):
    """Model for storing email verification tokens."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='verification_token',
        help_text="The user who needs to verify their email."
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="The verification token."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    expires_at = models.DateTimeField(
        verbose_name="Expires At"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Is Used",
        help_text="Indicates whether the token has been used."
    )

    def __str__(self):
        return f"Verification token for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 24 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Check if the token is valid (not expired and not used)."""
        return not self.is_used and timezone.now() < self.expires_at


class ActionVerificationToken(models.Model):
    """Model for storing action verification tokens (for critical actions)."""
    ACTION_TYPES = (
        ('delete_product', 'Delete Product'),
        ('bulk_delete', 'Bulk Delete'),
        ('update_stock', 'Update Stock'),
        ('change_password', 'Change Password'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='action_tokens',
        help_text="The user who initiated the action."
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="The verification token."
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name="Action Type"
    )
    object_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Object ID",
        help_text="ID of the object being acted upon."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    expires_at = models.DateTimeField(
        verbose_name="Expires At"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Is Used",
        help_text="Indicates whether the token has been used."
    )

    def __str__(self):
        return f"{self.action_type} verification for {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 1 hour from creation
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Check if the token is valid (not expired and not used)."""
        return not self.is_used and timezone.now() < self.expires_at
