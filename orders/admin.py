from django.contrib import admin
from .models import Order, OrderItem, OrderItemExtra, ManualSale, ManualSaleItem


class OrderItemExtraInline(admin.TabularInline):
    model = OrderItemExtra
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'order_type', 'status', 'total', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'order_type', 'payment_method')
    search_fields = ('customer_name', 'phone', 'session_key')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price')
    inlines = [OrderItemExtraInline]


class ManualSaleItemInline(admin.TabularInline):
    model = ManualSaleItem
    extra = 0


@admin.register(ManualSale)
class ManualSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'sale_date', 'total_amount', 'session_reference', 'logged_by')
    list_filter = ('sale_date',)
    search_fields = ('customer_name', 'phone', 'session_reference')
    inlines = [ManualSaleItemInline]
