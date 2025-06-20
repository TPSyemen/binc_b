// حماية الوصول للداشبورد (يتم تضمينه في جميع صفحات الداشبورد)
(function() {
    var email = localStorage.getItem('dashboard_email');
    if(localStorage.getItem('dashboard_logged_in') !== '1' || email !== 'admin@gmail.com') {
        // حفظ الصفحة المطلوبة للعودة إليها بعد تسجيل الدخول
        localStorage.setItem('dashboard_redirect', window.location.pathname + window.location.search);
        window.location.href = '/static/login.html';
    }

    // تحقق من صلاحية التوكن قبل أي طلب API
    async function checkTokenValidity() {
        const token = localStorage.getItem('access_token');
        if (!token) return false;
        // جرب طلب بسيط محمي
        const res = await fetch('/api/auth/users/', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.status === 401) {
            // التوكن منتهي أو غير صالح
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.setItem('dashboard_redirect', window.location.pathname + window.location.search);
            window.location.href = '/static/login.html';
            return false;
        }
        return true;
    }
    // استدعِ هذا التحقق عند تحميل أي صفحة داشبورد
    checkTokenValidity();
})();
