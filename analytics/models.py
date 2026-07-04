from django.db import models
from catalog.models import Product


class VisitorSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(max_length=255, blank=True)
    landing_path = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=255, blank=True)
    is_bot = models.BooleanField(default=False)

    def __str__(self):
        return self.session_key


class PageView(models.Model):
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='pageviews')
    path = models.CharField(max_length=255)
    page_label = models.CharField(max_length=60, blank=True)
    entered_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    is_duration_final = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['entered_at'])]

    def __str__(self):
        return f'{self.page_label or self.path} · {self.entered_at:%Y-%m-%d %H:%M}'


class CartEvent(models.Model):
    EVENT_CHOICES = [('add', 'Agregar'), ('remove', 'Quitar'), ('update', 'Actualizar')]

    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='cart_events')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'])]


class WishlistEvent(models.Model):
    EVENT_CHOICES = [('add', 'Agregar'), ('remove', 'Quitar')]

    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='wishlist_events')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'])]


class CheckoutEvent(models.Model):
    STEP_CHOICES = [('started', 'Iniciado')]

    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='checkout_events')
    step = models.CharField(max_length=20, choices=STEP_CHOICES, default='started')
    created_at = models.DateTimeField(auto_now_add=True)


class ProductViewEvent(models.Model):
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='product_views')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='view_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'])]


class WhatsappClickEvent(models.Model):
    """Clic en el botón de WhatsApp — señal de intención de compra antes de
    que el staff registre (o no) la venta manualmente."""
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='whatsapp_clicks')
    created_at = models.DateTimeField(auto_now_add=True)


class InstagramClickEvent(models.Model):
    """Clic en el botón de Instagram — misma señal de intención que
    WhatsappClickEvent, para comparar cuántos clientes prefieren cada canal."""
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='instagram_clicks')
    created_at = models.DateTimeField(auto_now_add=True)
