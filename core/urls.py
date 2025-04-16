from django.urls import path
from .views import RegisterAPIView, LoginAPIView, LogoutAPIView, AccessPointLoginAPIView
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'core'  # Define app namespace for better URL management

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
