from decimal import Decimal

from .emails import send_order_confirmation
from .models import OrderItem, OrderItemExtra
from .whatsapp import send_order_whatsapp


def place_order(request, form, cart):
    """Crea la Order y sus líneas a partir del carrito de la sesión, limpia el
    carrito y dispara el email de confirmación si corresponde. `form` ya debe
    estar validado (form.is_valid() == True) antes de llamar esto."""
    lines = cart.lines()
    subtotal = cart.subtotal()
    zone = form.cleaned_data.get('delivery_zone')
    delivery_fee = zone.fee if form.cleaned_data['order_type'] == 'delivery' and zone else Decimal('0')

    order = form.save(commit=False)
    order.session_key = request.session.session_key or ''
    order.user = request.user if request.user.is_authenticated else None
    order.subtotal = subtotal
    order.delivery_fee = delivery_fee
    order.total = subtotal + delivery_fee
    order.status = 'confirmed'
    order.save()

    for line in lines:
        item = OrderItem.objects.create(
            order=order, product=line['product'],
            quantity=line['quantity'], unit_price=line['product'].price,
        )
        for extra, extra_qty in line['extras']:
            OrderItemExtra.objects.create(
                order_item=item, extra=extra, quantity=extra_qty, unit_price=extra.price)

    cart.clear()
    request.session.pop('checkout_started_logged', None)

    if order.email:
        send_order_confirmation(order, request)

    # Envía el detalle del pedido al cliente por WhatsApp desde el número que el
    # administrador conectó. No rompe el checkout si falla (lo maneja internamente).
    send_order_whatsapp(order)

    return order
