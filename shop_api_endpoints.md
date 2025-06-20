# خطوات إنشاء متجر جديد من البداية للنهاية

---

## 1. تسجيل مستخدم جديد (مالك)
- **URL:** `https://binc-b-1.onrender.com/api/auth/register/`
- **Method:** `POST`
- **Body (JSON):**
  ```json
  {
    "username": "newowner",
    "email": "owner@example.com",
    "password": "your_password",
    "user_type": "owner"
  }
  ```

---

## 2. تسجيل الدخول
- **URL:** `https://binc-b-1.onrender.com/api/auth/login/`
- **Method:** `POST`
- **Body (JSON):**
  ```json
  {
    "email": "owner@example.com",
    "password": "your_password"
  }
  ```
- **Response:**
  - access: (استخدمه في جميع الطلبات التالية)
  - refresh

  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1MDQ3NjM0NywiaWF0IjoxNzUwMzg5OTQ3LCJqdGkiOiJhMDVlN2U5YmVkN2I0YmQ3YmJiMDQ0NDRkM2JiMTI2NyIsInVzZXJfaWQiOjM1fQ.jbpZDXQZsNb7kyTg7Qi18RrWv5DaBRWpyaoCSrbGt-Y",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUwMzkxNzQ3LCJpYXQiOjE3NTAzODk5NDcsImp0aSI6ImU5NTQ1YjNhNDJlMDQxYjZhYTgwNWEzY2ZkMjE2MWNjIiwidXNlcl9pZCI6MzV9.GrlfcKQkbNGXi8RhHl9VBOJGM16adl-7JTuiuaBPpPE",
    "user": {
        "username": "newowner",
        "email": "owner@example.com",
        "user_type": "owner"
    },
    "permissions": []
}

---

## 3. إنشاء متجر جديد
- **URL:** `https://binc-b-1.onrender.com/api/shop/register/`
- **Method:** `POST`
- **Headers:**
  - Authorization: Bearer <access_token>
  - Content-Type: multipart/form-data
- **Body (form-data):**
  - name: متجر التقنية الحديثة
  - address: الرياض، حي العليا، شارع الملك فهد
  - logo: (اختر صورة شعار حقيقية من جهازك)
  - url: https://techstore.com

---

## 4. التحقق من وجود متجر للمالك
- **URL:** `https://binc-b-1.onrender.com/api/shop/check/`
- **Method:** `POST`
- **Headers:**
  - Authorization: Bearer <access_token>
- **Body:** لا حاجة لإرسال بيانات (body فارغ)

---

## مثال باستخدام curl (إنشاء متجر)
```bash
curl -X POST https://binc-b-1.onrender.com/api/shop/register/ \
  -H "Authorization: Bearer <access_token>" \
  -F "name=متجر التقنية الحديثة" \
  -F "address=الرياض، حي العليا، شارع الملك فهد" \
  -F "logo=@/Users/youruser/Desktop/logo.png" \
  -F "url=https://techstore.com"
```

---

> استبدل `<access_token>` بالتوكن الخاص بك، و`logo` بمسار صورة حقيقية على جهازك.

---

## التغييرات على السيريلزر (للمطورين فقط)

### ShopSerializer
- **إضافة حقل الشعار (logo):**
  - تم إضافة حقل الشعار إلى السيريلزر مع جعله غير مطلوب (optional) ويمكن أن يكون فارغًا (nullable).

```python
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = (..., 'logo', ...)
        extra_kwargs = {
            'logo': {'required': False, 'allow_null': True}
        }
```
