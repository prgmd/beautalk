from django.contrib import admin
from .models import Product, Review

# admin 사이트에 Product 테이블 저장
admin.site.register(Product)
admin.site.register(Review)