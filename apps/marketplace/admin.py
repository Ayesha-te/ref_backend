from django.contrib import admin
from .models import Product, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "price_usd", "is_active", "created_at")
    list_filter = ("is_active",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("buyer", "product", "quantity", "total_usd", "status", "created_at")
    list_filter = ("status",)