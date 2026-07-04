import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_order_confirmation(order, request=None):
    """Envía la confirmación por email. Nunca debe romper el checkout: el
    pedido ya está guardado en BD cuando esto se llama, así que una falla de
    SMTP solo se registra en el log."""
    tracking_path = reverse('orders:order_success', args=[order.id]) + f'?t={order.access_token}'
    tracking_url = request.build_absolute_uri(tracking_path) if request else tracking_path
    body = render_to_string('orders/email/order_confirmation.txt', {
        'order': order,
        'tracking_url': tracking_url,
        'instagram_url': settings.INSTAGRAM_URL,
    })
    try:
        send_mail(
            subject=f'Confirmación de tu pedido #{order.id} · Mordé',
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception('No se pudo enviar el email de confirmación del pedido #%s', order.id)
