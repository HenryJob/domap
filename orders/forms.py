from django import forms
from django.forms import inlineformset_factory
from .models import Order, ManualSale, ManualSaleItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name', 'phone', 'email', 'order_type', 'address',
            'scheduled_date', 'scheduled_time', 'payment_method', 'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Ingresa tu nombre'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej. 987 654 321'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ej. tucorreo@ejemplo.com (opcional)'}),
            'order_type': forms.RadioSelect(attrs={'class': 'btn-check'}),
            'address': forms.TextInput(attrs={'placeholder': 'Ej. Av. La Marina 1234, San Miguel'}),
            # Inputs de texto potenciados por Flatpickr (ver cart_detail.html).
            # El formato explícito garantiza que el valor inicial (hoy) se
            # renderice como 2026-07-04 para que Flatpickr lo lea bien.
            'scheduled_date': forms.DateInput(
                attrs={'class': 'js-date-picker', 'placeholder': 'Elige la fecha', 'autocomplete': 'off'},
                format='%Y-%m-%d',
            ),
            'scheduled_time': forms.TimeInput(
                attrs={'class': 'js-time-picker', 'placeholder': 'Elige la hora', 'autocomplete': 'off'},
                format='%H:%M',
            ),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej. Sin azúcar añadida, más miel, etc.'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'btn-check'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('order_type') == 'delivery' and not cleaned.get('address'):
            self.add_error('address', 'La dirección es obligatoria para delivery.')
        return cleaned


class OrderLookupForm(forms.Form):
    order_number = forms.IntegerField(label='Número de pedido', min_value=1)
    phone = forms.CharField(label='Teléfono', max_length=20)


class ManualSaleForm(forms.ModelForm):
    class Meta:
        model = ManualSale
        fields = ['customer_name', 'phone', 'sale_date', 'total_amount', 'session_reference', 'notes']
        widgets = {
            'sale_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'session_reference': forms.TextInput(attrs={'placeholder': 'Ej. AB12CD3D (opcional)'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


ManualSaleItemFormSet = inlineformset_factory(
    ManualSale, ManualSaleItem,
    fields=['product', 'quantity', 'unit_price'],
    extra=2, can_delete=True,
)
