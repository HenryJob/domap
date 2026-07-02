from django.conf import settings
from django.db import models
from django.utils import timezone
from catalog.models import Product, Extra


class Order(models.Model):
    ORDER_TYPE_CHOICES = [('delivery', 'Delivery'), ('recojo', 'Recojo')]
    PAYMENT_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('yape_plin', 'Yape / Plin'),
        ('tarjeta', 'Tarjeta de débito/crédito'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    # Valor (no FK) comparado contra VisitorSession.session_key para
    # correlacionar el pedido con su sesión de analítica sin acoplar las apps.
    session_key = models.CharField(max_length=40, blank=True, db_index=True)

    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='delivery')
    address = models.CharField(max_length=255, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default='efectivo')
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} · {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def line_total(self):
        extras_total = sum(e.unit_price * e.quantity for e in self.extras.all())
        return (self.unit_price + extras_total) * self.quantity

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'


class OrderItemExtra(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='extras')
    extra = models.ForeignKey(Extra, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.extra.name}'


class ManualSale(models.Model):
    """Venta cerrada por WhatsApp y registrada manualmente por el staff,
    para que cuente en la conversión total y los ingresos del dashboard."""
    customer_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    session_reference = models.CharField(
        max_length=12, blank=True, db_index=True,
        help_text='Código corto que el cliente comparte por WhatsApp, copiado de su sesión web (opcional).')
    notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f'Venta WhatsApp #{self.id} · S/ {self.total_amount}'


class ManualSaleItem(models.Model):
    sale = models.ForeignKey(ManualSale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'{self.quantity} x {self.product or "producto"}'
