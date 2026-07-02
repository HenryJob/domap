from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404

from cart.cart import Cart
from .forms import OrderForm, ManualSaleForm, ManualSaleItemFormSet
from .models import Order, OrderItem, OrderItemExtra, ManualSale

PEDIDOS_STEPS = [
    {'icon': '🎁', 'title': 'Elige tu producto', 'description': 'Escoge tu Mordé favorito desde el menú.'},
    {'icon': '🛵', 'title': 'Define tu forma de pedido', 'description': 'Selecciona delivery o recojo, fecha y hora.'},
    {'icon': '📋', 'title': 'Confirmamos tu orden', 'description': 'Revisamos los detalles y preparamos tu waffle al momento.'},
    {'icon': '💛', 'title': 'Recibe y disfruta', 'description': 'Te lo entregamos o lo recoges y disfrutas fresco y delicioso.'},
]


def _log_checkout_started(request):
    try:
        from analytics.services import log_checkout_started
        log_checkout_started(request)
    except ImportError:
        pass


def _cart_summary_context(cart):
    delivery_fee = Decimal(str(settings.DELIVERY_FEE))
    cart_subtotal = cart.subtotal()
    return {
        'cart_lines': cart.lines(),
        'cart_subtotal': cart_subtotal,
        'delivery_fee': delivery_fee,
        'cart_total': cart_subtotal + delivery_fee,
    }


def cart_summary_partial(request):
    """Devuelve solo el HTML del resumen del pedido, para refrescarlo por AJAX
    sin recargar la página (y así no perder lo que el cliente ya escribió en
    el formulario de Completa tu pedido)."""
    cart = Cart(request)
    return render(request, 'orders/_summary_partial.html', _cart_summary_context(cart))


def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if cart.is_empty():
            messages.error(request, 'Tu carrito está vacío. Agrega un producto antes de continuar.')
            return redirect('catalog:menu')

        if form.is_valid():
            lines = cart.lines()
            subtotal = cart.subtotal()
            delivery_fee = Decimal(str(settings.DELIVERY_FEE)) if form.cleaned_data['order_type'] == 'delivery' else Decimal('0')

            order = form.save(commit=False)
            order.session_key = request.session.session_key or ''
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
            return redirect('orders:order_success', order_id=order.id)
    else:
        if not cart.is_empty():
            _log_checkout_started(request)
        initial = {'order_type': 'delivery', 'payment_method': 'efectivo'}
        form = OrderForm(initial=initial)

    context = {'form': form, 'pedidos_steps': PEDIDOS_STEPS, **_cart_summary_context(cart)}
    return render(request, 'orders/checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})


@staff_member_required
def manual_sale_create(request):
    if request.method == 'POST':
        form = ManualSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.logged_by = request.user
            sale.save()
            formset = ManualSaleItemFormSet(request.POST, instance=sale)
            if formset.is_valid():
                formset.save()
            messages.success(request, 'Venta de WhatsApp registrada correctamente.')
            return redirect('orders:manual_sale_list')
        formset = ManualSaleItemFormSet(request.POST)
    else:
        form = ManualSaleForm()
        formset = ManualSaleItemFormSet()

    return render(request, 'orders/manual_sale_form.html', {'form': form, 'formset': formset})


@staff_member_required
def manual_sale_list(request):
    sales = ManualSale.objects.prefetch_related('items').all()[:100]
    return render(request, 'orders/manual_sale_list.html', {'sales': sales})
