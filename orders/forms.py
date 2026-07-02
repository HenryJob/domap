from django import forms
from django.forms import inlineformset_factory
from .models import Order, ManualSale, ManualSaleItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name', 'phone', 'order_type', 'address',
            'scheduled_date', 'scheduled_time', 'payment_method', 'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Ingresa tu nombre'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej. 987 654 321'}),
            'order_type': forms.RadioSelect(attrs={'class': 'btn-check'}),
            'address': forms.TextInput(attrs={'placeholder': 'Ej. Av. La Marina 1234, San Miguel'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej. Sin azúcar añadida, más miel, etc.'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'btn-check'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('order_type') == 'delivery' and not cleaned.get('address'):
            self.add_error('address', 'La dirección es obligatoria para delivery.')
        return cleaned


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
