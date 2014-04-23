from django.contrib import admin
from apps.main.models import Product, Purchase, ProductImage, UserCard, UserProfile


admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(ProductImage)
admin.site.register(UserCard)
admin.site.register(UserProfile)
