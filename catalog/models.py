from django.db import models
from django.urls import reverse


class Product(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    price_is_from = models.BooleanField(
        default=False, help_text='Muestra el precio como "Desde S/ X" (ej. Personalizado)')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_combo = models.BooleanField(default=False)
    is_customizable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='Aparece en el preview de la página de Inicio')
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:menu') + f'#producto-{self.slug}'


class Extra(models.Model):
    name = models.CharField(max_length=60)
    icon_emoji = models.CharField(max_length=8, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
