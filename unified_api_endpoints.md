# Unified API Endpoints Documentation (توثيق جميع نقاط النهاية)

---

## المنتجات (Products)

### قائمة المنتجات
- **URL:** `/api/products/`
- **Method:** `GET`
- **View:** ProductListView
- **Serializer:** ProductListSerializer
- **Model:** Product
- **الصلاحيات:** متاح للجميع (نتائج مخصصة حسب نوع المستخدم)
- **مثال استجابة:**
```json
[
  {
    "id": "1",
    "name": "iPhone 15 Pro",
    "price": 100,
    "original_price": 120,
    "discount": 17,
    "category": {"id": "2", "name": "هواتف"},
    "image_url": "https://...",
    "rating": 4.5,
    "in_stock": true,
    "is_active": true
  }
]
```

### تفاصيل منتج
- **URL:** `/api/products/{product_id}/`
- **Method:** `GET`
- **View:** ProductDetailView
- **Serializer:** ProductDetailSerializer
- **Model:** Product
- **الصلاحيات:** متاح للجميع (المنتجات غير النشطة للأدمن فقط)
- **مثال استجابة:**
```json
{
  "id": "1",
  "name": "iPhone 15 Pro",
  "description": "هاتف رائد ...",
  "price": 100,
  "original_price": 120,
  "discount": 17,
  "category": {"id": "2", "name": "هواتف"},
  "brand": {"id": "3", "name": "Apple"},
  "shop": {"id": "10", "name": "Apple Store"},
  "image_url": "https://...",
  "in_stock": true,
  "rating": 4.5,
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "reviews": [
    {"id": "100", "user": {"id": "20", "name": "أحمد"}, "rating": 5, "comment": "ممتاز", "created_at": "2024-06-01T12:00:00Z"}
  ],
  "video_url": "https://...",
  "release_date": "2024-01-01",
  "likes": 100,
  "dislikes": 5,
  "neutrals": 2,
  "views": 1200,
  "is_banned": false
}
```

### إنشاء منتج جديد
- **URL:** `/api/products/create/`
- **Method:** `POST`
- **View:** ProductCreateView
- **Serializer:** ProductDetailSerializer
- **Model:** Product
- **الصلاحيات:** فقط للمالك أو الأدمن (Authorization مطلوب)
- **Body:** name, price, category_id, ...
- **مثال استجابة:**
```json
{
  "id": "2",
  "name": "منتج جديد",
  "price": 200,
  "original_price": 250,
  "discount": 20,
  "category": {"id": "2", "name": "هواتف"},
  "brand": {"id": "3", "name": "Apple"},
  "shop": {"id": "10", "name": "Apple Store"},
  "image_url": "https://...",
  "rating": 0,
  "is_active": true,
  "in_stock": true,
  "created_at": "2024-06-22T12:00:00Z"
}
```

### تحديث منتج
- **URL:** `/api/products/{product_id}/update/`
- **Method:** `PUT`/`PATCH`
- **View:** ProductUpdateView
- **Serializer:** ProductDetailSerializer
- **Model:** Product
- **الصلاحيات:** فقط للمالك (صاحب المنتج) أو الأدمن (Authorization مطلوب)
- **Body:** الحقول التي تريد تعديلها فقط
- **مثال استجابة:**
```json
{
  "id": "1",
  "name": "iPhone 15 Pro (معدل)",
  ... (نفس حقول تفاصيل المنتج)
}
```

### حذف منتج
- **URL:** `/api/products/{product_id}/delete/`
- **Method:** `DELETE`
- **View:** ProductDeleteView
- **Model:** Product
- **الصلاحيات:** فقط للمالك (صاحب المنتج) أو الأدمن (Authorization مطلوب)
- **مثال استجابة:**
```json
{"message": "Product deleted successfully"}
```

### المنتجات المميزة
- **URL:** `/api/products/featured/`
- **Method:** `GET`
- **View:** FeaturedProductsView
- **Serializer:** ProductListSerializer
- **Model:** Product
- **الصلاحيات:** متاح للجميع
- **مثال استجابة:**
```json
[
  {
    "id": "1",
    "name": "iPhone 15 Pro",
    "is_featured": true,
    ... (نفس حقول قائمة المنتجات)
  }
]
```

### البحث عن المنتجات
- **URL:** `/api/products/search/`
- **Method:** `GET`
- **View:** ProductSearchView
- **Serializer:** ProductListSerializer
- **Model:** Product
- **الصلاحيات:** متاح للجميع
- **Query Parameters:** query, category, brand, ...
- **مثال استجابة:**
```json
[
  {
    "id": "1",
    "name": "iPhone 15 Pro",
    ... (نفس حقول قائمة المنتجات)
  }
]
```

### المنتجات التي تمت مشاهدتها مؤخرًا
- **URL:** `/api/products/recently-viewed/`
- **Method:** `GET`
- **View:** RecentlyViewedProductsView
- **مثال استجابة:**
```json
{
  "recently_viewed": [
    {"id": "1", "name": "iPhone 15 Pro", ...}
  ]
}
```

### منتجات مشابهة
- **URL:** `/api/products/{product_id}/similar/`
- **Method:** `GET`
- **View:** SimilarProductsView
- **Serializer:** ProductListSerializer, ProductDetailSerializer
- **Model:** Product
- **الصلاحيات:** متاح للجميع
- **مثال استجابة:**
```json
{
  "current_product": { ... (تفاصيل المنتج) },
  "similar_products": [ { ... (نفس حقول قائمة المنتجات) } ]
}
```

### تاريخ أسعار المنتج
- **URL:** `/api/products/{product_id}/price-history/`
- **Method:** `GET`
- **View:** ProductPriceHistoryView
- **Model:** Product (+ price_history)
- **الصلاحيات:** متاح للجميع
- **مثال استجابة:**
```json
{"product_id": "1", "price_history": [{"date": "2024-01-01", "price": 1800.0}]}
```

---

## المتاجر (Shops)

### قائمة المتاجر
- **URL:** `/api/shop/`
- **Method:** GET
- **View:** ShopListView
- **Serializer:** ShopSerializer
- **Model:** Shop
- **مثال استجابة:**
```json
[
  {"id": "1", "name": "Apple Store", "logo": "https://..."}
]
```

### تفاصيل متجر
- **URL:** `/api/shop/{shop_id}/`
- **Method:** GET
- **View:** ShopDetailView
- **Serializer:** ShopSerializer
- **Model:** Shop
- **مثال استجابة:**
```json
{
  "id": "1",
  "name": "Apple Store",
  "address": "الرياض ...",
  "description": "متجر معتمد ...",
  "logo": "https://...",
  "banner": "https://...",
  "url": "https://...",
  "phone": "0500000000",
  "email": "info@apple.com",
  "social_media": {"facebook": "...", "twitter": "..."},
  "owner": {"id": "10", "username": "apple_owner", "email": "owner@apple.com", "is_active": true},
  "product_count": 10,
  "completion_percentage": 90
}
```

### إنشاء متجر جديد
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

### التوصيات المخصصة للمستخدم
- **URL:** `/api/recommendations/`
- **Method:** GET
- **View:** RecommendationView
- **Serializer:** ProductRecommendationSerializer
- **Model:** ProductRecommendation, Product
- **مثال استجابة:**
```json
{
  "preferred": [
    {"id": "1", "name": "iPhone 15 Pro", "brand": "Apple", "score": 92.5, ... }
  ],
  "liked": [
    {"id": "2", "name": "Galaxy S24 Ultra", "brand": "Samsung", "score": 89.0, ... }
  ]
}
```

### التوصيات الهجينة
- **URL:** `/api/recommendations/hybrid/`
- **Method:** GET
- **View:** HybridRecommendationView
- **Serializer:** ProductRecommendationSerializer
- **Model:** ProductRecommendation, Product
- **مثال استجابة:**
```json
[
  {"id": "1", "name": "iPhone 15 Pro", "brand": "Apple", "score": 92.5, ... }
]
```

---

## المراجعات (Reviews)

### إضافة مراجعة
- **URL:** `/reviews/add/`
- **Method:** POST
- **View:** ReviewListCreateView
- **Serializer:** CreateReviewSerializer
- **Model:** Review
- **مثال استجابة:**
```json
{"id": "100", "product": "1", "rating": 5, "comment": "ممتاز", "user": {"id": "20", "name": "أحمد"}, "created_at": "2024-06-01T12:00:00Z"}
```

### قائمة مراجعات منتج
- **URL:** `/reviews/products/{product_id}/reviews/`
- **Method:** GET
- **View:** ProductReviewsView
- **Serializer:** ReviewSerializer
- **Model:** Review
- **مثال استجابة:**
```json
[
  {"id": "100", "rating": 5, "comment": "ممتاز", "user": {"id": "20", "name": "أحمد"}, "created_at": "2024-06-01T12:00:00Z"}
]
```

---

## المقارنة (Comparison)

### مقارنة منتج مع المنتجات المتشابهة
- **URL:** `/api/comparison/{product_id}/compare/`
- **Method:** GET
- **View:** ComparisonView
- **Serializer:** ProductDetailSerializer
- **Model:** Product
- **مثال استجابة:**
```json
{
  "product": { ... },
  "similar_products": [ { ... } ]
}
```

### مقارنة بين عدة منتجات
- **URL:** `/api/comparison/`
- **Method:** POST
- **View:** ComparisonView
- **Serializer:** ProductDetailSerializer
- **Model:** Product
- **مثال استجابة:**
```json
{
  "products": [ { ... }, { ... } ],
  "comparison": { "fields": ["name", "brand", "price", "rating", "likes", "dislikes", "views", "is_featured"] },
  "best_product": { ... },
  "note": "تم وسم المنتج الأفضل بناءً على التقييم وعدد المشاهدات."
}
```

---

## العروض والخصومات (Promotions)

### قائمة العروض
- **URL:** `/api/promotions/`
- **Method:** GET
- **View:** PromotionListView
- **Serializer:** PromotionSerializer
- **Model:** Promotion
- **مثال استجابة:**
```json
[
  {"id": "200", "title": "خصم الصيف", "description": "خصم 10% على جميع المنتجات", "discount_percent": 10, "start_date": "2024-07-01", "end_date": "2024-07-10", "is_active": true}
]
```

### كود الخصم
- **URL:** `/api/promotions/discount-codes/`
- **Method:** POST
- **View:** DiscountCodeListCreateView
- **Serializer:** DiscountCodeSerializer
- **Model:** DiscountCode
- **مثال استجابة:**
```json
{"id": "300", "code": "DISCOUNT2024", "discount_percent": 10, "is_active": true, "valid_until": "2024-07-10"}
```

---

## الإشعارات (Notifications)

### قائمة الإشعارات
- **URL:** `/api/notifications/`
- **Method:** GET
- **View:** NotificationListView
- **Serializer:** NotificationSerializer
- **Model:** Notification
- **مثال استجابة:**
```json
[
  {"id": "400", "title": "تنبيه جديد", "body": "تم تحديث حالة طلبك", "extra_data": {"order_id": "123"}, "action_url": "/orders/123", "is_read": false, "created_at": "2024-06-01T12:00:00Z"}
]
```

---

## الوقت الحقيقي (Realtime)

### إشعارات WebSocket
- **URL:** `ws/notifications/`
- **Method:** WebSocket
- **Consumer:** NotificationConsumer
- **Model:** Notification
- **مثال رسالة:**
```json
{"type": "notification", "title": "تنبيه جديد", "body": "تم تحديث حالة طلبك", "created_at": "2024-06-01T12:00:00Z"}
```
