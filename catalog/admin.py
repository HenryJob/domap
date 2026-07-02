from django.contrib import admin
from .models import Product, Extra


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'price_is_from', 'is_combo', 'is_customizable',
                     'is_featured', 'is_active', 'display_order')
    list_editable = ('display_order', 'is_featured', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_combo', 'is_customizable', 'is_featured', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_emoji', 'price', 'is_active', 'display_order')
    list_editable = ('price', 'is_active', 'display_order')
