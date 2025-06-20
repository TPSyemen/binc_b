# Unified API Endpoints Documentation (توثيق جميع نقاط النهاية)

---

## المنتجات (Products)

### 1. قائمة المنتجات
- **URL:** `/api/products/`
- **Method:** `GET`
- **Headers:** (اختياري) Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
[
  {"id": "...", "name": "...", "price": 100, ...}
]
```

### 2. تفاصيل منتج
- **URL:** `/api/products/{product_id}/`
- **Method:** `GET`
- **مثال استجابة:**
```json
{"id": "...", "name": "...", ...}
```

### 3. إنشاء منتج جديد
- **URL:** `/api/products/create/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: multipart/form-data
- **Body:** name, price, category_id, ...
- **مثال استجابة:**
```json
{"id": "...", "name": "...", ...}
```

### 4. تحديث منتج
- **URL:** `/api/products/{product_id}/update/`
- **Method:** `PUT`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: multipart/form-data
- **Body:** (الحقول التي تريد تعديلها فقط)
- **مثال استجابة:**
```json
{"id": "...", "name": "...", ...}
```

### 5. حذف منتج
- **URL:** `/api/products/{product_id}/delete/`
- **Method:** `DELETE`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
{"detail": "Product deleted successfully."}
```

### 6. المنتجات المميزة
- **URL:** `/api/products/featured/`
- **Method:** `GET`
- **مثال استجابة:**
```json
[{"id": "...", "name": "...", "is_featured": true, ...}]
```

### 7. البحث عن المنتجات
- **URL:** `/api/products/search/`
- **Method:** `GET`
- **Query Parameters:** query, category, brand, min_price, max_price, ...
- **مثال استجابة:**
```json
[{"id": "...", "name": "...", ...}]
```

### 8. المنتجات التي تمت مشاهدتها مؤخرًا
- **URL:** `/api/products/recently-viewed/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
[{"id": "...", "name": "...", ...}]
```

### 9. منتجات مشابهة
- **URL:** `/api/products/{product_id}/similar/`
- **Method:** `GET`
- **مثال استجابة:**
```json
{"current_product": { ... }, "similar_products": [ { ... }, ... ]}
```

### 10. تاريخ أسعار المنتج
- **URL:** `/api/products/{product_id}/price-history/`
- **Method:** `GET`
- **مثال استجابة:**
```json
{"product_id": "...", "price_history": [{"date": "2024-01-01", "price": 1800.0}]}
```

---

## المتاجر (Shops)

### 1. قائمة المتاجر
- **URL:** `/api/shop/`
- **Method:** `GET`
- **مثال استجابة:**
```json
[{"id": "...", "name": "...", "logo": "..."}]
```

### 2. تفاصيل متجر
- **URL:** `/api/shop/{shop_id}/`
- **Method:** `GET`
- **مثال استجابة:**
```json
{"id": "...", "name": "...", "logo": "...", ...}
```

### 3. إنشاء متجر جديد
- **URL:** `/api/shop/create/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: multipart/form-data
- **Body:** name, logo (اختياري), ...
- **مثال استجابة:**
```json
{"id": "...", "name": "...", ...}
```

---

## التوصيات (Recommendations)

### 1. التوصيات المخصصة للمستخدم
- **URL:** `/api/recommendations/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
{
  "preferred": [
    {"id": "1", "name": "iPhone 15 Pro", "brand": "Apple", "score": 92.5, "is_featured": true}
  ],
  "liked": [
    {"id": "2", "name": "Galaxy S24 Ultra", "brand": "Samsung", "score": 89.0}
  ],
  "new": [
    {"id": "3", "name": "Pixel 9", "brand": "Google", "score": 85.0}
  ],
  "popular": [
    {"id": "4", "name": "Redmi Note 13", "brand": "Xiaomi", "score": 80.0}
  ]
}
```

### 2. التوصيات الهجينة
- **URL:** `/api/recommendations/hybrid/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
[{ ... }, { ... }]
```

### 3. تتبع سلوك المستخدم
- **URL:** `/api/recommendations/track-behavior/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: application/json
- **Body:**
```json
{
  "product_id": "معرف المنتج",
  "action": "view"  // أو "like" أو "purchase"
}
```
- **مثال استجابة:**
```json
{"success": true}
```

---

## المراجعات (Reviews)

### 1. إضافة مراجعة
- **URL:** `/reviews/add/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: application/json
- **Body:**
```json
{"product_id": "...", "comment": "..."}
```
- **ملاحظة:** لا يمكن إرسال rating، حيث يتم توليده تلقائيًا من تحليل نص التعليق.
- **مثال استجابة:**
```json
{"id": "...", "product": "...", "rating": 5, "comment": "...", ...}
```

### 2. قائمة مراجعات منتج
- **URL:** `/reviews/products/{product_id}/reviews/`
- **Method:** `GET`
- **مثال استجابة:**
```json
[{"id": "...", "rating": 5, "comment": "...", ...}]
```

---

## المقارنة (Comparison)

### 1. مقارنة منتج مع المنتجات المتشابهة
- **URL:** `/api/comparison/{product_id}/compare/`
- **Method:** `GET`
- **مثال استجابة:**
```json
{
  "product": { ... },
  "similar_products": [ { ... }, ... ]
}
```

### 2. مقارنة بين عدة منتجات
- **URL:** `/api/comparison/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>, Content-Type: application/json
- **Body:**
```json
{"product_ids": ["id1", "id2"]}
```
- **ملاحظة:** لا يمكن مقارنة منتجات من فئات مختلفة. إذا حاولت ذلك، ستظهر الرسالة التالية:
```json
{"detail": "لا يمكن مقارنة منتجات من فئات مختلفة. يرجى اختيار منتجات من نفس الفئة فقط."}
```
- **مثال استجابة:**
```json
{
  "products": [ { ... }, { ... } ],
  "comparison": { "fields": ["name", "brand", "price", "rating", "likes", "dislikes", "views", "is_featured"] },
  "best_product": { ... },
  "note": "تم وسم المنتج الأفضل بناءً على التقييم وعدد المشاهدات."
}
```

### 3. مقارنة جميع المنتجات وإرجاع الأفضل
- **URL:** `/api/comparison/?best=1`
- **Method:** `GET`
- **مثال استجابة:**
```json
{
  "best_product": { ... },
  "note": "تم اختيار هذا المنتج كأفضل منتج بناءً على التقييم وعدد المشاهدات."
}
```

---

## التفضيلات والمفضلة (Preferences & Favorites)

### 1. تفضيلات المستخدم
- **URL:** `/api/user/preferences/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
{"min_price": 100, "max_price": 2000, "preferred_brands": ["Apple", "Samsung"]}
```

### 2. المنتجات المفضلة
- **URL:** `/api/user/favorites/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
[{"id": "...", "name": "...", ...}]
```

---

## الإشعارات (Notifications)

### 1. قائمة الإشعارات
- **URL:** `/api/notifications/`
- **Method:** `GET`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
[{"id": "...", "title": "...", "body": "...", ...}]
```

---

## المصادقة (Authentication)

### 1. تسجيل مستخدم جديد
- **URL:** `/api/auth/register/`
- **Method:** `POST`
- **Headers:** Content-Type: application/json
- **Body:**
```json
{"email": "user@email.com", "password": "your_password", "name": "User Name"}
```
- **مثال استجابة:**
```json
{"id": 1, "email": "user@email.com", "name": "User Name"}
```

### 2. تسجيل الدخول
- **URL:** `/api/auth/login/`
- **Method:** `POST`
- **Headers:** Content-Type: application/json
- **Body:**
```json
{"email": "user@email.com", "password": "your_password"}
```
- **مثال استجابة:**
```json
{"access": "...", "refresh": "...", "user": {"id": 1, "email": "user@email.com", "name": "User Name"}}
```

### 3. تحديث التوكن
- **URL:** `/api/auth/refresh/`
- **Method:** `POST`
- **Headers:** Content-Type: application/json
- **Body:**
```json
{"refresh": "..."}
```
- **مثال استجابة:**
```json
{"access": "..."}
```

### 4. تسجيل الخروج
- **URL:** `/api/auth/logout/`
- **Method:** `POST`
- **Headers:** Authorization: Bearer <access_token>
- **مثال استجابة:**
```json
{"detail": "Successfully logged out."}
```

### 5. إعادة تعيين كلمة المرور
- **URL:** `/api/auth/reset-password/`
- **Method:** `POST`
- **Headers:** Content-Type: application/json
- **Body:**
```json
{"email": "user@email.com"}
```
- **مثال استجابة:**
```json
{"detail": "Password reset e-mail has been sent."}
```

---

> استبدل `<access_token>` بالتوكن الخاص بك، و`{product_id}` أو `{shop_id}` بالمعرف المطلوب.
