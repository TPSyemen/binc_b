from django.contrib import admin
from .models import User, Shop, Product, Category, Brand

admin.site.register(User)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)