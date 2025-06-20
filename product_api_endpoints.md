# Product API Endpoints (نقاط نهاية المنتج)

---

## 1. قائمة المنتجات
- **URL:** `https://binc-b-1.onrender.com/products/`
- **Method:** `GET`
- **الوصف:** عرض جميع المنتجات مع دعم التصفية والبحث.

---

## 2. تفاصيل منتج
- **URL:** `https://binc-b-1.onrender.com/products/{product_id}/`
- **Method:** `GET`
- **الوصف:** عرض تفاصيل منتج محدد.

---

## 3. إنشاء منتج جديد
- **URL:** `https://binc-b-1.onrender.com/products/create/`
- **Method:** `POST`
- **Headers:**
  - Authorization: Bearer <access_token>
  - Content-Type: multipart/form-data
- **Body (form-data):**
  - name: اسم المنتج
  - price: 150.0
  - original_price: 200.0
  - category_id: رقم التصنيف
  - brand_id: رقم العلامة التجارية
  - description: وصف المنتج
  - image_url: (رابط أو ملف صورة)
  - video_url: (اختياري)
  - release_date: 2023-01-01
  - is_active: true
  - in_stock: true
  - stock: 10
  - shop_id: رقم المتجر

---

## 4. تحديث منتج
- **URL:** `https://binc-b-1.onrender.com/products/{product_id}/update/`
- **Method:** `PUT`
- **Headers:**
  - Authorization: Bearer <access_token>
  - Content-Type: multipart/form-data
- **Body (form-data):**
  - (نفس حقول الإنشاء ويمكنك إرسال ما تريد تعديله فقط)

---

## 5. حذف منتج
- **URL:** `https://binc-b-1.onrender.com/products/{product_id}/delete/`
- **Method:** `DELETE`
- **Headers:**
  - Authorization: Bearer <access_token>

---

## 6. المنتجات المميزة
- **URL:** `https://binc-b-1.onrender.com/products/featured/`
- **Method:** `GET`

---

## 7. البحث عن المنتجات
- **URL:** `https://binc-b-1.onrender.com/products/search/`
- **Method:** `GET`
- **Query Parameters:**
  - query: كلمة البحث
  - category: رقم التصنيف
  - brand: رقم العلامة التجارية
  - min_price: أقل سعر
  - max_price: أعلى سعر
  - sort_by: ترتيب حسب
  - order: asc/desc
  - page: رقم الصفحة
  - limit: عدد النتائج

---

## 8. المنتجات التي تمت مشاهدتها مؤخرًا
- **URL:** `https://binc-b-1.onrender.com/products/recently-viewed/`
- **Method:** `GET`
- **Headers:**
  - Authorization: Bearer <access_token>

---

## 9. منتجات مشابهة
- **URL:** `https://binc-b-1.onrender.com/products/{product_id}/similar/`
- **Method:** `GET`

---

## 10. تاريخ أسعار المنتج
- **URL:** `https://binc-b-1.onrender.com/products/{product_id}/price-history/`
- **Method:** `GET`

---

> استبدل `<access_token>` بالتوكن الخاص بك، و`{product_id}` برقم المنتج المطلوب.
