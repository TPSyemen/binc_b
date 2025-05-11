from django.shortcuts import render
from django.http import HttpResponse
from django.urls import get_resolver

def api_index(request):
    """
    عرض صفحة فهرس لجميع نقاط النهاية API في المشروع
    """
    # تجميع معلومات API حسب التطبيق
    api_endpoints = {
        'المصادقة (Authentication)': [
            {'name': 'تسجيل مستخدم جديد', 'url': '/api/auth/register/', 'method': 'POST'},
            {'name': 'تسجيل الدخول', 'url': '/api/auth/login/', 'method': 'POST'},
            {'name': 'تسجيل الخروج', 'url': '/api/auth/logout/', 'method': 'POST'},
            {'name': 'تحديث الرمز المميز', 'url': '/api/auth/token/refresh/', 'method': 'POST'},
        ],
        'المنتجات (Products)': [
            {'name': 'قائمة المنتجات', 'url': '/api/products/', 'method': 'GET'},
            {'name': 'تفاصيل المنتج', 'url': '/api/products/<product_id>/', 'method': 'GET'},
            {'name': 'إنشاء منتج', 'url': '/api/products/create/', 'method': 'POST'},
            {'name': 'تحديث منتج', 'url': '/api/products/<product_id>/update/', 'method': 'PUT'},
            {'name': 'حذف منتج', 'url': '/api/products/<product_id>/delete/', 'method': 'DELETE'},
            {'name': 'المنتجات المميزة', 'url': '/api/products/featured/', 'method': 'GET'},
            {'name': 'البحث عن منتجات', 'url': '/api/products/search/', 'method': 'GET'},
            {'name': 'المنتجات المشاهدة مؤخراً', 'url': '/api/products/recently-viewed/', 'method': 'GET'},
            {'name': 'منتجات مشابهة', 'url': '/api/products/<product_id>/similar/', 'method': 'GET'},
            {'name': 'تفاعل مع منتج', 'url': '/api/products/<product_id>/reaction/', 'method': 'POST'},
        ],
        'المخزون (Inventory)': [
            {'name': 'تحديث مخزون منتج', 'url': '/api/products/<product_id>/inventory/', 'method': 'POST'},
            {'name': 'تحديث مخزون متعدد', 'url': '/api/products/bulk-inventory/', 'method': 'POST'},
            {'name': 'تحديث مخزون بعد التحقق', 'url': '/api/products/verified-inventory/<token_id>/', 'method': 'POST'},
        ],
        'المتاجر (Shops)': [
            {'name': 'التحقق من المتجر', 'url': '/api/shop/check/', 'method': 'GET'},
            {'name': 'تسجيل متجر', 'url': '/api/shop/register/', 'method': 'POST'},
        ],
        'لوحة التحكم (Dashboard)': [
            {'name': 'إحصائيات لوحة التحكم', 'url': '/api/dashboard/stats/', 'method': 'GET'},
            {'name': 'منتجات المالك', 'url': '/api/dashboard/products/', 'method': 'GET'},
            {'name': 'تفاصيل منتج المالك', 'url': '/api/dashboard/products/<product_id>/', 'method': 'GET'},
            {'name': 'تحليلات المالك', 'url': '/api/dashboard/analytics/', 'method': 'GET'},
            {'name': 'إعدادات متجر المالك', 'url': '/api/dashboard/settings/', 'method': 'GET'},
        ],
        'المقارنة (Comparison)': [
            {'name': 'مقارنة المنتجات', 'url': '/api/comparison/<product_id>/compare/', 'method': 'GET'},
        ],
        'التوصيات (Recommendations)': [
            {'name': 'الحصول على التوصيات', 'url': '/api/recommendations/', 'method': 'GET'},
            {'name': 'التوصيات الهجينة', 'url': '/api/recommendations/hybrid/', 'method': 'GET'},
            {'name': 'تتبع سلوك المستخدم', 'url': '/api/recommendations/track-behavior/', 'method': 'POST'},
        ],
        'الإشعارات (Notifications)': [
            {'name': 'قائمة الإشعارات', 'url': '/api/notifications/', 'method': 'GET'},
            {'name': 'حذف جميع الإشعارات', 'url': '/api/notifications/', 'method': 'DELETE'},
            {'name': 'تفاصيل الإشعار', 'url': '/api/notifications/<notification_id>/', 'method': 'GET'},
            {'name': 'حذف إشعار', 'url': '/api/notifications/<notification_id>/', 'method': 'DELETE'},
            {'name': 'تعيين جميع الإشعارات كمقروءة', 'url': '/api/notifications/mark-all-read/', 'method': 'PUT'},
            {'name': 'توليد إشعارات ذكية', 'url': '/api/notifications/generate-ai/', 'method': 'POST'},
        ],
        'المفضلة (Favorites)': [
            {'name': 'قائمة المنتجات المفضلة', 'url': '/api/user/favorites/', 'method': 'GET'},
            {'name': 'تبديل منتج كمفضل', 'url': '/api/user/favorites/toggle/<product_id>/', 'method': 'POST'},
            {'name': 'حالة المنتج المفضل', 'url': '/api/user/favorites/status/<product_id>/', 'method': 'GET'},
        ],
        'التفضيلات (Preferences)': [
            {'name': 'الحصول على تفضيلات المستخدم', 'url': '/api/user/preferences/', 'method': 'GET'},
            {'name': 'تحديث تفضيلات المستخدم', 'url': '/api/user/preferences/', 'method': 'POST'},
            {'name': 'تبديل تفضيل العلامة التجارية', 'url': '/api/user/preferences/brands/toggle/<brand_id>/', 'method': 'POST'},
            {'name': 'حالة تفضيل العلامة التجارية', 'url': '/api/user/preferences/brands/status/<brand_id>/', 'method': 'GET'},
        ],
        'التحقق (Verification)': [
            {'name': 'إرسال تحقق البريد الإلكتروني', 'url': '/api/verification/verify-email/send/', 'method': 'POST'},
            {'name': 'تأكيد تحقق البريد الإلكتروني', 'url': '/api/verification/verify-email/confirm/<token>/', 'method': 'GET'},
            {'name': 'إرسال تحقق الإجراء', 'url': '/api/verification/verify-action/send/', 'method': 'POST'},
            {'name': 'تأكيد تحقق الإجراء', 'url': '/api/verification/verify-action/confirm/<token>/', 'method': 'GET'},
        ],
        'التقييمات (Reviews)': [
            {'name': 'قائمة تقييمات المنتج', 'url': '/api/products/<product_id>/reviews/', 'method': 'GET'},
            {'name': 'إنشاء تقييم', 'url': '/api/products/<product_id>/reviews/create/', 'method': 'POST'},
            {'name': 'تفاصيل التقييم', 'url': '/api/products/<product_id>/reviews/<review_id>/', 'method': 'GET'},
            {'name': 'تحديث التقييم', 'url': '/api/products/<product_id>/reviews/<review_id>/update/', 'method': 'PUT'},
            {'name': 'حذف التقييم', 'url': '/api/products/<product_id>/reviews/<review_id>/delete/', 'method': 'DELETE'},
        ],
    }

    # إنشاء قالب HTML بسيط
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Best In Click API - فهرس نقاط النهاية</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #2980b9;
                margin-top: 30px;
                border-right: 4px solid #3498db;
                padding-right: 10px;
            }
            .endpoint-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 40px;
            }
            .endpoint-card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                padding: 15px;
                width: calc(33% - 20px);
                min-width: 300px;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .endpoint-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .endpoint-name {
                font-weight: bold;
                margin-bottom: 10px;
                color: #2c3e50;
            }
            .endpoint-url {
                font-family: monospace;
                background-color: #f7f7f7;
                padding: 8px;
                border-radius: 4px;
                margin-bottom: 10px;
                word-break: break-all;
            }
            .method {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                color: white;
                font-size: 0.8em;
                font-weight: bold;
                margin-left: 10px;
            }
            .GET { background-color: #61affe; }
            .POST { background-color: #49cc90; }
            .PUT { background-color: #fca130; }
            .DELETE { background-color: #f93e3e; }
            .PATCH { background-color: #50e3c2; }
            header {
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }
            footer {
                text-align: center;
                margin-top: 50px;
                padding: 20px;
                color: #7f8c8d;
                border-top: 1px solid #ddd;
            }
            @media (max-width: 768px) {
                .endpoint-card {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Best In Click API</h1>
            <p>فهرس نقاط النهاية API المتاحة في المشروع</p>
        </header>
    """

    # إضافة كل قسم من نقاط النهاية
    for category, endpoints in api_endpoints.items():
        html_content += f"""
        <h2>{category}</h2>
        <div class="endpoint-container">
        """
        
        for endpoint in endpoints:
            method_class = endpoint['method']
            html_content += f"""
            <div class="endpoint-card">
                <div class="endpoint-name">{endpoint['name']}</div>
                <div class="endpoint-url">{endpoint['url']} <span class="method {method_class}">{endpoint['method']}</span></div>
            </div>
            """
        
        html_content += "</div>"

    # إغلاق HTML
    html_content += """
        <footer>
            <p>Best In Click &copy; 2023 - جميع الحقوق محفوظة</p>
        </footer>
    </body>
    </html>
    """

    return HttpResponse(html_content)
