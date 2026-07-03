from decimal import Decimal

from django.conf import settings


def summary_context(cart):
    delivery_fee = Decimal(str(settings.DELIVERY_FEE))
    cart_subtotal = cart.subtotal()
    return {
        'cart_lines': cart.lines(),
        'cart_subtotal': cart_subtotal,
        'delivery_fee': delivery_fee,
        'cart_total': cart_subtotal + delivery_fee,
    }
