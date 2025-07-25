"""
binc_b/urls.py
--------------
Main URL configuration for the project. Includes all app endpoints and admin.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    api_index, apps_dashboard, home_view, register_view, login_view, logout_view,
    products_view, search_view, recommendations_view, compare_view,
    stores_view, wishlist_view, profile_view, reviews_view, notifications_view,
    product_detail_view, store_detail_view, write_review_view, edit_profile_view,
    account_settings_view, forgot_password_view
)
from django.http import HttpResponse, JsonResponse
from core.views_site_admin import AdminShopListView

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('healthz/', health_check, name='health-check'),
    path('', home_view, name='home'),

    # Authentication URLs
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),

    # Main site URLs
    path('products/', products_view, name='products'),
    path('products/<int:product_id>/', product_detail_view, name='product_detail'),
    path('search/', search_view, name='search'),
    path('recommendations/', recommendations_view, name='recommendations'),
    path('compare/', compare_view, name='compare'),
    path('stores/', stores_view, name='stores'),
    path('stores/<int:store_id>/', store_detail_view, name='store_detail'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('reviews/', reviews_view, name='reviews'),
    path('reviews/write/', write_review_view, name='write_review'),
    path('notifications/', notifications_view, name='notifications'),
    path('account/settings/', account_settings_view, name='account_settings'),

    # Dashboard URLs
    path('apps-dashboard/', apps_dashboard, name='apps-dashboard'),
    path('dashboard/', apps_dashboard, name='dashboard'),
    path('users-dashboard/', lambda r: open_dashboard_page(r, 'users_dashboard.html'), name='users-dashboard'),
    path('products-dashboard/', lambda r: open_dashboard_page(r, 'products_dashboard.html'), name='products-dashboard'),
    path('shops-dashboard/', lambda r: open_dashboard_page(r, 'shops_dashboard.html'), name='shops-dashboard'),
    path('recommendations-dashboard/', lambda r: open_dashboard_page(r, 'recommendations_dashboard.html'), name='recommendations-dashboard'),
    path('reviews-dashboard/', lambda r: open_dashboard_page(r, 'reviews_dashboard.html'), name='reviews-dashboard'),
    path('comparison-dashboard/', lambda r: open_dashboard_page(r, 'comparison_dashboard.html'), name='comparison-dashboard'),
    path('favorites-dashboard/', lambda r: open_dashboard_page(r, 'favorites_dashboard.html'), name='favorites-dashboard'),
    path('notifications-dashboard/', lambda r: open_dashboard_page(r, 'notifications_dashboard.html'), name='notifications-dashboard'),
    path('preferences-dashboard/', lambda r: open_dashboard_page(r, 'preferences_dashboard.html'), name='preferences-dashboard'),
    path('auth-dashboard/', lambda r: open_dashboard_page(r, 'auth_dashboard.html'), name='auth-dashboard'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/shop/', include('products.urls_shop')),
    path('api/products/', include('products.urls')),
    path('api/comparison/', include('comparison.urls')),
    path('api/dashboard/', include('products.urls_dashboard')),
    path('categories/', include('products.urls_categories')),
    path('api/promotions/', include('promotions.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/notifications/', include('core.urls_notifications')),
    path('api/user/', include('core.urls_favorites')),
    path('api/user/preferences/', include('core.urls_preferences')),
    path('api/verification/', include('core.urls_verification')),
    path('api/store-integration/', include('store_integration.urls')),  # Store integration endpoints
    path('api/', include('api.urls')),  # Frontend integration APIs
    path('login/', lambda r: open_dashboard_page(r, 'login.html'), name='login'),
    path('api/shops/admin/', AdminShopListView.as_view(), name='admin-shop-list'),
    path('brands-dashboard/', lambda r: open_dashboard_page(r, 'brands_dashboard.html'), name='brands-dashboard'),
    path('api/brands/', include('products.urls_brands')),
    path('categories-dashboard/', lambda r: open_dashboard_page(r, 'categories_dashboard.html'), name='categories-dashboard'),
    path('api/categories/', include('products.urls_categories')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def open_dashboard_page(request, page):
    import os
    from django.http import HttpResponse
    dashboard_path = os.path.join('static', page)
    try:
        with open(dashboard_path, encoding='utf-8') as f:
            html = f.read()
        protect_js = '''<script>
        // حماية إضافية: لا يسمح إلا لحساب الأدمن
        var email = localStorage.getItem('dashboard_email');
        if(localStorage.getItem('dashboard_logged_in') !== '1' || email !== 'admin@gmail.com') {
            window.location.href = '/static/login.html';
        }
        </script>'''
        html = html.replace('</head>', protect_js + '\n</head>')
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f'<h2>تعذر تحميل الصفحة: {e}</h2>', status=500)
