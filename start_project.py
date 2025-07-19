#!/usr/bin/env python3
"""
مشغل منصة التجارة الإلكترونية الذكية
E-Commerce Hub Platform Launcher
"""

import os
import sys
import subprocess
import platform

def print_banner():
    """طباعة شعار المشروع"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🛍️  منصة التجارة الإلكترونية الذكية  🛍️              ║
    ║              E-Commerce Hub Platform                         ║
    ║                                                              ║
    ║  ✨ مقارنة ذكية للمنتجات مع الذكاء الاصطناعي               ║
    ║  🔍 بحث متقدم وتوصيات مخصصة                               ║
    ║  🏪 تكامل مع متاجر متعددة                                   ║
    ║  📊 تحليلات شاملة ولوحات تحكم                              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """التحقق من إصدار Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ خطأ: يتطلب Python 3.8 أو أحدث")
        print(f"   الإصدار الحالي: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - متوافق")
    return True

def check_django():
    """التحقق من وجود Django"""
    try:
        import django
        print(f"✅ Django {django.get_version()} - متوفر")
        return True
    except ImportError:
        print("⚠️  Django غير مثبت - سيتم تثبيته تلقائياً")
        return False

def install_requirements():
    """تثبيت المتطلبات"""
    print("\n📦 تثبيت المتطلبات...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ تم تثبيت المتطلبات بنجاح")
        return True
    except subprocess.CalledProcessError:
        print("❌ فشل في تثبيت المتطلبات")
        return False

def setup_database():
    """إعداد قاعدة البيانات"""
    print("\n🗄️  إعداد قاعدة البيانات...")
    
    try:
        # إنشاء migrations
        print("   إنشاء migrations...")
        subprocess.check_call([
            sys.executable, "manage.py", "makemigrations"
        ])
        
        # تطبيق migrations
        print("   تطبيق migrations...")
        subprocess.check_call([
            sys.executable, "manage.py", "migrate"
        ])
        
        print("✅ تم إعداد قاعدة البيانات بنجاح")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في إعداد قاعدة البيانات: {e}")
        return False

def create_superuser():
    """إنشاء مستخدم إداري"""
    response = input("\n👤 هل تريد إنشاء مستخدم إداري؟ (y/n): ").lower()
    if response in ['y', 'yes', 'نعم']:
        try:
            subprocess.call([
                sys.executable, "manage.py", "createsuperuser"
            ])
        except KeyboardInterrupt:
            print("\n⏭️  تم تخطي إنشاء المستخدم الإداري")

def start_server():
    """تشغيل الخادم"""
    print("\n🚀 تشغيل خادم التطوير...")
    print("📍 الخادم سيعمل على: http://127.0.0.1:8000")
    print("🌐 يمكن الوصول من الشبكة على: http://0.0.0.0:8000")
    print("\n📋 الواجهات المتاحة:")
    print("   🏠 الصفحة الرئيسية: http://127.0.0.1:8000/")
    print("   🔍 البحث: http://127.0.0.1:8000/products/")
    print("   ⚖️  المقارنة: http://127.0.0.1:8000/compare/")
    print("   👤 لوحة المستخدم: http://127.0.0.1:8000/dashboard/")
    print("   🛠️  لوحة الإدارة: http://127.0.0.1:8000/admin/")
    print("   📚 توثيق API: http://127.0.0.1:8000/api/docs/")
    print("\n⏹️  اضغط Ctrl+C لإيقاف الخادم")
    print("=" * 60)
    
    try:
        subprocess.call([
            sys.executable, "manage.py", "runserver", "0.0.0.0:8000"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف الخادم. شكراً لاستخدام المنصة!")

def main():
    """الدالة الرئيسية"""
    print_banner()
    
    # التحقق من إصدار Python
    if not check_python_version():
        sys.exit(1)
    
    # التحقق من Django
    django_available = check_django()
    
    # تثبيت المتطلبات إذا لزم الأمر
    if not django_available or not os.path.exists('venv'):
        if not install_requirements():
            sys.exit(1)
    
    # إعداد قاعدة البيانات
    if not setup_database():
        sys.exit(1)
    
    # إنشاء مستخدم إداري
    create_superuser()
    
    # تشغيل الخادم
    start_server()

if __name__ == "__main__":
    main()
