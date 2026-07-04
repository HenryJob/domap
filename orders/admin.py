from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import reverse

from .models import (
    Order, OrderItem, OrderItemExtra, ManualSale, ManualSaleItem, WhatsAppConnection,
)
from .whatsapp import connection_context


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


@admin.register(WhatsAppConnection)
class WhatsAppConnectionAdmin(admin.ModelAdmin):
    """Expone la pantalla de conexión/estado de WhatsApp dentro de /admin.
    No es un modelo real: la vista de "lista" muestra el QR y las acciones."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_staff

    def changelist_view(self, request, extra_context=None):
        # URL de esta misma pantalla, para que las acciones (prueba, reiniciar,
        # desconectar) vuelvan aquí dentro del admin en vez de salir al sitio.
        back = reverse('admin:orders_whatsappconnection_changelist')
        ctx = {
            **self.admin_site.each_context(request),
            'title': 'WhatsApp — conectar número',
            'opts': self.model._meta,
            'back_url': back,
            **connection_context(),
        }
        return TemplateResponse(request, 'admin/orders/whatsapp_connection.html', ctx)
