from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SavedAddress


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com'}))

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password1', 'password2']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
            'username': forms.TextInput(attrs={'placeholder': 'Usuario'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class SavedAddressForm(forms.ModelForm):
    class Meta:
        model = SavedAddress
        fields = ['label', 'address', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Ej. Casa, Trabajo'}),
            'address': forms.TextInput(attrs={'placeholder': 'Ej. Av. La Marina 1234, San Miguel'}),
        }
