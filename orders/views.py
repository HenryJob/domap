from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from cart.cart import Cart
from cart.services import summary_context
from .forms import OrderLookupForm, ManualSaleForm, ManualSaleItemFormSet
from .models import Order, ManualSale


def cart_summary_partial(request):
    """Devuelve solo el HTML del resumen del pedido, para refrescarlo por AJAX
    sin recargar la página (y así no perder lo que el cliente ya escribió en
    el formulario de Completa tu pedido)."""
    cart = Cart(request)
    return render(request, 'orders/_summary_partial.html', summary_context(cart))


def checkout(request):
    """El carrito (cart:cart_detail) ya gestiona todo el pedido en una sola
    página; esta ruta se conserva solo por compatibilidad con enlaces
    existentes (footer, favoritos guardados, etc.)."""
    return redirect('cart:cart_detail')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    token = request.GET.get('t', '')
    owns_via_user = request.user.is_authenticated and order.user_id == request.user.id
    owns_via_token = bool(token) and token == order.access_token
    if not (owns_via_user or owns_via_token):
        raise Http404()
    return render(request, 'orders/order_success.html', {'order': order})


def order_lookup(request):
    if request.method == 'POST':
        form = OrderLookupForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(
                id=form.cleaned_data['order_number'],
                phone=form.cleaned_data['phone'],
            ).first()
            if order:
                success_url = reverse('orders:order_success', args=[order.id]) + f'?t={order.access_token}'
                return redirect(success_url)
            messages.error(request, 'No encontramos un pedido con esos datos.')
    else:
        form = OrderLookupForm()
    return render(request, 'orders/order_lookup.html', {'form': form})


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
