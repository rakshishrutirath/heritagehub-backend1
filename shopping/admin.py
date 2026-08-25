from django.contrib import admin
from .models import ProductCategory, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'price',
        'display_order',
        'is_active',
    ]

    list_filter = [
        'category',
        'is_active',
    ]

    search_fields = [
        'name',
        'description',
    ]

    ordering = [
        'display_order',
    ]