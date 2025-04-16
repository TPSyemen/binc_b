from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

# تعديل نموذج التسجيل ليشمل اختيار نوع المستخدم
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="أدخل بريدك الإلكتروني.")
    
    USER_TYPE_CHOICES = [
        ('owner', 'Owner'),
        ('customer', 'Customer'),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        help_text="اختر نوع المستخدم."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']
