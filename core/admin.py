from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy
from .models import User, Shop, Product, Category, Brand

# حل مشكلة TokenAdmin
TokenAdmin.raw_id_fields = ['user']

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')

admin.site.register(User, UserAdmin)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)