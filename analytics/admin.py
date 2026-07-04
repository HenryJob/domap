from django.contrib import admin
from .models import (
    VisitorSession, PageView, CartEvent, WishlistEvent,
    CheckoutEvent, ProductViewEvent, WhatsappClickEvent, InstagramClickEvent,
)


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'first_seen', 'last_seen', 'is_bot')
    list_filter = ('is_bot',)
    search_fields = ('session_key',)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('session', 'page_label', 'path', 'entered_at', 'duration_seconds', 'is_duration_final')
    list_filter = ('page_label',)


@admin.register(CartEvent)
class CartEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'product', 'event_type', 'quantity', 'created_at')
    list_filter = ('event_type',)


@admin.register(WishlistEvent)
class WishlistEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'product', 'event_type', 'created_at')
    list_filter = ('event_type',)


@admin.register(CheckoutEvent)
class CheckoutEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'step', 'created_at')


@admin.register(ProductViewEvent)
class ProductViewEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'product', 'created_at')


@admin.register(WhatsappClickEvent)
class WhatsappClickEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'created_at')


@admin.register(InstagramClickEvent)
class InstagramClickEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'created_at')
