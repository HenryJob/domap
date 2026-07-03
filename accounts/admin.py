from django.contrib import admin
from .models import SavedAddress


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address', 'is_default')
    search_fields = ('user__username', 'label', 'address')
