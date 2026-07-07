from django import forms

from catalog.models import Extra, Product
from orders.models import DeliveryZone, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'price', 'price_is_from', 'image',
            'is_combo', 'is_customizable', 'combo_products',
            'is_active', 'is_featured', 'display_order',
        ]
        widgets = {
            'combo_products': forms.CheckboxSelectMultiple,
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['combo_products'].queryset = Product.objects.filter(
            is_combo=False).order_by('name')
        if self.instance.pk:
            self.fields['combo_products'].queryset = Product.objects.exclude(
                pk=self.instance.pk).order_by('name')


class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['name', 'icon_emoji', 'price', 'is_active', 'display_order']


class DeliveryZoneForm(forms.ModelForm):
    class Meta:
        model = DeliveryZone
        fields = ['name', 'fee', 'active']


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
