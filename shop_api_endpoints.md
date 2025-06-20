# Shop API Endpoints (نقاط نهاية المتجر)

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
  - access: استخدمه في جميع الطلبات التالية

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
  - url: https://techstore.com
  - logo: (اختياري، صورة شعار المتجر)

---

## 4. التحقق من وجود متجر للمالك
- **URL:** `https://binc-b-1.onrender.com/api/shop/check/`
- **Method:** `GET`
- **Headers:**
  - Authorization: Bearer <access_token>
- **Body:** لا حاجة لإرسال بيانات (body فارغ)

---

> استبدل `<access_token>` بالتوكن الخاص بك.
