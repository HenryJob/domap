from decimal import Decimal


def summary_context(cart, delivery_zone=None):
    delivery_fee = delivery_zone.fee if delivery_zone else Decimal('0')
    cart_subtotal = cart.subtotal()
    return {
        'cart_lines': cart.lines(),
        'cart_subtotal': cart_subtotal,
        'delivery_fee': delivery_fee,
        'cart_total': cart_subtotal + delivery_fee,
    }
