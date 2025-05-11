# Best In Click (BINC) Backend

![Best In Click Logo](https://example.com/logo.png)

## 🌟 نظرة عامة

**Best In Click (BINC)** هو نظام خلفي (Backend) متكامل لمنصة تسوق إلكتروني مبنية باستخدام Django وDjango REST Framework. يوفر هذا المشروع واجهات برمجة تطبيقات (APIs) شاملة لدعم تطبيق تسوق إلكتروني متكامل مع العديد من الميزات المتقدمة.

## 🚀 الميزات الرئيسية

- **نظام مصادقة متكامل**: تسجيل المستخدمين، تسجيل الدخول/الخروج، تحديث الرموز المميزة، إعادة تعيين كلمات المرور
- **إدارة المنتجات**: إنشاء، عرض، تحديث وحذف المنتجات مع دعم للصور المتعددة والمواصفات
- **إدارة المتاجر**: تسجيل المتاجر، تحديث معلومات المتجر، متابعة المتاجر
- **نظام تقييمات ومراجعات**: تقييم المنتجات، كتابة المراجعات، التصويت على المراجعات المفيدة
- **لوحة تحكم للبائعين**: إحصائيات، تحليلات، إدارة المنتجات والمخزون
- **نظام توصيات متقدم**: توصيات مخصصة للمستخدمين بناءً على سلوكهم وتفضيلاتهم
- **مقارنة المنتجات**: مقارنة مواصفات وأسعار المنتجات المختلفة
- **إشعارات في الوقت الحقيقي**: إشعارات للمستخدمين حول المنتجات والتفاعلات
- **تفضيلات المستخدم**: حفظ وإدارة تفضيلات المستخدم للعلامات التجارية والفئات

## 🛠️ التقنيات المستخدمة

- **Django**: إطار عمل Python للتطوير السريع
- **Django REST Framework**: لبناء واجهات برمجة التطبيقات RESTful
- **Channels**: لدعم الاتصالات في الوقت الحقيقي
- **JWT**: للمصادقة الآمنة
- **SQLite/PostgreSQL**: لتخزين البيانات
- **scikit-learn & pandas**: لنظام التوصيات المتقدم

## 📋 متطلبات النظام

- Python 3.10+
- Django 5.1
- وجميع المكتبات المذكورة في ملف `requirements.txt`

## ⚙️ التثبيت والإعداد

### 1. استنساخ المستودع

```bash
git clone https://github.com/TPSymene/binc_b.git
cd binc_b
```

### 2. إنشاء بيئة افتراضية وتفعيلها

```bash
# على نظام Windows
python -m venv backend_env
backend_env\Scripts\activate

# على نظام Linux/Mac
python -m venv backend_env
source backend_env/bin/activate
```

### 3. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 4. إعداد قاعدة البيانات

```bash
python manage.py migrate
```

### 5. إنشاء مستخدم مسؤول

```bash
python manage.py createsuperuser
```

### 6. تشغيل الخادم المحلي

```bash
python manage.py runserver
```

بعد ذلك، يمكنك الوصول إلى:
- واجهة المستخدم الرئيسية: http://localhost:8000/
- لوحة تحكم المسؤول: http://localhost:8000/admin/
- توثيق API: http://localhost:8000/api/

## 📚 هيكل المشروع

```
binc_b/
├── binc_b/                  # إعدادات المشروع الرئيسية
├── core/                    # تطبيق المستخدمين والمصادقة
├── products/                # تطبيق المنتجات والفئات
├── reviews/                 # تطبيق التقييمات والمراجعات
├── promotions/              # تطبيق العروض والتخفيضات
├── recommendations/         # تطبيق التوصيات
├── comparison/              # تطبيق مقارنة المنتجات
├── realtime/                # تطبيق الإشعارات في الوقت الحقيقي
├── templates/               # قوالب HTML
├── static/                  # الملفات الثابتة (CSS، JS، الصور)
├── media/                   # ملفات الوسائط المرفوعة
├── manage.py                # سكريبت إدارة Django
└── requirements.txt         # متطلبات المشروع
```

## 📝 توثيق API

يمكنك الاطلاع على توثيق كامل لجميع نقاط نهاية API في ملف [api_endpoints.txt](api_endpoints.txt).

## 🔄 مخطط قاعدة البيانات

يمكنك الاطلاع على مخطط قاعدة البيانات في ملف [database_schema.txt](database_schema.txt) أو مشاهدة المخطط البصري في [my_project_ERD.pdf](my_project_ERD.pdf).

## 👥 المساهمة

نرحب بالمساهمات! يرجى اتباع الخطوات التالية:

1. Fork المستودع
2. إنشاء فرع جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'إضافة ميزة رائعة'`)
4. Push إلى الفرع (`git push origin feature/amazing-feature`)
5. فتح طلب Pull Request

## 📄 الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE).

## 📞 التواصل

إذا كان لديك أي أسئلة أو استفسارات، يرجى التواصل معنا عبر:

- البريد الإلكتروني: ttt.ppp.sss.77@gmaile.com
