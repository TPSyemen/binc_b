# برومبت بناء صفحة React لتسجيل مالك متجر وإنشاء متجر جديد

## المطلوب:

برجاء بناء صفحة React متكاملة (أو مجموعة صفحات) تتكامل مع الـ API التالي:

1. **تسجيل حساب مالك (Owner):**
   - نموذج تسجيل يرسل البيانات إلى:
     - `POST /api/auth/register/`
     - Body: `{ "email": "...", "password": "...", "name": "..." }`
   - بعد نجاح التسجيل، يتم توجيه المستخدم لتسجيل الدخول.

2. **تسجيل الدخول:**
   - نموذج تسجيل دخول يرسل البيانات إلى:
     - `POST /api/auth/login/`
     - Body: `{ "email": "...", "password": "..." }`
   - عند النجاح، يتم حفظ الـ access_token في localStorage أو state.

3. **التحقق من وجود متجر:**
   - بعد تسجيل الدخول، يتم إرسال طلب:
     - `GET /api/shop/check/`
     - Header: `Authorization: Bearer <access_token>`
   - إذا كانت الاستجابة:
     ```json
     { "has_shop": true, "shop": { ... } }
     ```
     يتم توجيه المستخدم إلى لوحة تحكم المتجر (لا يمكن للمالك إنشاء أكثر من متجر واحد).
   - إذا كانت الاستجابة:
     ```json
     { "has_shop": false }
     ```
     يتم عرض نموذج إنشاء متجر (يمكن للمالك إنشاء متجره الأول فقط إذا لم يكن لديه متجر).
   - إذا كانت الاستجابة:
     ```json
     { "detail": "ليس لديك صلاحية للقيام بهذا الإجراء." }
     ```
     يجب إظهار رسالة للمستخدم بأنه لا يملك صلاحية كمالك متجر، ولا يمكنه إنشاء متجر.

4. **إنشاء متجر جديد:**
   - فقط المالك الذي لا يملك أي متجر يمكنه إنشاء متجر جديد واحد فقط.
   - نموذج بيانات المتجر (اسم، وصف، شعار، ...)
   - عند الإرسال:
     - `POST /api/shop/create/`
     - Header: `Authorization: Bearer <access_token>`
     - Body: بيانات المتجر (يفضل استخدام `multipart/form-data` إذا كان هناك صورة)
   - عند النجاح، يتم توجيه المستخدم إلى لوحة تحكم المتجر.

## مثال كامل لطلب إنشاء متجر جديد:

### Endpoint:
POST /api/shop/create/

### Headers:
- Authorization: Bearer <access_token>
- Content-Type: multipart/form-data

### Body (جميع الحقول الممكنة):
- name: اسم المتجر (نص)
- description: وصف المتجر (نص)
- logo: ملف صورة شعار المتجر (اختياري)
- banner: ملف صورة بانر المتجر (اختياري)
- address: العنوان الكامل (نص)
- phone: رقم الهاتف (نص)
- email: البريد الإلكتروني للمتجر (نص)
- website: رابط الموقع الإلكتروني (نص)
- social_media: سلسلة JSON (مثال: '{"facebook": "...", "twitter": "...", "instagram": "..."}')
- business_hours: سلسلة JSON (مثال: '[{"day": "Monday", "open": "09:00", "close": "18:00"}, ...]')

### مثال body باستخدام formData في جافاسكريبت:
```js
const formData = new FormData();
formData.append('name', 'متجري الجديد');
formData.append('description', 'وصف المتجر');
formData.append('logo', fileLogo); // ملف صورة
formData.append('banner', fileBanner); // ملف صورة
formData.append('address', 'اليمن - صنعاء');
formData.append('phone', '+967-123456789');
formData.append('email', 'shop@email.com');
formData.append('website', 'https://myshop.com');
formData.append('social_media', JSON.stringify({ facebook: 'https://facebook.com/myshop' }));
formData.append('business_hours', JSON.stringify([
  { day: 'Monday', open: '09:00', close: '18:00' },
  { day: 'Friday', open: '10:00', close: '16:00' }
]));
```

### مثال استجابة (Response) كامل:
```json
{
  "id": "shop_id",
  "name": "متجري الجديد",
  "description": "وصف المتجر",
  "logo_url": "https://example.com/myshop_logo.jpg",
  "banner_url": "https://example.com/myshop_banner.jpg",
  "owner": {
    "id": "user_id",
    "username": "اسم المالك"
  },
  "address": "اليمن - صنعاء",
  "phone": "+967-123456789",
  "email": "shop@email.com",
  "website": "https://myshop.com",
  "social_media": {
    "facebook": "https://facebook.com/myshop"
  },
  "business_hours": [
    {"day": "Monday", "open": "09:00", "close": "18:00"},
    {"day": "Friday", "open": "10:00", "close": "16:00"}
  ],
  "rating": 0.0,
  "review_count": 0,
  "product_count": 0,
  "follower_count": 0,
  "created_at": "2025-06-22T10:00:00Z",
  "updated_at": "2025-06-22T10:00:00Z"
}
```

## ملاحظات:
- يجب حماية جميع الطلبات التي تتطلب صلاحية مالك باستخدام التوكن.
- لا يمكن للمالك إنشاء أكثر من متجر واحد.
- إذا حاول المستخدم العادي أو غير المالك الوصول لهذه الصفحة، يجب منعه برسالة مناسبة.
- يفضل استخدام React Router للتنقل بين الصفحات (تسجيل، دخول، إنشاء متجر، لوحة التحكم).
- يجب التعامل مع جميع الأخطاء (مثل: البريد مستخدم مسبقاً، كلمة مرور ضعيفة، لديك متجر بالفعل، ...).

## مثال تسلسل الاستخدام:
1. المستخدم يفتح صفحة التسجيل ويختار "مالك متجر".
2. بعد التسجيل وتسجيل الدخول، يتم التحقق تلقائياً إذا كان لديه متجر.
3. إذا لم يكن لديه متجر، يظهر له فورم إدخال بيانات المتجر.
4. بعد إنشاء المتجر، يتم توجيهه للوحة تحكم المتجر.

## روابط الـ API:
- تسجيل مالك: `POST /api/auth/register/`
- تسجيل دخول: `POST /api/auth/login/`
- تحقق من وجود متجر: ``
- إنشاء متجر: `POST /api/shop/create/`

---

يرجى بناء صفحة React (أو مجموعة صفحات) تحقق هذا السيناريو وتتكامل مع هذه الـ endpoints.
