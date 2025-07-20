from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, Shop, Owner


class CustomUserCreationForm(UserCreationForm):
    """
    نموذج تسجيل مستخدم مخصص يدعم نموذج المستخدم المخصص
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل بريدك الإلكتروني'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الاسم الأول'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم العائلة'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الهاتف (اختياري)'
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial='customer',
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'اسم المستخدم'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور'
        })

        # تخصيص رسائل الخطأ
        self.fields['password1'].help_text = 'يجب أن تحتوي كلمة المرور على 6 أحرف على الأقل.'
        self.fields['password2'].help_text = 'أدخل نفس كلمة المرور للتأكيد.'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني مستخدم بالفعل.")
        return email

    def clean_user_type(self):
        user_type = self.cleaned_data.get('user_type')
        if not user_type:
            return 'customer'  # القيمة الافتراضية
        return user_type

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1 and len(password1) < 6:
            raise ValidationError("كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("كلمات المرور غير متطابقة.")
        return password2

    def _post_clean(self):
        super()._post_clean()
        # تجاهل بعض قيود كلمة المرور الافتراضية
        password = self.cleaned_data.get('password2')
        if password:
            try:
                from django.contrib.auth.password_validation import validate_password
                # تطبيق فقط MinimumLengthValidator
                from django.contrib.auth.password_validation import MinimumLengthValidator
                validator = MinimumLengthValidator(6)
                validator.validate(password, self.instance)
            except ValidationError:
                pass  # تجاهل أخطاء كلمة المرور الأخرى

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user


class StoreOwnerRegistrationForm(CustomUserCreationForm):
    """
    نموذج تسجيل صاحب متجر مع معلومات المتجر
    """
    store_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المتجر'
        })
    )
    business_license = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الرخصة التجارية'
        })
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'عنوان المتجر',
            'rows': 3
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'owner'
        self.fields['phone'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'owner'
        if commit:
            user.save()
            # إنشاء ملف صاحب المتجر
            owner = Owner.objects.create(
                user=user,
                email=user.email,
                password=user.password,  # كلمة المرور مشفرة بالفعل
                business_license=self.cleaned_data['business_license']
            )
            # إنشاء متجر للمستخدم
            Shop.objects.create(
                owner=owner,
                name=self.cleaned_data['store_name'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                url=f"https://bestinclick.com/shop/{user.username}",  # رابط افتراضي
                email=user.email
            )
        return user


class CustomLoginForm(forms.Form):
    """
    نموذج تسجيل دخول مخصص
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم أو البريد الإلكتروني',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="كلمة المرور",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            # محاولة تسجيل الدخول بالبريد الإلكتروني أو اسم المستخدم
            user = None
            
            # محاولة البحث بالبريد الإلكتروني أولاً
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    "اسم المستخدم أو كلمة المرور غير صحيحة.",
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        التحكم في السماح بتسجيل الدخول
        """
        if not user.is_active:
            raise ValidationError(
                "هذا الحساب غير مفعل.",
                code='inactive'
            )

    def get_user(self):
        return self.user_cache




from django import forms
from .models import Product, Category, Brand

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'category', 'price', 'original_price',
                  'is_featured', 'release_date', 'description', 'image_url',
                  'video_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Price'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Original Price (Optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product Description'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Product Image URL (Optional)'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Product Video URL (Optional)'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'name': 'Product Name',
            'brand': 'Brand',
            'category': 'Category',
            'price': 'Price',
            'original_price': 'Original Price',
            'is_featured': 'Is Featured?',
            'release_date': 'Release Date',
            'description': 'Description',
            'image_url': 'Image URL',
            'video_url': 'Video URL',
            'is_active': 'Is Active?',
        }

    # You might want to filter brand and category choices if they are user-specific
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: if brands or categories are specific to the owner, filter them here.
        # self.fields['brand'].queryset = Brand.objects.filter(owner=self.request.user.owner_profile)
        # self.fields['category'].queryset = Category.objects.filter(shop=self.instance.shop) # If categories are shop-specific