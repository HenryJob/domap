"""Funciones que el resto de apps (catalog/cart/orders) llaman para registrar
eventos de analítica, sin que esas apps dependan de los modelos de analytics."""

from .models import CartEvent, WishlistEvent, CheckoutEvent, ProductViewEvent, WhatsappClickEvent


def _session_or_none(request):
    return getattr(request, 'visitor_session', None)


def log_cart_event(request, product_id, event_type, quantity=1):
    session = _session_or_none(request)
    if session is None:
        return
    CartEvent.objects.create(session=session, product_id=product_id, event_type=event_type, quantity=quantity)


def log_wishlist_event(request, product_id, event_type):
    session = _session_or_none(request)
    if session is None:
        return
    WishlistEvent.objects.create(session=session, product_id=product_id, event_type=event_type)


def log_checkout_started(request):
    session = _session_or_none(request)
    if session is None:
        return
    if request.session.get('checkout_started_logged'):
        return
    CheckoutEvent.objects.create(session=session, step='started')
    request.session['checkout_started_logged'] = True


def log_product_views(request, products):
    session = _session_or_none(request)
    if session is None or not products:
        return
    ProductViewEvent.objects.bulk_create(
        [ProductViewEvent(session=session, product=p) for p in products]
    )


def log_whatsapp_click(request):
    session = _session_or_none(request)
    if session is None:
        return
    WhatsappClickEvent.objects.create(session=session)
