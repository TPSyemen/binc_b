from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import os

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
