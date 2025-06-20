// حماية الوصول للداشبورد (يتم تضمينه في جميع صفحات الداشبورد)
(function() {
    var email = localStorage.getItem('dashboard_email');
    if(localStorage.getItem('dashboard_logged_in') !== '1' || email !== 'admin@gmail.com') {
        // حفظ الصفحة المطلوبة للعودة إليها بعد تسجيل الدخول
        localStorage.setItem('dashboard_redirect', window.location.pathname + window.location.search);
        window.location.href = '/static/login.html';
    }
})();
