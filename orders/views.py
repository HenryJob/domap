from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cart.cart import Cart
from cart.services import summary_context
from .forms import OrderLookupForm, ManualSaleForm, ManualSaleItemFormSet
from .models import Order, ManualSale, DeliveryZone
from .whatsapp import EvolutionClient, EvolutionError, connection_context, normalize_phone


def cart_summary_partial(request):
    """Devuelve solo el HTML del resumen del pedido, para refrescarlo por AJAX
    sin recargar la página (y así no perder lo que el cliente ya escribió en
    el formulario de Completa tu pedido)."""
    cart = Cart(request)
    zone = DeliveryZone.objects.filter(id=request.GET.get('zone'), active=True).first()
    return render(request, 'orders/_summary_partial.html', summary_context(cart, zone))


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
            messages.success(request, 'Venta registrada correctamente.')
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


# --- Conexión de WhatsApp (Evolution API) ---------------------------------
def _safe_next(request, default='orders:whatsapp_connect'):
    """Devuelve la URL de `next` si es del mismo sitio (evita open-redirect);
    si no, la vista por defecto. Sirve para volver al admin tras una acción."""
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(default)


@staff_member_required
def whatsapp_connect(request):
    """Página de staff: muestra el estado y el QR para que el administrador
    conecte su número de WhatsApp escaneándolo con su teléfono."""
    return render(request, 'orders/whatsapp_connect.html', connection_context())


@staff_member_required
def whatsapp_state(request):
    """Endpoint JSON para que la página consulte el estado y refresque el QR
    sin recargar (polling mientras el admin escanea)."""
    ctx = connection_context()
    return JsonResponse({
        'state': ctx['state'],
        'qr_base64': ctx['qr_base64'],
        'error': ctx['error'],
    })


@staff_member_required
@require_POST
def whatsapp_logout(request):
    """Desconecta el número actual (para conectar otro)."""
    try:
        EvolutionClient().logout()
        messages.success(request, 'WhatsApp desconectado. Escanea el QR para conectar un número.')
    except EvolutionError as exc:
        messages.error(request, f'No se pudo desconectar: {exc}')
    return _safe_next(request)


@staff_member_required
@require_POST
def whatsapp_test(request):
    """Envía un mensaje de prueba al número indicado y reporta el resultado
    real (o el error), para diagnosticar el envío sin hacer un pedido."""
    raw = request.POST.get('phone', '')
    number = normalize_phone(raw)
    if not number:
        messages.error(request, f'El número "{raw}" no es válido.')
        return _safe_next(request)

    client = EvolutionClient()
    state = client.connection_state()
    if state != 'open':
        messages.error(request, f'El número no está conectado (estado: {state or "sin instancia"}). Escanea el QR primero.')
        return _safe_next(request)

    try:
        client.send_text(number, '✅ Prueba de Mordé: WhatsApp conectado correctamente.')
        messages.success(request, f'Mensaje de prueba enviado a {number}. Revisa ese WhatsApp.')
    except EvolutionError as exc:
        messages.error(request, f'No se pudo enviar: {exc}')
    return _safe_next(request)


@staff_member_required
@require_POST
def whatsapp_restart(request):
    """Borra y recrea la instancia para forzar un QR nuevo (cuando quedó
    atascada sin generar el código)."""
    try:
        EvolutionClient().restart_instance()
        messages.success(request, 'Instancia reiniciada. Espera unos segundos a que aparezca el nuevo QR.')
    except EvolutionError as exc:
        messages.error(request, f'No se pudo reiniciar: {exc}')
    return _safe_next(request)
