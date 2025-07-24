from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from core.forms import CustomUserCreationForm, StoreOwnerRegistrationForm, CustomLoginForm
import os

def home_view(request):
    """
    عرض الصفحة الرئيسية الجديدة
    """
    return render(request, 'home.html')

def register_view(request):
    """
    صفحة التسجيل المحسنة مع دعم العملاء وأصحاب المتاجر
    """
    success = False
    form = None

    if request.method == 'POST':
        role = request.POST.get('role', 'customer')

        if role == 'store_owner':
            form = StoreOwnerRegistrationForm(request.POST)
        else:
            form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')

                if role == 'store_owner':
                    messages.success(request, f'تم إنشاء حساب صاحب المتجر {username} بنجاح!')
                else:
                    messages.success(request, f'تم إنشاء حساب العميل {username} بنجاح!')

                success = True

                # تسجيل دخول المستخدم تلقائياً
                login(request, user)

                # توجيه المستخدم حسب نوعه
                if role == 'store_owner':
                    return redirect('/dashboard/')  # لوحة تحكم صاحب المتجر
                else:
                    return redirect('/')  # الصفحة الرئيسية للعميل

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
                print(f"Registration error: {str(e)}")  # للتشخيص
        else:
            # إضافة رسائل خطأ مفصلة
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            print(f"Form errors: {form.errors}")  # للتشخيص
    else:
        # إنشاء نموذج فارغ للعرض الأولي
        form = CustomUserCreationForm()

    return render(request, 'register.html', {
        'form': form,
        'success': success
    })

def login_view(request):
    """
    صفحة تسجيل الدخول المحسنة مع ربط الباك إند
    """
    if request.user.is_authenticated:
        return redirect('home')

    success = False

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            remember_me = form.cleaned_data.get('remember_me', False)

            # تسجيل دخول المستخدم
            login(request, user)

            # إعداد مدة الجلسة حسب "تذكرني"
            if remember_me:
                request.session.set_expiry(1209600)  # أسبوعان
            else:
                request.session.set_expiry(0)  # إنتهاء عند إغلاق المتصفح

            messages.success(request, f'Welcome back, {user.username}!')
            success = True

            # إعادة توجيه للصفحة المطلوبة أو الرئيسية
            next_url = request.GET.get('next', '/')
            if success:
                return redirect(next_url)
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {
        'form': form,
        'success': success
    })

def logout_view(request):
    """
    تسجيل الخروج
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {username}! You have been logged out successfully.')
    return redirect('home')

def products_view(request):
    """
    صفحة المنتجات
    """
    return render(request, 'products.html')

def search_view(request):
    """
    صفحة البحث
    """
    query = request.GET.get('q', '')
    return render(request, 'search.html', {'query': query})

def recommendations_view(request):
    """
    صفحة التوصيات
    """
    return render(request, 'recommendations.html')

def compare_view(request):
    """
    صفحة المقارنة
    """
    return render(request, 'compare.html')

def stores_view(request):
    """
    صفحة المتاجر
    """
    return render(request, 'stores.html')

def wishlist_view(request):
    """
    صفحة قائمة الأمنيات
    """
    return render(request, 'wishlist.html')

def profile_view(request):
    """
    صفحة الملف الشخصي
    """
    return render(request, 'profile.html')

def reviews_view(request):
    """
    صفحة المراجعات
    """
    return render(request, 'reviews.html')

def notifications_view(request):
    """
    صفحة الإشعارات
    """
    return render(request, 'notifications.html')

def product_detail_view(request, product_id):
    """
    تفاصيل المنتج
    """
    return render(request, 'product_details.html', {'product_id': product_id})

def store_detail_view(request, store_id):
    """
    تفاصيل المتجر
    """
    return render(request, 'store_details.html', {'store_id': store_id})

def write_review_view(request):
    """
    كتابة مراجعة
    """
    return render(request, 'write_review.html')

def edit_profile_view(request):
    """
    تعديل الملف الشخصي
    """
    return render(request, 'edit_profile.html')

def account_settings_view(request):
    """
    إعدادات الحساب
    """
    return render(request, 'account_settings.html')

def forgot_password_view(request):
    """
    نسيان كلمة المرور
    """
    return render(request, 'forgot_password.html')

def api_index(request):
    """
    إذا لم يكن المستخدم مسجلاً دخوله (حسب localStorage)، يعيد توجيهه لصفحة تسجيل الدخول.
    """
    # تحقق من الكوكيز (لأن localStorage لا يعمل في السيرفر، سنستخدم كود جافاسكريبت في الصفحة)
    dashboard_path = os.path.join('static', 'api_dashboard.html')
    try:
        with open(dashboard_path, encoding='utf-8') as f:
            html = f.read()
        # أضف كود جافاسكريبت لمنع الوصول إذا لم يكن مسجلاً دخوله
        protect_js = '''<script>
        if(localStorage.getItem('dashboard_logged_in') !== '1') {
            window.location.href = '/static/login.html';
        }
        </script>'''
        html = html.replace('</head>', protect_js + '\n</head>')
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f'<h2>تعذر تحميل صفحة الداشبورد: {e}</h2>', status=500)

def apps_dashboard(request):
    """
    عرض لوحة تحكم جميع التطبيقات (apps_dashboard.html)
    """
    dashboard_path = os.path.join('static', 'apps_dashboard.html')
    try:
        with open(dashboard_path, encoding='utf-8') as f:
            html = f.read()
        # حماية الوصول بنفس آلية الداشبورد (تسجيل الدخول)
        protect_js = '''<script>
        if(localStorage.getItem('dashboard_logged_in') !== '1') {
            window.location.href = '/static/login.html';
        }
        </script>'''
        html = html.replace('</head>', protect_js + '\n</head>')
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f'<h2>تعذر تحميل لوحة التحكم: {e}</h2>', status=500)
