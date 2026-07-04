from django import template
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote

register = template.Library()


@register.simple_tag(takes_context=True)
def whatsapp_order_link(context, message=None):
    """Build a wa.me deep link, prefilled with a short session reference code
    so staff can correlate a WhatsApp sale back to the visitor's session."""
    request = context.get('request')
    code = ''
    if request is not None and request.session.session_key:
        code = request.session.session_key[:8].upper()
    text = message or 'Hola Mordé, quiero hacer un pedido.'
    if code:
        text = f'{text} (Código: {code})'
    return f'https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(text)}'


@register.simple_tag
def instagram_dm_link():
    """Instagram no soporta prellenar el mensaje de un DM como wa.me; este
    link simplemente abre el chat directo con la cuenta del negocio."""
    return f'https://ig.me/m/{settings.INSTAGRAM_HANDLE}'


@register.simple_tag(takes_context=True)
def whatsapp_session_code(context):
    request = context.get('request')
    if request is not None and request.session.session_key:
        return request.session.session_key[:8].upper()
    return ''


@register.filter
def soles(value):
    try:
        return f'S/ {float(value):.2f}'
    except (TypeError, ValueError):
        return value
